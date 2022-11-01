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
        self.root.geometry("1000x400")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.wm_attributes("-topmost", False)  # Default False

        # ------------------ Frames ------------------
        self.f1_toolbar = ttk.Frame(self.root)
        self.f1_toolbar.pack(side="top", fill="x", expand=False)

        self.f2_textBox = ttk.Frame(self.root)
        self.f2_textBox.pack(side="top", fill="both", expand=True)

        self.f3_toolbar = ttk.Frame(self.root)
        self.f3_toolbar.pack(side="top", fill="x", expand=False)

        self.f4_statusbar = ttk.Frame(self.root)
        self.f4_statusbar.pack(side="bottom", fill="x", expand=False)

        # ------------------ Elements ------------------
        # -- f1_toolbar
        # mode
        self.modeLabel = ttk.Label(self.f1_toolbar, text="Mode:")
        self.modeLabel.pack(side="left", fill="x", padx=5, pady=5, expand=False)

        self.modeCombobox = ttk.Combobox(self.f1_toolbar, values=["Transcribe", "Translate", "Trasncribe and Translate"])
        self.modeCombobox.current(0)
        self.modeCombobox.pack(side="left", fill="x", padx=5, pady=5, expand=False)

        # model
        self.modelLabel = ttk.Label(self.f1_toolbar, text="Model:")
        self.modelLabel.pack(side="left", fill="x", padx=5, pady=5, expand=False)

        self.modelCombobox = ttk.Combobox(self.f1_toolbar, values=["Tiny (~32x speed)", "Base (~16x speed)", "Small (~6x speed)", "Medium (~2x speed)", "Large (1x speed)"])
        self.modelCombobox.current(0)
        self.modelCombobox.pack(side="left", fill="x", padx=5, pady=5, expand=False)
        CreateToolTip(
            self.modelCombobox,
            """
            \rModel size, larger models are more accurate but slower and require more VRAM/CPU power. 
            \rIf you have a low end GPU, use Tiny or Base. Don't use large unless you really need it or have super computer because it's very slow.
            \rModel specs: \n- Tiny: ~1 GB Vram\n- Base: ~1 GB Vram\n- Small: ~2 GB Vram\n- Medium: ~5 GB Vram\n- Large: ~10 GB Vram""".strip(),
            wraplength=400,
        )

        # from
        self.fromLabel = ttk.Label(self.f1_toolbar, text="From:")
        self.fromLabel.pack(side="left", padx=5, pady=5)

        self.selectSourceLang = ttk.Combobox(self.f1_toolbar, values=["auto", "english"])
        self.selectSourceLang.current(0)
        self.selectSourceLang.pack(side="left", padx=5, pady=5)

        # to
        self.toLabel = ttk.Label(self.f1_toolbar, text="To:")
        self.toLabel.pack(side="left", padx=5, pady=5)

        self.selectTargetLang = ttk.Combobox(self.f1_toolbar, values=["english", "spanish"])
        self.selectTargetLang.current(0)
        self.selectTargetLang.pack(side="left", padx=5, pady=5)

        # swap
        self.btnSwap = ttk.Button(self.f1_toolbar, text="Swap")
        self.btnSwap.pack(side="left", padx=5, pady=5)

        # clear
        self.btnClear = ttk.Button(self.f1_toolbar, text="Clear")
        self.btnClear.pack(side="left", padx=5, pady=5)

        # -- f2_textBox
        self.tbLeftBg = tk.Frame(self.f2_textBox, bg="#7E7E7E")
        self.tbLeftBg.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.textBoxLeft = tk.Text(self.tbLeftBg, height=5, width=25, relief="flat", font=("Segoe UI", 10))  # font=("Segoe UI", 10), yscrollcommand=True, relief="flat"
        self.textBoxLeft.bind("<Key>", self.allowedTbKey)
        self.textBoxLeft.pack(padx=1, pady=1, fill="both", expand=True)

        self.tbRightBg = tk.Frame(self.f2_textBox, bg="#7E7E7E")
        self.tbRightBg.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.textBoxRight = tk.Text(self.tbRightBg, height=5, width=25, relief="flat", font=("Segoe UI", 10))
        self.textBoxRight.bind("<Key>", self.allowedTbKey)
        self.textBoxRight.pack(padx=1, pady=1, fill="both", expand=True)

        # -- f3_toolbar
        self.btn_record_stop = ttk.Button(self.f3_toolbar, text="Record Mic")
        self.btn_record_stop.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.btn_record_stop, "Record using your default microphone")

        self.btn_record_stop = ttk.Button(self.f3_toolbar, text="Record PC Sound")
        self.btn_record_stop.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.btn_record_stop, "Record sound from your PC ")

        self.btn_record_file = ttk.Button(self.f3_toolbar, text="Record from file")
        self.btn_record_file.pack(side="left", padx=5, pady=5)
        CreateToolTip(self.btn_record_file, "Record from a file (video or audio)")

        # -- f4_statusbar
        # load bar
        self.loadBar = ttk.Progressbar(self.f4_statusbar, orient="horizontal", length=200, mode="determinate")
        self.loadBar.pack(side="left", padx=5, pady=5, fill="x", expand=True)

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
    # Disable writing, allow copy
    def allowedTbKey(self, event):
        key = event.keysym

        # Allow
        if key.lower() in ["left", "right"]:  # Arrow left right
            return
        if 12 == event.state and key == "a":  # Ctrl + a
            return
        if 12 == event.state and key == "c":  # Ctrl + c
            return

        # If not allowed
        return "break"


if __name__ == "__main__":
    main = MainWindow()
    tray = AppTray()  # Start tray app in the background
    main.root.mainloop()  # Start main app
