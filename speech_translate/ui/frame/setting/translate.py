from tkinter import Frame, LabelFrame, Text, Toplevel, ttk
from typing import Union

from speech_translate.linker import sj
from speech_translate.ui.custom.checkbutton import CustomCheckButton
from speech_translate.ui.custom.tooltip import tk_tooltip, tk_tooltips


class SettingTranslate:
    """
    Textboox tab in setting window.
    """
    def __init__(self, root: Toplevel, master_frame: Union[ttk.Frame, Frame]):
        self.root = root
        self.master = master_frame

        # ------------------ Options ------------------
        self.lf_translate_options = LabelFrame(self.master, text="• Options")
        self.lf_translate_options.pack(side="top", fill="x", padx=5, pady=5)

        self.f_translate_options_1 = ttk.Frame(self.lf_translate_options)
        self.f_translate_options_1.pack(side="top", fill="x", pady=5, padx=5)

        # ---- proxies
        self.lf_proxies = ttk.LabelFrame(self.f_translate_options_1, text="• Proxies List")
        self.lf_proxies.pack(side="left", fill="x", padx=5, pady=(0, 5), expand=True)

        self.f_proxies_1 = ttk.Frame(self.lf_proxies)
        self.f_proxies_1.pack(side="left", fill="x", pady=5, padx=5, expand=True)

        self.f_proxies_1_1 = ttk.Frame(self.f_proxies_1)
        self.f_proxies_1_1.pack(side="top", fill="x", expand=True)

        self.f_proxies_1_2 = ttk.Frame(self.f_proxies_1)
        self.f_proxies_1_2.pack(side="top", fill="x", expand=True)

        self.f_proxies_1_3 = ttk.Frame(self.f_proxies_1)
        self.f_proxies_1_3.pack(side="top", fill="x", expand=True)

        self.f_proxies_2 = ttk.Frame(self.lf_proxies)
        self.f_proxies_2.pack(side="left", fill="x", pady=5, padx=5, expand=True)

        self.f_proxies_2_1 = ttk.Frame(self.f_proxies_2)
        self.f_proxies_2_1.pack(side="top", fill="x", expand=True)

        self.f_proxies_2_2 = ttk.Frame(self.f_proxies_2)
        self.f_proxies_2_2.pack(side="top", fill="x", expand=True)

        self.f_proxies_2_3 = ttk.Frame(self.f_proxies_2)
        self.f_proxies_2_3.pack(side="top", fill="x", expand=True)

        self.lbl_proxies_https = ttk.Label(self.f_proxies_1_1, text="HTTPS")
        self.lbl_proxies_https.pack(side="left", padx=5, fill="x", expand=True)

        self.sb_proxies_https = ttk.Scrollbar(self.f_proxies_1_2)
        self.sb_proxies_https.pack(side="right", fill="y")

        self.tb_proxies_https = Text(self.f_proxies_1_2, width=27, height=10)
        self.tb_proxies_https.insert("end", str(sj.cache["https_proxy"]).strip())
        self.tb_proxies_https.pack(side="left", padx=5, pady=5, fill="both", expand=True)
        self.tb_proxies_https.bind(
            "<KeyRelease>", lambda e: sj.save_key("https_proxy",
                                                  self.tb_proxies_https.get("1.0", "end").strip())
        )
        self.tb_proxies_https.configure(yscrollcommand=self.sb_proxies_https.set)
        self.sb_proxies_https.configure(command=self.tb_proxies_https.yview)
        tk_tooltips(
            [self.lbl_proxies_https, self.tb_proxies_https],
            "HTTPS proxies list separated by new line, tab, or space. If there are "
            "multiple proxies, it will be chosen randomly."
            "\n\nExample input:\nhttps://proxy1:port\nhttps://proxy2:port",
            wrap_len=250,
        )

        self.cbtn_proxies_https = CustomCheckButton(
            self.f_proxies_1_3,
            sj.cache["https_proxy_enable"],
            lambda x: sj.save_key("https_proxy_enable", x),
            text="Enable https proxy",
            style="Switch.TCheckbutton"
        )
        self.cbtn_proxies_https.pack(side="left", padx=5, pady=(0, 5))

        self.lbl_proxies_http = ttk.Label(self.f_proxies_2_1, text="HTTP")
        self.lbl_proxies_http.pack(side="left", padx=5, fill="x", expand=True)

        self.sb_proxies_http = ttk.Scrollbar(self.f_proxies_2_2)
        self.sb_proxies_http.pack(side="right", fill="y")

        self.tb_proxies_http = Text(self.f_proxies_2_2, width=27, height=10)
        self.tb_proxies_http.insert("end", str(sj.cache["http_proxy"]).strip())
        self.tb_proxies_http.pack(side="left", padx=5, pady=5, fill="both", expand=True)
        self.tb_proxies_http.bind(
            "<KeyRelease>", lambda e: sj.save_key("http_proxy",
                                                  self.tb_proxies_http.get("1.0", "end").strip())
        )
        self.tb_proxies_http.configure(yscrollcommand=self.sb_proxies_http.set)
        self.sb_proxies_http.configure(command=self.tb_proxies_http.yview)
        tk_tooltips(
            [self.lbl_proxies_http, self.tb_proxies_http],
            "HTTP proxies list separated by new line, tab, or space. If there "
            "are multiple proxies, it will be chosen randomly."
            "\n\nExample input:\nhttp://proxy1:port\nhttp://proxy2:port",
            wrap_len=250,
        )

        self.cbtn_proxies_http = CustomCheckButton(
            self.f_proxies_2_3,
            sj.cache["http_proxy_enable"],
            lambda x: sj.save_key("http_proxy_enable", x),
            text="Enable http proxy",
            style="Switch.TCheckbutton"
        )
        self.cbtn_proxies_http.pack(side="left", padx=5, pady=(0, 5))

        # ------------------ Libre translate ------------------
        self.lf_libre = LabelFrame(self.master, text="• Libre Translate Setting")
        self.lf_libre.pack(side="top", fill="x", padx=5, pady=5)

        self.f_libre_1 = ttk.Frame(self.lf_libre)
        self.f_libre_1.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_libre_link = ttk.Label(self.f_libre_1, text="Host / URL Of Hosted Libre Translate")
        self.lbl_libre_link.pack(side="left", padx=5, pady=(0, 5))

        self.entry_libre_link = ttk.Entry(self.f_libre_1, width=40)
        self.entry_libre_link.insert(0, sj.cache["libre_link"])
        self.entry_libre_link.pack(side="left", padx=5, pady=(0, 5))
        self.entry_libre_link.bind("<KeyRelease>", lambda e: sj.save_key("libre_link", self.entry_libre_link.get()))
        tk_tooltips(
            [self.lbl_libre_link, self.entry_libre_link],
            "The host of Libre Translate (example: https://libretranslate.com or http://127.0.0.1:5000/)." \
            "\n\nYou can check out the official instance/mirrors at https://github.com/LibreTranslate/LibreTranslate " \
            "or host your own instance. \n\nIt is recommended to host your own instance for free and faster result " \
            "without limit \n\nAlso, keep in mind that the language code that is set for libretranslate in this app " \
            "is for libretranslate version 1.5.1",
            wrap_len=400,
        )

        self.lbl_libre_key = ttk.Label(self.f_libre_1, text="API Key")
        self.lbl_libre_key.pack(side="left", padx=5, pady=(0, 5))

        self.entry_libre_key = ttk.Entry(self.f_libre_1)
        self.entry_libre_key.insert(0, sj.cache["libre_api_key"])
        self.entry_libre_key.pack(side="left", padx=5, pady=(0, 5))
        self.entry_libre_key.bind("<KeyRelease>", lambda e: sj.save_key("libre_api_key", self.entry_libre_key.get()))
        tk_tooltips(
            [self.lbl_libre_key, self.entry_libre_key],
            "Libre Translate API Key. Leave empty if not needed or host locally.",
        )

        self.cbtn_supress_empty_api_key = CustomCheckButton(
            self.f_libre_1,
            sj.cache["supress_libre_api_key_warning"],
            lambda x: sj.save_key("supress_libre_api_key_warning", x),
            text="Supress Empty API Key",
            style="Switch.TCheckbutton"
        )
        self.cbtn_supress_empty_api_key.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(self.cbtn_supress_empty_api_key, "Supress warning when libre api key is empty.")
