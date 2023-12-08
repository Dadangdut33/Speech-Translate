from tkinter import TclError, Text, Tk, Toplevel, messagebox, ttk
from typing import List, Literal, Optional, Union

from speech_translate._path import p_app_icon
from speech_translate.utils.helper import tb_copy_only

opened: List = []


class MBoxText:
    """
    A kind of message box that suppose to show a lot of text
    """
    def __init__(self, mbox_id: str, parent: Union[Tk, Toplevel], title: str, text: str, geometry=None) -> None:
        # Check if already opened
        if mbox_id in opened:
            return

        opened.append(mbox_id)
        self.mbox_id = mbox_id
        self.root = Toplevel(parent)
        self.root.title(title)
        self.root.transient(parent)
        relative_pos = f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}"
        self.root.geometry(geometry + relative_pos if geometry else relative_pos)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.minsize(200, 200)

        self.f_1 = ttk.Frame(self.root)
        self.f_1.pack(fill="both", expand=True, side="top", padx=5, pady=5)

        self.tb = Text(self.f_1, wrap="word", font=("Arial", 10))
        self.tb.insert("end", text)
        self.tb.bind( # bind scrollwheel to change font size
            "<Control-MouseWheel>", lambda event: self.increase_font_size() if event.delta > 0 else self.lower_font_size()
        )
        self.tb.bind("<Key>", tb_copy_only)  # Disable textbox input
        self.tb.pack(fill="both", expand=True, side="left")

        self.scrollbar = ttk.Scrollbar(self.f_1, orient="vertical", command=self.tb.yview)
        self.scrollbar.pack(fill="y", side="right")
        self.tb.configure(yscrollcommand=self.scrollbar.set)
        self.sb_width = self.scrollbar.winfo_width()

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(p_app_icon)
        except Exception:
            pass

    def lower_font_size(self):
        self.current_font_size -= 1
        if self.current_font_size < 3:
            self.current_font_size = 3
        self.tb.configure(font=("Arial", self.current_font_size))

    def increase_font_size(self):
        self.current_font_size += 1
        if self.current_font_size > 20:
            self.current_font_size = 20
        self.tb.configure(font=("Arial", self.current_font_size))

    def on_close(self):
        try:
            opened.remove(self.mbox_id)
        except ValueError:
            pass

        try:
            self.root.destroy()
        except TclError:
            pass


def mbox(title: str, text: str, style: Literal[0, 1, 2, 3], parent: Optional[Union[Tk, Toplevel]] = None):
    """Message Box, made simpler
    ##  Styles:
    ##  0 : info
    ##  1 : warning
    ##  2 : error
    ##  3 : Yes No
    """
    if style == 0:
        return messagebox.showinfo(title, text, parent=parent)  # Return ok x same as ok
    elif style == 1:
        return messagebox.showwarning(title, text, parent=parent)  # Return ok x same as ok
    elif style == 2:
        return messagebox.showerror(title, text, parent=parent)  # Return ok x same as ok
    elif style == 3:
        return messagebox.askyesno(title, text, parent=parent)  # Return True False, x can't be clicked
