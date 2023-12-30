from tkinter import Frame, LabelFrame, Toplevel, font, ttk
from typing import Callable, List, Union

from tkhtmlview import HTMLText

from speech_translate._constants import APP_NAME, PREVIEW_WORDS
from speech_translate.linker import bc, sj
from speech_translate.ui.custom.checkbutton import CustomCheckButton
from speech_translate.ui.custom.combobox import ComboboxWithKeyNav
from speech_translate.ui.custom.spinbox import SpinboxNumOnly
from speech_translate.ui.custom.tooltip import tk_tooltip, tk_tooltips
from speech_translate.utils.helper import choose_color, emoji_img, generate_color


class BaseTbSetting:
    """
    Base class for the textbox settings.
    """
    def __init__(
        self, root: Toplevel, master_frame: Union[ttk.Frame, Frame], title: str, f_type: str, is_main: bool,
        preview_changes_tb: Callable, fonts: List
    ):
        self.lf = LabelFrame(master_frame, text=title)
        self.lf.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.f_1 = ttk.Frame(self.lf)
        self.f_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_2 = ttk.Frame(self.lf)
        self.f_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_3 = ttk.Frame(self.lf)
        self.f_3.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_max = ttk.Label(self.f_1, text="Max Length", width=16)
        self.lbl_max.pack(side="left", padx=5)
        self.spn_max = SpinboxNumOnly(
            root,
            self.f_1,
            1,
            5000,
            lambda x: sj.save_key(f"tb_{f_type}_max", int(x)) or preview_changes_tb(),
            initial_value=sj.cache[f"tb_{f_type}_max"],
            width=38
        )
        self.spn_max.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_max, self.spn_max],
            "Max character shown. Keep in mind that the result is also limited by "
            "the max buffer and max sentence in the record setting",
        )

        self.cbtn_limit_max = CustomCheckButton(
            self.f_1,
            sj.cache[f"tb_{f_type}_limit_max"],
            lambda x: sj.save_key(f"tb_{f_type}_limit_max", x) or preview_changes_tb(),
            text="Enable",
            style="Switch.TCheckbutton"
        )
        self.cbtn_limit_max.pack(side="left", padx=5)

        self.lbl_max_per_line = ttk.Label(self.f_2, text="Max Per Line", width=16)
        self.lbl_max_per_line.pack(side="left", padx=5)
        self.spn_max_per_line = SpinboxNumOnly(
            root,
            self.f_2,
            1,
            5000,
            lambda x: sj.save_key(f"tb_{f_type}_max_per_line", int(x)) or preview_changes_tb(),
            initial_value=sj.cache[f"tb_{f_type}_max_per_line"],
            width=38
        )
        self.spn_max_per_line.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_max_per_line, self.spn_max_per_line],
            "Max character shown per line. Separator needs to contain a line break (\\n) for this to work",
        )

        self.cbtn_limit_max_per_line = CustomCheckButton(
            self.f_2,
            sj.cache[f"tb_{f_type}_limit_max_per_line"],
            lambda x: sj.save_key(f"tb_{f_type}_limit_max_per_line", x) or preview_changes_tb(),
            text="Enable",
            style="Switch.TCheckbutton"
        )
        self.cbtn_limit_max_per_line.pack(side="left", padx=5)

        self.lbl_font = ttk.Label(self.f_3, text="Font", width=16)
        self.lbl_font.pack(side="left", padx=5)
        self.cb_font = ComboboxWithKeyNav(self.f_3, values=fonts, state="readonly", width=30)
        self.cb_font.set(sj.cache[f"tb_{f_type}_font"])
        self.cb_font.pack(side="left", padx=5)
        self.cb_font.bind(
            "<<ComboboxSelected>>",
            lambda e: sj.save_key(f"tb_{f_type}_font", self.cb_font.get()) or preview_changes_tb(),
        )
        self.spn_font_size = SpinboxNumOnly(
            root,
            self.f_3,
            3,
            120,
            lambda x: sj.save_key(f"tb_{f_type}_font_size", int(x)) or preview_changes_tb(),
            initial_value=sj.cache[f"tb_{f_type}_font_size"],
            width=3
        )
        tk_tooltip(self.spn_font_size, "Font Size")
        self.spn_font_size.pack(side="left", padx=5)
        self.cbtn_font_bold = CustomCheckButton(
            self.f_3,
            sj.cache[f"tb_{f_type}_font_bold"],
            lambda x: sj.save_key(f"tb_{f_type}_font_bold", x) or preview_changes_tb(),
            text="Bold",
            style="Switch.TCheckbutton"
        )
        self.cbtn_font_bold.pack(side="left", padx=5)

        if not is_main:
            self.f_4 = ttk.Frame(self.lf)
            self.f_4.pack(side="top", fill="x", pady=5, padx=5)

            self.lbl_font_color = ttk.Label(self.f_4, text="Font Color", width=16)
            self.lbl_font_color.pack(side="left", padx=5)
            self.entry_font_color = ttk.Entry(self.f_4, width=10)
            self.entry_font_color.insert("end", sj.cache[f"tb_{f_type}_font_color"])
            self.entry_font_color.pack(side="left", padx=5)
            self.entry_font_color.bind(
                "<Button-1>",
                lambda e: choose_color(self.entry_font_color, self.entry_font_color.get(), root) or sj.
                save_key(f"tb_{f_type}_font_color", self.entry_font_color.get()) or preview_changes_tb(),
            )
            self.entry_font_color.bind("<Key>", lambda e: "break")

            self.lbl_bg_color = ttk.Label(self.f_4, text="Background Color")
            self.lbl_bg_color.pack(side="left", padx=5)
            self.entry_bg_color = ttk.Entry(self.f_4, width=10)
            self.entry_bg_color.insert("end", sj.cache[f"tb_{f_type}_bg_color"])
            self.entry_bg_color.pack(side="left", padx=5)
            self.entry_bg_color.bind(
                "<Button-1>",
                lambda e: choose_color(self.entry_bg_color, self.entry_bg_color.get(), root) or sj.
                save_key(f"tb_{f_type}_bg_color", self.entry_bg_color.get()) or preview_changes_tb(),
            )
            self.entry_bg_color.bind("<Key>", lambda e: "break")

        self.f_5 = ttk.Frame(self.lf)
        self.f_5.pack(side="top", fill="x", pady=5, padx=5)

        self.cbtn_use_conf_color = CustomCheckButton(
            self.f_5,
            sj.cache[f"tb_{f_type}_use_conf_color"],
            lambda x: sj.save_key(f"tb_{f_type}_use_conf_color", x) or preview_changes_tb(),
            text="Colorize text based on confidence value when available"
        )
        self.cbtn_use_conf_color.pack(side="left", padx=5)

        self.cbtn_auto_scroll = CustomCheckButton(
            self.f_5,
            sj.cache[f"tb_{f_type}_auto_scroll"],
            lambda x: sj.save_key(f"tb_{f_type}_auto_scroll", x) or preview_changes_tb(),
            text="Auto Scroll"
        )
        self.cbtn_auto_scroll.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_auto_scroll,
            "Automatically scroll to the bottom when new text is added",
        )

        tk_tooltips(
            [self.cbtn_limit_max, self.cbtn_limit_max_per_line],
            "Enable character limit",
        )


