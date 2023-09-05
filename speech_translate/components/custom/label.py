# make a custom ttk label that have bold font for its title, format is like this:
# [title] text
# combination of 2 packed labels

import tkinter as tk
from tkinter import ttk


class LabelTitleText:
    def __init__(self, master, title, text, **kwargs):
        self.master = master
        self.title = title
        self.text = text
        self.kwargs = kwargs
        self.label = ttk.Label(self.master, **self.kwargs)
        self.lbl_title = ttk.Label(self.label, text=self.title, font=("TkDefaultFont 9 bold"))
        self.lbl_text = ttk.Label(self.label, text=self.text)
        self.lbl_title.pack(side="left")
        self.lbl_text.pack(side="left")

    def pack(self, **kwargs):
        self.label.pack(**kwargs)

    def set_text(self, text):
        self.lbl_text.configure(text=text)

    def set_title(self, title):
        self.lbl_title.configure(text=title)

    def set_title_font(self, font):
        self.lbl_title.configure(font=font)

    def set_text_font(self, font):
        self.lbl_text.configure(font=font)


class DraggableLabel(tk.Label):
    def __init__(self, parent, root, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.root = root
        self.bind("<Button-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.on_motion)
        self.x = 0
        self.y = 0

    def start_move(self, event):
        self.x = event.x_root - self.root.winfo_x()
        self.y = event.y_root - self.root.winfo_y()

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_motion(self, event):
        if self.x is not None and self.y is not None:
            new_x = event.x_root - self.x
            new_y = event.y_root - self.y
            self.root.geometry("+%s+%s" % (new_x, new_y))
