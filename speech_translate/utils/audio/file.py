from os import path
from datetime import datetime
from threading import Thread
from time import gmtime, sleep, strftime, time
from tkinter import Toplevel, filedialog, ttk
from typing import List, Literal, Union

import stable_whisper  # https://github.com/jianfch/stable-ts # has no static annotation hence many type ignore
from whisper.tokenizer import TO_LANGUAGE_CODE
from kill_thread import kill_thread

from speech_translate._path import app_icon, dir_export, dir_alignment, dir_refinement
from speech_translate.ui.custom.label import LabelTitleText
from speech_translate.ui.custom.dialog import ModResultInputDialog, QueueDialog
from speech_translate.ui.custom.message import mbox
from speech_translate._logging import logger
from speech_translate.globals import gc, sj

from ..helper import cbtn_invoker, get_proxies, native_notify, filename_only, start_file, up_first_case
from ..whisper.helper import get_model, get_model_args, get_tc_args, save_output_stable_ts, model_values
from ..translate.translator import translate

# Global variable
# to track which file is processed
# index 0 (even) is the name of the file, index 1 (odd) is the status (True if success, False if failed)
processed_tc = []
processed_tl = []


# run in threaded environment with queue and exception to cancel
def cancellable_tc(
    audio_name: str,
    lang_source: str,
    lang_target: str,
    stable_tc,
    stable_tl,
    auto: bool,
    transcribe: bool,
    translate: bool,
    engine: str,
    save_name: str,
    tracker_name: str,
    **whisper_args,
) -> None:
    """
    Transcribe and translate audio/video file with whisper.
    Also cancelable like the cancellable_tl function

    Args
    ----
    audio_name: str
        path to file
    lang_source: str
        source language
    lang_target: str
        target language
    model_loaded: whisper.Whisper
        loaded whisper model for transcribing
    model_tl: whisper.Whisper
        loaded whisper model for translating
    auto: bool
        if True, source language will be auto detected
    transcribe: bool
        if True, transcribe the audio
    translate: bool
        if True, translate the transcription
    engine: str
        engine to use for translation
    tracker_name: str
        name to track the progress
    **whisper_args:
        whisper parameter

    Returns
    -------
    None
    """
    assert gc.mw is not None
    start = time()
    gc.enable_tc()

    try:
        f_name = save_name.replace("{task}", "transcribe")
        f_name = f_name.replace("{task-short}", "tc")

        logger.info("-" * 50)
        logger.info("Transcribing")
        logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")

        fail = False
        fail_msg = ""
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]

        def run_threaded():
            try:
                result = stable_tc(audio_name, task="transcribe", **whisper_args)
                gc.data_queue.put(result)  # borrow gc_data_queue to pass result
            except Exception as e:
                nonlocal fail, fail_msg
                fail = True
                fail_msg = e

        thread = Thread(target=run_threaded, daemon=True)
        thread.start()

        while thread.is_alive():
            if not gc.transcribing:
                logger.debug("Cancelling transcription")
                kill_thread(thread)
                raise Exception("Cancelled")
            sleep(0.1)

        if fail:
            raise Exception(fail_msg)

        result_tc: stable_whisper.WhisperResult = gc.data_queue.get()

        # export if transcribe mode is on
        if transcribe:
            result_text = result_tc.text.strip()

            if len(result_text) > 0:
                gc.file_tced_counter += 1
                save_output_stable_ts(result_tc, path.join(export_to, f_name), sj.cache["export_to"], sj)
            else:
                logger.warning("Transcribed Text is empty")

        # start translation thread if translate mode is on
        if translate:
            # send result as srt if not using whisper because it will be send to translation API.
            # If using whisper translation will be done using whisper model
            to_tl = result_tc if engine not in model_values else audio_name
            translateThread = Thread(
                target=cancellable_tl,
                args=[to_tl, lang_source, lang_target, stable_tl, engine, auto, save_name, tracker_name],
                kwargs=whisper_args,
                daemon=True,
            )

            translateThread.start()  # Start translation in a new thread to prevent blocking

        processed_tc.append(tracker_name)
        processed_tc.append(True)
        logger.debug(f"Transcribing Audio: {f_name} | Time Taken: {time() - start:.2f}s")
    except Exception as e:
        processed_tc.append(tracker_name)
        processed_tc.append(False)
        if str(e) == "Cancelled":
            logger.info("Transcribing cancelled")
        else:
            logger.exception(e)
            native_notify("Error: Transcribing Audio", str(e))
    finally:
        gc.disable_tc()


