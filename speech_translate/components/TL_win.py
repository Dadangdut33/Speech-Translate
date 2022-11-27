import sys
import tkinter as tk
import tkinter.ttk as ttk

sys.path.append("..")
from Globals import fJson, gClass, app_icon
from .Tooltip import CreateToolTip
from utils.Beep import beep


# Classes
class TlsWindow:
    """Detached Translated Window"""

    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Translated Speech")
        self.root.geometry("600x160")
        self.root.wm_withdraw()
        self.currentOpacity = 1.0
        self.always_on_top = False
        self.tooltip_disabled = False
        self.hidden_top = False
        gClass.detached_tlw = self  # type: ignore

        # Top frame
        self.frame_1 = ttk.Frame(self.root)
        self.frame_1.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.fTooltip = CreateToolTip(self.frame_1, "Commands:\n-Alt + scroll to change opacity\n-Alt + t to toggle top window\n-Alt + o to toggle always on top\n-Alt + x to toggle on/off this tooltip")

        # textbox and its scrollbar
        self.scrollbar = ttk.Scrollbar(self.frame_1, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.textbox = tk.Text(
            self.frame_1,
            wrap=tk.WORD,
            font=(fJson.settingCache["textbox"]["detached_tl"]["font"], fJson.settingCache["textbox"]["detached_tl"]["font_size"]),
            fg=fJson.settingCache["textbox"]["detached_tl"]["font_color"],
            bg=fJson.settingCache["textbox"]["detached_tl"]["bg_color"],
        )
        self.textbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.textbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.textbox.yview)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.root.bind("<Alt-KeyPress-t>", lambda event: self.toggle_hidden_top())
        self.root.bind("<Alt-KeyPress-o>", lambda event: self.toggle_always_on_top())
        self.root.bind("<Alt-KeyPress-x>", lambda event: self.disable_tooltip())
        self.root.bind("<Alt-MouseWheel>", lambda event: self.change_opacity(event))

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except:
            pass

    # disable tooltip
    def disable_tooltip(self):
        beep()
        self.tooltip_disabled = not self.tooltip_disabled
        if self.tooltip_disabled:
            self.fTooltip.hidetip()
            self.fTooltip.opacity = 0
        else:
            self.fTooltip.showTip()
            self.fTooltip.opacity = self.currentOpacity

    # show/hide top
    def toggle_hidden_top(self):
        beep()
        self.hidden_top = not self.hidden_top
        self.root.overrideredirect(self.hidden_top)

    # Stay on top
    def toggle_always_on_top(self):
        beep()
        self.always_on_top = not self.always_on_top
        self.root.wm_attributes("-topmost", self.always_on_top)

    # Show/Hide
    def show(self):
        self.root.attributes("-alpha", 1)
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    # opacity change
    def change_opacity(self, event):
        if event.delta > 0:
            self.currentOpacity += 0.05
        else:
            self.currentOpacity -= 0.05

        if self.currentOpacity > 1:
            self.currentOpacity = 1
        elif self.currentOpacity < 0.1:
            self.currentOpacity = 0.1

        self.root.attributes("-alpha", self.currentOpacity)
        self.fTooltip.opacity = self.currentOpacity
