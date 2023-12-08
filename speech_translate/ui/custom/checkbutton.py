from tkinter import BooleanVar, ttk


# pylint: disable=keyword-arg-before-vararg
class CustomCheckButton(ttk.Checkbutton):
    """
    Custom Checkbutton that can be used to invoke a callback when the value changes.
    """
    def __init__(self, master, initial_value: bool, callback=None, state="", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.var = BooleanVar(master, value=initial_value)
        self.configure(variable=self.var)

        if state != "":
            self.configure(state=state)

        if callback:
            self.callback = callback
            self.configure(command=lambda: self.callback(self.get_value()))

    def get_value(self):
        return self.var.get()
