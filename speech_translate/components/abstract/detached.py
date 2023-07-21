import platform
import tkinter as tk
from tkinter import ttk
from typing import Literal

from speech_translate._path import app_icon
from speech_translate._contants import SUBTITLE_PLACEHOLDER
from speech_translate.globals import sj, gc
from speech_translate.utils.beep import beep
from speech_translate.components.custom.tooltip import CreateToolTip
from speech_translate.components.custom.message import mbox


# Classes
class AbstractDetachedSubtitleWindow:
    """Detached Subtitle Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: tk.Tk, title: str, winType: Literal["tc", "tl"]):
        self.master = master
        self.root = tk.Toplevel(master)
        self.root.title(title)
        self.root.geometry("800x200")
        self.root.wm_withdraw()

        # ------------------ #
        self.winType = winType
        self.winString = ""
        self.x = 0
        self.y = 0
        self.currentOpacity = 1.0
        self.always_on_top = tk.IntVar()
        self.no_tooltip = tk.IntVar()
        self.no_title_bar = tk.IntVar()
        self.click_through = tk.IntVar()
        if winType == "tc":
            gc.ex_tcw = self  # type: ignore
            self.winString = "Transcribe"
        elif winType == "tl":
            gc.ex_tlw = self  # type: ignore
            self.winString = "Translate"

        # Window option
        assert gc.style is not None
        gc.style.configure("TranslatedSub.TFrame", background=sj.cache[f"ex_{winType}_bg"])

        # Top frame
        self.frame_1 = ttk.Frame(self.root, style="TranslatedSub.TFrame")
        self.frame_1.pack(side="top", fill="both", expand=True)
        self.fTooltip = CreateToolTip(self.frame_1, "Right click for interaction menu\n\nTips: You can drag the window by dragging from the label", wrapLength=400)

        self.labelText = tk.Label(
            self.frame_1,
            font=(sj.cache[f"tb_ex_{winType}_font"], sj.cache[f"tb_ex_{winType}_font_size"], "bold" if sj.cache[f"tb_ex_{winType}_font_bold"] else "normal"),
            fg=sj.cache[f"tb_ex_{winType}_font_color"],
            bg=sj.cache[f"tb_ex_{winType}_bg_color"],
            wraplength=600,
            justify="left",
            text=SUBTITLE_PLACEHOLDER # This is to prevent the label from being too small
        )
        self.labelText.pack(side="top")

        self.menuDropdown = tk.Menu(self.root, tearoff=0)

        self.menuDropdown.add_separator()
        self.menuDropdown.add_command(label=title)
        self.menuDropdown.add_separator()
        self.menuDropdown.add_command(label="Close", command=lambda: self.on_closing())
        self.menuDropdown.add_separator()
        self.menuDropdown.add_command(label="Copy", command=lambda: self.copy_tb_content(), accelerator="Alt + C")
        self.menuDropdown.add_separator()
        self.menuDropdown.add_checkbutton(label="Hide Title bar", command=lambda: self.toggle_title_bar(fromKeyBind=False), onvalue=1, offvalue=0, variable=self.no_title_bar, accelerator="Alt + T")
        if platform.system() == "Windows":
            self.click_through.set(int(sj.cache[f"ex_{winType}_click_through"]))
            self.menuDropdown.add_checkbutton(label="Click Through/Transparent", command=lambda: self.toggle_click_through(fromKeyBind=False), onvalue=1, offvalue=0, variable=self.click_through, accelerator="Alt + S")
            self.toggle_click_through(fromKeyBind=False, onInit=True)
        self.menuDropdown.add_checkbutton(label="Always On Top", command=lambda: self.toggle_always_on_top(fromKeyBind=False), onvalue=1, offvalue=0, variable=self.always_on_top, accelerator="Alt + O")
        self.menuDropdown.add_separator()
        self.menuDropdown.add_command(label="Increase Opacity by 0.1", command=lambda: self.increase_opacity(), accelerator="Alt + Mouse Wheel Up")
        self.menuDropdown.add_command(label="Decrease Opacity by 0.1", command=lambda: self.decrease_opacity(), accelerator="Alt + Mouse Wheel Down")
        self.menuDropdown.add_separator()
        self.menuDropdown.add_checkbutton(label="Hide Tooltip", command=lambda: self.toggle_tooltip(fromKeyBind=False), onvalue=1, offvalue=0, variable=self.no_tooltip, accelerator="Alt + X")
        self.menuDropdown.add_separator()
        self.menuDropdown.add_command(label="Keyboard Shortcut Keys", command=lambda: self.show_shortcut_keys())

        # init settings
        self.always_on_top.set(int(sj.cache[f"ex_{winType}_always_on_top"]))
        self.toggle_always_on_top(fromKeyBind=False, onInit=True)

        self.no_title_bar.set(int(sj.cache[f"ex_{winType}_no_title_bar"]))
        self.toggle_title_bar(fromKeyBind=False, onInit=True)

        self.no_tooltip.set(int(sj.cache[f"ex_{winType}_no_tooltip"]))
        self.toggle_tooltip(fromKeyBind=False, onInit=True)

        # ------------------------------------------------------------------------
        # Binds
        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # rclick menu
        self.root.bind("<Button-3>", lambda event: self.menuDropdown.post(event.x_root, event.y_root))

        # keybinds
        if platform.system() == "Windows":
            self.root.bind("<Alt-KeyPress-s>", lambda event: self.toggle_click_through())
        self.root.bind("<Alt-KeyPress-c>", lambda event: self.copy_tb_content())
        self.root.bind("<Alt-KeyPress-t>", lambda event: self.toggle_title_bar())
        self.root.bind("<Alt-KeyPress-o>", lambda event: self.toggle_always_on_top())
        self.root.bind("<Alt-KeyPress-x>", lambda event: self.toggle_tooltip())
        self.root.bind("<Alt-MouseWheel>", lambda event: self.change_opacity(event))

        # bind resize
        self.frame_1.bind("<Configure>", lambda event: self.on_resize(event))

        # bind drag on label text
        self.labelText.bind("<ButtonPress-1>", self.StartMove)
        self.labelText.bind("<ButtonRelease-1>", self.StopMove)
        self.labelText.bind("<B1-Motion>", self.OnMotion)

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except:
            pass

    def on_resize(self, event):
        """
        Method to resize the window.
        """
        # update wraplength
        if event.width >= 300: # minimum width
            self.labelText.config(wraplength=event.width)

    def StartMove(self, event):
        self.x = event.x
        self.y = event.y

    def StopMove(self, event):
        self.x = None
        self.y = None

    def OnMotion(self, event):
        x = event.x_root - self.x - self.labelText.winfo_rootx() + self.labelText.winfo_rootx()
        y = event.y_root - self.y - self.labelText.winfo_rooty() + self.labelText.winfo_rooty()
        self.root.geometry("+%s+%s" % (x, y))

    def check_height_resize(self):
        """
        Method to resize the window height if label text height is more than the window height.
        """
        if self.labelText.winfo_height() > self.frame_1.winfo_height():
            self.root.geometry(f"{self.root.winfo_width()}x{self.labelText.winfo_height()}")

    def show_shortcut_keys(self):
        """
        Method to show shortcut keys.
        """
        mbox(
            "Shortcut keys command for detached window",
            "Alt + scroll to change opacity\nAlt + c to copy text\nAlt + t to toggle title bar (remove title bar)\nAlt + s to toggle click through or transparent window\nAlt + o to toggle always on top\nAlt + x to toggle on/off this tooltip\n\nTips: You can drag the window by dragging from the label",
            0,
        )

    # toggle tooltip
    def toggle_tooltip(self, fromKeyBind=True, onInit=False):
        """
        Method to toggle tooltip.
        If from keybind, then toggle the value manually.
        If on init, then don't save the setting and don't beep.
        """
        if fromKeyBind:
            self.no_tooltip.set(0 if self.no_tooltip.get() == 1 else 1)

        if not onInit:
            beep()
            sj.savePartialSetting(f"ex_{self.winType}_no_tooltip", self.no_tooltip.get())

        if self.no_tooltip.get() == 1:
            self.fTooltip.hidetip()
            self.fTooltip.opacity = 0
        else:
            self.fTooltip.showTip()
            self.fTooltip.opacity = self.currentOpacity

    # show/hide title bar
    def toggle_title_bar(self, fromKeyBind=True, onInit=False):
        """
        Method to toggle title bar.
        If from keybind, then toggle the value manually.
        If on init, then don't save the setting and don't beep.
        """
        if fromKeyBind:
            self.no_title_bar.set(0 if self.no_title_bar.get() == 1 else 1)

        if not onInit:
            beep()
            sj.savePartialSetting(f"ex_{self.winType}_no_title_bar", self.no_title_bar.get())

        self.root.overrideredirect(True if self.no_title_bar.get() == 1 else False)
        
    def toggle_click_through(self, fromKeyBind=True, onInit=False):
        """
        Method to toggle click through. Only on windows.
        If from keybind, then toggle the value manually.
        If on init, then don't save the setting and don't beep.
        """
        if platform.system() != "Windows":
            return
        if fromKeyBind:
            self.click_through.set(0 if self.click_through.get() == 1 else 1)

        if not onInit:
            beep()
            sj.savePartialSetting(f"ex_{self.winType}_click_through", self.click_through.get())

        if self.click_through.get() == 1:
            self.root.wm_attributes("-transparentcolor", sj.cache[f"ex_{self.winType}_bg"])
        else:
            self.root.wm_attributes("-transparentcolor", "")
        
    def toggle_always_on_top(self, fromKeyBind=True, onInit=False):
        """
        Method to toggle always on top.
        If from keybind, then toggle the value manually.
        If on init, then don't save the setting and don't beep.
        """
        if fromKeyBind:
            self.always_on_top.set(0 if self.always_on_top.get() == 1 else 1)

        if not onInit:
            beep()
            sj.savePartialSetting(f"ex_{self.winType}_always_on_top", self.always_on_top.get())

        self.root.wm_attributes("-topmost", True if self.always_on_top.get() == 1 else False)

    def show(self):
        """
        Method to show the window.
        """
        self.root.wm_deiconify()
        self.root.attributes("-alpha", 1)
        self.show_relative_to_master()

    def show_relative_to_master(self):
        x = self.master.winfo_x()
        y = self.master.winfo_y()

        self.root.geometry("+%d+%d" % (x + 100, y + 200))

    def on_closing(self):
        self.root.wm_withdraw()

    def increase_opacity(self):
        """
        Method to increase the opacity of the window by 0.1.
        """
        self.currentOpacity += 0.1
        if self.currentOpacity > 1:
            self.currentOpacity = 1
        self.root.attributes("-alpha", self.currentOpacity)
        self.fTooltip.opacity = self.currentOpacity

    def decrease_opacity(self):
        """
        Method to decrease the opacity of the window by 0.1.
        """
        self.currentOpacity -= 0.1
        if self.currentOpacity < 0.1:
            self.currentOpacity = 0.1
        self.root.attributes("-alpha", self.currentOpacity)
        self.fTooltip.opacity = self.currentOpacity

    # opacity change
    def change_opacity(self, event):
        """
        Method to change the opacity of the window by scrolling.

        Args:
            event (event): event object
        """
        if event.delta > 0:
            self.currentOpacity += 0.1
        else:
            self.currentOpacity -= 0.1

        if self.currentOpacity > 1:
            self.currentOpacity = 1
        elif self.currentOpacity < 0.1:
            self.currentOpacity = 0.1
        self.root.attributes("-alpha", self.currentOpacity)
        self.fTooltip.opacity = self.currentOpacity

    def copy_tb_content(self):
        """
        Method to copy the textbox content to clipboard.
        """
        self.root.clipboard_clear()
        self.root.clipboard_append(self.labelText.cget("text").strip())
