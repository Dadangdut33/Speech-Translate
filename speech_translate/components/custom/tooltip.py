__all__ = ["CreateToolTip", "createMultipleTooltips", "CreateToolTipOnText"]

import tkinter as tk
from tkinter import ttk
from typing import List, Union
from speech_translate.utils.helper import tb_copy_only


class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """

    # ----------------------------------------------------------------------
    def __init__(self, widget, text="widget info", delay=250, wrapLength=180, opacity=1.0, always_on_top=True, center=False):
        self.waitTime = delay  # miliseconds
        self.wrapLength = wrapLength  # pixels
        self.widget = widget
        self.text = text
        self.opacity = opacity
        self.center = center
        self.always_on_top = always_on_top
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.root = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waitTime, self.showTip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showTip(self, event=None):
        x = y = 0
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        # creates a toplevel window
        self.root = tk.Toplevel(self.widget)

        # Make it stay on top
        self.root.wm_attributes("-topmost", self.always_on_top)

        # Make it a little transparent
        self.root.wm_attributes("-alpha", self.opacity)

        # Leaves only the label and removes the app window
        self.root.wm_overrideredirect(True)
        if self.center:
            d = self.root.winfo_width() - self.widget.winfo_width()
            x += d // 2

        self.root.wm_geometry("+%d+%d" % (x, y))

        label = tk.Label(self.root, text=self.text, justify="left", relief="solid", borderwidth=1, wraplength=self.wrapLength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.root
        self.root = None
        if tw:
            tw.destroy()


def createMultipleTooltips(widgets: List[tk.Widget], text: str, delay: int = 250, wrapLength: int = 180, opacity: float = 1.0, always_on_top: bool = True, center: bool = False):
    """
    Create multiple tooltips for a list of widgets
    """
    for widget in widgets:
        CreateToolTip(widget, text, delay, wrapLength, opacity, always_on_top, center)


class CreateToolTipOnText:
    def __init__(self, widget: Union[tk.Text, tk.Entry, ttk.Entry], text: str, delay=250, opacity=0.9, always_on_top=True, geometry=None):
        self.waitTime = delay  # miliseconds
        self.widget = widget
        self.text = text
        self.opacity = opacity
        self.always_on_top = always_on_top
        self.geometry = geometry
        self.widget.bind("<FocusIn>", self.enter)
        self.widget.bind("<FocusOut>", self.leave)

        self.id = None
        self.root = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waitTime, self.showTip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showTip(self, event=None):
        x = y = 0
        x, y, width, _ = self.widget.bbox("insert")  # type: ignore

        # make position to be on the bottom side of the widget
        x += self.widget.winfo_rootx()
        y += self.widget.winfo_rooty() + 20

        # creates a toplevel window
        self.root = tk.Toplevel(self.widget)
        self.root.wm_attributes("-topmost", True)  # Make it stay on top
        self.root.wm_attributes("-alpha", self.opacity)  # Make it a little transparent
        self.root.wm_overrideredirect(True)  # Leaves only the label and removes the app window

        if self.geometry:
            self.root.wm_geometry(f"{self.geometry}+{x}+{y}")  # position
        else:
            self.root.wm_geometry(f"+{x}+{y}")  # position

        self.f_1 = ttk.Frame(self.root)
        self.f_1.pack(fill="both", expand=True, side="top", padx=5, pady=5)

        self.tb = tk.Text(self.f_1, wrap=tk.WORD, font=("Arial", 10))
        self.tb.insert("end", self.text)
        self.tb.pack(fill="both", expand=True, side="left")
        self.tb.bind("<Key>", lambda event: tb_copy_only(event))  # Disable textbox input

        self.scrollbar = ttk.Scrollbar(self.f_1, orient=tk.VERTICAL, command=self.tb.yview)
        self.scrollbar.pack(fill="y", side="right")
        self.tb.config(yscrollcommand=self.scrollbar.set)

    def hidetip(self):
        tw = self.root
        self.root = None
        if tw:
            tw.destroy()
