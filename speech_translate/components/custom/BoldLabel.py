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
        self.label_title = ttk.Label(self.label, text=self.title, font=("TkDefaultFont 9 bold"))
        self.label_text = ttk.Label(self.label, text=self.text)
        self.label_title.pack(side="left")
        self.label_text.pack(side="left")

    def pack(self, **kwargs):
        self.label.pack(**kwargs)

    def set_text(self, text):
        self.label_text.config(text=text)

    def set_title(self, title):
        self.label_title.config(text=title)

    def set_title_font(self, font):
        self.label_title.config(font=font)

    def set_text_font(self, font):
        self.label_text.config(font=font)
