__all__ = ["tk_tooltip", "Tooltip", "tk_tooltips", "CreateToolTipOnText"]

from tkinter import Entry, Label, Text, Toplevel, Widget, ttk
from typing import List, Union


def tb_copy_only(event):
    key = event.keysym

    # Allow
    allowed_event = [4, 8, 12]
    if key.lower() in ["left", "right"]:  # Arrow left right
        return
    if event.state in allowed_event and key.lower() == "a":  # Ctrl + a
        return
    if event.state in allowed_event and key.lower() == "c":  # Ctrl + c
        return

    # If not allowed
    return "break"


class Tooltip(object):
    """
    create a tooltip for a given widget
    """

    # ----------------------------------------------------------------------
    def __init__(
        self,
        widget,
        text: str,
        delay: int = 250,
        wrap_len: int = 180,
        opacity: float = 1.0,
        always_on_top: bool = True,
        center: bool = False,
    ):
        self.delay = delay  # miliseconds
        self.wrap_len = wrap_len  # pixels
        self.widget = widget
        self.text = text
        self.opacity = opacity
        self.center = center
        self.always_on_top = always_on_top
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.after_id = None
        self.root = None
        try:
            self.widget.configure(cursor="question_arrow")
        except Exception:
            pass

    def enter(self, _event=None):
        self.schedule()

    def leave(self, _event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.after_id = self.widget.after(self.delay, self.show_tip)

    def unschedule(self):
        after_id = self.after_id
        self.after_id = None
        if after_id:
            self.widget.after_cancel(after_id)

    def show_tip(self, _event=None):
        x = y = 0
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        # creates a toplevel window
        self.root = Toplevel(self.widget)

        # Make it stay on top
        self.root.wm_attributes("-topmost", self.always_on_top)

        # Make it a little transparent
        self.root.wm_attributes("-alpha", self.opacity)

        # Leaves only the label and removes the app window
        self.root.wm_overrideredirect(True)
        if self.center:
            d = self.root.winfo_width() - self.widget.winfo_width()
            x += d // 2

        self.root.wm_geometry(f"+{x}+{y}")

        label = Label(self.root, text=self.text, justify="left", relief="solid", borderwidth=1, wraplength=self.wrap_len)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.root
        self.root = None
        if tw:
            tw.destroy()


def tk_tooltip(
    widget: Union[Widget, ttk.Widget],
    text: str,
    delay: int = 250,
    wrap_len: int = 180,
    opacity: float = 1.0,
    always_on_top: bool = True,
    center: bool = False,
):
    """
    Create a tooltip for a given widget
    """
    return Tooltip(widget, text, delay, wrap_len, opacity, always_on_top, center)


def tk_tooltips(
    widgets: List[Widget],
    text: str,
    delay: int = 250,
    wrap_len: int = 180,
    opacity: float = 1.0,
    always_on_top: bool = True,
    center: bool = False,
):
    """
    Create multiple tooltips for a list of widgets
    """
    tooltips = []
    for widget in widgets:
        tooltips.append(tk_tooltip(widget, text, delay, wrap_len, opacity, always_on_top, center))

    return tooltips


class CreateToolTipOnText:
    """
    Tooltip on text widget, shown below it
    """
    def __init__(
        self,
        widget: Union[Text, Entry, ttk.Entry],
        text: str,
        delay=250,
        opacity=0.9,
        always_on_top=True,
        geometry=None,
        auto_width=True,
        focus_out_bind=None
    ):
        self.delay = delay  # miliseconds
        self.widget = widget
        self.text = text
        self.opacity = opacity
        self.always_on_top = always_on_top
        self.geometry = geometry
        self.auto_width = auto_width
        self.focus_out_bind = focus_out_bind
        self.widget.bind("<FocusIn>", self.enter)
        self.widget.bind("<FocusOut>", self.leave)
        self.focused = False
        self.showing = False

        self.after_id = None
        self.root = None

    def enter(self, _event=None):
        self.focused = True
        self.schedule()

    def leave(self, _event=None):
        self.focused = False
        self.unschedule()
        self.widget.after(self.delay, self.hidetip)
        if self.focus_out_bind:
            self.focus_out_bind()

    def schedule(self):
        self.unschedule()
        self.after_id = self.widget.after(self.delay, self.show_tip)

    def unschedule(self):
        after_id = self.after_id
        self.after_id = None
        if after_id:
            self.widget.after_cancel(after_id)

    def show_tip(self, _event=None):
        # pylint: disable=attribute-defined-outside-init
        if self.showing:  # still showing
            return

        self.showing = True

        # make position to be on the bottom side of the widget
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + 20

        # creates a toplevel window
        self.root = Toplevel(self.widget)
        self.root.wm_attributes("-topmost", True)  # Make it stay on top
        self.root.wm_attributes("-alpha", self.opacity)  # Make it a little transparent
        self.root.wm_overrideredirect(True)  # Leaves only the label and removes the app window

        if self.geometry:
            if self.auto_width:
                self.geometry = f"{self.widget.winfo_width()}x{self.geometry.split('x')[1]}"

            self.root.wm_geometry(f"{self.geometry}+{x}+{y}")  # position
        else:
            self.root.wm_geometry(f"+{x}+{y}")  # position

        self.f_1 = ttk.Frame(self.root)
        self.f_1.pack(fill="both", expand=True, side="top", padx=5, pady=5)

        self.tb = Text(self.f_1, wrap="word", font=("Arial", 10))
        self.tb.insert("end", self.text)
        self.tb.bind("<Key>", tb_copy_only)  # Disable textbox input
        self.tb.bind("<FocusIn>", self.make_focus)
        self.tb.bind("<Button-1>", self.make_focus)
        self.tb.pack(fill="both", expand=True, side="left")

        self.sb = ttk.Scrollbar(self.f_1, orient="vertical", command=self.tb.yview)
        self.sb.pack(fill="y", side="right")
        self.sb.bind("<FocusIn>", self.make_focus)
        self.sb.bind("<Button-1>", self.make_focus)
        self.tb.configure(yscrollcommand=self.sb.set)

    def make_focus(self, _event):
        self.focused = True

    def hidetip(self):
        if self.focused:  # still focused
            return

        self.showing = False
        tw = self.root
        self.root = None
        if tw:
            tw.destroy()
