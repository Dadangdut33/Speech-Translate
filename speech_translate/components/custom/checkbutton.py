from tkinter import ttk


class CustomCheckButton(ttk.Checkbutton):
    def __init__(self, master, initial_value: bool, callback=None, state="", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        if initial_value:
            self.invoke()
        else:
            self.invoke()
            self.invoke()

        if state != "":
            self.configure(state=state)

        if callback:
            self.callback = callback
            self.configure(command=lambda: self.callback(self.get_value()))

    def get_value(self):
        return self.instate(["selected"])
