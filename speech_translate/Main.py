from sys import exit
import tkinter as tk
import tkinter.ttk as ttk
from notifypy import Notify
from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image, ImageDraw

from components.MBox import Mbox
from Globals import gClass


class AppTray:
    """
    tray app
    """

    def __init__(self):
        # -- Tray
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
        self.icon = icon("Speech Translate", self.create_image(64, 64, "black", "white"), "Speech Translate", self.menu)
        self.icon.run_detached()

    # -- Open app
    def open_app(self):
        assert gClass.mw is not None  # Show main window
        gClass.mw.show_window()

    # Exit app by flagging runing false to stop main loop
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

        self.root.title("Speech Translate")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.wm_attributes("-topmost", False)  # Default False

        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Menubar
        self.menubar = tk.Menu(self.root)
        self.fileMenu = tk.Menu(self.menubar, tearoff=0)
        self.fileMenu.add_command(label="Hide", command=lambda: self.root.withdraw())
        self.fileMenu.add_command(label="Exit", command=self.quit_app)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)

        self.root.config(menu=self.menubar)

        # ------------------ Variables ------------------
        # Flags
        self.notifiedHidden = False
        gClass.mw = self  # type: ignore

        # ------------------ Main ------------------
        # Start polling
        self.root.after(1000, self.isRunningPoll)

    # Quit the app
    def quit_app(self):
        if gClass.tray:
            gClass.tray.icon.stop()
        self.root.destroy()
        try:
            exit()
        except SystemExit:
            pass

    def show_window(self):
        self.root.after(0, self.root.deiconify)

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


if __name__ == "__main__":
    main = MainWindow()
    tray = AppTray()  # Start tray app in the background
    main.root.mainloop()  # Start main app
