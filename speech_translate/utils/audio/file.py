from os import path
from ast import literal_eval
from datetime import datetime
from shlex import quote
from textwrap import wrap
from threading import Thread
from time import gmtime, sleep, strftime, time
from tkinter import Toplevel, filedialog, ttk
from typing import Dict, List

import whisper_timestamped as whisper

from speech_translate._path import app_icon, dir_export
from speech_translate.components.custom.label import LabelTitleText
from speech_translate.components.custom.message import mbox
from speech_translate.custom_logging import logger
from speech_translate.globals import gc, sj

from ..helper import cbtn_invoker, get_proxies, nativeNotify, filename_only, save_file_with_dupe_check, start_file
from ..whisper.helper import (
    convert_str_options_to_dict, get_temperature, srt_whisper_to_txt_format_stamps, txt_to_srt_whisper_format_stamps,
    whisper_result_to_srt, srt_whisper_to_txt_format, model_values
)
from ..translate.translator import google_tl, libre_tl, memory_tl


# run in threaded environment with queue and exception to cancel
def cancellable_tc(
    audio_name: str,
    lang_source: str,
    lang_target: str,
    model_loaded: whisper.Whisper,
    model_tl: whisper.Whisper,
    auto: bool,
    transcribe: bool,
    translate: bool,
    engine: str,
    save_name: str,
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
    **whisper_args:
        whisper parameter

    Returns
    -------
    None
    """
    assert gc.mw is not None
    start = time()
    gc.enable_tc()
    gc.mw.start_loadBar()

    try:
        result_Tc = ""
        f_save = save_name.replace("{task}", "transcribe")
        f_save = f_save.replace("{task-short}", "tc")

        logger.info("-" * 50)
        logger.info(f"Transcribing: {f_save}")

        logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")

        fail = False
        failMsg = ""

        def run_threaded():
            try:
                result = whisper.transcribe(
                    model_loaded,
                    audio_name,
                    task="transcribe",
                    language=lang_source if not auto else None,
                    **whisper_args,
                )
                gc.data_queue.put(result)
            except Exception as e:
                nonlocal fail, failMsg
                fail = True
                failMsg = str(e)

        thread = Thread(target=run_threaded, daemon=True)
        thread.start()

        while thread.is_alive():
            if not gc.transcribing:
                logger.debug("Cancelling transcription")
                raise Exception("Cancelled")
            sleep(0.1)

        if fail:
            raise Exception(failMsg)

        result_Tc = gc.data_queue.get()

        # export to file
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]

        # export if transcribe mode is on
        if transcribe:
            resultTxt = result_Tc["text"].strip()  # type: ignore

            if len(resultTxt) > 0:
                gc.file_tced_counter += 1
                resultSrt = whisper_result_to_srt(result_Tc)

                save_file_with_dupe_check(path.join(export_to, f_save), ".txt", resultTxt)
                save_file_with_dupe_check(path.join(export_to, f_save), ".srt", resultSrt)

                gc.insert_result_mw(f"{f_save} - Transcribed & saved to .txt and .srt", "tc")
            else:
                gc.insert_result_mw(f"{f_save} - Failed to save. It is empty (no text get from transcription)", "tc")
                logger.warning("Transcribed Text is empty")

        # start translation thread if translate mode is on
        if translate:
            # send result as srt if not using whisper because it will be send to translation API.
            # If using whisper translation will be done using whisper model
            to_tl = whisper_result_to_srt(result_Tc) if engine not in model_values else audio_name
            translateThread = Thread(
                target=cancellable_tl,
                args=[
                    to_tl,
                    lang_source,
                    lang_target,
                    model_tl,
                    engine,
                    auto,
                    save_name,
                ],
                kwargs=whisper_args,
                daemon=True,
            )

            translateThread.start()  # Start translation in a new thread to prevent blocking

        logger.debug(f"Transcribing Audio: {f_save} | Time Taken: {time() - start:.2f}s")
    except Exception as e:
        if str(e) == "Cancelled":
            logger.info("Transcribing cancelled")
        else:
            logger.exception(e)
            nativeNotify("Error: Transcribing Audio", str(e))
    finally:
        gc.disable_tc()
        gc.mw.stop_loadBar()


def cancellable_tl(
    query: str,
    lang_source: str,
    lang_target: str,
    model_loaded: whisper.Whisper,
    engine: str,
    auto: bool,
    save_name: str,
    **whisper_args,
):
    """
    Translate the result of file input using either whisper model or translation API
    This function is cancellable with the cancel flag that is set by the cancel button and will be checked periodically every
    0.1 seconds. If the cancel flag is set, the function will raise an exception to stop the thread

    We use thread instead of multiprocessing because it seems to be faster and easier to use

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
    **whisper_args:
        whisper parameter

    Returns
    -------
    None
    """
    assert gc.mw is not None
    start = time()
    gc.enable_tl()
    gc.mw.start_loadBar()

    try:
        literal_eval(quote(sj.cache["separate_with"]))
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]
        f_save = save_name.replace("{task}", "translate")
        f_save = f_save.replace("{task-short}", "tl")

        logger.info("-" * 50)
        logger.info(f"Translating: {f_save}")

        if engine in model_values:
            try:
                logger.debug("Translating with whisper")
                logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")

                fail = False
                failMsg = ""

                def run_threaded():
                    try:
                        result = whisper.transcribe(
                            model_loaded,
                            query,
                            task="translate",
                            language=lang_source if not auto else None,
                            **whisper_args,
                        )
                        gc.data_queue.put(result)
                    except Exception as e:
                        nonlocal fail, failMsg
                        fail = True
                        failMsg = str(e)

                thread = Thread(target=run_threaded, daemon=True)
                thread.start()

                while thread.is_alive():
                    if not gc.translating:
                        logger.debug("Cancelling translation")
                        raise Exception("Cancelled")
                    sleep(0.1)

                if fail:
                    raise Exception(failMsg)

                result_Tl_whisper = gc.data_queue.get()

            except Exception as e:
                gc.disable_tl()  # flag processing as done if error
                gc.mw.stop_loadBar()
                if str(e) == "Cancelled":
                    logger.info("Translation cancelled")
                else:
                    logger.exception(e)
                    nativeNotify("Error: translating with whisper failed", str(e))
                return

            # if whisper, sended text (toTranslate) is the audio file path
            resultTxt = result_Tl_whisper["text"].strip()  # type: ignore

            if len(resultTxt) > 0:
                gc.file_tled_counter += 1
                resultSrt = whisper_result_to_srt(result_Tl_whisper)

                save_file_with_dupe_check(path.join(export_to, f_save), ".txt", resultTxt)
                save_file_with_dupe_check(path.join(export_to, f_save), ".srt", resultSrt)

                gc.insert_result_mw(f"{f_save} - Translated & saved to .txt and .srt", "tl")
            else:
                gc.insert_result_mw(f"{f_save} - Failed to save. It is empty (no text get from transcription)", "tl")
                logger.warning("Translated Text is empty")
        else:
            # limit to 5000 characters
            toTranslates = wrap(query, 5000, break_long_words=False, replace_whitespace=False)
            toTranslates_txt = []
            timestamps = []
            for query in toTranslates:
                query, timestamp = srt_whisper_to_txt_format_stamps(query)
                toTranslates_txt.append(query)
                timestamps.append(timestamp)
            result_Tl = []
            debug_log = sj.cache["debug_translate"]
            proxies = get_proxies(sj.cache["http_proxy"], sj.cache["https_proxy"])

            # translate each part
            for query, timestamp in zip(toTranslates_txt, timestamps):
                if engine == "Google":
                    logger.debug("Translating with google translate")
                    success, result = google_tl(query, lang_source, lang_target, proxies, debug_log)
                    if not success:
                        nativeNotify("Error: translation with google failed", result)

                elif engine == "LibreTranslate":
                    logger.debug("Translating with libre translate")
                    success, result = libre_tl(
                        query,
                        lang_source,
                        lang_target,
                        sj.cache["libre_https"],
                        sj.cache["libre_host"],
                        sj.cache["libre_port"],
                        sj.cache["libre_api_key"],
                        proxies,
                        debug_log,
                    )
                    if not success:
                        nativeNotify("Error: translation with libre failed", result)

                elif engine == "MyMemoryTranslator":
                    logger.debug("Translating with mymemorytranslator")
                    success, result = memory_tl(query, lang_source, lang_target, proxies, debug_log)
                    if not success:
                        nativeNotify("Error: translation with mymemory failed", result)
                else:
                    raise Exception("Invalid engine. Got: " + engine)  # should never happen

                result = txt_to_srt_whisper_format_stamps(result, timestamp)
                result_Tl.append(result)

            if len(result_Tl) > 0:
                gc.file_tled_counter += 1

            for i, results in enumerate(result_Tl):
                # sended text (toTranslate parameter) is sended in srt format
                # so the result that we got from translation is as srt
                resultSrt = results
                resultTxt = srt_whisper_to_txt_format(resultSrt)  # format it back to txt

                if len(resultSrt) > 0:
                    save_name_part = f"{f_save}_pt{i + 1}" if len(result_Tl) > 1 else f_save

                    save_file_with_dupe_check(path.join(export_to, f_save), ".txt", resultTxt)
                    save_file_with_dupe_check(path.join(export_to, f_save), ".srt", resultSrt)

                    gc.insert_result_mw(f"{save_name_part} - Translated & saved to .txt and .srt", "tl")
                else:
                    gc.insert_result_mw(f"{f_save} - Failed to save. It is empty (no text get from transcription)", "tl")
                    logger.warning("Translated Text is empty")

        logger.debug(f"Translating: {f_save} | Time Taken: {time() - start:.2f}s")
    except Exception as e:
        logger.exception(e)
        nativeNotify("Error: translating failed", str(e))
    finally:
        gc.disable_tl()  # flag processing as done. No need to check for transcription because it is done before this
        gc.mw.stop_loadBar()


def import_file(
    files: List[str], model_name: str, lang_source: str, lang_target: str, transcribe: bool, translate: bool, engine: str
) -> None:
    """Function to transcribe and translate from audio/video files.

    Args
    ----
    files (list[str])
        The path to the audio/video file.
    modelKey (str)
        The key of the model in modelSelectDict as the selected model to use
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

    btn_add = ttk.Button(frame_btn_1, text="Add", state="disabled")
    btn_add.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    btn_cancel = ttk.Button(frame_btn_1, text="Cancel", state="disabled", style="Accent.TButton")
    btn_cancel.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    try:
        startProc = time()
        logger.info("Start Process (FILE)")
        gc.file_tced_counter = 0
        gc.file_tled_counter = 0

        auto = lang_source == "auto detect"
        tl_engine_whisper = engine in model_values

        # load model
        model_tc = whisper.load_model(model_name)
        model_tl = whisper.load_model(engine) if tl_engine_whisper else None

        temperature = sj.cache["temperature"]
        whisper_args = sj.cache["whisper_extra_args"]
        export_format: str = sj.cache["export_format"]
        file_slice_start = (None if sj.cache["file_slice_start"] == "" else int(sj.cache["file_slice_start"]))
        file_slice_end = None if sj.cache["file_slice_end"] == "" else int(sj.cache["file_slice_end"])

        success, data = get_temperature(temperature)
        if not success:
            raise Exception(data)
        else:
            temperature = data

        # assert temperature is not string
        if isinstance(temperature, str):
            raise Exception("temperature must be a floating point number")

        success, data = convert_str_options_to_dict(sj.cache["whisper_extra_args"])
        if not success:
            raise Exception(data)
        else:
            whisper_args = data
            assert isinstance(whisper_args, Dict)
            whisper_args["temperature"] = temperature
            whisper_args["initial_prompt"] = sj.cache["initial_prompt"]
            whisper_args["condition_on_previous_text"] = sj.cache["condition_on_previous_text"]
            whisper_args["compression_ratio_threshold"] = sj.cache["compression_ratio_threshold"]
            whisper_args["logprob_threshold"] = sj.cache["logprob_threshold"]
            whisper_args["no_speech_threshold"] = sj.cache["no_speech_threshold"]

        # assert whisper_extra_args is an object
        if not isinstance(whisper_args, dict):
            raise Exception("whisper_extra_args must be an object")

        # update button text
        gc.mw.btn_import_file.configure(text="Cancel")

        timerStart = time()
        taskname = "Transcribe & Translate" if transcribe and translate else "Transcribe" if transcribe else "Translate"
        language = f"from {lang_source} to {lang_target}" if translate else lang_source

        def add_to_files():
            nonlocal files
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

        def cancel():
            # confirm
            if mbox("Cancel confirmation", "Are you sure you want to cancel file process?", 3, master):
                assert gc.mw is not None
                gc.mw.from_file_stop()

        def update_modal_ui():
            nonlocal timerStart
            if gc.recording:
                if transcribe:
                    current_file_counter = gc.file_tced_counter
                else:
                    current_file_counter = gc.file_tled_counter

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
                progress_bar["value"] = (
                    current_file_counter / len(files) * 100
                )  # update the progress bar based on percentage

                root.after(1000, update_modal_ui)

        # widgets
        lbl_task_name.configure(text="Task: " + taskname + f" {language} with {model_name} model")
        lbl_elapsed.set_text(f"{round(time() - timerStart, 2)}s")
        cbtn_open_folder.configure(state="normal")
        cbtn_invoker(sj.cache["auto_open_dir_export"], cbtn_open_folder)
        btn_add.configure(state="normal", command=add_to_files)
        btn_cancel.configure(state="normal", command=cancel)

        update_modal_ui()

        for file in files:
            if not gc.recording:  # if cancel button is pressed
                return

            # Proccess it
            file_name = filename_only(file)
            save_name = datetime.now().strftime(export_format)
            save_name = save_name.replace("{file}", file_name[file_slice_start:file_slice_end])
            save_name = save_name.replace("{lang-source}", lang_source)
            save_name = save_name.replace("{lang-target}", lang_target)
            save_name = save_name.replace("{model}", model_name)
            save_name = save_name.replace("{engine}", engine)

            if translate and tl_engine_whisper and not transcribe:  # if only translating and using the whisper engine
                proc_thread = Thread(
                    target=cancellable_tl,
                    args=[
                        file,
                        lang_source,
                        lang_target,
                        model_name,
                        engine,
                        auto,
                        save_name,
                    ],
                    kwargs=whisper_args,
                    daemon=True,
                )
            else:
                # will automatically check translate on or not depend on input
                # translate is called from here because other engine need to get transcribed text first if translating
                proc_thread = Thread(
                    target=cancellable_tc,
                    args=[
                        file,
                        lang_source,
                        lang_target,
                        model_tc,
                        model_tl,
                        auto,
                        transcribe,
                        translate,
                        engine,
                        save_name,
                    ],
                    kwargs=whisper_args,
                    daemon=True,
                )

            proc_thread.start()
            proc_thread.join()  # wait for thread to finish until continue to next file

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