def cancellable_tl(
    query: Union[str, stable_whisper.WhisperResult],
    lang_source: str,
    lang_target: str,
    stable_tl,
    engine: str,
    auto: bool,
    save_name: str,
    tracker_name: str,
    **whisper_args,
):
    """
    Translate the result of file input using either whisper model or translation API
    This function is cancellable with the cancel flag that is set by the cancel button and will be checked periodically every
    0.1 seconds. If the cancel flag is set, the function will raise an exception to stop the thread

    Args
    ----
    query: str
        audio file path if engine is whisper, text in .srt format if engine is translation API
    lang_source: str
        source language
    lang_target: str
        target language
    model_loaded: whisper.Whisper
        loaded whisper model
    engine: str
        engine to use
    auto: bool
        whether to use auto language detection
    save_name: str
        name of the file to save the translation to
    tracker_name: str
        name to track the progress
    **whisper_args:
        whisper parameter

    Returns
    -------
    None
    """
    assert gc.mw is not None
    start = time()
    gc.enable_tl()

    try:
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]
        f_name = save_name.replace("{task}", "translate")
        f_name = f_name.replace("{task-short}", "tl")

        logger.info("-" * 50)
        logger.info("Translating")

        if engine in model_values:
            logger.debug("Translating with whisper")
            logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")

            fail = False
            fail_msg = ""

            def run_threaded():
                try:
                    result = stable_tl(query, task="translate", **whisper_args)
                    gc.data_queue.put(result)
                except Exception as e:
                    nonlocal fail, fail_msg
                    fail = True
                    fail_msg = e

            thread = Thread(target=run_threaded, daemon=True)
            thread.start()

            while thread.is_alive():
                if not gc.translating:
                    logger.debug("Cancelling translation")
                    kill_thread(thread)
                    raise Exception("Cancelled")
                sleep(0.1)

            if fail:
                raise Exception(fail_msg)

            result_tl: stable_whisper.WhisperResult = gc.data_queue.get()

            # if whisper, sended text (toTranslate) is the audio file path
            resultTxt = result_tl.text.strip()

            if len(resultTxt) > 0:
                gc.file_tled_counter += 1
                save_output_stable_ts(result_tl, path.join(export_to, f_name), sj.cache["export_to"], sj)
            else:
                logger.warning("Translated Text is empty")
        else:
            assert isinstance(query, stable_whisper.WhisperResult)
            if len(query.text.strip()) == 0:
                logger.warning("Translated Text is empty")
                return

            debug_log = sj.cache["debug_translate"]
            proxies = get_proxies(sj.cache["http_proxy"], sj.cache["https_proxy"])
            kwargs = {}
            if engine == "LibreTranslate":
                kwargs["libre_https"] = sj.cache["libre_https"],
                kwargs["libre_host"] = sj.cache["libre_host"],
                kwargs["libre_port"] = sj.cache["libre_port"],
                kwargs["libre_api_key"] = sj.cache["libre_api_key"],

            fail = False
            fail_msg = ""

            def run_threaded():
                try:
                    # translate every text and words in each segments, replace it
                    segment_texts = [segment.text for segment in query.segments]

                    # tl text in that segment
                    success, result = translate(
                        engine, segment_texts, lang_source, lang_target, proxies, debug_log, **kwargs
                    )

                    # replace
                    word_replaced_segment_id = []
                    for segment in query.segments:
                        # also add space back because its removed automatically in the api call
                        segment.text = result.pop(0) + " "

                        # because each word is taken from the text, we can replace the word with the translated text
                        # but we fierst need to check wether the length of splitted translated text is same as the length of words
                        if sj.cache["word_level"]:
                            temp = segment.text.split()
                            if len(temp) == len(segment.words):
                                word_replaced_segment_id.append(segment.id)
                                for word in segment.words:
                                    word.word = temp.pop(0)  # replace

                    if sj.cache["word_level"]:
                        for segment in query.segments:
                            # if already replaced, skip
                            if segment.id in word_replaced_segment_id:
                                continue

                            # tl words in that segment
                            word_texts = [word.word for word in segment.words]
                            success, result = translate(
                                engine, word_texts, lang_source, lang_target, proxies, debug_log, **kwargs
                            )
                            if not success:
                                native_notify(f"Error: translation with {engine} failed", result)
                                raise Exception(result)

                            # replace
                            for word in segment.words:
                                word.word = result.pop(0)

                except Exception as e:
                    nonlocal fail, fail_msg
                    fail = True
                    fail_msg = e

            thread = Thread(target=run_threaded, daemon=True)
            thread.start()

            while thread.is_alive():
                if not gc.translating:
                    logger.debug("Cancelling translation")
                    kill_thread(thread)
                    raise Exception("Cancelled")
                sleep(0.1)

            if fail:
                raise Exception(fail_msg)

            gc.file_tled_counter += 1
            save_output_stable_ts(query, path.join(export_to, f_name), sj.cache["export_to"], sj)

        processed_tl.append(tracker_name)
        processed_tl.append(True)
        logger.debug(f"Translated: {f_name} | Time Taken: {time() - start:.2f}s")
    except Exception as e:
        processed_tl.append(tracker_name)
        processed_tl.append(False)
        if str(e) == "Cancelled":
            logger.info("Translation cancelled")
        else:
            logger.exception(e)
            native_notify(f"Error: translation with {engine} failed", str(e))
    finally:
        gc.disable_tl()  # flag processing as done. No need to check for transcription because it is done before this


