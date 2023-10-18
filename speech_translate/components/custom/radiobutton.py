from tkinter import ttk


class CustomRadioButton(ttk.Radiobutton):
    def __init__(self, master, initial_value: bool, callback, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.callback = callback
        if initial_value:
            self.invoke()
        else:
            self.invoke()
            self.invoke()

        self.configure(command=lambda: self.callback(self.get_value()))

    def get_value(self):
        return self.instate(["selected"])
