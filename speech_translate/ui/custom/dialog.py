import os
from tkinter import IntVar, ttk, Tk, Toplevel, filedialog, StringVar, BooleanVar, messagebox, Text
from typing import List, Literal, Union
from time import sleep
from threading import Thread

from tksheet import Sheet
from loguru import logger

from speech_translate._path import app_icon
from speech_translate._logging import dir_log, current_log
from speech_translate.ui.custom.combobox import CategorizedComboBox, ComboboxWithKeyNav
from speech_translate.utils.whisper.helper import model_keys
from speech_translate.utils.translate.language import (
    engine_select_source_dict, engine_select_target_dict, whisper_compatible
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
        mode: Literal["File Import", "Refinement", "Alignment"],
        headers: List,
        submit_func,
        theme,
        **file_import_kwargs,
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

        self.frame_model = ttk.Frame(self.root)
        self.frame_model.pack(expand=True, fill="x", padx=5, pady=5)

        ttk.Label(self.frame_model, text="Model:" if mode != "File Import" else "Transcribe:").pack(padx=5, side="left")
        self.var_model = StringVar(self.root)
        self.cb_model = ComboboxWithKeyNav(self.frame_model, textvariable=self.var_model, values=model_keys)
        self.cb_model.pack(padx=5, side="left")

        if mode == "File Import":

            def cb_engine_change(_event=None):
                if _event:
                    # check if engine is whisper and currently in translate only mode
                    # if yes, will make the transcribe model combobox disabled
                    if _event in model_keys and self.var_task_transcribe.get() and not self.var_task_translate.get():
                        self.cb_model.configure(state="disabled")
                    else:
                        self.cb_model.configure(state="readonly")

                    # Then update the target cb list with checks
                    self.cb_source_lang["values"] = engine_select_source_dict[self.var_model.get()]
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
                    if self.var_engine.get() in model_keys:
                        self.cb_model.configure(state="disabled")
                    else:
                        self.cb_model.configure(state="readonly")
                    self.btn_start.configure(state="normal")

                else:
                    self.cb_source_lang.configure(state="disabled")
                    self.cb_target_lang.configure(state="disabled")
                    self.cb_engine.configure(state="disabled")
                    self.cb_model.configure(state="disabled")
                    self.btn_start.configure(state="disabled")

            # Translate engine
            ttk.Label(self.frame_model, text="Translate:").pack(padx=5, side="left")
            self.var_engine = StringVar(self.root)
            self.cb_engine = CategorizedComboBox(
                self.root,
                self.frame_model, {
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
            ttk.Label(self.frame_model, text="From:").pack(padx=5, side="left")
            self.var_source_lang = StringVar(self.root)
            self.cb_source_lang = ComboboxWithKeyNav(self.frame_model, textvariable=self.var_source_lang)
            self.cb_source_lang.pack(padx=5, side="left")

            # Lang to
            ttk.Label(self.frame_model, text="To:").pack(padx=5, side="left")
            self.var_target_lang = StringVar(self.root)
            self.cb_target_lang = ComboboxWithKeyNav(self.frame_model, textvariable=self.var_target_lang)
            self.cb_target_lang.pack(padx=5, side="left")

            # Task
            ttk.Label(self.frame_model, text="Task:").pack(padx=5, side="left")
            self.var_task_transcribe = BooleanVar(self.root)
            self.var_task_translate = BooleanVar(self.root)

            self.cbtn_transcribe = ttk.Checkbutton(
                self.frame_model, text="Transcribe", variable=self.var_task_transcribe, command=cbtn_task_change
            )
            self.cbtn_transcribe.pack(padx=5, side="left")
            self.cbtn_translate = ttk.Checkbutton(
                self.frame_model, text="Translate", variable=self.var_task_translate, command=cbtn_task_change
            )
            self.cbtn_translate.pack(padx=5, side="left")

            self.var_model.set(file_import_kwargs["set_cb_model"])
            self.var_engine.set(file_import_kwargs["set_cb_engine"])
            self.var_source_lang.set(file_import_kwargs["set_cb_source_lang"])
            self.var_target_lang.set(file_import_kwargs["set_cb_target_lang"])
            self.var_task_transcribe.set(file_import_kwargs["set_task_transcribe"])
            self.var_task_translate.set(file_import_kwargs["set_task_translate"])
            self.cb_source_lang["values"] = engine_select_source_dict[self.var_model.get()]
            self.cb_target_lang["values"] = engine_select_target_dict[self.var_engine.get()]

        self.frame_sheet = ttk.Frame(self.root)
        self.frame_sheet.pack(expand=True, fill="both", padx=5, pady=5)
        self.sheet = Sheet(self.frame_sheet, headers=headers, show_x_scrollbar=False)
        self.sheet.enable_bindings()
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

        if mode == "File Import":
            cbtn_task_change()  # type: ignore

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
        self.sheet.set_all_column_widths(w // len(self.headers) - 45)

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
        self.root.destroy()


class FileImportDialog(FileOperationDialog):
    def __init__(self, master, title: str, submit_func, theme: str, **kwargs):
        super().__init__(master, title, "File Import", ["Audio / Video File"], submit_func, theme, **kwargs)

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
            self.var_model.get(), self.var_engine.get(), self.var_source_lang.get(), self.var_target_lang.get(),
            self.var_task_transcribe.get(), self.var_task_translate.get(), [x[0] for x in self.data_list]
        )
        if status:  # if status is True, meaning process thread is successfully started, then close the window
            self.root.destroy()


class RefinementDialog(FileOperationDialog):
    def __init__(self, master, title: str, submit_func, theme: str, **kwargs):
        super().__init__(master, title, "Refinement", ["Source File", "Refinement File"], submit_func, theme, **kwargs)

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
            self.result_file_chooser = (("JSON", "*.json"), )
        else:
            # *Alignment
            # -> kwargs = {"audio": audio_file, "text": either json parsed into WhisperResult (WhisperResult(result_file)) or plain text read from file}
            # model.align("audio.wav", WhisperResult("result.json") or "text from .txt file")
            self.audio_file_chooser = (
                ("Audio files", "*.wav *.mp3 *.ogg *.flac *.aac *.wma *.m4a"),
                ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
            )
            self.result_file_chooser = (("JSON", "*.json"), ("Text", "*.txt"))

        self.f_1 = ttk.Frame(self.root)
        self.f_1.pack(padx=5, pady=(5, 0), expand=True, fill="x")

        self.f_2 = ttk.Frame(self.root)
        self.f_2.pack(padx=5, expand=True, fill="x")

        ttk.Label(self.f_1, text="Source File", width=14).pack(side="left", padx=(0, 5))
        self.audio_file_entry = ttk.Entry(self.f_1)
        self.audio_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.audio_file_entry.bind("<Key>", lambda e: "break")

        ttk.Button(self.f_1, text="Browse", command=self.browse_audio_file).pack(side="left")

        ttk.Label(self.f_2, text=f"{mode} File", width=14).pack(side="left", padx=(0, 5))
        self.result_file_entry = ttk.Entry(self.f_2)
        self.result_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.result_file_entry.bind("<Key>", lambda e: "break")

        ttk.Button(self.f_2, text="Browse", command=self.browse_result_file).pack(side="left")

        if with_lang:
            self.f_3 = ttk.Frame(self.root)
            self.f_3.pack(padx=5, expand=True, fill="x")

            ttk.Label(self.f_3, text="Language", width=14).pack(padx=(0, 5), side="left")
            self.select_cb = ComboboxWithKeyNav(self.f_3, values=["None"] + whisper_compatible, state="readonly")
            self.select_cb.pack(fill="x", expand=True, side="left")
            self.select_cb.current(0)

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

    def browse_audio_file(self):
        temp = filedialog.askopenfilename(
            title=f"Select a file that you wish to do {self.mode} on",
            filetypes=self.audio_file_chooser,
        )
        if len(temp) > 0:
            self.audio_file = temp
            self.audio_file_entry.delete(0, "end")
            self.audio_file_entry.insert(0, self.audio_file)

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

        if self.with_lang:
            self.lang_value = self.select_cb.get()
        self.root.destroy()

    def cancel(self):
        self.audio_file = None
        self.result_file = None
        self.lang_value = None

        self.root.destroy()

    def reset(self):
        self.audio_file = None
        self.result_file = None
        self.lang_value = None

        self.audio_file_entry.delete(0, "end")
        self.result_file_entry.delete(0, "end")

    def get_input(self):
        self.root.wait_window()
        if self.lang_value == "None":
            self.lang_value = None

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

        self.text_log = Text(self.frame_bottom, height=4, width=50, font=("Consolas", 8))
        self.text_log.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))
        self.text_log.bind("<Key>", lambda event: "break")
        self.text_log.insert(1.0, "Preparing...")

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(app_icon)
        except Exception:
            pass

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
        try:
            content = open(os.path.join(dir_log, current_log), "r", encoding="utf-8").read().strip()
        except Exception as e:
            content = "Failed to read log file\nError: " + str(e)

        # get only last 4 lines
        content = "\n".join(content.split("\n")[-4:])
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
