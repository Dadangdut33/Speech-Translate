from tkinter import IntVar, ttk, Tk, Toplevel, filedialog, StringVar, BooleanVar, messagebox, Text
from typing import List, Literal, Union
from time import sleep
from threading import Thread

from tksheet import Sheet
from loguru import logger

from speech_translate._path import app_icon
from speech_translate._logging import recent_stderr
from speech_translate.ui.custom.tooltip import tk_tooltip, tk_tooltips
from speech_translate.ui.custom.label import LabelTitleText
from speech_translate.ui.custom.combobox import CategorizedComboBox, ComboboxWithKeyNav
from speech_translate.utils.whisper.helper import model_keys
from speech_translate.utils.translate.language import (
    engine_select_source_dict, engine_select_target_dict, whisper_compatible_uppercase
)


class MultipleChoiceQuestion:
    def __init__(self, parent: Union[Tk, Toplevel], title: str, prompt: str, options: List):
        self.master = parent
        self.title = title
        self.prompt = prompt
        self.options = options
        self.choice = None

        self.root = Toplevel(self.master)
        self.root.resizable(False, False)
        self.root.geometry("+400+250")
        self.root.attributes('-topmost', True)
        self.root.title(title)
        self.root.transient(parent)

        if self.prompt:
            ttk.Label(self.root, text=self.prompt).pack(padx=5, pady=5)

        self.v = IntVar()
        for i, option in enumerate(self.options):
            ttk.Radiobutton(self.root, text=option, variable=self.v, value=i).pack(anchor="w", padx=5, pady=5)

        ttk.Button(self.root, text="Submit", command=self.submit).pack(padx=5, pady=5)
        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except Exception:
            pass

    def submit(self):
        if self.v.get() == -1:
            return  # No option selected
        self.choice = self.options[self.v.get()]
        self.root.destroy()

    def get_choice(self):
        self.root.wait_window()
        return self.choice


def prompt_with_choices(parent: Union[Tk, Toplevel], title: str, prompt: str, options: List):
    """
    Prompt with choices
    """
    temp = MultipleChoiceQuestion(parent, title, prompt, options)
    res = temp.get_choice()
    return res


