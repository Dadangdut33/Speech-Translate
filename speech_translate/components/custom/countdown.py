import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Union

from speech_translate.components.custom.message import mbox
from speech_translate._path import app_icon


class CountdownWindow:
    """Countdown window"""

    # ----------------------------------------------------------------------
    def __init__(
        self,
        master: Union[tk.Tk, tk.Toplevel],
        countdown: int,
        title: str,
        taskname: str,
        cancelFunc=None,
        geometry=None,
        notify_done=True,
    ) -> None:
        self.taskname = taskname
        self.master = master
        self.root = tk.Toplevel(master)
        self.root.title(title)
        self.root.transient(master)
        self.notify_done = notify_done
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

        self.lbl = ttk.Label(self.mf, text=f"Current Task: {taskname}\nWill be done in: {countdown} seconds")
        self.lbl.pack(side="top", fill="x", padx=5, pady=5, expand=True)

        if cancelFunc:
            self.btn = ttk.Button(self.mf, text="Cancel", command=cancelFunc)
            self.btn.pack(side="bottom", fill="x", padx=5, pady=5, expand=True)

        threading.Thread(target=self.start_counting, args=(countdown,)).start()

    # ----------------------------------------------------------------------
    def start_counting(self, countdown: int) -> None:
        """Start counting down"""
        counter = countdown
        while counter > 0:
            time.sleep(1)
            counter -= 1
            if counter > 0:
                self.lbl.configure(text=f"Current Task: {self.taskname}\nWill be done in: {counter} seconds")
            else:
                self.root.destroy()
                if self.notify_done:
                    mbox("Countdown", f"{self.taskname} is done", 0, self.master)
                break

    def do_nothing_on_close(self) -> None:
        pass
