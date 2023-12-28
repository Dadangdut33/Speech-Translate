from threading import Thread
from tkinter import Canvas, Tk, Toplevel, ttk

from loguru import logger
from PIL import Image, ImageTk
from requests import get

from speech_translate._constants import APP_NAME
from speech_translate._path import p_app_icon
from speech_translate._version import __version__
from speech_translate.linker import bc, sj
from speech_translate.ui.custom.tooltip import tk_tooltip
from speech_translate.utils.helper import native_notify, no_connection_notify, open_url


# Classes
class AboutWindow:
    """About Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: Tk):
        self.root = Toplevel(master)
        self.root.title(APP_NAME + " | About")
        self.root.geometry("375x220")
        self.root.minsize(375, 220)
        self.root.maxsize(500, 300)
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
            self.canvas_img = Canvas(self.f_top, width=100, height=100)
            self.canvas_img.pack(side="top", padx=5, pady=5)
            self.img_obj = Image.open(p_app_icon.replace(".ico", ".png"))
            self.img_obj = self.img_obj.resize((100, 100))

            self.img = ImageTk.PhotoImage(self.img_obj)
            self.canvas_img.create_image(2, 50, anchor="w", image=self.img)
        except Exception:
            self.lbl_not_found = ttk.Label(self.f_top, text="Fail To Load Logo, Logo not found", foreground="red")
            self.lbl_not_found.pack(side="top", padx=5, pady=5)
            self.root.geometry("375x325")

        self.lbl_title = ttk.Label(
            self.f_top, text="Speech Translate", font=("Helvetica", 12, "bold"), style="BrighterTFrameBg.TLabel"
        )
        self.lbl_title.pack(padx=5, pady=2, side="top")

        self.lbl_content = ttk.Label(
            self.f_top,
            text="An open source Speech Transcription and Translation tool.\n"
            "Made using Whisper OpenAI and some translation API.",
            style="BrighterTFrameBg.TLabel",
        )
        self.lbl_content.pack(padx=5, pady=0, side="top")

        # Label for version
        self.f_bot_l_1 = ttk.Frame(self.f_bot_l, style="Bottom.TFrame")
        self.f_bot_l_1.pack(side="top", fill="both", expand=True)

        self.f_bot_l_2 = ttk.Frame(self.f_bot_l, style="Bottom.TFrame")
        self.f_bot_l_2.pack(side="top", fill="both", expand=True)

        self.lbl_version = ttk.Label(self.f_bot_l_1, text=f"Version: {__version__}", font=("Segoe UI", 8))
        self.lbl_version.pack(padx=5, pady=2, ipadx=0, side="left")

        self.update_text = "Click to check for update"
        self.update_fg = "blue"
        self.update_func = self.check_for_update
        self.lbl_check_update = ttk.Label(
            self.f_bot_l_1, text=self.update_text, foreground=self.update_fg, font=("Segoe UI", 8), cursor="hand2"
        )
        self.lbl_check_update.pack(padx=5, pady=0, side="left")
        self.lbl_check_update.bind("<Button-1>", self.update_func)
        self.tooltip_check_update = tk_tooltip(self.lbl_check_update, "Click to check for update")

        self.lbl_cuda = ttk.Label(self.f_bot_l_2, text="Device: " + bc.cuda)
        self.lbl_cuda.pack(padx=5, pady=2, ipadx=0, side="left")
        tk_tooltip(
            self.lbl_cuda,
            "Detected CUDA Device.\n\nNote that your device still need to be compatible with " \
            "the CUDA version used by the program (CUDA 11.8) in order to be used.",
        )

        # Button
        self.btn_ok = ttk.Button(self.f_bot_r, text="Ok", command=self.on_closing, width=10, style="Accent.TButton")
        self.btn_ok.pack(padx=5, pady=5, side="right")

        # ------------------------------
        bc.about = self
        self.checking = False
        self.checking_on_start = False

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(p_app_icon)
        except Exception:
            pass

        # ------------------------------
        # on init
        self.__on_init()

    # check update on start
    def __on_init(self):
        if sj.cache["checkUpdateOnStart"]:
            logger.info("Checking for update on start")
            self.checking_on_start = True
            self.check_for_update()

    # Show/Hide
    def show(self):
        self.root.deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    # Open link
    def open_dl_link(self, _event=None):
        open_url("https://github.com/Dadangdut33/Speech-Translate/releases/tag/latest")

    def check_for_update(self, _event=None, notify_up_to_date=False):
        if self.checking:
            return

        self.checking = True
        self.update_text = "Checking..."
        self.update_fg = "black"
        self.tooltip_check_update.text = "Checking... Please wait"
        self.lbl_check_update.configure(text=self.update_text, foreground=self.update_fg)
        self.root.update()
        logger.info("Checking for update...")

        Thread(target=self.req_update_check, daemon=True, args=[notify_up_to_date]).start()

    def req_update_check(self, notify_up_to_date=False):
        try:
            # request to github api, compare version. If not same tell user to update
            req = get("https://api.github.com/repos/Dadangdut33/Speech-Translate/releases/latest", timeout=7)

            if req is not None and req.status_code == 200:
                data = req.json()
                latest_version = str(data["tag_name"])
                if __version__ < latest_version:
                    logger.info(f"New version found: {latest_version}")
                    self.update_text = "New version available"
                    self.update_fg = "blue"
                    self.update_func = self.open_dl_link
                    self.tooltip_check_update.text = "Click to go to the latest release page"
                    native_notify("New version available", "Visit the repository to download the latest update")
                else:
                    logger.info("No update available")
                    self.update_text = "You are using the latest version"
                    self.update_fg = "green"
                    self.update_func = self.check_for_update
                    self.tooltip_check_update.text = "Up to date"
                    if notify_up_to_date:
                        native_notify("Up to date", "You are using the latest version")
            else:
                logger.warning("Failed to check for update")
                self.update_text = "Fail to check for update!"
                self.update_fg = "red"
                self.update_func = self.check_for_update
                self.tooltip_check_update.text = "Click to try again"
                if not self.checking_on_start:  # suppress error if checking on start
                    native_notify("Fail to check for app update!", "Click to try again")

            self.lbl_check_update.configure(text=self.update_text, foreground=self.update_fg)
            self.lbl_check_update.bind("<Button-1>", self.update_func)

            self.checking = False
        except Exception as e:
            if "HTTPSConnectionPool" in str(e):
                logger.error("No Internet Connection! / Host might be down")
                no_connection_notify(msg="Fail to check app for update!")
            else:
                logger.exception(e)
        finally:
            self.checking = False