class SettingTextbox:
    """
    Textbox tab in setting window.
    """
    def __init__(self, root: Toplevel, master_frame: Union[ttk.Frame, Frame]):
        self.root = root
        self.master = master_frame
        self.preview_emoji = emoji_img(16, "🔍", "dark" in sj.cache["theme"])
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
        self.opt_tb_mw_tc = BaseTbSetting(
            self.root, self.f_tb_param_1, "• Main Window Transcribed Speech", "mw_tc", True, self.preview_changes_tb,
            self.fonts
        )
        self.opt_tb_mw_tl = BaseTbSetting(
            self.root, self.f_tb_param_1, "• Main Window Translated Speech", "mw_tl", True, self.preview_changes_tb,
            self.fonts
        )

        self.opt_tb_ex_tc = BaseTbSetting(
            self.root, self.f_tb_param_2, "• Subtitle Window for Transcribed Speech", "ex_tc", False,
            self.preview_changes_tb, self.fonts
        )
        self.opt_tb_ex_tl = BaseTbSetting(
            self.root, self.f_tb_param_2, "• Subtitle Window for Translated Speech", "ex_tl", False, self.preview_changes_tb,
            self.fonts
        )

        # ------------------ Other ------------------
        # # -----
        self.lf_param_other = LabelFrame(self.f_tb_param_3, text="• Other")
        self.lf_param_other.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.lf_confidence = ttk.LabelFrame(self.lf_param_other, text="• Confidence")
        self.lf_confidence.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.f_confidence_1 = ttk.Frame(self.lf_confidence)
        self.f_confidence_1.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_gradient_low_conf = ttk.Label(self.f_confidence_1, text="Low Confidence", width=16)
        self.lbl_gradient_low_conf.pack(side="left", padx=5)

        self.entry_gradient_low_conf = ttk.Entry(self.f_confidence_1, width=10)
        self.entry_gradient_low_conf.insert("end", sj.cache["gradient_low_conf"])
        self.entry_gradient_low_conf.pack(side="left", padx=5)
        self.entry_gradient_low_conf.bind(
            "<Button-1>",
            lambda e: choose_color(self.entry_gradient_low_conf, self.entry_gradient_low_conf.get(), self.root) or sj.
            save_key("gradient_low_conf", self.entry_gradient_low_conf.get()) or self.preview_changes_tb(),
        )
        self.entry_gradient_low_conf.bind("<Key>", lambda e: "break")

        self.lbl_gradient_high_conf = ttk.Label(self.f_confidence_1, text="High Confidence", width=16)
        self.lbl_gradient_high_conf.pack(side="left", padx=5)

        self.entry_gradient_high_conf = ttk.Entry(self.f_confidence_1, width=10)
        self.entry_gradient_high_conf.insert("end", sj.cache["gradient_high_conf"])
        self.entry_gradient_high_conf.pack(side="left", padx=5)
        self.entry_gradient_high_conf.bind(
            "<Button-1>",
            lambda e: choose_color(self.entry_gradient_high_conf, self.entry_gradient_high_conf.get(), self.root) or sj.
            save_key("gradient_high_conf", self.entry_gradient_high_conf.get()) or self.preview_changes_tb(),
        )
        self.entry_gradient_high_conf.bind("<Key>", lambda e: "break")

        self.btn_preview_gradient = ttk.Button(self.f_confidence_1, image=self.preview_emoji, command=self.preview_gradient)
        self.btn_preview_gradient.pack(side="left", padx=5)
        tk_tooltip(self.btn_preview_gradient, "Preview gradient")

        def keep_one_disabled(value: bool, other_widget: ttk.Checkbutton):
            if value:
                other_widget.configure(state="disabled")
            else:
                other_widget.configure(state="normal")

        self.cbtn_colorize_per_segment = CustomCheckButton(
            self.f_confidence_1,
            sj.cache["colorize_per_segment"],
            lambda x: sj.save_key("colorize_per_segment", x) or keep_one_disabled(x, self.cbtn_colorize_per_word),
            text="Colorize per segment",
            style="Switch.TCheckbutton"
        )
        self.cbtn_colorize_per_segment.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_colorize_per_segment,
            "Check this option if you want to colorize the text based on the total probability value" \
            "of words in each segment. This color will be set based on the color below",
        )

        self.cbtn_colorize_per_word = CustomCheckButton(
            self.f_confidence_1,
            sj.cache["colorize_per_word"],
            lambda x: sj.save_key("colorize_per_word", x) or keep_one_disabled(x, self.cbtn_colorize_per_segment),
            text="Colorize per word",
            style="Switch.TCheckbutton"
        )
        self.cbtn_colorize_per_word.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_colorize_per_word,
            "Check this option if you want to colorize the text based on the probability value of each word. "
            "This color will be set based on the color below",
        )

        # on init disable the other option if one is enabled
        if sj.cache["colorize_per_segment"]:
            self.cbtn_colorize_per_word.configure(state="disabled")
        elif sj.cache["colorize_per_word"]:
            self.cbtn_colorize_per_segment.configure(state="disabled")

        # ------------------ Preview ------------------
        # tb 1
        self.tb_preview_1 = HTMLText(
            self.f_tb_1,
            height=3,
            width=27,
            wrap="word",
            font=(
                sj.cache["tb_mw_tc_font"],
                sj.cache["tb_mw_tc_font_size"],
                "bold" if sj.cache["tb_mw_tc_font_bold"] else "normal",
            ),
            background=self.root.cget("bg"),
        )
        self.tb_preview_1.bind("<Key>", "break")
        self.tb_preview_1.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        self.tb_preview_2 = HTMLText(
            self.f_tb_1,
            height=3,
            width=27,
            wrap="word",
            font=(
                sj.cache["tb_mw_tl_font"],
                sj.cache["tb_mw_tl_font_size"],
                "bold" if sj.cache["tb_mw_tl_font_bold"] else "normal",
            ),
            background=self.root.cget("bg"),
        )
        self.tb_preview_2.bind("<Key>", "break")
        self.tb_preview_2.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        # tb 2
        self.tb_preview_3 = HTMLText(
            self.f_tb_2,
            height=3,
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
        self.tb_preview_3.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        self.tb_preview_4 = HTMLText(
            self.f_tb_2,
            height=3,
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
        self.tb_preview_4.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        # --------------------------
        self.__init_setting_once()

    # ------------------ Functions ------------------
    def __init_setting_once(self):
        self.preview_changes_tb()

    def tb_delete(self):
        self.tb_preview_1.delete("1.0", "end")
        self.tb_preview_2.delete("1.0", "end")
        self.tb_preview_3.delete("1.0", "end")
        self.tb_preview_4.delete("1.0", "end")

    def tb_insert_preview(self):
        to_insert = PREVIEW_WORDS

        self.tb_preview_1.insert("end", "TC Main window: " + to_insert)
        self.tb_preview_2.insert("end", "TL Main window: " + to_insert)
        self.tb_preview_3.insert("end", "TC Subtitle window: " + to_insert)
        self.tb_preview_4.insert("end", "TL Subtitle window: " + to_insert)

    def preview_changes_tb(self):
        if bc.mw is None:
            return

        self.tb_delete()
        self.tb_insert_preview()

        bc.mw.tb_transcribed.configure(
            font=(
                self.opt_tb_mw_tc.cb_font.get(),
                int(self.opt_tb_mw_tc.spn_font_size.get()),
                "bold" if self.opt_tb_mw_tc.cbtn_font_bold.instate(["selected"]) else "normal",
            )
        )
        self.tb_preview_1.configure(
            font=(
                self.opt_tb_mw_tc.cb_font.get(),
                int(self.opt_tb_mw_tc.spn_font_size.get()),
                "bold" if self.opt_tb_mw_tc.cbtn_font_bold.instate(["selected"]) else "normal",
            )
        )

        bc.mw.tb_translated.configure(
            font=(
                self.opt_tb_mw_tl.cb_font.get(),
                int(self.opt_tb_mw_tl.spn_font_size.get()),
                "bold" if self.opt_tb_mw_tl.cbtn_font_bold.instate(["selected"]) else "normal",
            )
        )
        self.tb_preview_2.configure(
            font=(
                self.opt_tb_mw_tl.cb_font.get(),
                int(self.opt_tb_mw_tl.spn_font_size.get()),
                "bold" if self.opt_tb_mw_tl.cbtn_font_bold.instate(["selected"]) else "normal",
            )
        )

        assert bc.ex_tcw is not None
        bc.ex_tcw.update_window_bg()
        self.tb_preview_3.configure(
            font=(
                self.opt_tb_ex_tc.cb_font.get(),
                int(self.opt_tb_ex_tc.spn_font_size.get()),
                "bold" if self.opt_tb_ex_tc.cbtn_font_bold.instate(["selected"]) else "normal",
            ),
            foreground=self.opt_tb_ex_tc.entry_font_color.get(),
            background=self.opt_tb_ex_tc.entry_bg_color.get(),
        )

        assert bc.ex_tlw is not None
        bc.ex_tlw.update_window_bg()
        self.tb_preview_4.configure(
            font=(
                self.opt_tb_ex_tl.cb_font.get(),
                int(self.opt_tb_ex_tl.spn_font_size.get()),
                "bold" if self.opt_tb_ex_tl.cbtn_font_bold.instate(["selected"]) else "normal",
            ),
            foreground=self.opt_tb_ex_tl.entry_font_color.get(),
            background=self.opt_tb_ex_tl.entry_bg_color.get(),
        )

    def preview_gradient(self):
        from matplotlib import pyplot as plt  # pylint: disable=import-outside-toplevel
        colors = [
            generate_color(i / 100, self.entry_gradient_low_conf.get(), self.entry_gradient_high_conf.get())
            for i in range(101)
        ]

        rgb_colors = [tuple(int(colors[i:i + 2], 16) for i in (1, 3, 5)) for colors in colors]

        plt.figure(figsize=(10, 5))
        plt.imshow([rgb_colors], interpolation="nearest", extent=[0, 1, 0, 1])  # type: ignore
        plt.title(
            f'Gradient Between {self.entry_gradient_low_conf.get()} as Low and {self.entry_gradient_high_conf.get()} as High'
        )
        plt.axis("off")
        # change window name
        if manager := plt.get_current_fig_manager():
            manager.set_window_title(
                f"Gradient Preview {self.entry_gradient_low_conf.get()} Low / " \
                f"{self.entry_gradient_high_conf.get()} High - {APP_NAME}"
            )
        plt.show()
