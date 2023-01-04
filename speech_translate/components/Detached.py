import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal

from speech_translate.Globals import fJson, gClass, app_icon
from speech_translate.utils.Beep import beep
from .Tooltip import CreateToolTip


# Classes
class AbstractDetachedWindow:
    """Detached Window"""

    # ----------------------------------------------------------------------
    def __init__(self, title, winType: Literal["tc", "tl"]):
        self.root = tk.Tk()
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
        self.always_on_top = False
        self.tooltip_disabled = False
        self.hidden_top = False
        self.clickThrough = False
        if winType == "tc":
            gClass.ex_tcw = self  # type: ignore
        elif winType == "tl":
            gClass.ex_tlw = self  # type: ignore

        # Top frame
        self.frame_1 = ttk.Frame(self.root)
        self.frame_1.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.fTooltip = CreateToolTip(
            self.frame_1,
            "Commands:\n-Alt + scroll to change opacity\n-Alt + t to toggle top window (remove top bar)\n-Alt + s to toggle click through or transparent window\n-Alt + o to toggle always on top\n-Alt + c to copy text\n-Alt + x to toggle on/off this tooltip",
            wrapLength=400,
        )

        self.labelText = tk.Label(
            self.frame_1,
            font=(fJson.settingCache[f"tb_ex_{winType}_font"], fJson.settingCache[f"tb_ex_{winType}_font_size"], "bold" if fJson.settingCache[f"tb_ex_{winType}_font_bold"] else "normal"),
            fg=fJson.settingCache[f"tb_ex_{winType}_font_color"],
            bg=fJson.settingCache[f"tb_ex_{winType}_bg_color"],
            wraplength=600,
            justify=tk.LEFT,
        )
        self.labelText.pack(side=tk.TOP)
        self.labelText.config(text="Hello, good morning, this is a test. I want to see what happened to the detach window. Go to the detach window. Check check. Hello. Go to the detach window.")

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.root.bind("<Alt-KeyPress-s>", lambda event: self.toggle_click_through())
        self.root.bind("<Alt-KeyPress-c>", lambda event: self.copy_tb_content())
        self.root.bind("<Alt-KeyPress-t>", lambda event: self.toggle_hidden_top())
        self.root.bind("<Alt-KeyPress-o>", lambda event: self.toggle_always_on_top())
        self.root.bind("<Alt-KeyPress-x>", lambda event: self.disable_tooltip())
        self.root.bind("<Alt-MouseWheel>", lambda event: self.change_opacity(event))

        # remove focus from textbox
        self.root.bind("<FocusIn>", lambda event: self.root.focus_force())

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

    def get_cur_text(self, update=False):
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
        self.root.attributes("-transparentcolor", "")
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    # opacity change
    def change_opacity(self, event):
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
        self.root.clipboard_clear()
        self.root.clipboard_append(self.labelText.cget("text").strip())

    def toggle_click_through(self):
        beep()
        self.clickThrough = not self.clickThrough
        if self.clickThrough:
            self.root.wm_attributes("-transparentcolor", self.root["bg"])
        else:
            self.root.wm_attributes("-transparentcolor", "")
