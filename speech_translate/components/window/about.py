import requests
import tkinter as tk
from tkinter import ttk
from time import sleep
from threading import Thread
from PIL import Image, ImageTk


from speech_translate._version import __version__
from speech_translate.custom_logging import logger
from speech_translate._path import app_icon
from speech_translate._contants import APP_NAME
from speech_translate.globals import gc, sj
from speech_translate.utils.helper import OpenUrl, nativeNotify
from speech_translate.components.custom.tooltip import CreateToolTip


# Classes
class AboutWindow:
    """About Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: tk.Tk):
        self.root = tk.Toplevel(master)
        self.root.title(APP_NAME + " | About")
        self.root.geometry("375x220")
        self.root.wm_withdraw()

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Top frame
        self.f_top = ttk.Frame(self.root, style="Brighter.TFrame")
        self.f_top.pack(side="top", fill="both", expand=True)

        self.f_bot = ttk.Frame(self.root, style="Bottom.TFrame")
        self.f_bot.pack(side="bottom", fill="x", expand=False)

        self.f_bot_l = ttk.Frame(self.f_bot, style="Bottom.TFrame")
        self.f_bot_l.pack(side="left", fill="both", expand=True)

        self.f_bot_r = ttk.Frame(self.f_bot, style="Bottom.TFrame")
        self.f_bot_r.pack(side="right", fill="both", expand=True)

        # Top frame
        try:  # Try catch the logo so if logo not found it can still run
            self.canvasImg = tk.Canvas(self.f_top, width=100, height=100)
            self.canvasImg.pack(side="top", padx=5, pady=5)
            self.imgObj = Image.open(app_icon.replace(".ico", ".png"))
            self.imgObj = self.imgObj.resize((100, 100), Image.ANTIALIAS)

            self.img = ImageTk.PhotoImage(self.imgObj)
            self.canvasImg.create_image(2, 50, anchor=tk.W, image=self.img)
        except Exception:
            self.logoNotFoud = ttk.Label(self.f_top, text="Fail To Load Logo, Logo not found", foreground="red")
            self.logoNotFoud.pack(side="top", padx=5, pady=5)
            self.root.geometry("375x325")

        self.titleLabel = ttk.Label(self.f_top, text="Speech Translate", font=("Helvetica", 12, "bold"), style="BrighterTFrameBg.TLabel")
        self.titleLabel.pack(padx=5, pady=2, side="top")

        self.contentLabel = ttk.Label(self.f_top, text="An open source Speech Transcription and Translation tool.\nMade using Whisper OpenAI and some translation API.", style="BrighterTFrameBg.TLabel")
        self.contentLabel.pack(padx=5, pady=0, side="top")

        # Label for version
        self.versionLabel = ttk.Label(self.f_bot_l, text=f"Version: {__version__}", font=("Segoe UI", 8))
        self.versionLabel.pack(padx=5, pady=2, ipadx=0, side="left")

        self.checkUpdateLabelText = "Click to check for update"
        self.checkUpdateLabelFg = "blue"
        self.checkUpdateLabelFunc = self.check_for_update
        self.checkUpdateLabel = ttk.Label(self.f_bot_l, text=self.checkUpdateLabelText, foreground=self.checkUpdateLabelFg, font=("Segoe UI", 8), cursor="hand2")
        self.checkUpdateLabel.pack(padx=5, pady=0, side="left")
        self.checkUpdateLabel.bind("<Button-1>", self.checkUpdateLabelFunc)
        self.tooltipCheckUpdate = CreateToolTip(self.checkUpdateLabel, "Click to check for update")

        # Button
        self.okBtn = ttk.Button(self.f_bot_r, text="Ok", command=self.on_closing, width=10, style="Accent.TButton")
        self.okBtn.pack(padx=5, pady=5, side="right")

        # ------------------------------
        gc.about = self
        self.checking = False
        self.checkingOnStart = False
        self.checkedGet = None

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except:
            pass

        # ------------------------------
        # on init
        self.onInit()

    # check update on start
    def onInit(self):
        if sj.cache["checkUpdateOnStart"]:
            logger.info("Checking for update on start")
            self.checkingOnStart = True
            self.check_for_update()

    # Show/Hide
    def show(self):
        self.root.after(0, self.root.deiconify)

    def on_closing(self):
        self.root.wm_withdraw()

    # Open link
    def open_dl_link(self, _event=None):
        OpenUrl("https://github.com/Dadangdut33/Speech-Translate/releases/tag/latest")

    def check_for_update(self, _event=None, onStart=False):
        if self.checking:
            return

        self.checking = True
        self.checkUpdateLabelText = "Checking..."
        self.checkUpdateLabelFg = "black"
        self.tooltipCheckUpdate.text = "Checking... Please wait"
        self.checkUpdateLabel.configure(text=self.checkUpdateLabelText, foreground=self.checkUpdateLabelFg)
        self.root.update()
        logger.info("Checking for update...")

        Thread(target=self.req_update_check, daemon=True).start()

    def req_update_check(self):
        try:
            # request to github api, compare version. If not same tell user to update
            req = requests.get("https://api.github.com/repos/Dadangdut33/Speech-Translate/releases/latest")

            if req is not None and req.status_code == 200:
                data = req.json()
                latest_version = str(data["tag_name"])
                if __version__ < latest_version:
                    logger.info(f"New version found: {latest_version}")
                    self.checkUpdateLabelText = "New version available"
                    self.checkUpdateLabelFg = "blue"
                    self.checkUpdateLabelFunc = self.open_dl_link
                    self.tooltipCheckUpdate.text = "Click to go to the latest release page"
                    nativeNotify("New version available", "Visit the repository to download the latest update")
                else:
                    logger.info("No update available")
                    self.checkUpdateLabelText = "You are using the latest version"
                    self.checkUpdateLabelFg = "green"
                    self.checkUpdateLabelFunc = self.check_for_update
                    self.tooltipCheckUpdate.text = "Up to date"
            else:
                logger.warning("Failed to check for update")
                self.checkUpdateLabelText = "Fail to check for update!"
                self.checkUpdateLabelFg = "red"
                self.checkUpdateLabelFunc = self.check_for_update
                self.tooltipCheckUpdate.text = "Click to try again"
                if not self.checkingOnStart:  # suppress error if checking on start
                    nativeNotify("Fail to check for update!", "Click to try again")

            self.checkUpdateLabel.configure(text=self.checkUpdateLabelText, foreground=self.checkUpdateLabelFg)
            self.checkUpdateLabel.bind("<Button-1>", self.checkUpdateLabelFunc)

            self.checking = False
        except Exception as e:
            logger.exception(e)
        finally:
            self.checking = False
