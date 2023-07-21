import tkinter as tk
from tkinter import ttk
from typing import Union

from speech_translate.components.custom.message import mbox
from speech_translate._path import app_icon


class CountdownWindow:
    """Countdown window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: Union[tk.Tk, tk.Toplevel], countdown: int, title: str, taskname: str, cancelFunc = None, geometry=None) -> None:
        self.taskname = taskname
        self.master = master
        self.root = tk.Toplevel(master)
        self.root.title(title)
        self.root.transient(master)
        self.root.geometry("300x100")
        self.root.wm_attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.do_nothing_on_close)
        self.root.geometry(geometry if geometry else "+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))
        try:
            self.root.iconbitmap(app_icon)
        except:
            pass

        self.mf = ttk.Frame(self.root)
        self.mf.pack(side="top", fill="both", padx=5, pady=5, expand=True)
        
        self.lbl = ttk.Label(self.mf, text=f"Current Task: {taskname}\nTask will be done in: {countdown}")
        self.lbl.pack(side="top", fill="x", padx=5, pady=5, expand=True)

        if cancelFunc:
            self.btn = ttk.Button(self.mf, text="Cancel", command=cancelFunc)
            self.btn.pack(side="bottom", fill="x", padx=5, pady=5, expand=True)

        self.root.after(1000, self.countdown, countdown)

    # ----------------------------------------------------------------------
    def countdown(self, countdown: int) -> None:
        countdown -= 1
        if countdown > 0:
            self.lbl.configure(text=f"Current Task: {self.taskname}\nTask will be done in: {countdown} seconds")
            self.root.after(1000, self.countdown, countdown)
        else:
            self.root.destroy()
            mbox("Countdown", f"Task {self.taskname} is done", 0, self.master)

    def do_nothing_on_close(self) -> None:
        pass