from tkinter import ttk, font, Toplevel, Frame, LabelFrame, Text
from typing import Union

from speech_translate._constants import PREVIEW_WORDS
from speech_translate.globals import sj, gc
from speech_translate.utils.helper import chooseColor, max_number, number_only
from speech_translate.utils.helper import cbtn_invoker
from speech_translate.components.custom.tooltip import tk_tooltip, tk_tooltips


class SettingTextbox:
    """
    Textboox tab in setting window.
    """
    def __init__(self, root: Toplevel, master_frame: Union[ttk.Frame, Frame]):
        self.root = root
        self.master = master_frame
        self.fonts = list(font.families())
        self.fonts.append("TKDefaultFont")
        self.fonts.sort()

        # ------------------ Textbox ------------------
        self.f_tb_param = ttk.Frame(self.master)
        self.f_tb_param.pack(side="top", fill="both", expand=False)

        self.f_tb_1 = ttk.Frame(self.master)
        self.f_tb_1.pack(side="top", fill="x")

        self.f_tb_2 = ttk.Frame(self.master)
        self.f_tb_2.pack(side="top", fill="x")

        self.f_tb_param_1 = ttk.Frame(self.f_tb_param)
        self.f_tb_param_1.pack(side="top", fill="x")

        self.f_tb_param_2 = ttk.Frame(self.f_tb_param)
        self.f_tb_param_2.pack(side="top", fill="x")

        self.f_tb_param_3 = ttk.Frame(self.f_tb_param)
        self.f_tb_param_3.pack(side="top", fill="x")

        # -----
        self.lf_param_mw_tc = LabelFrame(self.f_tb_param_1, text="• Main Window Transcribed Speech")
        self.lf_param_mw_tc.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.f_mw_tc_1 = ttk.Frame(self.lf_param_mw_tc)
        self.f_mw_tc_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_mw_tc_2 = ttk.Frame(self.lf_param_mw_tc)
        self.f_mw_tc_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_mw_tc_3 = ttk.Frame(self.lf_param_mw_tc)
        self.f_mw_tc_3.pack(side="top", fill="x", pady=5, padx=5)

        self.lf_param_mw_tl = LabelFrame(self.f_tb_param_1, text="• Main Window Translated Speech")
        self.lf_param_mw_tl.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.f_mw_tl_1 = ttk.Frame(self.lf_param_mw_tl)
        self.f_mw_tl_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_mw_tl_2 = ttk.Frame(self.lf_param_mw_tl)
        self.f_mw_tl_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_mw_tl_3 = ttk.Frame(self.lf_param_mw_tl)
        self.f_mw_tl_3.pack(side="top", fill="x", pady=5, padx=5)

        self.lf_param_ex_tc = LabelFrame(self.f_tb_param_2, text="• Subtitle Window Transcribed Speech")
        self.lf_param_ex_tc.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.f_ex_tc_1 = ttk.Frame(self.lf_param_ex_tc)
        self.f_ex_tc_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_ex_tc_2 = ttk.Frame(self.lf_param_ex_tc)
        self.f_ex_tc_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_ex_tc_3 = ttk.Frame(self.lf_param_ex_tc)
        self.f_ex_tc_3.pack(side="top", fill="x", pady=5, padx=5)

        self.f_ex_tc_4 = ttk.Frame(self.lf_param_ex_tc)
        self.f_ex_tc_4.pack(side="top", fill="x", pady=5, padx=5)

        self.lf_param_ex_tl = LabelFrame(self.f_tb_param_2, text="• Subtitle Window Translated Speech")
        self.lf_param_ex_tl.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.f_ex_tl_1 = ttk.Frame(self.lf_param_ex_tl)
        self.f_ex_tl_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_ex_tl_2 = ttk.Frame(self.lf_param_ex_tl)
        self.f_ex_tl_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_ex_tl_3 = ttk.Frame(self.lf_param_ex_tl)
        self.f_ex_tl_3.pack(side="top", fill="x", pady=5, padx=5)

        self.f_ex_tl_4 = ttk.Frame(self.lf_param_ex_tl)
        self.f_ex_tl_4.pack(side="top", fill="x", pady=5, padx=5)

        # -----
        self.lf_param_other = LabelFrame(self.f_tb_param_3, text="• Other")
        self.lf_param_other.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.f_other_1 = ttk.Frame(self.lf_param_other)
        self.f_other_1.pack(side="top", fill="x", pady=5, padx=5)

        # -------------
        # mw tc
        # 1
        self.lbl_mw_tc_max = ttk.Label(self.f_mw_tc_1, text="Max Length", width=16)
        self.lbl_mw_tc_max.pack(side="left", padx=5)
        self.spn_mw_tc_max = ttk.Spinbox(
            self.f_mw_tc_1,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=38,
        )
        self.spn_mw_tc_max.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_mw_tc_max,
                0,
                5000,
                lambda: sj.save_key("tb_mw_tc_max", int(self.spn_mw_tc_max.get())),
            ) or self.preview_changes_tb(),
        )
        self.spn_mw_tc_max.pack(side="left", padx=5)
        self.cbtn_mw_tc_limit_max = ttk.Checkbutton(self.f_mw_tc_1, text="Enable", style="Switch.TCheckbutton")
        self.cbtn_mw_tc_limit_max.pack(side="left", padx=5)

        # 2
        self.lbl_mw_tc_max_per_line = ttk.Label(self.f_mw_tc_2, text="Max Per Line", width=16)
        self.lbl_mw_tc_max_per_line.pack(side="left", padx=5)
        self.spn_mw_tc_max_per_line = ttk.Spinbox(
            self.f_mw_tc_2,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=38,
        )
        self.spn_mw_tc_max_per_line.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_mw_tc_max_per_line,
                0,
                5000,
                lambda: sj.save_key("tb_mw_tc_max_per_line", int(self.spn_mw_tc_max_per_line.get())),
            ) or self.preview_changes_tb(),
        )
        self.spn_mw_tc_max_per_line.pack(side="left", padx=5)
        self.cbtn_mw_tc_limit_max_per_line = ttk.Checkbutton(self.f_mw_tc_2, text="Enable", style="Switch.TCheckbutton")
        self.cbtn_mw_tc_limit_max_per_line.pack(side="left", padx=5)

        # 3
        self.lbl_mw_tc_font = ttk.Label(self.f_mw_tc_3, text="Font", width=16)
        self.lbl_mw_tc_font.pack(side="left", padx=5)
        self.cb_mw_tc_font = ttk.Combobox(self.f_mw_tc_3, values=self.fonts, state="readonly", width=30)
        self.cb_mw_tc_font.pack(side="left", padx=5)
        self.cb_mw_tc_font.bind(
            "<<ComboboxSelected>>",
            lambda e: sj.save_key("tb_mw_tc_font", self.cb_mw_tc_font.get()) or self.preview_changes_tb(),
        )
        self.spn_mw_tc_font_size = ttk.Spinbox(
            self.f_mw_tc_3,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=3,
        )
        self.spn_mw_tc_font_size.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_mw_tc_font_size,
                3,
                120,
                lambda: sj.save_key("tb_mw_tc_font_size", int(self.spn_mw_tc_font_size.get())),
            ) or self.preview_changes_tb(),
        )
        tk_tooltip(self.spn_mw_tc_font_size, "Font Size")
        self.spn_mw_tc_font_size.pack(side="left", padx=5)
        self.cbtn_mw_tc_font_bold = ttk.Checkbutton(self.f_mw_tc_3, text="Bold", style="Switch.TCheckbutton")
        self.cbtn_mw_tc_font_bold.pack(side="left", padx=5)

        # -------------
        # mw tl
        # 1
        self.lbl_mw_tl_max = ttk.Label(self.f_mw_tl_1, text="Max Length", width=16)
        self.lbl_mw_tl_max.pack(side="left", padx=5)
        self.spn_mw_tl_max = ttk.Spinbox(
            self.f_mw_tl_1,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=38,
        )
        self.spn_mw_tl_max.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_mw_tl_max,
                0,
                5000,
                lambda: sj.save_key("tb_mw_tl_max", int(self.spn_mw_tl_max.get())),
            ) or self.preview_changes_tb(),
        )
        self.spn_mw_tl_max.pack(side="left", padx=5)
        self.cbtn_mw_tl_limit_max = ttk.Checkbutton(self.f_mw_tl_1, text="Enable", style="Switch.TCheckbutton")
        self.cbtn_mw_tl_limit_max.pack(side="left", padx=5)

        # 2
        self.lbl_mw_tl_max_per_line = ttk.Label(self.f_mw_tl_2, text="Max Per Line", width=16)
        self.lbl_mw_tl_max_per_line.pack(side="left", padx=5)
        self.spn_mw_tl_max_per_line = ttk.Spinbox(
            self.f_mw_tl_2,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=38,
        )
        self.spn_mw_tl_max_per_line.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_mw_tl_max_per_line,
                0,
                5000,
                lambda: sj.save_key("tb_mw_tl_max_per_line", int(self.spn_mw_tl_max_per_line.get())),
            ) or self.preview_changes_tb(),
        )
        self.spn_mw_tl_max_per_line.pack(side="left", padx=5)
        self.cbtn_mw_tl_limit_max_per_line = ttk.Checkbutton(self.f_mw_tl_2, text="Enable", style="Switch.TCheckbutton")
        self.cbtn_mw_tl_limit_max_per_line.pack(side="left", padx=5)

        # 3
        self.lbl_mw_tl_font = ttk.Label(self.f_mw_tl_3, text="Font", width=16)
        self.lbl_mw_tl_font.pack(side="left", padx=5)
        self.cb_mw_tl_font = ttk.Combobox(self.f_mw_tl_3, values=self.fonts, state="readonly", width=30)
        self.cb_mw_tl_font.pack(side="left", padx=5)
        self.cb_mw_tl_font.bind(
            "<<ComboboxSelected>>",
            lambda e: sj.save_key("tb_mw_tl_font", self.cb_mw_tl_font.get()) or self.preview_changes_tb(),
        )
        self.spn_mw_tl_font_size = ttk.Spinbox(
            self.f_mw_tl_3,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=3,
        )
        self.spn_mw_tl_font_size.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_mw_tl_font_size,
                3,
                120,
                lambda: sj.save_key("tb_mw_tl_font_size", int(self.spn_mw_tl_font_size.get())),
            ) or self.preview_changes_tb(),
        )
        tk_tooltip(self.spn_mw_tl_font_size, "Font Size")
        self.spn_mw_tl_font_size.pack(side="left", padx=5)
        self.cbtn_mw_tl_font_bold = ttk.Checkbutton(self.f_mw_tl_3, text="Bold", style="Switch.TCheckbutton")
        self.cbtn_mw_tl_font_bold.pack(side="left", padx=5)

        # -------------
        # detached tc
        # 1
        self.lbl_ex_tc_max = ttk.Label(self.f_ex_tc_1, text="Max Length", width=16)
        self.lbl_ex_tc_max.pack(side="left", padx=5)
        self.spn_ex_tc_max = ttk.Spinbox(
            self.f_ex_tc_1,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=38,
        )
        self.spn_ex_tc_max.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_ex_tc_max,
                0,
                5000,
                lambda: sj.save_key("tb_ex_tc_max", int(self.spn_ex_tc_max.get())),
            ) or self.preview_changes_tb(),
        )
        self.spn_ex_tc_max.pack(side="left", padx=5)
        self.cbtn_ex_tc_limit_max = ttk.Checkbutton(self.f_ex_tc_1, text="Enable", style="Switch.TCheckbutton")
        self.cbtn_ex_tc_limit_max.pack(side="left", padx=5)

        # 2
        self.lbl_ex_tc_max_per_line = ttk.Label(self.f_ex_tc_2, text="Max Per Line", width=16)
        self.lbl_ex_tc_max_per_line.pack(side="left", padx=5)
        self.spn_ex_tc_max_per_line = ttk.Spinbox(
            self.f_ex_tc_2,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=38,
        )
        self.spn_ex_tc_max_per_line.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_ex_tc_max_per_line,
                0,
                5000,
                lambda: sj.save_key("tb_ex_tc_max_per_line", int(self.spn_ex_tc_max_per_line.get())),
            ) or self.preview_changes_tb(),
        )
        self.spn_ex_tc_max_per_line.pack(side="left", padx=5)
        self.cbtn_ex_tc_limit_max_per_line = ttk.Checkbutton(self.f_ex_tc_2, text="Enable", style="Switch.TCheckbutton")
        self.cbtn_ex_tc_limit_max_per_line.pack(side="left", padx=5)

        # 3
        self.lbl_ex_tc_font = ttk.Label(self.f_ex_tc_3, text="Font", width=16)
        self.lbl_ex_tc_font.pack(side="left", padx=5)
        self.cb_ex_tc_font = ttk.Combobox(self.f_ex_tc_3, values=self.fonts, state="readonly", width=30)
        self.cb_ex_tc_font.pack(side="left", padx=5)
        self.cb_ex_tc_font.bind(
            "<<ComboboxSelected>>",
            lambda e: sj.save_key("tb_ex_tc_font", self.cb_ex_tc_font.get()) or self.preview_changes_tb(),
        )
        self.spn_ex_tc_font_size = ttk.Spinbox(
            self.f_ex_tc_3,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=3,
        )
        self.spn_ex_tc_font_size.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_ex_tc_font_size,
                3,
                120,
                lambda: sj.save_key("tb_ex_tc_font_size", int(self.spn_ex_tc_font_size.get())),
            ) or self.preview_changes_tb(),
        )
        tk_tooltip(self.spn_ex_tc_font_size, "Font Size")
        self.spn_ex_tc_font_size.pack(side="left", padx=5)
        self.cbtn_ex_tc_font_bold = ttk.Checkbutton(self.f_ex_tc_3, text="Bold", style="Switch.TCheckbutton")
        self.cbtn_ex_tc_font_bold.pack(side="left", padx=5)

        # 4
        self.lbl_ex_tc_font_color = ttk.Label(self.f_ex_tc_4, text="Font Color", width=16)
        self.lbl_ex_tc_font_color.pack(side="left", padx=5)
        self.entry_ex_tc_font_color = ttk.Entry(self.f_ex_tc_4, width=10)
        self.entry_ex_tc_font_color.pack(side="left", padx=5)
        self.entry_ex_tc_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tc_font_color, self.entry_ex_tc_font_color.get(), self.root) or sj.
            save_key("tb_ex_tc_font_color", self.entry_ex_tc_font_color.get()) or self.preview_changes_tb(),
        )
        self.entry_ex_tc_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_tc_bg_color = ttk.Label(self.f_ex_tc_4, text="Background Color")
        self.lbl_ex_tc_bg_color.pack(side="left", padx=5)
        self.entry_ex_tc_bg_color = ttk.Entry(self.f_ex_tc_4, width=10)
        self.entry_ex_tc_bg_color.pack(side="left", padx=5)
        self.entry_ex_tc_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tc_bg_color, self.entry_ex_tc_bg_color.get(), self.root) or sj.
            save_key("tb_ex_tc_bg_color", self.entry_ex_tc_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_ex_tc_bg_color.bind("<Key>", lambda e: "break")

        # -------------
        # detached tl
        self.lbl_ex_tl_max = ttk.Label(self.f_ex_tl_1, text="Max Length", width=16)
        self.lbl_ex_tl_max.pack(side="left", padx=5)
        self.spn_ex_tl_max = ttk.Spinbox(
            self.f_ex_tl_1,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=38,
        )
        self.spn_ex_tl_max.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_ex_tl_max,
                0,
                5000,
                lambda: sj.save_key("tb_ex_tl_max", int(self.spn_ex_tl_max.get())),
            ) or self.preview_changes_tb(),
        )
        self.spn_ex_tl_max.pack(side="left", padx=5)
        self.cbtn_ex_tl_limit_max = ttk.Checkbutton(self.f_ex_tl_1, text="Enable", style="Switch.TCheckbutton")
        self.cbtn_ex_tl_limit_max.pack(side="left", padx=5)

        # 2
        self.lbl_ex_tl_max_per_line = ttk.Label(self.f_ex_tl_2, text="Max Per Line", width=16)
        self.lbl_ex_tl_max_per_line.pack(side="left", padx=5)
        self.spn_ex_tl_max_per_line = ttk.Spinbox(
            self.f_ex_tl_2,
            from_=0,
            to=5000,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=38,
        )
        self.spn_ex_tl_max_per_line.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_ex_tl_max_per_line,
                0,
                5000,
                lambda: sj.save_key("tb_ex_tl_max_per_line", int(self.spn_ex_tl_max_per_line.get())),
            ) or self.preview_changes_tb(),
        )
        self.spn_ex_tl_max_per_line.pack(side="left", padx=5)
        self.cbtn_ex_tl_limit_max_per_line = ttk.Checkbutton(self.f_ex_tl_2, text="Enable", style="Switch.TCheckbutton")
        self.cbtn_ex_tl_limit_max_per_line.pack(side="left", padx=5)

        # 3
        self.lbl_ex_tl_font = ttk.Label(self.f_ex_tl_3, text="Font", width=16)
        self.lbl_ex_tl_font.pack(side="left", padx=5)
        self.cb_ex_tl_font = ttk.Combobox(self.f_ex_tl_3, values=self.fonts, state="readonly", width=30)
        self.cb_ex_tl_font.pack(side="left", padx=5)
        self.cb_ex_tl_font.bind(
            "<<ComboboxSelected>>",
            lambda e: sj.save_key("tb_ex_tl_font", self.cb_ex_tl_font.get()) or self.preview_changes_tb(),
        )
        self.spn_ex_tl_font_size = ttk.Spinbox(
            self.f_ex_tl_3,
            from_=3,
            to=120,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
            width=3,
        )
        self.spn_ex_tl_font_size.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_ex_tl_font_size,
                3,
                120,
                lambda: sj.save_key("tb_ex_tl_font_size", int(self.spn_ex_tl_font_size.get())),
            ) or self.preview_changes_tb(),
        )
        tk_tooltip(self.spn_ex_tl_font_size, "Font Size")
        self.spn_ex_tl_font_size.pack(side="left", padx=5)
        self.cbtn_ex_tl_font_bold = ttk.Checkbutton(self.f_ex_tl_3, text="Bold", style="Switch.TCheckbutton")
        self.cbtn_ex_tl_font_bold.pack(side="left", padx=5)

        # 4
        self.lbl_ex_tl_font_color = ttk.Label(self.f_ex_tl_4, text="Font Color", width=16)
        self.lbl_ex_tl_font_color.pack(side="left", padx=5)
        self.entry_ex_tl_font_color = ttk.Entry(self.f_ex_tl_4, width=10)
        self.entry_ex_tl_font_color.pack(side="left", padx=5)
        self.entry_ex_tl_font_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tl_font_color, self.entry_ex_tl_font_color.get(), self.root) or sj.
            save_key("tb_ex_tl_font_color", self.entry_ex_tl_font_color.get()) or self.preview_changes_tb(),
        )
        self.entry_ex_tl_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_tl_bg_color = ttk.Label(self.f_ex_tl_4, text="Background Color")
        self.lbl_ex_tl_bg_color.pack(side="left", padx=5)
        self.entry_ex_tl_bg_color = ttk.Entry(self.f_ex_tl_4, width=10)
        self.entry_ex_tl_bg_color.pack(side="left", padx=5)
        self.entry_ex_tl_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor(self.entry_ex_tl_bg_color, self.entry_ex_tl_bg_color.get(), self.root) or sj.
            save_key("tb_ex_tl_bg_color", self.entry_ex_tl_bg_color.get()) or self.preview_changes_tb(),
        )
        self.entry_ex_tl_bg_color.bind("<Key>", lambda e: "break")

        # ------------------ Other ------------------
        self.cbtn_parse_arabic = ttk.Checkbutton(self.f_other_1, text="Parse Arabic character", style="Switch.TCheckbutton")
        self.cbtn_parse_arabic.pack(side="left", padx=5, pady=5)
        tk_tooltip(
            self.cbtn_parse_arabic,
            "Check this option if you want to transcribe Arabic character. "
            "This will fix the display issue of Arabic character",
        )

        # ------------------ Preview ------------------
        # tb 1
        self.tb_preview_1 = Text(
            self.f_tb_1,
            height=5,
            width=27,
            wrap="word",
            font=(
                sj.cache["tb_mw_tc_font"],
                sj.cache["tb_mw_tc_font_size"],
                "bold" if sj.cache["tb_mw_tc_font_bold"] else "normal",
            ),
        )
        self.tb_preview_1.bind("<Key>", "break")
        self.tb_preview_1.insert("end", "TC Main window:\n" + PREVIEW_WORDS)
        self.tb_preview_1.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        self.tb_preview_2 = Text(
            self.f_tb_1,
            height=5,
            width=27,
            wrap="word",
            font=(
                sj.cache["tb_mw_tl_font"],
                sj.cache["tb_mw_tl_font_size"],
                "bold" if sj.cache["tb_mw_tl_font_bold"] else "normal",
            ),
        )
        self.tb_preview_2.bind("<Key>", "break")
        self.tb_preview_2.insert("end", "TL Main window:\n" + PREVIEW_WORDS)
        self.tb_preview_2.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        # tb 2
        self.tb_preview_3 = Text(
            self.f_tb_2,
            height=5,
            width=27,
            wrap="word",
            font=(
                sj.cache["tb_ex_tc_font"],
                sj.cache["tb_ex_tc_font_size"],
                "bold" if sj.cache["tb_ex_tc_font_bold"] else "normal",
            ),
            foreground=sj.cache["tb_ex_tc_font_color"],
            background=sj.cache["tb_ex_tc_bg_color"],
        )
        self.tb_preview_3.bind("<Key>", "break")
        self.tb_preview_3.insert("end", "TC Subtitle window:\n" + PREVIEW_WORDS)
        self.tb_preview_3.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        self.tb_preview_4 = Text(
            self.f_tb_2,
            height=5,
            width=27,
            wrap="word",
            font=(
                sj.cache["tb_ex_tl_font"],
                sj.cache["tb_ex_tl_font_size"],
                "bold" if sj.cache["tb_ex_tl_font_bold"] else "normal",
            ),
            foreground=sj.cache["tb_ex_tl_font_color"],
            background=sj.cache["tb_ex_tl_bg_color"],
        )
        self.tb_preview_4.bind("<Key>", "break")
        self.tb_preview_4.insert("end", "TL Subtitle window:\n" + PREVIEW_WORDS)
        self.tb_preview_4.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        # --------------------------
        # tooltips
        tk_tooltips(
            [
                self.lbl_mw_tc_max, self.spn_mw_tc_max, self.lbl_mw_tl_max, self.spn_mw_tl_max, self.lbl_ex_tc_max,
                self.spn_ex_tc_max, self.lbl_ex_tl_max, self.spn_ex_tl_max
            ],
            "Max character shown. Keep in mind that the result is also limited by "
            "the max buffer and max sentence in the record setting",
        )
        tk_tooltips(
            [
                self.lbl_mw_tc_max_per_line, self.spn_mw_tc_max_per_line, self.lbl_mw_tl_max_per_line,
                self.spn_mw_tl_max_per_line, self.lbl_ex_tc_max_per_line, self.spn_ex_tc_max_per_line,
                self.lbl_ex_tl_max_per_line, self.spn_ex_tl_max_per_line
            ],
            "Max character shown per line.\n\n"
            "Separator needs to contain a line break (\\n) for this to work",
        )
        tk_tooltips(
            [
                self.cbtn_mw_tc_limit_max, self.cbtn_mw_tc_limit_max_per_line, self.cbtn_mw_tl_limit_max,
                self.cbtn_mw_tl_limit_max_per_line, self.cbtn_ex_tc_limit_max, self.cbtn_ex_tc_limit_max_per_line,
                self.cbtn_ex_tl_limit_max, self.cbtn_ex_tl_limit_max_per_line
            ],
            "Enable character limit",
        )

        # --------------------------
        self.init_setting_once()

    # ------------------ Functions ------------------

    def init_setting_once(self):
        self.tb_delete()

        self.spn_mw_tc_max.set(sj.cache["tb_mw_tc_max"])
        cbtn_invoker(sj.cache["tb_mw_tc_limit_max"], self.cbtn_mw_tc_limit_max)
        self.spn_mw_tc_max_per_line.set(sj.cache["tb_mw_tc_max_per_line"])
        cbtn_invoker(sj.cache["tb_mw_tc_limit_max_per_line"], self.cbtn_mw_tc_limit_max_per_line)
        self.cb_mw_tc_font.set(sj.cache["tb_mw_tc_font"])
        self.spn_mw_tc_font_size.set(sj.cache["tb_mw_tc_font_size"])
        cbtn_invoker(sj.cache["tb_mw_tc_font_bold"], self.cbtn_mw_tc_font_bold)

        self.spn_mw_tl_max.set(sj.cache["tb_mw_tl_max"])
        cbtn_invoker(sj.cache["tb_mw_tl_limit_max"], self.cbtn_mw_tl_limit_max)
        self.spn_mw_tl_max_per_line.set(sj.cache["tb_mw_tl_max_per_line"])
        cbtn_invoker(sj.cache["tb_mw_tl_limit_max_per_line"], self.cbtn_mw_tl_limit_max_per_line)
        self.cb_mw_tl_font.set(sj.cache["tb_mw_tl_font"])
        self.spn_mw_tl_font_size.set(sj.cache["tb_mw_tl_font_size"])
        cbtn_invoker(sj.cache["tb_mw_tl_font_bold"], self.cbtn_mw_tl_font_bold)

        self.spn_ex_tc_max.set(sj.cache["tb_ex_tc_max"])
        cbtn_invoker(sj.cache["tb_ex_tc_limit_max"], self.cbtn_ex_tc_limit_max)
        self.spn_ex_tc_max_per_line.set(sj.cache["tb_ex_tc_max_per_line"])
        cbtn_invoker(sj.cache["tb_ex_tc_limit_max_per_line"], self.cbtn_ex_tc_limit_max_per_line)
        self.cb_ex_tc_font.set(sj.cache["tb_ex_tc_font"])
        self.spn_ex_tc_font_size.set(sj.cache["tb_ex_tc_font_size"])
        cbtn_invoker(sj.cache["tb_ex_tc_font_bold"], self.cbtn_ex_tc_font_bold)
        self.entry_ex_tc_font_color.insert(0, sj.cache["tb_ex_tc_font_color"])
        self.entry_ex_tc_bg_color.insert(0, sj.cache["tb_ex_tc_bg_color"])

        self.spn_ex_tl_max.set(sj.cache["tb_ex_tl_max"])
        cbtn_invoker(sj.cache["tb_ex_tl_limit_max"], self.cbtn_ex_tl_limit_max)
        self.spn_ex_tl_max_per_line.set(sj.cache["tb_ex_tl_max_per_line"])
        cbtn_invoker(sj.cache["tb_ex_tl_limit_max_per_line"], self.cbtn_ex_tl_limit_max_per_line)
        self.cb_ex_tl_font.set(sj.cache["tb_ex_tl_font"])
        self.spn_ex_tl_font_size.set(sj.cache["tb_ex_tl_font_size"])
        cbtn_invoker(sj.cache["tb_ex_tl_font_bold"], self.cbtn_ex_tl_font_bold)
        self.entry_ex_tl_font_color.insert(0, sj.cache["tb_ex_tl_font_color"])
        self.entry_ex_tl_bg_color.insert(0, sj.cache["tb_ex_tl_bg_color"])

        cbtn_invoker(sj.cache["parse_arabic"], self.cbtn_parse_arabic)

        self.configure_commands()
        self.preview_changes_tb()

    def configure_commands(self):
        """
        To prevent the command from being called multiple times, we need to configure the command
          just once after the setting is initialized
        """
        self.spn_mw_tc_max.configure(
            command=lambda: sj.save_key("tb_mw_tc_max", int(self.spn_mw_tc_max.get())) or self.preview_changes_tb()
        )
        self.spn_mw_tc_max_per_line.configure(
            command=lambda: sj.save_key("tb_mw_tc_max_per_line", int(self.spn_mw_tc_max_per_line.get())) or self.
            preview_changes_tb()
        )
        self.spn_mw_tc_font_size.configure(
            command=lambda: sj.save_key("tb_mw_tc_font_size", int(self.spn_mw_tc_font_size.get())) or self.
            preview_changes_tb()
        )
        self.cbtn_ex_tc_limit_max.configure(
            command=lambda: sj.save_key("tb_mw_tc_limit_max", self.cbtn_mw_tc_limit_max.instate(["selected"])) or self.
            preview_changes_tb()
        )
        self.cbtn_mw_tc_limit_max_per_line.configure(
            command=lambda: sj.save_key(
                "tb_mw_tc_limit_max_per_line", self.cbtn_mw_tc_limit_max_per_line.instate(["selected"])
            ) or self.preview_changes_tb()
        )
        self.cbtn_mw_tc_font_bold.configure(
            command=lambda: sj.save_key("tb_mw_tc_font_bold", self.cbtn_mw_tc_font_bold.instate(["selected"])) or self.
            preview_changes_tb()
        )

        self.spn_mw_tl_max.configure(
            command=lambda: sj.save_key("tb_mw_tl_max", int(self.spn_mw_tl_max.get())) or self.preview_changes_tb()
        )
        self.spn_mw_tl_max_per_line.configure(
            command=lambda: sj.save_key("tb_mw_tl_max_per_line", int(self.spn_mw_tl_max_per_line.get())) or self.
            preview_changes_tb()
        )
        self.spn_mw_tl_font_size.configure(
            command=lambda: sj.save_key("tb_mw_tl_font_size", int(self.spn_mw_tl_font_size.get())) or self.
            preview_changes_tb()
        )
        self.cbtn_mw_tl_limit_max.configure(
            command=lambda: sj.save_key("tb_mw_tl_limit_max", self.cbtn_mw_tl_limit_max.instate(["selected"])) or self.
            preview_changes_tb()
        )
        self.cbtn_mw_tl_limit_max_per_line.configure(
            command=lambda: sj.save_key(
                "tb_mw_tl_limit_max_per_line", self.cbtn_mw_tl_limit_max_per_line.instate(["selected"])
            ) or self.preview_changes_tb()
        )
        self.cbtn_mw_tl_font_bold.configure(
            command=lambda: sj.save_key("tb_mw_tl_font_bold", self.cbtn_mw_tl_font_bold.instate(["selected"])) or self.
            preview_changes_tb()
        )

        self.spn_ex_tc_max.configure(
            command=lambda: sj.save_key("tb_ex_tc_max", int(self.spn_ex_tc_max.get())) or self.preview_changes_tb()
        )
        self.spn_ex_tc_max_per_line.configure(
            command=lambda: sj.save_key("tb_ex_tc_max_per_line", int(self.spn_ex_tc_max_per_line.get())) or self.
            preview_changes_tb()
        )
        self.spn_ex_tc_font_size.configure(
            command=lambda: sj.save_key("tb_ex_tc_font_size", int(self.spn_ex_tc_font_size.get())) or self.
            preview_changes_tb()
        )
        self.cbtn_ex_tc_limit_max.configure(
            command=lambda: sj.save_key("tb_ex_tc_limit_max", self.cbtn_ex_tc_limit_max.instate(["selected"])) or self.
            preview_changes_tb()
        )
        self.cbtn_ex_tc_limit_max_per_line.configure(
            command=lambda: sj.save_key(
                "tb_ex_tc_limit_max_per_line", self.cbtn_ex_tc_limit_max_per_line.instate(["selected"])
            ) or self.preview_changes_tb()
        )
        self.cbtn_ex_tc_font_bold.configure(
            command=lambda: sj.save_key("tb_ex_tc_font_bold", self.cbtn_ex_tc_font_bold.instate(["selected"])) or self.
            preview_changes_tb()
        )

        self.spn_ex_tl_max.configure(
            command=lambda: sj.save_key("tb_ex_tl_max", int(self.spn_ex_tl_max.get())) or self.preview_changes_tb()
        )
        self.spn_ex_tl_max_per_line.configure(
            command=lambda: sj.save_key("tb_ex_tl_max_per_line", int(self.spn_ex_tl_max_per_line.get())) or self.
            preview_changes_tb()
        )
        self.spn_ex_tl_font_size.configure(
            command=lambda: sj.save_key("tb_ex_tl_font_size", int(self.spn_ex_tl_font_size.get())) or self.
            preview_changes_tb()
        )
        self.cbtn_ex_tl_limit_max.configure(
            command=lambda: sj.save_key("tb_ex_tl_limit_max", self.cbtn_ex_tl_limit_max.instate(["selected"])) or self.
            preview_changes_tb()
        )
        self.cbtn_ex_tl_limit_max_per_line.configure(
            command=lambda: sj.save_key(
                "tb_ex_tl_limit_max_per_line", self.cbtn_ex_tl_limit_max_per_line.instate(["selected"])
            ) or self.preview_changes_tb()
        )
        self.cbtn_ex_tl_font_bold.configure(
            command=lambda: sj.save_key("tb_ex_tl_font_bold", self.cbtn_ex_tl_font_bold.instate(["selected"])) or self.
            preview_changes_tb()
        )

        self.cbtn_parse_arabic.configure(
            command=lambda: sj.save_key("parse_arabic", self.cbtn_parse_arabic.instate(["selected"]))
        )

    def tb_delete(self):
        self.entry_ex_tc_font_color.delete(0, "end")
        self.entry_ex_tc_bg_color.delete(0, "end")

        self.entry_ex_tl_font_color.delete(0, "end")
        self.entry_ex_tl_bg_color.delete(0, "end")

    def preview_changes_tb(self):
        if gc.mw is None:
            return

        gc.mw.tb_transcribed.configure(
            font=(
                self.cb_mw_tc_font.get(),
                int(self.spn_mw_tc_font_size.get()),
                "bold" if self.cbtn_mw_tc_font_bold.instate(["selected"]) else "normal",
            )
        )
        self.tb_preview_1.configure(
            font=(
                self.cb_mw_tc_font.get(),
                int(self.spn_mw_tc_font_size.get()),
                "bold" if self.cbtn_mw_tc_font_bold.instate(["selected"]) else "normal",
            )
        )

        gc.mw.tb_translated.configure(
            font=(
                self.cb_mw_tl_font.get(),
                int(self.spn_mw_tl_font_size.get()),
                "bold" if self.cbtn_mw_tl_font_bold.instate(["selected"]) else "normal",
            )
        )
        self.tb_preview_2.configure(
            font=(
                self.cb_mw_tl_font.get(),
                int(self.spn_mw_tl_font_size.get()),
                "bold" if self.cbtn_mw_tl_font_bold.instate(["selected"]) else "normal",
            )
        )

        assert gc.ex_tcw is not None
        gc.ex_tcw.lbl_text.configure(
            font=(
                self.cb_ex_tc_font.get(),
                int(self.spn_ex_tc_font_size.get()),
                "bold" if self.cbtn_ex_tc_font_bold.instate(["selected"]) else "normal",
            ),
            foreground=self.entry_ex_tc_font_color.get(),
            background=self.entry_ex_tc_bg_color.get(),
        )
        self.tb_preview_3.configure(
            font=(
                self.cb_ex_tc_font.get(),
                int(self.spn_ex_tc_font_size.get()),
                "bold" if self.cbtn_ex_tc_font_bold.instate(["selected"]) else "normal",
            ),
            foreground=self.entry_ex_tc_font_color.get(),
            background=self.entry_ex_tc_bg_color.get(),
        )

        assert gc.ex_tlw is not None
        gc.ex_tlw.lbl_text.configure(
            font=(
                self.cb_ex_tl_font.get(),
                int(self.spn_ex_tl_font_size.get()),
                "bold" if self.cbtn_ex_tl_font_bold.instate(["selected"]) else "normal",
            ),
            foreground=self.entry_ex_tl_font_color.get(),
            background=self.entry_ex_tl_bg_color.get(),
        )
        self.tb_preview_4.configure(
            font=(
                self.cb_ex_tl_font.get(),
                int(self.spn_ex_tl_font_size.get()),
                "bold" if self.cbtn_ex_tl_font_bold.instate(["selected"]) else "normal",
            ),
            foreground=self.entry_ex_tl_font_color.get(),
            background=self.entry_ex_tl_bg_color.get(),
        )
