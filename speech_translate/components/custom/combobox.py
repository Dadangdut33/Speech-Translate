from tkinter import ttk


class ComboboxTypeOnCustom(ttk.Combobox):
    def __init__(self, master, values, save_func, initial_value=None):
        super().__init__(master, values=values)
        self.values = values
        self.prev = None
        self.save_func = save_func

        if initial_value is not None:
            if initial_value in values:
                self.set(initial_value)
            else:
                raise ValueError(f"Invalid initial value: {initial_value}")

        self.configure(state='readonly')  # Initially set to read-only

        # Bind the select event to the on_select function
        self.bind("<<ComboboxSelected>>", self.on_select)

        # Bind the KeyRelease event to capture text input
        self.bind("<KeyRelease>", self.on_key_release)

    def on_select(self, event):
        selected_item = self.get()
        if selected_item == "Custom":
            if self.prev is None:
                self.prev = "1"
                self.set("1")
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
            if value < 1:
                self.set("1")
                self.prev = "1"
            elif value > 25:
                self.set("25")
                self.prev = "25"
            else:
                self.prev = typed_text

            self.save_func(self.prev)
        elif typed_text == "":
            self.set("1")
            self.prev = "1"
            self.save_func(self.prev)
        else:
            self.set(self.prev)
