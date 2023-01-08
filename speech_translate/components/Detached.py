import tkinter as tk
import tkinter.ttk as ttk
import platform
from typing import Literal

from speech_translate.Globals import fJson, gClass, app_icon
from speech_translate.utils.Beep import beep
from .Tooltip import CreateToolTip
from .MBox import Mbox


# Classes
class AbstractDetachedWindow:
    """Detached Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master, title: str, winType: Literal["tc", "tl"]):
        self.root = tk.Toplevel(master)
        self.root.title(title)
        self.root.geometry("600x160")
        self.root.wm_withdraw()

        # ------------------ #
        self.winType = winType
        self.x = 0
        self.y = 0
        self.curText = ""
        self.updateTb = False
        self.getTbVal = False
        self.currentOpacity = 1.0
        self.always_on_top = tk.IntVar()
        self.tooltip_disabled = tk.IntVar()
        self.hidden_top = tk.IntVar()
        self.clickThrough = tk.IntVar()
        if winType == "tc":
            gClass.ex_tcw = self  # type: ignore
        elif winType == "tl":
            gClass.ex_tlw = self  # type: ignore

        # ------------------ #
        # Top frame
        self.frame_1 = ttk.Frame(self.root)
        self.frame_1.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.fTooltip = CreateToolTip(self.frame_1, "Right click for interaction menu\n\nTips: You can drag the window by dragging from the label", wrapLength=400)

        self.labelText = tk.Label(
            self.frame_1,
            font=(fJson.settingCache[f"tb_ex_{winType}_font"], fJson.settingCache[f"tb_ex_{winType}_font_size"], "bold" if fJson.settingCache[f"tb_ex_{winType}_font_bold"] else "normal"),
            fg=fJson.settingCache[f"tb_ex_{winType}_font_color"],
            bg=fJson.settingCache[f"tb_ex_{winType}_bg_color"],
            wraplength=600,
            justify=tk.LEFT,
        )
        self.labelText.pack(side=tk.TOP)

        self.menuDropdown = tk.Menu(self.root, tearoff=0)
        self.menuDropdown.add_command(label="Copy", command=lambda: self.copy_tb_content(), accelerator="Alt + C")
        self.menuDropdown.add_separator()
        self.menuDropdown.add_checkbutton(label="Hide Title bar", command=lambda: self.toggle_hidden_top(False), onvalue=1, offvalue=0, variable=self.hidden_top, accelerator="Alt + T")
        if platform.system() == "Windows":
            self.menuDropdown.add_checkbutton(label="Click Through/Transparent", command=lambda: self.toggle_click_through(False), onvalue=1, offvalue=0, variable=self.clickThrough, accelerator="Alt + S")
        self.menuDropdown.add_checkbutton(label="Always On Top", command=lambda: self.toggle_always_on_top(False), onvalue=1, offvalue=0, variable=self.always_on_top, accelerator="Alt + O")
        self.menuDropdown.add_separator()
        self.menuDropdown.add_command(label="Increase Opacity by 0.1", command=lambda: self.increase_opacity(), accelerator="Alt + Mouse Wheel Up")
        self.menuDropdown.add_command(label="Decrease Opacity by 0.1", command=lambda: self.decrease_opacity(), accelerator="Alt + Mouse Wheel Down")
        self.menuDropdown.add_separator()
        self.menuDropdown.add_checkbutton(label="Hide Tooltip", command=lambda: self.disable_tooltip(False), onvalue=1, offvalue=0, variable=self.tooltip_disabled, accelerator="Alt + X")
        self.menuDropdown.add_separator()
        self.menuDropdown.add_command(label="Keyboard Shortcut Keys", command=lambda: self.show_shortcut_keys())

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
        self.root.bind("<Alt-KeyPress-t>", lambda event: self.toggle_hidden_top())
        self.root.bind("<Alt-KeyPress-o>", lambda event: self.toggle_always_on_top())
        self.root.bind("<Alt-KeyPress-x>", lambda event: self.disable_tooltip())
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

        # ------------------ Polling ------------------
        self.root.after(100, self.textUpdatePoll)

    # curText polling
    def textUpdatePoll(self):
        """
        Method to update the textbox value in a thread without runtimeerror.
        Updating is done by setting flag to true and then checking it here.
        """
        if self.getTbVal:
            self.curText = self.labelText.cget("text")
            self.getTbVal = False

        if self.updateTb:
            self.labelText.config(text=self.curText)
            self.check_height_resize()
            self.updateTb = False

        self.root.after(100, self.textUpdatePoll)

    def update_text(self):
        """
        Method to update the textbox value in a thread without runtimeerror.
        Setting flag to true will update the textbox value in the pollingStuff method.
        """
        self.updateTb = True

    def get_cur_text(self):
        """
        Method to update self.curText value with the textbox value in a thread without runtimeerror.
        Setting flag to true will update the self.curText value in the pollingStuff method.
        """
        self.getTbVal = True

    def on_resize(self, event):
        """
        Method to resize the window.
        """
        # update wraplength
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
        Mbox(
            "Shortcut keys command for detached window",
            "Alt + scroll to change opacity\nAlt + c to copy text\nAlt + t to toggle title bar (remove title bar)\nAlt + s to toggle click through or transparent window\nAlt + o to toggle always on top\nAlt + x to toggle on/off this tooltip\n\nTips: You can drag the window by dragging from the label",
            0,
        )

    # disable tooltip
    def disable_tooltip(self, fromKeyBind=True):
        """
        Method to toggle tooltip.
        """
        beep()
        if fromKeyBind:
            self.tooltip_disabled.set(0 if self.tooltip_disabled.get() == 1 else 1)

        if self.tooltip_disabled.get() == 1:
            self.fTooltip.hidetip()
            self.fTooltip.opacity = 0
        else:
            self.fTooltip.showTip()
            self.fTooltip.opacity = self.currentOpacity

    # show/hide top
    def toggle_hidden_top(self, fromKeyBind=True):
        """
        Method to toggle hidden top.
        """
        beep()
        if fromKeyBind:
            self.hidden_top.set(0 if self.hidden_top.get() == 1 else 1)

        self.root.overrideredirect(True if self.hidden_top.get() == 1 else False)

    def toggle_click_through(self, fromKeyBind=True):
        """
        Method to toggle click through. Only on windows.
        """
        beep()
        if fromKeyBind:
            self.clickThrough.set(0 if self.clickThrough.get() == 1 else 1)

        if self.clickThrough.get() == 1:
            self.root.wm_attributes("-transparentcolor", self.root["bg"])
        else:
            self.root.wm_attributes("-transparentcolor", "")

    def toggle_always_on_top(self, fromKeyBind=True):
        """
        Method to toggle always on top.
        """

        beep()
        if fromKeyBind:
            self.always_on_top.set(0 if self.always_on_top.get() == 1 else 1)

        self.root.wm_attributes("-topmost", True if self.always_on_top.get() == 1 else False)

    def show(self):
        """
        Method to show the window.
        """
        self.root.wm_deiconify()
        self.root.attributes("-alpha", 1)
        if platform.system() == "Windows":
            self.root.attributes("-transparentcolor", "")

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