def import_file(
    files: List[str], model_name_tc: str, lang_source: str, lang_target: str, transcribe: bool, translate: bool, engine: str
) -> None:
    """Function to transcribe and translate from audio/video files.

    Args
    ----
    files (list[str])
        The path to the audio/video file.
    model_name_tc (str)
        The model to use for transcribing.
    lang_source (str)
        The language of the input.
    lang_target (str)
        The language to translate to.
    transcibe (bool)
        Whether to transcribe the audio.
    translate (bool)
        Whether to translate the audio.
    engine (str)
        The engine to use for the translation.

    Returns
    -------
        None
    """
    assert gc.mw is not None
    # window to show progress
    master = gc.mw.root
    root = Toplevel(master)
    root.title("File Import Progress")
    root.transient(master)
    root.geometry("450x225")
    root.protocol("WM_DELETE_WINDOW", lambda: master.state("iconic"))  # minimize window when click close button
    root.geometry("+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))
    try:
        root.iconbitmap(app_icon)
    except Exception:
        pass

    # widgets
    frame_lbl = ttk.Frame(root)
    frame_lbl.pack(side="top", fill="both", padx=5, pady=5, expand=True)

    frame_lbl_1 = ttk.Frame(frame_lbl)
    frame_lbl_1.pack(side="top", fill="x", expand=True)

    frame_lbl_2 = ttk.Frame(frame_lbl)
    frame_lbl_2.pack(side="top", fill="x", expand=True)

    frame_lbl_3 = ttk.Frame(frame_lbl)
    frame_lbl_3.pack(side="top", fill="x", expand=True)

    frame_lbl_4 = ttk.Frame(frame_lbl)
    frame_lbl_4.pack(side="top", fill="x", expand=True)

    frame_lbl_5 = ttk.Frame(frame_lbl)
    frame_lbl_5.pack(side="top", fill="x", expand=True)

    frame_lbl_6 = ttk.Frame(frame_lbl)
    frame_lbl_6.pack(side="top", fill="x", expand=True)

    frame_btn = ttk.Frame(root)
    frame_btn.pack(side="top", fill="x", padx=5, pady=5, expand=True)

    frame_btn_1 = ttk.Frame(frame_btn)
    frame_btn_1.pack(side="top", fill="x", expand=True)

    frame_btn_2 = ttk.Frame(frame_btn)
    frame_btn_2.pack(side="top", fill="x", expand=True)

    lbl_task_name = ttk.Label(frame_lbl_1, text="Task: ⌛")
    lbl_task_name.pack(side="left", fill="x", padx=5, pady=5)

    lbl_files = LabelTitleText(frame_lbl_2, "Files: ", f"{len(files)}")
    lbl_files.pack(side="left", fill="x", padx=5, pady=5)

    lbl_tced = LabelTitleText(frame_lbl_3, "Transcribed: ", f"{gc.file_tced_counter}")
    lbl_tced.pack(side="left", fill="x", padx=5, pady=5)

    lbl_tled = LabelTitleText(frame_lbl_3, "Translated: ", f"{gc.file_tled_counter}")
    lbl_tled.pack(side="left", fill="x", padx=5, pady=5)

    lbl_elapsed = LabelTitleText(frame_lbl_4, "Elapsed: ", "0s")
    lbl_elapsed.pack(side="left", fill="x", padx=5, pady=5)

    progress_bar = ttk.Progressbar(frame_lbl_5, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    cbtn_open_folder = ttk.Checkbutton(
        frame_lbl_6,
        text="Open folder after process",
        state="disabled",
        command=lambda: sj.save_key("auto_open_dir_export", cbtn_open_folder.instate(["selected"])),
    )
    cbtn_open_folder.pack(side="left", fill="x", padx=5, pady=5)

    global processed_tc, processed_tl
    processed_tc = []
    processed_tl = []

    def get_queue_data():
        nonlocal files, transcribe, translate
        show = []
        for file in files:
            status = ""
            if transcribe:
                status += f"{'Transcribed' if  processed_tc[ processed_tc.index(file) + 1] else 'Failed to Transcribe'}" if file in processed_tc else "Waiting for Transcription"
            if translate:
                status += f", {'Translated' if  processed_tl[ processed_tl.index(file) + 1] else 'Failed to Translate'}" if file in processed_tl else ", Waiting for Translation"

            show.append([file, status])

        return show

    queue_window = QueueDialog(
        root, "File Import Queue", ["Audio / Video File", "Status"], get_queue_data(), theme=sj.cache["theme"]
    )
    queue_window.update_sheet()

    btn_add = ttk.Button(frame_btn_1, text="Add", state="disabled")
    btn_add.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    btn_show_queue = ttk.Button(frame_btn_1, text="Toggle Queue Window", command=queue_window.toggle_show)
    btn_show_queue.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    btn_cancel = ttk.Button(frame_btn_1, text="Cancel", state="disabled", style="Accent.TButton")
    btn_cancel.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    try:
        startProc = time()
        logger.info("Start Process (FILE)")
        gc.file_tced_counter = 0
        gc.file_tled_counter = 0

        auto = lang_source == "auto detect"
        tl_engine_whisper = engine in model_values

        export_format: str = sj.cache["export_format"]
        file_slice_start = (None if sj.cache["file_slice_start"] == "" else int(sj.cache["file_slice_start"]))
        file_slice_end = None if sj.cache["file_slice_end"] == "" else int(sj.cache["file_slice_end"])
        visualize_suppression = sj.cache["visualize_suppression"]

        # load model
        model_args = get_model_args(sj.cache)
        _, _, stable_tc, stable_tl = get_model(
            transcribe, translate, tl_engine_whisper, model_name_tc, engine, sj.cache, **model_args
        )
        whisper_args = get_tc_args(stable_tc if transcribe else stable_tl, sj.cache)
        whisper_args["language"] = TO_LANGUAGE_CODE[lang_source.lower()] if not auto else None
        if sj.cache["use_faster_whisper"] and lang_source == "english":  # to remove warning from stable-ts
            whisper_args["language"] = None

        # update button text
        gc.mw.btn_import_file.configure(text="Cancel")

        timerStart = time()
        adding = False
        taskname = "Transcribe & Translate" if transcribe and translate else "Transcribe" if transcribe else "Translate"
        language = f"from {lang_source} to {lang_target}" if translate else lang_source
        logger.info(f"Model Args: {model_args}")
        logger.info(f"Process Args: {whisper_args}")
        current_file_counter = 0

        def add_to_files():
            nonlocal files, adding
            adding = True
            to_add = filedialog.askopenfilenames(
                title="Select a file",
                filetypes=(
                    ("Audio files", "*.wav *.mp3 *.ogg *.flac *.aac *.wma *.m4a"),
                    ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
                    ("All files", "*.*"),
                ),
            )

            # if still recording / processing file and user select / add files
            if gc.recording and len(to_add) > 0:
                if transcribe:
                    current_file_counter = gc.file_tced_counter
                else:
                    current_file_counter = gc.file_tled_counter
                files.extend(list(to_add))
                lbl_files.set_text(text=f"{current_file_counter}/{len(files)}")

            adding = False

        def cancel():
            # confirm
            if mbox("Cancel confirmation", "Are you sure you want to cancel file process?", 3, master):
                assert gc.mw is not None
                gc.mw.from_file_stop()

        def update_modal_ui():
            nonlocal timerStart, current_file_counter
            if gc.recording:

                lbl_files.set_text(text=f"{current_file_counter}/{len(files)}")
                lbl_elapsed.set_text(text=f"{strftime('%H:%M:%S', gmtime(time() - timerStart))}")

                if current_file_counter > 0:
                    lbl_files.set_text(
                        text=f"{current_file_counter}/{len(files)} ({filename_only(files[current_file_counter - 1])})"
                    )
                else:
                    lbl_files.set_text(
                        text=f"{current_file_counter}/{len(files)} ({filename_only(files[current_file_counter])})"
                    )

                if transcribe:
                    lbl_tced.set_text(text=f"{gc.file_tced_counter}")
                if translate:
                    lbl_tled.set_text(text=f"{gc.file_tled_counter}")

                # update progressbar
                prog_file_len = len(files) * 2 if transcribe and translate else len(files)
                progress_bar["value"] = (current_file_counter / prog_file_len * 100)

                queue_window.update_sheet(get_queue_data())
                root.after(1000, update_modal_ui)

        # widgets
        lbl_task_name.configure(text=f"Task: {taskname} {language} with {model_name_tc} model")
        lbl_elapsed.set_text(f"{round(time() - timerStart, 2)}s")
        cbtn_open_folder.configure(state="normal")
        cbtn_invoker(sj.cache["auto_open_dir_export"], cbtn_open_folder)
        btn_add.configure(state="normal", command=add_to_files)
        btn_cancel.configure(state="normal", command=cancel)

        update_modal_ui()
        gc.mw.start_loadBar()

        for file in files:
            if not gc.recording:  # if cancel button is pressed
                return

            # Proccess it
            logger.debug("FILE PROCESSING: " + file)
            file_name = filename_only(file)
            save_name = datetime.now().strftime(export_format)
            save_name = save_name.replace("{file}", file_name[file_slice_start:file_slice_end])
            save_name = save_name.replace("{lang-source}", lang_source)
            save_name = save_name.replace("{lang-target}", lang_target)
            save_name = save_name.replace("{model}", model_name_tc)
            save_name = save_name.replace("{engine}", engine)

            if visualize_suppression:
                stable_whisper.visualize_suppression(
                    file,
                    path.join(
                        dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"],
                        f"{save_name.replace('{task}', 'visualized')}.png"
                    )
                )

            if translate and tl_engine_whisper and not transcribe:  # if only translating and using the whisper engine
                proc_thread = Thread(
                    target=cancellable_tl,
                    args=[file, lang_source, lang_target, stable_tl, engine, auto, save_name, file],
                    kwargs=whisper_args,
                    daemon=True,
                )
            else:
                # will automatically check translate on or not depend on input
                # translate is called from here because other engine need to get transcribed text first if translating
                proc_thread = Thread(
                    target=cancellable_tc,
                    args=[
                        file, lang_source, lang_target, stable_tc, stable_tl, auto, transcribe, translate, engine, save_name,
                        file
                    ],
                    kwargs=whisper_args,
                    daemon=True,
                )

            proc_thread.start()
            proc_thread.join()  # wait for thread to finish until continue to next file
            current_file_counter += 1

            while adding:
                sleep(0.3)

        if translate:
            # create loop to wait for translation to finish
            # because translation is not waited in the tc thread
            while gc.translating:
                sleep(0.1)

        # destroy progress window
        if root.winfo_exists():
            root.after(100, root.destroy)

        logger.info(f"End process (FILE) [Total time: {time() - startProc:.2f}s]")

        # turn off loadbar
        gc.mw.stop_loadBar("file")
        gc.disable_rec()  # update flag

        if gc.file_tced_counter > 0 or gc.file_tled_counter > 0:
            # open folder
            if sj.cache["auto_open_dir_export"]:
                export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]
                start_file(export_to)

        resultMsg = (
            f"Transcribed {gc.file_tced_counter} file(s) and Translated {gc.file_tled_counter} file(s)"
            if transcribe and translate else
            f"Transcribed {gc.file_tced_counter} file(s)" if transcribe else f"Translated {gc.file_tled_counter} file(s)"
        )
        mbox(f"File {taskname} Done", resultMsg, 0)
    except Exception as e:
        logger.error("Error occured while processing file(s)")
        logger.exception(e)
        assert gc.mw is not None
        mbox("Error occured while processing file(s)", f"{str(e)}", 2, gc.mw.root)
        gc.mw.from_file_stop(prompt=False, notify=False)

        if root.winfo_exists():
            root.after(1000, root.destroy)  # destroy progress window


def mod_result(source_files: List, mod_files: List[str], model_name_tc: str, mode: Literal["refinement", "alignment"]):
    """Function to modify the result of the transcribe and translate process.
    To modify these results we use the refine or align function from stable whisper.

    The ui is from the import_file function, modify to fit the refine and align process.

    Parameters
    ----------
    source_files : List
        List of source files
    model_name_tc : str
        _description_
    mode : Literal[&quot;refinement&quot;, &quot;alignment&quot;]
        _description_
    """

    assert gc.mw is not None
    # window to show progress
    master = gc.mw.root
    root = Toplevel(master)
    root.title(f"File {up_first_case(mode)} Progress")
    root.transient(master)
    root.geometry("450x225")
    root.protocol("WM_DELETE_WINDOW", lambda: master.state("iconic"))  # minimize window when click close button
    root.geometry("+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))
    try:
        root.iconbitmap(app_icon)
    except Exception:
        pass

    # widgets
    frame_lbl = ttk.Frame(root)
    frame_lbl.pack(side="top", fill="both", padx=5, pady=5, expand=True)

    frame_lbl_1 = ttk.Frame(frame_lbl)
    frame_lbl_1.pack(side="top", fill="x", expand=True)

    frame_lbl_2 = ttk.Frame(frame_lbl)
    frame_lbl_2.pack(side="top", fill="x", expand=True)

    frame_lbl_3 = ttk.Frame(frame_lbl)
    frame_lbl_3.pack(side="top", fill="x", expand=True)

    frame_lbl_4 = ttk.Frame(frame_lbl)
    frame_lbl_4.pack(side="top", fill="x", expand=True)

    frame_lbl_5 = ttk.Frame(frame_lbl)
    frame_lbl_5.pack(side="top", fill="x", expand=True)

    frame_lbl_6 = ttk.Frame(frame_lbl)
    frame_lbl_6.pack(side="top", fill="x", expand=True)

    frame_btn = ttk.Frame(root)
    frame_btn.pack(side="top", fill="x", padx=5, pady=5, expand=True)

    frame_btn_1 = ttk.Frame(frame_btn)
    frame_btn_1.pack(side="top", fill="x", expand=True)

    frame_btn_2 = ttk.Frame(frame_btn)
    frame_btn_2.pack(side="top", fill="x", expand=True)

    lbl_task_name = ttk.Label(frame_lbl_1, text="Task: ⌛")
    lbl_task_name.pack(side="left", fill="x", padx=5, pady=5)

    lbl_files = LabelTitleText(frame_lbl_2, "Files: ", f"{len(source_files)}")
    lbl_files.pack(side="left", fill="x", padx=5, pady=5)

    lbl_processed = LabelTitleText(frame_lbl_3, "Processed: ", "0")
    lbl_processed.pack(side="left", fill="x", padx=5, pady=5)

    lbl_elapsed = LabelTitleText(frame_lbl_4, "Elapsed: ", "0s")
    lbl_elapsed.pack(side="left", fill="x", padx=5, pady=5)

    progress_bar = ttk.Progressbar(frame_lbl_5, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    cbtn_open_folder = ttk.Checkbutton(
        frame_lbl_6,
        text="Open folder after process",
        state="disabled",
        command=lambda: sj.save_key(f"auto_open_dir_{mode}", cbtn_open_folder.instate(["selected"])),
    )
    cbtn_open_folder.pack(side="left", fill="x", padx=5, pady=5)

    btn_add = ttk.Button(frame_btn_1, text="Add", state="disabled")
    btn_add.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    btn_cancel = ttk.Button(frame_btn_1, text="Cancel", state="disabled", style="Accent.TButton")
    btn_cancel.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    try:
        logger.info("Start Process (FILE)")
        startProc = time()
        gc.mod_file_counter = 0
        adding = False
        action_name = "Refined" if mode == "refinement" else "Aligned"

        # load model
        model_args = get_model_args(sj.cache)
        model = stable_whisper.load_model(model_name_tc, **model_args)
        mod_dict = {"refinement": model.refine, "alignment": model.align}
        mod_function = mod_dict[mode]

        whisper_args = get_tc_args(mod_function, sj.cache)

        # add lang on the loop later
        timerStart = time()
        logger.info(f"Model Args: {model_args}")
        logger.info(f"Process Args: {whisper_args}")

        def add_to_files():
            nonlocal source_files, adding
            if adding:
                return

            adding = True
            source_f, mode_f, lang = ModResultInputDialog(
                root, "Add File Pair", up_first_case(mode), with_lang=True if mode == "alignment" else False
            ).get_input()

            # if still processing file and user select / add files
            if source_f and mode_f:
                if mode == "alignment":
                    source_files.extend((source_f, mode_f, lang))
                else:
                    source_files.extend((source_f, mode_f))

                lbl_files.set_text(text=f"{gc.mod_file_counter}/{len(source_files)}")

            adding = False

        def cancel():
            # confirm
            if mbox("Cancel confirmation", f"Are you sure you want to cancel {mode} process?", 3, master):
                assert gc.mw is not None
                if mode == "refinement":
                    gc.mw.refinement_stop()
                else:
                    gc.mw.alignment_stop()

        def update_modal_ui():
            nonlocal timerStart
            if gc.recording:

                lbl_files.set_text(text=f"{gc.mod_file_counter}/{len(source_files)}")
                lbl_elapsed.set_text(text=f"{strftime('%H:%M:%S', gmtime(time() - timerStart))}")

                if gc.mod_file_counter > 0:
                    lbl_files.set_text(
                        text=
                        f"{gc.mod_file_counter}/{len(source_files)} ({filename_only(source_files[gc.mod_file_counter - 1][0])})"
                    )
                else:
                    lbl_files.set_text(
                        text=
                        f"{gc.mod_file_counter}/{len(source_files)} ({filename_only(source_files[gc.mod_file_counter][0])})"
                    )

                lbl_processed.set_text(text=f"{gc.mod_file_counter}")

                # update progressbar
                prog_file_len = len(source_files)
                progress_bar["value"] = (gc.mod_file_counter / prog_file_len * 100)

                root.after(1000, update_modal_ui)

        def read_txt(file):
            with open(file, "r", encoding="utf-8") as f:
                return f.read()

        # widgets
        lbl_task_name.configure(text=f"Task {mode} with {model_name_tc} model")
        lbl_elapsed.set_text(f"{round(time() - timerStart, 2)}s")
        cbtn_open_folder.configure(state="normal")
        cbtn_invoker(sj.cache["auto_open_dir_export"], cbtn_open_folder)
        btn_add.configure(state="normal", command=add_to_files)
        btn_cancel.configure(state="normal", command=cancel)

        update_modal_ui()
        gc.mw.start_loadBar()

        if mode == "refinement":
            export_to = dir_refinement if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"] + "/refinement"
        else:
            export_to = dir_alignment if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"] + "/alignment"

        for file in source_files:
            # file = (source_file, mode_file, lang) -> lang is only present if mode is alignment
            fail = False
            fail_msg = ""

            if not gc.recording:  # if cancel button is pressed
                return

            # Proccess it
            logger.debug("PROCESSING: " + str(file))
            audio = file[0]
            save_name = f"{filename_only(audio)}_{action_name.lower()}"
            mod_source = stable_whisper.WhisperResult(file[1]) if file[1].endswith(".json") else read_txt(file[1])
            if mode == "alignment":
                whisper_args["language"] = TO_LANGUAGE_CODE[file[2].lower()] if file[2] is not None else None

            def start_thread():
                nonlocal mod_source
                try:
                    result = mod_function(audio, mod_source, **whisper_args)
                    gc.data_queue.put(result)
                except Exception as e:
                    nonlocal fail, fail_msg
                    fail = True
                    fail_msg = e

            thread = Thread(target=start_thread, daemon=True)
            thread.start()

            while thread.is_alive():
                if not gc.recording:
                    logger.debug(f"Cancelling {mode}")
                    kill_thread(thread)
                    raise Exception("Cancelled")
                sleep(0.1)

            if fail:
                raise Exception(fail_msg)

            result: stable_whisper.WhisperResult = gc.data_queue.get()
            save_output_stable_ts(result, path.join(export_to, save_name), sj.cache["export_to"], sj)

            gc.mod_file_counter += 1

            while adding:
                sleep(0.3)

        # destroy progress window
        if root.winfo_exists():
            root.after(100, root.destroy)

        logger.info(f"End process ({mode}) [Total time: {time() - startProc:.2f}s]")

        # turn off loadbar
        gc.mw.stop_loadBar()
        gc.disable_rec()  # update flag

        if gc.mod_file_counter > 0:
            # open folder
            if sj.cache["auto_open_dir_export"]:
                start_file(export_to)

        mbox(f"File {mode} Done", f"{action_name} {gc.mod_file_counter} file(s)", 0)
    except Exception as e:
        logger.error("Error occured while processing file(s)")
        logger.exception(e)
        assert gc.mw is not None
        mbox("Error occured while processing file(s)", f"{str(e)}", 2, gc.mw.root)
        gc.mw.from_file_stop(prompt=False, notify=False)

        if root.winfo_exists():
            root.after(1000, root.destroy)  # destroy progress window
