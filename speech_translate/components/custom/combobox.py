from tkinter import ttk
from typing import List


class ComboboxTypeOnCustom(ttk.Combobox):
    """
    Combobox that allows to type on custom value
    Designed for integer values
    """
    def __init__(self, master, values: List[str], vmin: str, vmax: str, save_func, initial_value: str, first_prev="1"):
        super().__init__(master, values=values.copy() + ["Custom"])
        self.values = values
        self.vmin = vmin
        self.vmax = vmax
        self.prev = None
        self.save_func = save_func
        self.first_prev = first_prev

        if initial_value in values:
            # selection in cb - readonly
            self.set(initial_value)
            self.configure(state='readonly')
        else:
            if not initial_value.isdigit():
                raise ValueError("Initial value must be a string of digit")

            # custom
            self.prev = initial_value
            self.set(initial_value)
            self.configure(state='normal')

        # Bind the select event to the on_select function
        self.bind("<<ComboboxSelected>>", self.on_select)

        # Bind the KeyRelease event to capture text input
        self.bind("<KeyRelease>", self.on_key_release)

    def on_select(self, event):
        selected_item = self.get()
        if selected_item == "Custom":
            if self.prev is None:
                self.prev = self.first_prev
                self.set(self.prev)
                self.save_func(self.prev)
            else:
                self.set(self.prev)
                self.save_func(self.prev)

            self.configure(state='normal')
        else:
            self.set(selected_item)
            self.configure(state='readonly')

    def on_key_release(self, event):
        typed_text = self.get()
        if typed_text.isdigit():
            value = int(typed_text)
            if value < int(self.vmin):
                self.set(self.vmin)
                self.prev = self.vmin
            elif value > int(self.vmax):
                self.set(self.vmax)
                self.prev = self.vmax
            else:
                self.prev = typed_text

            self.save_func(self.prev)
        elif typed_text == "":
            self.set(self.vmin)
            self.prev = self.vmin
            self.save_func(self.prev)
        else:
            self.set(self.prev)
