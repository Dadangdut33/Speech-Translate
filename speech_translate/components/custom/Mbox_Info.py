import tkinter as tk
from tkinter import ttk
from typing import Union, List
from speech_translate._path import app_icon

opened: List[int] = []


class Mbox_InfoTb:
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
        self.f_1.pack(fill=tk.BOTH, expand=True, side=tk.TOP, padx=5, pady=5)

        self.f_2 = ttk.Frame(self.root)
        self.f_2.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM, padx=5, pady=5)

        self.tb = tk.Text(self.f_1, wrap=tk.WORD, font=("Arial", 10))
        self.tb.insert(tk.END, text)
        self.tb.bind("<Control-MouseWheel>", lambda event: self.increase_font_size() if event.delta > 0 else self.lower_font_size())  # bind scrollwheel to change font size
        self.tb.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.scrollbar = ttk.Scrollbar(self.f_1, orient=tk.VERTICAL, command=self.tb.yview)
        self.scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.tb.config(yscrollcommand=self.scrollbar.set)

        self.btn = ttk.Button(self.f_2, text="OK", command=self.on_close)
        self.btn.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, padx=5, pady=5)

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
            print(e)
            pass

        try:
            self.root.destroy()
        except tk.TclError as e:
            print(e)
            pass
