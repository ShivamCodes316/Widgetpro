# -*- coding: utf-8 -*-
"""
Motivation Widget — Tkinter
Features:
- Borderless, draggable, resizable (bottom-right grip)
- Always-on-top toggle (pin icon)
- Auto-save text + formatting (bold, colors, sizes) to JSON
- Remembers window size/position, colors, border thickness, opacity, base font
- Right-click menu + top toolbar for styling
- Choose system fonts from dropdown; load a .ttf via "Font ▸ Load TTF"
- Customize background / text / accent (caret) / border colors; border thickness
Tested on Python 3.13 (Windows). No external packages required.
"""

import json, os, sys
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from tkinter import font as tkfont

APP_NAME = "Motivation Widget"
STATE_FILE = "widget_state.json"

# ----------------------------
# Utilities for state storage
# ----------------------------
def safe_int(x, default):
    try: return int(x)
    except: return default

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def ensure_state_file(path):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load_state(path):
    ensure_state_file(path)
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_state(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ----------------------------
# Default settings
# ----------------------------
DEFAULTS = {
    "geometry": "600x320+100+100",
    "always_on_top": True,
    "alpha": 1.0,
    "colors": {
        "background": "#0A1F44",   # navy
        "text":       "#FFFFFF",   # white
        "accent":     "#FFD700",   # gold (caret)
        "border":     "#222222"    # dark border
    },
    "border_thickness": 2,
    "base_font": {"family": "Segoe UI", "size": 16, "weight": "normal", "slant": "roman"},
    "content": {
        "text": "",
        "tags": {}  # tagname -> {"config": {...}, "ranges": [["1.0","1.4"], ...]}
    }
}

# ----------------------------
# Main App
# ----------------------------
class MotivationWidget:
    def __init__(self, master):
        self.root = master
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)

        # load state
        self.state = load_state(STATE_FILE)
        self._apply_defaults()

        # outer border via root bg; inner frame uses background color
        self.root.config(bg=self.state["colors"]["border"])
        try:
            self.root.geometry(self.state["geometry"])
        except:
            self.root.geometry(DEFAULTS["geometry"])

        self.root.attributes("-topmost", bool(self.state["always_on_top"]))
        self.root.attributes("-alpha", float(self.state["alpha"]))

        # ---- Layout
        self.container = tk.Frame(self.root, bg=self.state["colors"]["background"], bd=self.state["border_thickness"])
        self.container.pack(expand=True, fill="both")

        # Title bar (drag handle + controls)
        self.titlebar = tk.Frame(self.container, bg=self.state["colors"]["background"])
        self.titlebar.pack(fill="x")

        self.title_label = tk.Label(self.titlebar, text=APP_NAME, fg="#B8C1D1",
                                    bg=self.state["colors"]["background"], font=("Segoe UI", 10, "bold"))
        self.title_label.pack(side="left", padx=(12, 8), pady=6)

        # Toolbar (font + style)
        self.toolbar = tk.Frame(self.container, bg=self.state["colors"]["background"])
        self.toolbar.pack(fill="x", padx=10, pady=(0, 6))

        # Font family dropdown
        self.font_families = sorted(set(tkfont.families()))
        self.base_font_var = tk.StringVar(value=self.state["base_font"]["family"])
        self.font_combo = ttk.Combobox(self.toolbar, values=self.font_families, textvariable=self.base_font_var, state="readonly", width=24)
        self.font_combo.pack(side="left", padx=(0, 6))
        self.font_combo.bind("<<ComboboxSelected>>", self.on_base_font_change)

        # Font size spinner
        self.base_size_var = tk.IntVar(value=self.state["base_font"]["size"])
        self.size_spin = tk.Spinbox(self.toolbar, from_=8, to=96, width=4, textvariable=self.base_size_var, command=self.on_base_font_change)
        self.size_spin.pack(side="left", padx=(0, 6))

        # Bold button
        self.bold_btn = tk.Button(self.toolbar, text="B", width=3, command=self.apply_bold)
        self.bold_btn.pack(side="left", padx=2)

        # +/- size buttons for selection
        self.big_btn = tk.Button(self.toolbar, text="A+", width=3, command=lambda: self.apply_size(delta=2))
        self.big_btn.pack(side="left", padx=2)
        self.small_btn = tk.Button(self.toolbar, text="A−", width=3, command=lambda: self.apply_size(delta=-2))
        self.small_btn.pack(side="left", padx=2)

        # Color for selection
        self.color_btn = tk.Button(self.toolbar, text="Color", command=self.apply_color)
        self.color_btn.pack(side="left", padx=6)

        # Background / Text / Accent / Border pickers
        self.bg_btn = tk.Button(self.toolbar, text="BG", command=lambda: self.pick_color("background"))
        self.bg_btn.pack(side="left", padx=2)
        self.txt_btn = tk.Button(self.toolbar, text="Text", command=lambda: self.pick_color("text"))
        self.txt_btn.pack(side="left", padx=2)
        self.caret_btn = tk.Button(self.toolbar, text="Caret", command=lambda: self.pick_color("accent"))
        self.caret_btn.pack(side="left", padx=2)
        self.border_btn = tk.Button(self.toolbar, text="Border", command=lambda: self.pick_color("border"))
        self.border_btn.pack(side="left", padx=2)

        # Border thickness
        self.border_var = tk.IntVar(value=int(self.state["border_thickness"]))
        self.border_spin = tk.Spinbox(self.toolbar, from_=0, to=16, width=3, textvariable=self.border_var, command=self.apply_border)
        self.border_spin.pack(side="left", padx=(6, 2))

        # Opacity
        self.alpha_var = tk.DoubleVar(value=float(self.state["alpha"]))
        self.alpha_scale = tk.Scale(self.toolbar, from_=0.5, to=1.0, resolution=0.05, orient="horizontal",
                                    variable=self.alpha_var, command=self.on_alpha_change, length=100)
        self.alpha_scale.pack(side="left", padx=(8, 2))

        # Font menu
        self.font_menu_btn = tk.Menubutton(self.toolbar, text="Font ▾", relief="raised")
        self.font_menu = tk.Menu(self.font_menu_btn, tearoff=0)
        self.font_menu.add_command(label="Load TTF...", command=self.load_ttf)
        self.font_menu_btn.config(menu=self.font_menu)
        self.font_menu_btn.pack(side="left", padx=(6, 2))

        # Pin (always-on-top) toggle
        self.pin_btn = tk.Button(self.toolbar, text=("📌" if self.state["always_on_top"] else "📍"),
                                 command=self.toggle_pin, width=3)
        self.pin_btn.pack(side="left", padx=(8, 2))

        # Save button (manual save)
        self.save_btn = tk.Button(self.toolbar, text="Save", command=self.save_all)
        self.save_btn.pack(side="left", padx=6)

        # Close button
        self.close_btn = tk.Button(self.titlebar, text="✕", fg="red",
                                   bg=self.state["colors"]["background"], bd=0, command=self.on_close)
        self.close_btn.pack(side="right", padx=10)

        # Minimize (hide) button — withdraw window; restore via rerun
        self.min_btn = tk.Button(self.titlebar, text="—", fg="#CCCCCC",
                                 bg=self.state["colors"]["background"], bd=0, command=self.on_minimize)
        self.min_btn.pack(side="right")

        # Base font for text area
        self.base_font = tkfont.Font(family=self.state["base_font"]["family"],
                                     size=self.state["base_font"]["size"],
                                     weight=self.state["base_font"]["weight"],
                                     slant=self.state["base_font"]["slant"])

        # Text widget
        self.text = tk.Text(
            self.container,
            wrap="word",
            font=self.base_font,
            bg=self.state["colors"]["background"],
            fg=self.state["colors"]["text"],
            insertbackground=self.state["colors"]["accent"],
            relief="flat",
            padx=18, pady=14
        )
        self.text.pack(expand=True, fill="both")

        # Right-click context menu
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Bold", command=self.apply_bold)
        self.menu.add_command(label="Color…", command=self.apply_color)
        self.menu.add_command(label="Increase Size", command=lambda: self.apply_size(delta=2))
        self.menu.add_command(label="Decrease Size", command=lambda: self.apply_size(delta=-2))
        self.text.bind("<Button-3>", self._show_menu)

        # Dragging on titlebar
        self.titlebar.bind("<Button-1>", self._start_move)
        self.titlebar.bind("<B1-Motion>", self._do_move)

        # Resize grip (bottom-right)
        self.resize_grip = tk.Frame(self.container, cursor="bottom_right_corner",
                                    bg=self.state["colors"]["background"], width=14, height=14)
        self.resize_grip.place(relx=1.0, rely=1.0, x=-14, y=-14, anchor="se")
        self.resize_grip.bind("<Button-1>", self._start_resize)
        self.resize_grip.bind("<B1-Motion>", self._do_resize)

        # Load content + tags
        self._load_content()

        # Autosave on typing / geometry changes
        self.text.bind("<KeyRelease>", lambda e: self.save_all())
        self.root.bind("<Configure>", self._on_configure)

        # Improve focus/selection
        self.text.focus_set()

    # ---------- State helpers ----------
    def _apply_defaults(self):
        # merge defaults with loaded state
        def deep_merge(dst, src):
            for k, v in src.items():
                if isinstance(v, dict):
                    dst[k] = deep_merge(dst.get(k, {}), v)
                else:
                    dst.setdefault(k, v)
            return dst

        self.state = deep_merge(self.state if isinstance(self.state, dict) else {}, DEFAULTS)

    # ---------- Window movement ----------
    def _start_move(self, e):
        self._drag_offx = e.x_root - self.root.winfo_x()
        self._drag_offy = e.y_root - self.root.winfo_y()

    def _do_move(self, e):
        x = e.x_root - self._drag_offx
        y = e.y_root - self._drag_offy
        self.root.geometry(f"+{x}+{y}")

    # ---------- Resize ----------
    def _start_resize(self, e):
        self._start_w = self.root.winfo_width()
        self._start_h = self.root.winfo_height()
        self._start_rx = e.x_root
        self._start_ry = e.y_root

    def _do_resize(self, e):
        dx = e.x_root - self._start_rx
        dy = e.y_root - self._start_ry
        w = clamp(self._start_w + dx, 320, 1600)
        h = clamp(self._start_h + dy, 180, 1200)
        self.root.geometry(f"{w}x{h}")

    # ---------- Context menu ----------
    def _show_menu(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    # ---------- Style actions on selection ----------
    def _get_selection(self):
        try:
            start = self.text.index("sel.first")
            end   = self.text.index("sel.last")
            return start, end
        except tk.TclError:
            return None, None

    def apply_bold(self):
        start, end = self._get_selection()
        if not start: return
        # make a bold font derived from current base font
        b = tkfont.Font(self.text, self.text.cget("font"))
        b.configure(weight="bold")
        self.text.tag_configure("bold", font=b)
        self.text.tag_add("bold", start, end)
        self.save_all()

    def apply_size(self, delta=2):
        start, end = self._get_selection()
        if not start: return
        base = tkfont.Font(self.text, self.text.cget("font"))
        new_size = clamp(base.cget("size") + delta, 8, 96)
        f = tkfont.Font(self.text, self.text.cget("font"))
        f.configure(size=new_size)
        tag_name = f"size_{new_size}"
        self.text.tag_configure(tag_name, font=f)
        self.text.tag_add(tag_name, start, end)
        self.save_all()

    def apply_color(self):
        start, end = self._get_selection()
        if not start: return
        color = colorchooser.askcolor(title="Pick text color")[1]
        if not color: return
        tag_name = f"color_{color}"
        self.text.tag_configure(tag_name, foreground=color)
        self.text.tag_add(tag_name, start, end)
        self.save_all()

    # ---------- Color / border / alpha ----------
    def pick_color(self, which):
        color = colorchooser.askcolor(title=f"Pick {which} color")[1]
        if not color: return
        self.state["colors"][which] = color
        if which == "background":
            self.container.config(bg=color)
            self.titlebar.config(bg=color)
            self.toolbar.config(bg=color)
            self.title_label.config(bg=color)
            self.close_btn.config(bg=color)
            self.min_btn.config(bg=color)
            self.resize_grip.config(bg=color)
            self.text.config(bg=color)
        elif which == "text":
            self.text.config(fg=color)
        elif which == "accent":
            self.text.config(insertbackground=color)
        elif which == "border":
            self.root.config(bg=color)
        self.save_all()

    def apply_border(self):
        val = safe_int(self.border_var.get(), 2)
        self.state["border_thickness"] = val
        # simulate border using internal padding frame thickness
        # (container already acts like inner panel; set its 'bd' via config doesn't show,
        # so we rebuild pack to keep it simple)
        self.container.pack_forget()
        self.container.pack(expand=True, fill="both", padx=val, pady=val)
        self.save_all()

    def on_alpha_change(self, _evt=None):
        a = float(self.alpha_var.get())
        self.state["alpha"] = a
        self.root.attributes("-alpha", a)
        self.save_all()

    def toggle_pin(self):
        cur = bool(self.state["always_on_top"])
        new = not cur
        self.state["always_on_top"] = new
        self.root.attributes("-topmost", new)
        self.pin_btn.config(text=("📌" if new else "📍"))
        self.save_all()

    # ---------- Fonts ----------
    def on_base_font_change(self, _evt=None):
        fam = self.base_font_var.get()
        size = safe_int(self.base_size_var.get(), 16)
        size = clamp(size, 8, 96)
        self.base_font.configure(family=fam, size=size)
        self.text.configure(font=self.base_font)
        self.state["base_font"]["family"] = fam
        self.state["base_font"]["size"] = size
        self.save_all()

    def load_ttf(self):
        path = filedialog.askopenfilename(
            title="Load a .ttf font",
            filetypes=[("TrueType Font", "*.ttf"), ("All files", "*.*")]
        )
        if not path: return
        # On Windows, simply placing TTF in same folder and referring by family name works
        # But we can also use tkfont.Font with "file" option via named font trick:
        try:
            # Attempt to register by creating a temp named font
            tmp = tkfont.Font(file=path)
            fam = tmp.actual("family")
            if fam not in self.font_families:
                self.font_families.append(fam)
                self.font_families.sort()
                self.font_combo["values"] = self.font_families
            self.base_font_var.set(fam)
            self.on_base_font_change()
        except Exception as e:
            messagebox.showerror("Font load failed", f"Could not load font:\n{e}")

    # ---------- Minimize / Close ----------
    def on_minimize(self):
        self.save_all()
        self.root.withdraw()  # hide; relaunch script to show again

    def on_close(self):
        self.save_all()
        self.root.destroy()

    # ---------- Persist content + tags ----------
    def _font_to_dict(self, f: tkfont.Font):
        return {
            "family": f.actual("family"),
            "size":   f.actual("size"),
            "weight": f.actual("weight"),
            "slant":  f.actual("slant"),
            "underline": int(f.actual("underline")),
            "overstrike": int(f.actual("overstrike")),
        }

    def _dict_to_font(self, d: dict):
        return tkfont.Font(
            family=d.get("family", "Segoe UI"),
            size=safe_int(d.get("size", 16), 16),
            weight=d.get("weight", "normal"),
            slant=d.get("slant", "roman"),
            underline=int(d.get("underline", 0)),
            overstrike=int(d.get("overstrike", 0)),
        )

    def _capture_tags(self):
        tags = {}
        for tag in self.text.tag_names():
            if tag in ("sel",):
                continue
            cfg = {}
            # capture font if set
            try:
                font_name = self.text.tag_cget(tag, "font")
                if font_name:
                    f = tkfont.Font(name=font_name, exists=True)
                    cfg["font"] = self._font_to_dict(f)
            except:
                pass
            # capture colors
            fg = self.text.tag_cget(tag, "foreground")
            bg = self.text.tag_cget(tag, "background")
            if fg: cfg["foreground"] = fg
            if bg: cfg["background"] = bg

            # capture ranges
            ranges = []
            tag_ranges = self.text.tag_ranges(tag)
            for i in range(0, len(tag_ranges), 2):
                start = tag_ranges[i]
                end   = tag_ranges[i+1]
                ranges.append([str(start), str(end)])

            if cfg or ranges:
                tags[tag] = {"config": cfg, "ranges": ranges}
        return tags

    def _apply_tags_from_state(self, tags):
        # configure and add back ranges
        for tag, data in tags.items():
            cfg = data.get("config", {})
            if "font" in cfg:
                f = self._dict_to_font(cfg["font"])
                self.text.tag_configure(tag, font=f)
            if "foreground" in cfg:
                self.text.tag_configure(tag, foreground=cfg["foreground"])
            if "background" in cfg:
                self.text.tag_configure(tag, background=cfg["background"])
            for start, end in data.get("ranges", []):
                try:
                    self.text.tag_add(tag, start, end)
                except:
                    pass

    def _load_content(self):
        content = self.state.get("content", {})
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content.get("text", ""))
        self._apply_tags_from_state(content.get("tags", {}))
        # apply container padding based on border thickness
        bt = int(self.state.get("border_thickness", 2))
        self.container.pack_forget()
        self.container.pack(expand=True, fill="both", padx=bt, pady=bt)

    def save_all(self):
        # text + tags
        self.state["content"]["text"] = self.text.get("1.0", "end-1c")
        self.state["content"]["tags"] = self._capture_tags()
        # colors and basic props
        self.state["colors"]["background"] = self.container["bg"]
        self.state["colors"]["text"] = self.text["fg"]
        self.state["colors"]["accent"] = self.text["insertbackground"]
        self.state["colors"]["border"] = self.root["bg"]
        self.state["border_thickness"] = int(self.border_var.get())
        self.state["alpha"] = float(self.alpha_var.get())
        self.state["always_on_top"] = bool(self.root.attributes("-topmost"))
        # base font
        self.state["base_font"]["family"] = self.base_font.actual("family")
        self.state["base_font"]["size"]   = self.base_font.actual("size")
        self.state["base_font"]["weight"] = self.base_font.actual("weight")
        self.state["base_font"]["slant"]  = self.base_font.actual("slant")
        # geometry
        try:
            self.state["geometry"] = self.root.geometry()
        except:
            pass
        save_state(STATE_FILE, self.state)

    def _on_configure(self, _evt=None):
        # save geometry changes (throttle is fine to omit for simplicity)
        try:
            self.state["geometry"] = self.root.geometry()
            save_state(STATE_FILE, self.state)
        except:
            pass


def main():
    root = tk.Tk()
    app = MotivationWidget(root)
    root.mainloop()

if __name__ == "__main__":
    main()
