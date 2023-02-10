__all__ = ["CreateToolTip"]
import tkinter as tk


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
