import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Literal, Union, Optional, List
from speech_translate._path import app_icon

opened: List[int] = []


class MBoxText:
    def __init__(self, id: int, parent: Union[tk.Tk, tk.Toplevel], title: str, text: str, geometry=None) -> None:
        # Check if already opened
        for i in opened:
            if i == id:
                return

        self.id = id
        self.root = tk.Toplevel(parent)
        self.root.title(title)
        self.root.transient(parent)
        self.root.geometry(geometry if geometry else "+{}+{}".format(parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.f_1 = ttk.Frame(self.root)
        self.f_1.pack(fill="both", expand=True, side="top", padx=5, pady=5)

        self.f_2 = ttk.Frame(self.root)
        self.f_2.pack(fill="both", expand=True, side="bottom", padx=5, pady=5)
     
        self.tb = tk.Text(self.f_1, wrap=tk.WORD, font=("Arial", 10))
        self.tb.insert("end", text)
        self.tb.bind("<Control-MouseWheel>", lambda event: self.increase_font_size() if event.delta > 0 else self.lower_font_size())  # bind scrollwheel to change font size
        self.tb.pack(fill="both", expand=True, side="left")

        self.scrollbar = ttk.Scrollbar(self.f_1, orient=tk.VERTICAL, command=self.tb.yview)
        self.scrollbar.pack(fill="y", side="right")
        self.tb.config(yscrollcommand=self.scrollbar.set)

        self.btn = ttk.Button(self.f_2, text="OK", command=self.on_close)
        self.btn.pack(fill="both", expand=True, side="right", padx=5, pady=5)

        opened.append(id)

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except:
            pass

    def lower_font_size(self):
        self.currentFontSize -= 1
        if self.currentFontSize < 3:
            self.currentFontSize = 3
        self.tb.configure(font=("Arial", self.currentFontSize))

    def increase_font_size(self):
        self.currentFontSize += 1
        if self.currentFontSize > 20:
            self.currentFontSize = 20
        self.tb.configure(font=("Arial", self.currentFontSize))

    def on_close(self):
        try:
            id = self.id
            opened.remove(id)
        except ValueError as e:
            pass

        try:
            self.root.destroy()
        except tk.TclError as e:
            pass

def mbox(title: str, text: str, style: Literal[0, 1, 2, 3], parent: Optional[Union[tk.Tk, tk.Toplevel]] = None):
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


# Testing
if __name__ == "__main__":
    root = tk.Tk()

    # -----------------
    mbox("Info", "Info no parent", 0)
    mbox("Warning", "Warning no parent", 1)
    mbox("Error", "Error no parent", 2)
    print(mbox("Yes No", "Yes No no parent", 3))

    # -----------------
    mbox("Info", "Info with parent", 0, parent=root)
    mbox("Warning", "Warning with parent", 1, parent=root)
    mbox("Error", "Error with parent", 2, parent=root)
    print(mbox("Yes No", "Yes No with parent", 3, parent=root))

    root.destroy()