class FileOperationDialog:
    def __init__(
        self,
        master,
        title: str,
        mode: Literal["File Import", "Refinement", "Alignment", "Translate"],
        headers: List,
        submit_func,
        theme,
        **kwargs,
    ):
        self.prev_width = None
        self.master = master
        self.submit_func = submit_func
        self.mode = mode
        self.data_list = []
        self.headers = headers

        self.root = Toplevel(self.master)
        self.root.geometry("+400+250")
        self.root.resizable(True, False)
        self.root.transient(master)
        self.root.title(title)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.frame_top = ttk.Frame(self.root)
        self.frame_top.pack(expand=True, fill="x", padx=5, pady=5)

        self.lbl_model = ttk.Label(self.frame_top, text="Model:" if mode != "File Import" else "Transcribe:")
        self.lbl_model.pack(padx=5, side="left")

        self.var_model = StringVar(self.root)
        self.cb_model = ComboboxWithKeyNav(self.frame_top, textvariable=self.var_model, values=model_keys)
        self.cb_model.pack(padx=5, side="left")
        self.var_model.set(kwargs["set_cb_model"])

        self.frame_sheet = ttk.Frame(self.root)
        self.frame_sheet.pack(expand=True, fill="both", padx=5, pady=5)
        self.sheet = Sheet(self.frame_sheet, headers=headers, show_x_scrollbar=False)
        self.sheet.enable_bindings()
        self.sheet.disable_bindings(
            "right_click_popup_menu",
            "rc_insert_column",
            "rc_delete_column",
            "rc_insert_row",
            "rc_delete_row",
        )
        self.sheet.edit_bindings(enable=False)
        self.sheet.pack(expand=True, fill="both")
        self.sheet.change_theme("dark green" if "dark" in theme else "light blue")

        self.frame_btn = ttk.Frame(self.root)
        self.frame_btn.pack(expand=True, fill="x", padx=5, pady=5)

        self.center_frame_btn = ttk.Frame(self.frame_btn)
        self.center_frame_btn.pack(side="top", padx=5, pady=5)

        self.btn_add = ttk.Button(self.center_frame_btn, text="Add Data", command=self.add_data)
        self.btn_add.pack(side="left", padx=5)

        self.btn_delete = ttk.Button(self.center_frame_btn, text="Delete Selected Row", command=self.delete_selected)
        self.btn_delete.pack(side="left", padx=5)

        self.btn_start = ttk.Button(self.center_frame_btn, text=f"Start {mode}", command=self.submit, style="Accent.TButton")
        self.btn_start.pack(side="left", padx=5)

        self.btn_cancel = ttk.Button(self.center_frame_btn, text="Cancel", command=self.on_close)
        self.btn_cancel.pack(side="left", padx=5)
        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except Exception:
            pass

        self.root.after(100, self.adjust_window_size)
        self.root.bind("<Configure>", lambda e: self.resize_sheet_width_to_window())

    def adjust_window_size(self):
        cur_height = self.root.winfo_height()
        self.root.geometry(f"600x{cur_height}")
        self.resize_sheet_width_to_window(with_check=False)

    def add_data(self):
        """
        Base function for adding file. Should be overridden
        """
        pass

    def update_sheet(self):
        self.sheet.set_sheet_data(self.data_list, reset_col_positions=False)

    def resize_sheet_width_to_window(self, with_check=True):
        w = self.root.winfo_width()
        if with_check and self.prev_width == w:
            return
        self.prev_width = w
        self.sheet.set_all_column_widths(w // len(self.headers) - 10)

    def delete_selected(self):
        selected_indexes = self.sheet.get_selected_rows(get_cells=False, return_tuple=True, get_cells_as_rows=True)
        if len(selected_indexes) > 0:
            if messagebox.askyesno(
                "Delete File Pair", "Are you sure you want to delete the selected file pair?", parent=self.root
            ):
                # reverse sort selected_indexes so we can delete from the end
                selected_indexes = sorted(selected_indexes, reverse=True)
                for index in selected_indexes:
                    del self.data_list[index]

                self.update_sheet()

    def submit(self):
        if len(self.data_list) == 0:
            messagebox.showerror("Error", "Add at least one file", parent=self.root)
            return

        self.submit_func(self.var_model.get(), self.data_list)
        self.root.destroy()

    def on_close(self):
        if not messagebox.askyesno("Cancel", "Are you sure you want to cancel?", parent=self.root):
            return

        self.root.destroy()


class FileImportDialog(FileOperationDialog):
    def __init__(self, master, title: str, submit_func, theme: str, **kwargs):
        super().__init__(master, title, "File Import", ["Audio / Video File"], submit_func, theme, **kwargs)

        def cb_engine_change(_event=None):
            # check if engine is whisper and currently in translate only mode
            # if yes, will make the source lang use based on the engine
            if _event in model_keys and self.var_task_transcribe.get() and not self.var_task_translate.get():
                self.cb_source_lang["values"] = engine_select_source_dict[self.var_engine.get()]
            else:
                self.cb_source_lang["values"] = engine_select_source_dict[self.var_model.get()]

            # Then update the target cb list with checks
            self.cb_target_lang["values"] = engine_select_target_dict[self.var_engine.get()]

            # check if the target lang is not in the new list
            if self.cb_target_lang.get() not in self.cb_target_lang["values"]:
                self.cb_target_lang.current(0)

            # check if the source lang is not in the new list
            if self.cb_source_lang.get() not in self.cb_source_lang["values"]:
                self.cb_source_lang.current(0)

        def cbtn_task_change():
            if self.var_task_transcribe.get() and self.var_task_translate.get():
                self.cb_model.configure(state="readonly")
                self.cb_engine.configure(state="readonly")
                self.cb_source_lang.configure(state="readonly")
                self.cb_target_lang.configure(state="readonly")
                self.btn_start.configure(state="normal")

            elif self.var_task_transcribe.get() and not self.var_task_translate.get():
                self.cb_source_lang.configure(state="readonly")
                self.cb_target_lang.configure(state="disabled")
                self.cb_engine.configure(state="disabled")
                self.cb_model.configure(state="readonly")
                self.btn_start.configure(state="normal")

            elif not self.var_task_transcribe.get() and self.var_task_translate.get():
                self.cb_source_lang.configure(state="readonly")
                self.cb_target_lang.configure(state="readonly")
                self.cb_engine.configure(state="readonly")
                self.cb_model.configure(state="disabled")
                self.btn_start.configure(state="normal")

            else:
                self.cb_source_lang.configure(state="disabled")
                self.cb_target_lang.configure(state="disabled")
                self.cb_engine.configure(state="disabled")
                self.cb_model.configure(state="disabled")
                self.btn_start.configure(state="disabled")

        # Translate engine
        ttk.Label(self.frame_top, text="Translate:").pack(padx=5, side="left")
        self.var_engine = StringVar(self.root)
        self.cb_engine = CategorizedComboBox(
            self.root,
            self.frame_top, {
                "Whisper": model_keys,
                "Google Translate": [],
                "LibreTranslate": [],
                "MyMemoryTranslator": []
            },
            cb_engine_change,
            textvariable=self.var_engine
        )
        self.cb_engine.pack(padx=5, side="left")

        # Lang from
        self.lbl_source_lang = ttk.Label(self.frame_top, text="From:")
        self.lbl_source_lang.pack(padx=5, side="left")
        self.var_source_lang = StringVar(self.root)
        self.cb_source_lang = ComboboxWithKeyNav(self.frame_top, textvariable=self.var_source_lang, state="readonly")
        self.cb_source_lang.pack(padx=5, side="left")

        # Lang to
        self.lbl_target_lang = ttk.Label(self.frame_top, text="To:")
        self.lbl_target_lang.pack(padx=5, side="left")
        self.var_target_lang = StringVar(self.root)
        self.cb_target_lang = ComboboxWithKeyNav(self.frame_top, textvariable=self.var_target_lang, state="readonly")
        self.cb_target_lang.pack(padx=5, side="left")

        # Task
        self.lbl_task = ttk.Label(self.frame_top, text="Task:")
        self.lbl_task.pack(padx=5, side="left")

        self.var_task_transcribe = BooleanVar(self.root)
        self.var_task_translate = BooleanVar(self.root)
        self.cbtn_transcribe = ttk.Checkbutton(
            self.frame_top, text="Transcribe", variable=self.var_task_transcribe, command=cbtn_task_change
        )
        self.cbtn_transcribe.pack(padx=5, side="left")
        self.cbtn_translate = ttk.Checkbutton(
            self.frame_top, text="Translate", variable=self.var_task_translate, command=cbtn_task_change
        )
        self.cbtn_translate.pack(padx=5, side="left")

        self.var_engine.set(kwargs["set_cb_engine"])
        self.var_source_lang.set(kwargs["set_cb_source_lang"])
        self.var_target_lang.set(kwargs["set_cb_target_lang"])
        self.var_task_transcribe.set(kwargs["set_task_transcribe"])
        self.var_task_translate.set(kwargs["set_task_translate"])
        self.cb_source_lang["values"] = engine_select_source_dict[self.var_model.get()]
        self.cb_target_lang["values"] = engine_select_target_dict[self.var_engine.get()]

        cbtn_task_change()

    def add_data(self):
        files = filedialog.askopenfilenames(
            title="Select a file",
            filetypes=(
                ("Audio files", "*.wav *.mp3 *.ogg *.flac *.aac *.wma *.m4a"),
                ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
                ("All files", "*.*"),
            ),
        )

        if len(files) == 0:
            return

        for file in files:
            self.data_list.append([file])

        self.update_sheet()

    def adjust_window_size(self):
        self.resize_sheet_width_to_window()

    def submit(self):
        if len(self.data_list) == 0:
            messagebox.showerror("Error", "Add at least one file", parent=self.root)
            return

        # convert self.data_list to 1d
        status = self.submit_func(
            self.var_model.get(), self.var_engine.get(),
            self.var_source_lang.get().lower(),
            self.var_target_lang.get().lower(), self.var_task_transcribe.get(), self.var_task_translate.get(),
            [x[0] for x in self.data_list]
        )
        if status:  # if status is True, meaning process thread is successfully started, then close the window
            self.root.destroy()


class TranslateResultDialog(FileOperationDialog):
    def __init__(self, master, title: str, submit_func, theme: str, **kwargs):
        super().__init__(master, title, "Translate", ["Transcription Result File (.json)"], submit_func, theme, **kwargs)
        self.lbl_model.pack_forget()
        self.cb_model.pack_forget()

        def cb_engine_change(_event=None):
            self.cb_target_lang["values"] = engine_select_target_dict[self.var_engine.get()]
            if self.cb_target_lang.get() not in self.cb_target_lang["values"]:
                self.cb_target_lang.current(0)

        # Translate engine
        ttk.Label(self.frame_top, text="Translate:").pack(padx=5, side="left")
        self.var_engine = StringVar(self.root)
        self.cb_engine = CategorizedComboBox(
            self.root,
            self.frame_top, {
                "Google Translate": [],
                "LibreTranslate": [],
                "MyMemoryTranslator": []
            },
            cb_engine_change,
            textvariable=self.var_engine
        )
        self.cb_engine.pack(padx=5, side="left")

        # Lang to
        self.lbl_target_lang = ttk.Label(self.frame_top, text="To:")
        self.lbl_target_lang.pack(padx=5, side="left")
        self.var_target_lang = StringVar(self.root)
        self.cb_target_lang = ComboboxWithKeyNav(self.frame_top, textvariable=self.var_target_lang, state="readonly")
        self.cb_target_lang.pack(padx=5, side="left")

        self.var_engine.set(kwargs["set_cb_engine"])
        self.var_target_lang.set(kwargs["set_cb_target_lang"])
        self.cb_target_lang["values"] = engine_select_target_dict[self.var_engine.get()]

        # add ? tooltip to frame_top
        self.hint = ttk.Label(self.frame_top, text="?", cursor="question_arrow", font="TkDefaultFont 9 bold")
        self.hint.pack(side="right", padx=5)
        tk_tooltip(
            self.hint,
            "Translate result of a transcription file. For this to work, you need to have a .json file of Whisper Result first.",
            wrapLength=300
        )

    def add_data(self):
        files = filedialog.askopenfilenames(
            title="Select a file",
            filetypes=(("JSON (Whisper Result)", "*.json"), ),
        )

        if len(files) == 0:
            return

        for file in files:
            self.data_list.append([file])

        self.update_sheet()

    def submit(self):
        if len(self.data_list) == 0:
            messagebox.showerror("Error", "Add at least one file", parent=self.root)
            return

        # convert self.data_list to 1d
        self.submit_func(self.var_engine.get(), self.var_target_lang.get().lower(), [x[0] for x in self.data_list])
        self.root.destroy()


class RefinementDialog(FileOperationDialog):
    def __init__(self, master, title: str, submit_func, theme: str, **kwargs):
        super().__init__(master, title, "Refinement", ["Source File", "Refinement File"], submit_func, theme, **kwargs)

        # add ? tooltip to frame_top
        self.hint = ttk.Label(self.frame_top, text="?", cursor="question_arrow", font="TkDefaultFont 9 bold")
        self.hint.pack(side="right", padx=5)
        tk_tooltip(
            self.hint,
            "Refine result of a transcription file. For this to work, you need to have a result of transcription file in .json form first.\n\n"
            "The program will try to re-transcribe the audio file with original whisper model if they found null token in the result file (which usually happen when transcribing using faster-whisper).",
            wrapLength=300
        )

    def add_data(self):
        source_f, mode_f, lang = ModResultInputDialog(self.root, "Add File Pair", self.mode, with_lang=False).get_input()

        if source_f and mode_f:
            self.data_list.append([source_f, mode_f])
            self.update_sheet()


class AlignmentDialog(FileOperationDialog):
    def __init__(self, master, title: str, submit_func, theme: str, **kwargs):
        super().__init__(
            master, title, "Alignment", ["Source File", "Alignment File", "Language"], submit_func, theme, **kwargs
        )

        # add ? tooltip to frame_top
        self.hint = ttk.Label(self.frame_top, text="?", cursor="question_arrow", font="TkDefaultFont 9 bold")
        self.hint.pack(side="right", padx=5)
        tk_tooltip(
            self.hint,
            "Align result of a transcription file. For this to work, you need to have a result of transcription file in .json form first.",
            wrapLength=300
        )

    def add_data(self):
        source_f, mode_f, lang = ModResultInputDialog(self.root, "Add File Pair", self.mode, with_lang=True).get_input()

        if source_f and mode_f:
            self.data_list.append([source_f, mode_f, lang])
            self.update_sheet()


class ModResultInputDialog:
    def __init__(self, master, title: str, mode: Union[Literal["Refinement", "Alignment"], str], with_lang=False):
        self.master = master
        self.audio_file = None
        self.result_file = None
        self.lang_value = None
        self.with_lang = with_lang
        self.mode = mode

        self.root = Toplevel(self.master)
        self.root.title(title)
        self.root.geometry("+400+250")
        self.root.resizable(True, False)
        self.root.transient(master)

        if mode == "Refinement":
            # *Refinement
            # WhisperResult can accept json directly which will be parsed into WhisperResult
            # -> kwargs = {"audio": audio_file, "result": WhisperResult(result_file)}
            # model.refine("audio.wav", WhisperResult("result.json"))

            self.audio_file_chooser = (
                ("Audio files", "*.wav *.mp3 *.ogg *.flac *.aac *.wma *.m4a"),
                ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
            )
            self.result_file_chooser = (("JSON (Whisper Result)", "*.json"), )
        else:
            # *Alignment
            # -> kwargs = {"audio": audio_file, "text": either json parsed into WhisperResult (WhisperResult(result_file)) or plain text read from file}
            # model.align("audio.wav", WhisperResult("result.json") or "text from .txt file")
            self.audio_file_chooser = (
                ("Audio files", "*.wav *.mp3 *.ogg *.flac *.aac *.wma *.m4a"),
                ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
            )
            self.result_file_chooser = (("JSON (Whisper Result)", "*.json"), ("Text (Plain text)", "*.txt"))

        self.f_1 = ttk.Frame(self.root)
        self.f_1.pack(padx=5, pady=(5, 0), expand=True, fill="x")

        self.f_2 = ttk.Frame(self.root)
        self.f_2.pack(padx=5, expand=True, fill="x")

        ttk.Label(self.f_1, text="Source File", width=14).pack(side="left", padx=(0, 5))
        self.source_file_entry = ttk.Entry(self.f_1)
        self.source_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.source_file_entry.bind("<Key>", lambda e: "break")

        self.btn_source_file = ttk.Button(self.f_1, text="Browse", command=self.browse_source_file)
        self.btn_source_file.pack(side="left")
        tk_tooltips(
            [self.source_file_entry, self.btn_source_file],
            f"This should be either an audio file or a video file that you wish to do {mode.lower()} on",
            wrapLength=300
        )

        ttk.Label(self.f_2, text=f"{mode} File", width=14).pack(side="left", padx=(0, 5))
        self.result_file_entry = ttk.Entry(self.f_2)
        self.result_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.result_file_entry.bind("<Key>", lambda e: "break")

        self.btn_result_file = ttk.Button(self.f_2, text="Browse", command=self.browse_result_file)
        self.btn_result_file.pack(side="left")
        tk_tooltips(
            [self.result_file_entry, self.btn_result_file],
            "This should be a .json file containing the result of transcription generated by stable whisper"
            if mode == "refinement" else
            "This should be either a .json file containing the result of a transcription generated by stable whisper or a .txt file containing the text to align with the audio file.",
            wrapLength=300
        )

        if with_lang:

            def lang_change(value):
                self.lang_value = value if value != "None" else None

            self.f_3 = ttk.Frame(self.root)
            self.f_3.pack(padx=5, expand=True, fill="x")

            ttk.Label(self.f_3, text="Language", width=14).pack(padx=(0, 5), side="left")
            self.select_cb = ComboboxWithKeyNav(self.f_3, values=["None"] + whisper_compatible_uppercase, state="readonly")
            self.select_cb.pack(fill="x", expand=True, side="left")
            self.select_cb.current(0)
            self.select_cb.bind("<<ComboboxSelected>>", lambda e: lang_change(self.select_cb.get()))

        self.f_btn = ttk.Frame(self.root)
        self.f_btn.pack(padx=5, pady=5, expand=True, fill="x")

        self.f_centered_btn = ttk.Frame(self.f_btn)
        self.f_centered_btn.pack(side="top")

        self.btn_add = ttk.Button(self.f_centered_btn, text="Add", command=self.add_file_pair, state="disabled")
        self.btn_add.pack(padx=5, side="left")

        self.btn_cancel = ttk.Button(self.f_centered_btn, text="Cancel", command=self.cancel)
        self.btn_cancel.pack(padx=5, side="left")

        self.btn_reset = ttk.Button(self.f_centered_btn, text="Reset", command=self.reset)
        self.btn_reset.pack(padx=5, side="left")

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except Exception:
            pass

        self.root.after(100, self.adjust_window_size)

    def adjust_window_size(self):
        cur_height = self.root.winfo_height()
        self.root.geometry(f"500x{cur_height}")

    def browse_source_file(self):
        temp = filedialog.askopenfilename(
            title=f"Select a file that you wish to do {self.mode} on",
            filetypes=self.audio_file_chooser,
        )
        if len(temp) > 0:
            self.audio_file = temp
            self.source_file_entry.delete(0, "end")
            self.source_file_entry.insert(0, self.audio_file)

        if self.audio_file is not None and self.result_file is not None:
            self.btn_add.config(state="enabled")
        else:
            self.btn_add.config(state="disabled")

    def browse_result_file(self):
        temp = filedialog.askopenfilename(
            title=f"Select result file for {self.mode}",
            filetypes=self.result_file_chooser,
        )

        if len(temp) > 0:
            self.result_file = temp
            self.result_file_entry.delete(0, "end")
            self.result_file_entry.insert(0, self.result_file)

        if self.audio_file is not None and self.result_file is not None:
            self.btn_add.config(state="enabled")
        else:
            self.btn_add.config(state="disabled")

    def add_file_pair(self):
        if self.audio_file is None or self.result_file is None:
            return

        self.root.destroy()

    def cancel(self):
        if self.audio_file is not None or self.result_file is not None or self.lang_value is not None:
            # ask if user really want to cancel
            if not messagebox.askyesno("Cancel", "Are you sure you want to cancel?", parent=self.root):
                return

        self.audio_file = None
        self.result_file = None
        self.lang_value = None

        self.root.destroy()

    def reset(self):
        self.audio_file = None
        self.result_file = None
        self.lang_value = None

        self.source_file_entry.delete(0, "end")
        self.result_file_entry.delete(0, "end")

    def get_input(self):
        self.root.wait_window()

        return self.audio_file, self.result_file, self.lang_value


class QueueDialog:
    def __init__(self, master: Union[Tk, Toplevel], title: str, headers: List, queue: List[List], theme: str):
        """A dialog for showing queue of files

        Parameters
        ----------
        master : Union[Tk, Toplevel]
            A tkinter window
        title : str
            Title of the dialog
        headers : List
            Headers of the table
        queue : List[List]
            Queue of files
        theme : str
            Theme of the dialog sheet
        """

        self.prev_width = None
        self.master = master
        self.queue = queue
        self.headers = headers
        self.showing = True  # Showing at first
        self.thread_refresh = None

        self.root = Toplevel(self.master)
        self.root.title(title)
        self.root.geometry("+400+250")
        self.root.resizable(True, False)
        self.root.transient(master)

        self.frame = ttk.Frame(self.root)
        self.frame.pack(expand=True, fill="both", padx=5, pady=5)

        self.sheet = Sheet(self.frame, headers=headers, show_x_scrollbar=False)
        self.sheet.enable_bindings()
        self.sheet.edit_bindings(enable=False)
        self.sheet.pack(expand=True, fill="both")
        self.sheet.change_theme("dark green" if "dark" in theme else "light blue")
        self.sheet.set_sheet_data(queue)

        self.frame_bottom = ttk.Frame(self.root)
        self.frame_bottom.pack(expand=True, fill="x", padx=5, pady=5)

        self.text_log = Text(self.frame_bottom, height=4, width=50, font=("Consolas", 10))
        self.text_log.pack(side="top", fill="both", expand=True, padx=5, pady=(0, 5))
        self.text_log.bind("<Key>", lambda event: "break")
        self.text_log.insert(1.0, "Preparing...")

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except Exception:
            pass

        # clear recent_stderr
        recent_stderr.clear()

        self.root.bind("<Configure>", lambda e: self.resize_sheet_width_to_window())
        self.root.after(0, self.after_show_called)
        self.root.after(100, self.adjust_window_size)

    def after_show_called(self):
        self.start_refresh_thread()

    def start_refresh_thread(self):
        if self.thread_refresh and self.thread_refresh.is_alive():
            return

        def update_periodically():
            while self.showing:
                try:
                    self.update_log()
                    sleep(1)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)

                    break

        self.thread_refresh = Thread(target=update_periodically, daemon=True)
        self.thread_refresh.start()

    def update_log(self):
        # get only last 4 lines
        content = "\n".join(recent_stderr[-4:])
        self.text_log.delete(1.0, "end")
        self.text_log.insert(1.0, content)
        self.text_log.see("end")  # scroll to the bottom

    def adjust_window_size(self):
        m_width = self.master.winfo_width()
        cur_height = self.root.winfo_height()
        self.root.geometry(f"900x{cur_height}+{m_width + 250}+250")
        self.resize_sheet_width_to_window()

    def update_sheet(self, queue=None):
        self.sheet.set_sheet_data(queue if queue is not None else self.queue, reset_col_positions=False)

    def resize_sheet_width_to_window(self, with_check=True):
        w = self.root.winfo_width()
        if with_check and self.prev_width == w:
            return
        self.prev_width = w
        self.sheet.set_all_column_widths(w // len(self.headers) - 10)

    def on_close(self):
        self.showing = False
        self.root.withdraw()

    def show(self):
        self.root.wm_deiconify()
        self.showing = True
        self.start_refresh_thread()

    def toggle_show(self):
        if self.showing:
            self.on_close()
        else:
            self.show()


class FileProcessDialog:
    def __init__(self, master: Union[Tk, Toplevel], title: str, mode: str, header: List, sj):

        # window to show progress
        self.root = Toplevel(master)
        self.root.title(title)
        self.root.transient(master)
        self.root.geometry("450x225")
        self.root.protocol("WM_DELETE_WINDOW", lambda: master.state("iconic"))  # minimize window when click close button
        self.root.geometry("+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))
        try:
            self.root.iconbitmap(app_icon)
        except Exception:
            pass

        # widgets
        self.frame_lbl = ttk.Frame(self.root)
        self.frame_lbl.pack(side="top", fill="both", padx=5, pady=5, expand=True)

        self.frame_lbl_1 = ttk.Frame(self.frame_lbl)
        self.frame_lbl_1.pack(side="top", fill="x", expand=True)

        self.frame_lbl_2 = ttk.Frame(self.frame_lbl)
        self.frame_lbl_2.pack(side="top", fill="x", expand=True)

        self.frame_lbl_3 = ttk.Frame(self.frame_lbl)
        self.frame_lbl_3.pack(side="top", fill="x", expand=True)

        self.frame_lbl_4 = ttk.Frame(self.frame_lbl)
        self.frame_lbl_4.pack(side="top", fill="x", expand=True)

        self.frame_lbl_5 = ttk.Frame(self.frame_lbl)
        self.frame_lbl_5.pack(side="top", fill="x", expand=True)

        self.frame_lbl_6 = ttk.Frame(self.frame_lbl)
        self.frame_lbl_6.pack(side="top", fill="x", expand=True)

        self.frame_btn = ttk.Frame(self.root)
        self.frame_btn.pack(side="top", fill="x", padx=5, pady=5, expand=True)

        self.frame_btn_1 = ttk.Frame(self.frame_btn)
        self.frame_btn_1.pack(side="top", fill="x", expand=True)

        self.lbl_task_name = ttk.Label(self.frame_lbl_1, text="Task: ⌛")
        self.lbl_task_name.pack(side="left", fill="x", padx=5, pady=5)

        self.lbl_files = LabelTitleText(self.frame_lbl_2, "Files: ", "⌛")
        self.lbl_files.pack(side="left", fill="x", padx=5, pady=5)

        self.lbl_processed = LabelTitleText(self.frame_lbl_3, "Processed: ", "0")
        self.lbl_processed.pack(side="left", fill="x", padx=5, pady=5)

        self.lbl_elapsed = LabelTitleText(self.frame_lbl_4, "Elapsed: ", "0s")
        self.lbl_elapsed.pack(side="left", fill="x", padx=5, pady=5)

        self.progress_bar = ttk.Progressbar(self.frame_lbl_5, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(side="left", fill="x", padx=5, pady=5, expand=True)

        self.cbtn_open_folder = ttk.Checkbutton(
            self.frame_lbl_6,
            text="Open folder after process",
            state="disabled",
            command=lambda: sj.save_key(f"auto_open_dir_{mode}", self.cbtn_open_folder.instate(["selected"])),
        )
        self.cbtn_open_folder.pack(side="left", fill="x", padx=5, pady=5)

        self.queue_window = QueueDialog(self.root, "Result Translate Queue", header, [[]], theme=sj.cache["theme"])
        self.queue_window.update_sheet()

        self.btn_add = ttk.Button(self.frame_btn_1, text="Add", state="disabled")
        self.btn_add.pack(side="left", fill="x", padx=5, pady=5, expand=True)

        self.btn_show_queue = ttk.Button(self.frame_btn_1, text="Toggle Queue Window", command=self.queue_window.toggle_show)
        self.btn_show_queue.pack(side="left", fill="x", padx=5, pady=5, expand=True)

        self.btn_cancel = ttk.Button(self.frame_btn_1, text="Cancel", state="disabled", style="Accent.TButton")
        self.btn_cancel.pack(side="left", fill="x", padx=5, pady=5, expand=True)
