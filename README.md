>> Motivation Widget

A customizable, borderless desktop widget for Windows, built with Tkinter.  
Easily display motivational quotes, reminders, or notes with rich formatting and persistent state.

>> Features

- **Borderless, draggable, resizable window** (bottom-right grip)
- **Always-on-top toggle** (pin icon)
- **Auto-save text and formatting** (bold, colors, sizes) to JSON
- **Remembers window size, position, colors, border thickness, opacity, and base font**
- **Right-click menu and top toolbar** for styling
- **Choose system fonts** from dropdown; **load a .ttf** via "Font ▸ Load TTF"
- **Customize background, text, accent (caret), and border colors**; border thickness
- **No external packages required** — pure Python and Tkinter

>> Usage

1. **Run the widget:**
    ```shell
    python Widget_front.py
    ```

2. **Customize your note:**
    - Use the toolbar to change font, size, color, and styling.
    - Right-click for quick formatting options.
    - Drag the window or resize from the bottom-right corner.
    - Use the pin icon to toggle always-on-top.

3. **All changes are auto-saved** to `widget_state.json` in the same folder.

>> Requirements

- **Python 3.13+**
- **Windows** (tested)
- No external dependencies

>> Files

- `Widget_front.py` — Main application
- `widget_state.json` — Auto-saved state (created on first run)

>> License

MIT License (see [LICENSE](LICENSE) if provided).

>> Screenshot


<img width="756" height="408" alt="image" src="https://github.com/user-attachments/assets/863bc0d9-87e3-464c-8095-54acc41f2769" />
<img width="1336" height="438" alt="image" src="https://github.com/user-attachments/assets/ed507689-6e81-4ac2-869b-81582ff5afc5" />

---

**Created by
