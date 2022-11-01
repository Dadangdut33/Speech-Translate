from sys import exit
import tkinter as tk
import tkinter.ttk as ttk
from notifypy import Notify
from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image, ImageDraw

from components.MBox import Mbox
from utils.Tooltip import CreateToolTip 
from Globals import gClass, version


class AppTray:
    """
    Tray app
    """

    def __init__(self):
        self.icon: icon = None  # type: ignore
        self.menu: menu = None  # type: ignore
        self.menu_items: tuple[item, item] = None  # type: ignore
        gClass.tray = self  # type: ignore
        self.create_tray()

    # -- Tray icon
    def create_image(self, width, height, color1, color2):
        # !Generic icon for now
        # TODO: Make icon
        # Generate an image and draw a pattern
        image = Image.new("RGB", (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
        dc.rectangle((0, height // 2, width // 2, height), fill=color2)

        return image

    # -- Create tray
    def create_tray(self):
        self.menu_items = (item("Show", self.open_app), item("Exit", self.exit_app))
        self.menu = menu(*self.menu_items)
        self.icon = icon("Speech Translate", self.create_image(64, 64, "black", "white"), f"Speech Translate V{version}", self.menu)
        self.icon.run_detached()

    # -- Open app
    def open_app(self):
        assert gClass.mw is not None  # Show main window
        gClass.mw.show_window()

    # -- Exit app by flagging runing false to stop main loop
    def exit_app(self):
        gClass.running = False


class MainWindow:
    """
    Main window of the app
    """

    def __init__(self):
        # ------------------ Window ------------------
        # UI
        self.root = tk.Tk()

        self.root.title(f"Speech Translate")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.wm_attributes("-topmost", False)  # Default False

        # ------------------ Frames ------------------
        self.f1_toolbar = ttk.Frame(self.root)
        self.f1_toolbar.pack(side="top", fill="x", expand=True)

        self.f2_textBox = ttk.Frame(self.root)
        self.f2_textBox.pack(side="top", fill="both", expand=True)

        self.f3_toolbar = ttk.Frame(self.root)
        self.f3_toolbar.pack(side="top", fill="x", expand=True)

        self.f4_textbox = ttk.Frame(self.root)
        self.f4_textbox.pack(side="top", fill="both", expand=True)

        self.f5_statusbar = ttk.Frame(self.root)
        self.f5_statusbar.pack(side="bottom", fill="x", expand=True)

        # ------------------ Elements ------------------
        # f1_toolbar
        self.btn_record_stop = ttk.Button(self.f1_toolbar, text="Record")
        self.btn_record_stop.pack(side="left", padx=5, pady=5)

        self.btn_record_file = ttk.Button(self.f1_toolbar, text="Record from file")
        self.btn_record_file.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.btn_record_file, "Record from a file (video or audio)")

        # f2_textBox
        self.tbTopBg = tk.Frame(self.f2_textBox, bg="#7E7E7E")
        self.tbTopBg.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        self.textBoxTop = tk.Text(self.tbTopBg, height=5, width=100, relief="flat")  # font=("Segoe UI", 10), yscrollcommand=True, relief="flat"
        self.textBoxTop.pack(padx=1, pady=1, fill="both", expand=True)

        # f3_toolbar
        self.fromLabel = ttk.Label(self.f3_toolbar, text="From:")
        self.fromLabel.pack(side="left", padx=5, pady=5)

        self.selectSourceLang = ttk.Combobox(
            self.f3_toolbar,
            values=["auto", "english"],
        )
        self.selectSourceLang.pack(side="left", padx=5, pady=5)

        self.toLabel = ttk.Label(self.f3_toolbar, text="To:")
        self.toLabel.pack(side="left", padx=5, pady=5)
        self.selectTargetLang = ttk.Combobox(
            self.f3_toolbar,
            values=["english", "spanish"],
        )
        self.selectTargetLang.pack(side="left", padx=5, pady=5)

        self.btnSwap = ttk.Button(self.f3_toolbar, text="Swap")
        self.btnSwap.pack(side="left", padx=5, pady=5)

        self.btnClear = ttk.Button(self.f3_toolbar, text="Clear")
        self.btnClear.pack(side="left", padx=5, pady=5)

        # f4_textbox
        self.tbBottomBg = tk.Frame(self.f4_textbox, bg="#7E7E7E")
        self.tbBottomBg.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        self.textBoxBottom = tk.Text(self.tbBottomBg, height=5, width=100, relief="flat")
        self.textBoxBottom.pack(padx=1, pady=1, fill="both", expand=True)

        # f5_statusbar
        # load bar
        self.loadBar = ttk.Progressbar(self.f5_statusbar, orient="horizontal", length=200, mode="determinate")
        self.loadBar.pack(side="left", padx=5, pady=5)

        # ------------------ Menubar ------------------
        self.menubar = tk.Menu(self.root)
        self.fmView = tk.Menu(self.menubar, tearoff=0)
        self.fmView.add_checkbutton(label="Stay on top", command=self.toggle_always_on_top)
        self.fmView.add_separator()
        self.fmView.add_command(label="Hide", command=lambda: self.root.withdraw())
        self.fmView.add_command(label="Exit", command=self.quit_app)
        self.menubar.add_cascade(label="File", menu=self.fmView)

        self.fmHelp = tk.Menu(self.menubar, tearoff=0)
        self.fmHelp.add_command(label="About", command=self.open_About)  # placeholder for now
        self.menubar.add_cascade(label="Help", menu=self.fmHelp)

        self.root.config(menu=self.menubar)

        # ------------------ Variables ------------------
        # Flags
        self.alwaysOnTop = False
        self.notifiedHidden = False
        gClass.mw = self  # type: ignore

        # ------------------ Bind keys ------------------
        self.root.bind("<F1>", self.open_About)

        # ------------------ Poll ------------------
        # Start polling
        self.root.after(1000, self.isRunningPoll)

    # ------------------ Handle Main window ------------------
    # Quit the app
    def quit_app(self):
        if gClass.tray:
            gClass.tray.icon.stop()
        self.root.destroy()
        try:
            exit()
        except SystemExit:
            pass

    # Show window
    def show_window(self):
        self.root.after(0, self.root.deiconify)

    # Close window
    def on_close(self):
        # Only show notification once
        if not self.notifiedHidden:
            notification = Notify()
            notification.title = "Speech Translate"
            notification.message = "The app is still running in the background."
            notification.send()
            self.notifiedHidden = True

        self.root.withdraw()

    # check if the app is running or not, used to close the app from tray
    def isRunningPoll(self):
        if not gClass.running:
            self.quit_app()

        self.root.after(1000, self.isRunningPoll)

    # Toggle Stay on top
    def toggle_always_on_top(self):
        self.alwaysOnTop = not self.alwaysOnTop
        self.root.wm_attributes("-topmost", self.alwaysOnTop)

    # ------------------ Open External Window ------------------
    def open_About(self, event=None):
        Mbox("About", "Speech Translate", 0)  # placeholder for now

    # --------------------------------------


if __name__ == "__main__":
    main = MainWindow()
    tray = AppTray()  # Start tray app in the background
    main.root.mainloop()  # Start main app
