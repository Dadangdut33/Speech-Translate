from os import listdir, path, remove
from tkinter import filedialog, ttk, Frame, LabelFrame, Toplevel, Event, Menu
from typing import Literal, Union
from speech_translate.ui.custom.checkbutton import CustomCheckButton
from speech_translate.ui.custom.combobox import ComboboxWithKeyNav
from speech_translate.ui.custom.message import MBoxText, mbox
from datetime import datetime

from speech_translate.linker import sj, bc
from speech_translate._path import dir_export, parameters_text
from speech_translate.utils.helper import filename_only, popup_menu, start_file, up_first_case
from speech_translate.utils.whisper.helper import get_task_format
from speech_translate.ui.custom.tooltip import tk_tooltip, tk_tooltips
from speech_translate.ui.custom.spinbox import SpinboxNumOnly


class SettingExport:
    """
    Textboox tab in setting window.
    """
    def __init__(self, root: Toplevel, master_frame: Union[ttk.Frame, Frame]):
        self.root = root
        self.master = master_frame

        # ------------------ Options ------------------
        # export
        self.lf_export_mode = LabelFrame(self.master, text="• Mode")
        self.lf_export_mode.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_mode_1 = ttk.Frame(self.lf_export_mode)
        self.f_export_mode_1.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_mode_2 = ttk.Frame(self.lf_export_mode)
        self.f_export_mode_2.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_mode_3 = ttk.Frame(self.lf_export_mode)
        self.f_export_mode_3.pack(side="top", fill="x", padx=5, pady=5)

        self.lf_export_limit = LabelFrame(self.master, text="• Limit Per Segment")
        self.lf_export_limit.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_limit_1 = ttk.Frame(self.lf_export_limit)
        self.f_export_limit_1.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_limit_2 = ttk.Frame(self.lf_export_limit)
        self.f_export_limit_2.pack(side="top", fill="x", padx=5, pady=5)

        self.lf_export_format = LabelFrame(self.master, text="• Naming Format")
        self.lf_export_format.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_format_1 = ttk.Frame(self.lf_export_format)
        self.f_export_format_1.pack(side="top", fill="x", padx=5, pady=5)

        self.f_expor_format_2 = ttk.Frame(self.lf_export_format)
        self.f_expor_format_2.pack(side="top", fill="x", padx=5, pady=5)

        self.f_export_format_3 = ttk.Frame(self.lf_export_format)
        self.f_export_format_3.pack(side="top", fill="x", padx=5, pady=5)

        self.lbl_output_mode = ttk.Label(self.f_export_mode_1, text="Mode", width=17)
        self.lbl_output_mode.pack(side="left", padx=5)

        def keep_one_enabled(value: bool, other_widget: ttk.Checkbutton):
            if not value:
                other_widget.configure(state="disabled")
            else:
                other_widget.configure(state="normal")

        self.cbtn_segment_level = CustomCheckButton(
            self.f_export_mode_1,
            sj.cache["segment_level"],
            lambda x: sj.save_key("segment_level", x) or keep_one_enabled(x, self.cbtn_word_level),
            text="Segment Level",
            style="Switch.TCheckbutton",
        )
        self.cbtn_segment_level.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_segment_level,
            "Export the text in segment level.\n\n*Either segment level or word level must be enabled.\n\nDefault is checked",
            wrapLength=350
        )

        self.cbtn_word_level = CustomCheckButton(
            self.f_export_mode_1,
            sj.cache["word_level"],
            lambda x: sj.save_key("word_level", x) or keep_one_enabled(x, self.cbtn_segment_level),
            text="Word Level",
            style="Switch.TCheckbutton",
        )
        self.cbtn_word_level.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_word_level,
            "Export the text in word level.\n\n*Either segment level or word level must be enabled.\n\nDefault is checked",
            wrapLength=350
        )

        self.lbl_export_to = ttk.Label(self.f_export_mode_2, text="Export to", width=17)
        self.lbl_export_to.pack(side="left", padx=5)

        self.cbtn_export_txt = CustomCheckButton(
            self.f_export_mode_2, "txt" in sj.cache["export_to"], lambda x: self.callback_export_to("txt", x), text="Text"
        )
        self.cbtn_export_txt.pack(side="left", padx=5)

        self.cbtn_export_json = CustomCheckButton(
            self.f_export_mode_2, "json" in sj.cache["export_to"], lambda x: self.callback_export_to("json", x), text="JSON"
        )
        self.cbtn_export_json.pack(side="left", padx=5)

        self.cbtn_export_srt = CustomCheckButton(
            self.f_export_mode_2, "srt" in sj.cache["export_to"], lambda x: self.callback_export_to("srt", x), text="SRT"
        )
        self.cbtn_export_srt.pack(side="left", padx=5)

        self.cbtn_export_ass = CustomCheckButton(
            self.f_export_mode_2, "ass" in sj.cache["export_to"], lambda x: self.callback_export_to("ass", x), text="ASS"
        )
        self.cbtn_export_ass.pack(side="left", padx=5)

        self.cbtn_export_vtt = CustomCheckButton(
            self.f_export_mode_2, "vtt" in sj.cache["export_to"], lambda x: self.callback_export_to("vtt", x), text="VTT"
        )
        self.cbtn_export_vtt.pack(side="left", padx=5)

        self.cbtn_export_tsv = CustomCheckButton(
            self.f_export_mode_2, "tsv" in sj.cache["export_to"], lambda x: self.callback_export_to("tsv", x), text="TSV"
        )
        self.cbtn_export_tsv.pack(side="left", padx=5)

        self.cbtn_export_csv = CustomCheckButton(
            self.f_export_mode_2, "csv" in sj.cache["export_to"], lambda x: self.callback_export_to("csv", x), text="CSV"
        )
        self.cbtn_export_csv.pack(side="left", padx=5)

        self.separator_fex_2 = ttk.Separator(self.f_export_mode_2, orient="vertical")
        self.separator_fex_2.pack(side="left", padx=5, fill="y")

        self.cbtn_visaulize_suppression = CustomCheckButton(
            self.f_export_mode_2,
            sj.cache["visualize_suppression"],
            lambda x: sj.save_key("visualize_suppression", x),
            text="Visualize Suppression",
            style="Switch.TCheckbutton",
        )
        self.cbtn_visaulize_suppression.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_visaulize_suppression,
            "Visualize which parts of the audio will likely be suppressed (i.e. marked as silent).\n\nDefault is unchecked",
            wrapLength=350
        )

        self.lbl_export = ttk.Label(self.f_export_mode_3, text="Export Folder", width=17)
        self.lbl_export.pack(side="left", padx=5)

        self.entry_export = ttk.Entry(self.f_export_mode_3)
        self.entry_export.pack(side="left", padx=5, fill="x", expand=True)
        tk_tooltip(self.entry_export, "The folder where exported text from import file are saved.")

        self.btn_export_config = ttk.Button(
            self.f_export_mode_3,
            image=bc.wrench_emoji,
            compound="center",
            width=3,
            command=lambda: popup_menu(self.root, self.menu_config_export)
        )
        self.btn_export_config.pack(side="left", padx=5)

        self.menu_config_export = Menu(self.master, tearoff=0)
        self.menu_config_export.add_command(
            label="Open", image=bc.open_emoji, compound="left", command=lambda: start_file(self.entry_export.get())
        )
        self.menu_config_export.add_separator()
        self.menu_config_export.add_command(
            label="Change Folder",
            image=bc.folder_emoji,
            compound="left",
            command=lambda: self.change_path("dir_export", self.entry_export)
        )
        self.menu_config_export.add_command(
            label="Set Back to Default",
            image=bc.reset_emoji,
            compound="left",
            command=lambda: self.path_default("dir_export", self.entry_export, dir_export),
        )
        self.menu_config_export.add_separator()
        self.menu_config_export.add_command(
            label="Empty Export Folder", image=bc.trash_emoji, compound="left", command=lambda: self.clear_export()
        )

        self.cbtn_auto_open_export = CustomCheckButton(
            self.f_export_mode_3,
            sj.cache["auto_open_dir_export"],
            lambda x: sj.save_key("auto_open_dir_export", x),
            text="Auto open",
            style="Switch.TCheckbutton",
        )
        self.cbtn_auto_open_export.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_auto_open_export,
            "Auto open the export folder after file import and the transcribe/translate process is done.",
            wrapLength=300,
        )

        def keybind_num(event: Event, widget: ttk.Entry):
            vsym = event.keysym
            vw = widget.get()
            v = event.char
            try:
                # check number or not
                int(v)  # pressed key
            except ValueError:
                # check value
                if vw == "":  # if empty
                    return "break"
                elif vsym == "minus":  # if minus
                    if "-" in vw:
                        replaced = vw.replace("-", "")
                        widget.delete(0, "end")
                        widget.insert(0, replaced)
                        return "break"
                    else:
                        replaced = "-" + vw
                        widget.delete(0, "end")
                        widget.insert(0, replaced)
                        return "break"

                # check pressed key
                if v != "\x08" and v != "":  # other than backspace and empty is not allowed
                    return "break"

        self.lbl_segment_max_words = ttk.Label(self.f_export_limit_1, text="Max Words", width=17)
        self.lbl_segment_max_words.pack(side="left", padx=5)
        self.spn_segment_max_words = SpinboxNumOnly(
            self.root,
            self.f_export_limit_1,
            1,
            100_000,
            lambda x: sj.save_key("segment_max_words", x),
            initial_value=sj.cache["segment_max_words"],
            allow_empty=True,
            delay=10,
        )
        self.spn_segment_max_words.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_segment_max_words, self.spn_segment_max_words],
            "Maximum number of words allowed in each segment.\n\nDefault is empty",
        )

        self.lbl_segment_max_chars = ttk.Label(self.f_export_limit_1, text="Max Chars", width=17)
        self.lbl_segment_max_chars.pack(side="left", padx=5)
        self.spn_segment_max_chars = SpinboxNumOnly(
            self.root,
            self.f_export_limit_1,
            1,
            100_000,
            lambda x: sj.save_key("segment_max_chars", x),
            initial_value=sj.cache["segment_max_chars"],
            allow_empty=True,
            delay=10,
        )
        self.spn_segment_max_chars.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_segment_max_chars, self.spn_segment_max_chars],
            "Maximum number of characters allowed in each segment.\n\nDefault is empty",
        )

        self.lbl_question_mark = ttk.Label(self.f_export_limit_1, width=17, image=bc.question_emoji)
        self.lbl_question_mark.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_question_mark,
            "If both limit `Max words` and `Max chars` are empty, no splitting of segments will be done.",
            wrapLength=300,
        )

        self.lbl_segment_split_or_newline = ttk.Label(self.f_export_limit_2, text="Separate Method", width=17)
        self.lbl_segment_split_or_newline.pack(side="left", padx=5)
        self.cb_segment_split_or_newline = ComboboxWithKeyNav(
            self.f_export_limit_2, values=["Split", "Newline"], state="readonly", width=23
        )
        self.cb_segment_split_or_newline.set(sj.cache["segment_split_or_newline"])
        self.cb_segment_split_or_newline.bind(
            "<<ComboboxSelected>>",
            lambda e: sj.save_key("segment_split_or_newline", self.cb_segment_split_or_newline.get()),
        )
        self.cb_segment_split_or_newline.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_segment_split_or_newline, self.cb_segment_split_or_newline],
            "Whether to splitting into separate segments the split points or insert line break.\n\nDefault is Split",
            wrapLength=300,
        )

        self.cbtn_segment_even_split = CustomCheckButton(
            self.f_export_limit_2,
            sj.cache["segment_even_split"],
            lambda x: sj.save_key("segment_even_split", x),
            text="Even Split",
            style="Switch.TCheckbutton",
        )
        self.cbtn_segment_even_split.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_segment_even_split,
            "Whether to evenly split a segment in length if it exceeds `max_chars` or `max_words`.\n\nDefault is checked",
            wrapLength=300,
        )

        self.lbl_slice_file_start = ttk.Label(self.f_export_format_1, text="Slice File Start", width=17)
        self.lbl_slice_file_start.pack(side="left", padx=5)
        self.spn_slice_file_start = SpinboxNumOnly(
            self.root,
            self.f_export_format_1,
            -256,
            256,
            lambda x: self.update_preview_export_format() or sj.save_key("file_slice_start", x),
            initial_value=sj.cache["file_slice_start"],
            allow_empty=True,
            delay=10,
        )
        self.spn_slice_file_start.pack(side="left", padx=5)

        self.lbl_slice_file_end = ttk.Label(self.f_export_format_1, text="Slice File End")
        self.lbl_slice_file_end.pack(side="left", padx=5)
        self.spn_slice_file_end = SpinboxNumOnly(
            self.root,
            self.f_export_format_1,
            -256,
            256,
            lambda x: self.update_preview_export_format() or sj.save_key("file_slice_end", x),
            initial_value=sj.cache["file_slice_end"],
            allow_empty=True,
            delay=10,
        )
        self.spn_slice_file_end.pack(side="left", padx=5)

        self.lbl_export_format = ttk.Label(self.f_expor_format_2, text="Export format", width=17)
        self.lbl_export_format.pack(side="left", padx=5)
        self.entry_export_format = ttk.Entry(self.f_expor_format_2)
        self.entry_export_format.insert(0, sj.cache["export_format"])
        self.entry_export_format.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_export_format.bind(
            "<KeyRelease>",
            lambda e: sj.save_key("export_format", self.entry_export_format.get()) or self.update_preview_export_format(),
        )

        available_params = (
            "Default value: %Y-%m-%d %f {file}/{task-lang}"
            "\nTo folderize the result you can use / in the format. Example: {file}/{task-lang-with}"
            "\n\nAvailable parameters:"
            "\n\n-----------------------------------------------------------------------------"
            "\n----- Parameters that can be used in any situation -----"
            "\n\n{strftime format such as %Y %m %d %H %M %f ...}"
            "\nTo see the full list of strftime format, see https://strftime.org/"
            "\n\n{file}"
            "\nWill be replaced with the file name"
            "\n\n{lang-source}"
            "\nWill be replaced with the source language if available. Example: english"
            "\n\n{lang-target}"
            "\nWill be replaced with the target language if available. Example: french"
            "\n\n{transcribe-with}"
            "\nWill be replaced with the transcription model name if available. Example: tiny"
            "\n\n{translate-with}"
            "\nWill be replaced with the translation engine name if available. Example: google translate"
            "\n\n----------------------------------------------------------------------"
            "\n----------- Parameters only related to task ------------"
            "\n\n{task}"
            "\nWill be replaced with the task name. Example: transcribed or translated"
            "\n\n{task-lang}"
            "\nWill be replaced with the task name alongside the language. Example: transcribed english or translated english to french"
            "\n\n{task-with}"
            "\nWill be replaced with the task name alongside the model or engine name. Example: transcribed with tiny or translated with google translate"
            "\n\n{task-lang-with}"
            "\nWill be replaced with the task name alongside the language and model or engine name. Example: transcribed english with tiny or translated english to french with google translate"
            "\n\n{task-short}"
            "\nWill be replaced with the task name but shorten. Example: tc or tl"
            "\n\n{task-short-lang}"
            "\nWill be replaced with the task name but shorten and alongside the language. Example: tc english or tl english to french"
            "\n\n{task-short-with}"
            "\nWill be replaced with the task name but shorten and alongside the model or engine name. Example: tc tiny or tl google translate"
            "\n\n{task-short-lang-with}"
            "\nWill be replaced with the task name but shorten and alongside the language and model or engine name. Example: tc english with tiny or tl english to french with google translate"
        )
        self.btn_help_export_format = ttk.Button(
            self.f_expor_format_2,
            image=bc.question_emoji,
            command=lambda: MBoxText("export-format", self.root, "Export formats", available_params),
            width=5,
        )
        self.btn_help_export_format.pack(side="left", padx=5)

        self.lbl_preview_export_format = ttk.Label(self.f_export_format_3, text="", width=17)  # padding helper
        self.lbl_preview_export_format.pack(side="left", padx=5, pady=(0, 5))

        self.lbl_preview_export_format_result = ttk.Label(self.f_export_format_3, text="...", foreground="gray")
        self.lbl_preview_export_format_result.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.lbl_preview_export_format_result,
            "Preview of the export format with the current settings\n"
            "Filename: this is an example video or audio file.mp4",
            wrapLength=350,
        )

        # --------------------------
        self.init_setting_once()

    # ------------------ Functions ------------------
    def init_setting_once(self):
        self.update_preview_export_format()

        if sj.cache["dir_export"] == "auto":
            self.path_default("dir_export", self.entry_export, dir_export, save=False, prompt=False)
        else:
            self.entry_export.configure(state="normal")
            self.entry_export.insert(0, sj.cache["dir_export"])
            self.entry_export.configure(state="readonly")

    def update_preview_export_format(self):
        try:
            assert bc.mw is not None
            filename = filename_only("this is an example video or audio file.mp4")
            slice_start = int(self.spn_slice_file_start.get()) if self.spn_slice_file_start.get() != "" else None
            slice_end = int(self.spn_slice_file_end.get()) if self.spn_slice_file_end.get() != "" else None
            task = "translated"
            short_task = "tl"
            model = bc.mw.cb_model.get()
            engine = bc.mw.cb_engine.get()
            source = bc.mw.cb_source_lang.get()
            target = bc.mw.cb_target_lang.get()
            format_dict = get_task_format(
                task,
                f"{task} {source} to {target}",
                f"{task} with {engine}",
                f"{task} {source} to {target} with {engine}",
            )
            format_dict.update(
                get_task_format(
                    short_task,
                    f"{short_task} {source} to {target}",
                    f"{short_task} with {engine}",
                    f"{short_task} {source} to {target} with {engine}",
                    short_only=True,
                )
            )

            save_name = datetime.now().strftime(self.entry_export_format.get())
            save_name = save_name.replace("{file}", filename[slice_start:slice_end])
            save_name = save_name.replace("{lang-source}", source)
            save_name = save_name.replace("{lang-target}", target)
            save_name = save_name.replace("{transcribe-with}", model)
            save_name = save_name.replace("{translate-with}", engine)
            for key, value in format_dict.items():
                save_name = save_name.replace(key, value)

            self.lbl_preview_export_format_result.configure(text=save_name)
        except Exception:
            pass

    def callback_export_to(
        self, value: Union[Literal["txt"], Literal["csv"], Literal["json"], Literal["srt"], Literal["ass"], Literal["vtt"],
                           Literal["tsv"]], add: bool
    ):
        try:
            export_list = sj.cache["export_to"].copy()
            if add:
                export_list.append(value)
            else:
                export_list.remove(value)

            sj.save_key("export_to", export_list)
        except Exception:
            pass

    def change_path(self, key: str, element: ttk.Entry):
        path = filedialog.askdirectory()
        if path != "":
            sj.save_key(key, path)
            element.configure(state="normal")
            element.delete(0, "end")
            element.insert(0, path)
            element.configure(state="readonly")

    def make_open_text(self, texts: str):
        if not path.exists(parameters_text):
            with open(parameters_text, "w", encoding="utf-8") as f:
                f.write(texts)

        start_file(parameters_text)

    def path_default(self, key: str, element: ttk.Entry, default_path: str, save=True, prompt=True):
        # prompt are you sure
        if prompt and not mbox(
            f"Set {up_first_case(key.split('_')[1])} Folder to Default",
            f"Are you sure you want to set {key.split('_')[1]} folder back to default?",
            3,
            self.root,
        ):
            return

        element.configure(state="normal")
        element.delete(0, "end")
        element.insert(0, default_path)
        element.configure(state="readonly")
        if save:
            sj.save_key(key, "auto")

    def clear_export(self):
        if mbox("Clear Export Folder", "Are you sure you want to clear the export folder?", 3, self.root):
            # get all the files in the export folder
            files = listdir(sj.cache["dir_export"])
            for file in files:
                remove(path.join(sj.cache["dir_export"], file))
