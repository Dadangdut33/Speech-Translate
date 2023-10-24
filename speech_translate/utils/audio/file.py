import logging
from os import path
from datetime import datetime
from threading import Thread
from time import gmtime, sleep, strftime, time
from tkinter import Toplevel, filedialog, ttk
from typing import Dict, List, Union
import torch

import whisper_timestamped as whisper

from speech_translate._path import app_icon, dir_export
from speech_translate.components.custom.label import LabelTitleText
from speech_translate.components.custom.message import mbox
from speech_translate.custom_logging import logger
from speech_translate.globals import gc, sj

from ..helper import cbtn_invoker, get_proxies, nativeNotify, filename_only, start_file
from ..whisper.helper import get_temperature, parse_args_whisper_timestamped, save_output, model_values
from ..translate.translator import translate


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
    plot: bool,
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
        result_tc = ""
        f_name = save_name.replace("{task}", "transcribe")
        f_name = f_name.replace("{task-short}", "tc")

        logger.info("-" * 50)
        logger.info(f"Transcribing: {f_name}")
        logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")

        fail = False
        failMsg = ""
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]

        def run_threaded():
            try:
                if plot:
                    whisper_args["plot_word_alignment"] = path.join(export_to, f_name)
                result = whisper.transcribe(
                    model_loaded, audio_name, task="transcribe", language=lang_source if not auto else None, **whisper_args
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

        result_tc = gc.data_queue.get()

        # export if transcribe mode is on
        if transcribe:
            resultTxt = result_tc["text"].strip()  # type: ignore

            if len(resultTxt) > 0:
                gc.file_tced_counter += 1
                save_output(result_tc, path.join(export_to, f_name), sj.cache["export_to"])
                gc.insert_to_mw(f"{f_name} - Transcribed", "tc", "\n")
            else:
                gc.insert_to_mw(f"{f_name} - Failed to save. It is empty (no text get from transcription)", "tc", "\n")
                logger.warning("Transcribed Text is empty")

        # start translation thread if translate mode is on
        if translate:
            # send result as srt if not using whisper because it will be send to translation API.
            # If using whisper translation will be done using whisper model
            to_tl = result_tc if engine not in model_values else audio_name
            translateThread = Thread(
                target=cancellable_tl,
                args=[to_tl, lang_source, lang_target, model_tl, engine, auto, save_name, plot],
                kwargs=whisper_args,
                daemon=True,
            )

            translateThread.start()  # Start translation in a new thread to prevent blocking

        logger.debug(f"Transcribing Audio: {f_name} | Time Taken: {time() - start:.2f}s")
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
    query: Union[str, Dict],
    lang_source: str,
    lang_target: str,
    model_loaded: whisper.Whisper,
    engine: str,
    auto: bool,
    save_name: str,
    plot: bool,
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
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]
        f_name = save_name.replace("{task}", "translate")
        f_name = f_name.replace("{task-short}", "tl")

        logger.info("-" * 50)
        logger.info(f"Translating: {f_name}")

        if engine in model_values:
            try:
                logger.debug("Translating with whisper")
                logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")

                fail = False
                failMsg = ""

                def run_threaded():
                    if plot:
                        whisper_args["plot_word_alignment"] = path.join(export_to, f_name)
                    try:
                        result = whisper.transcribe(
                            model_loaded,
                            query,
                            task="translate",
                            language=lang_source if not auto else None,
                            **whisper_args
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
                save_output(result_Tl_whisper, path.join(export_to, f_name), sj.cache["export_to"])
                gc.insert_to_mw(f"{f_name} - Translated", "tl", "\n")
            else:
                gc.insert_to_mw(f"{f_name} - Failed to save. It is empty (no text get from transcription)", "tl", "\n")
                logger.warning("Translated Text is empty")
        else:
            assert isinstance(query, Dict)
            if len(query["text"].strip()) == 0:
                gc.insert_to_mw(f"{f_name} - Failed to save. It is empty (no text get from transcription)", "tl", "\n")
                return

            debug_log = sj.cache["debug_translate"]
            proxies = get_proxies(sj.cache["http_proxy"], sj.cache["https_proxy"])
            kwargs = {}
            if engine == "LibreTranslate":
                kwargs["libre_https"] = sj.cache["libre_https"],
                kwargs["libre_host"] = sj.cache["libre_host"],
                kwargs["libre_port"] = sj.cache["libre_port"],
                kwargs["libre_api_key"] = sj.cache["libre_api_key"],

            # translate every text and words in each segments, replace it
            text_all = ""
            for segment in query["segments"]:
                # tl text in that segment
                success, result = translate(engine, segment["text"], lang_source, lang_target, proxies, debug_log, **kwargs)
                if not success:
                    nativeNotify(f"Error: translation with {engine} failed", result)
                    raise Exception(result)

                segment["text"] = result
                text_all += result + " "

                # check if any of the items in the list end with ".words"
                # meaning export to per words is enabled, making us have to translate the words in the segment
                if any(item.endswith(".words") for item in sj.cache["export_to"]):
                    # tl words in that segment
                    for word in segment["words"]:
                        success, result = translate(
                            engine, word["text"], lang_source, lang_target, proxies, debug_log, **kwargs
                        )
                        if not success:
                            nativeNotify(f"Error: translation with {engine} failed", result)
                            raise Exception(result)

                        word["text"] = result

            gc.file_tled_counter += 1
            query["text"] = text_all.strip()
            save_output(query, path.join(export_to, f_name), sj.cache["export_to"])
            gc.insert_to_mw(f"{f_name} - Translated", "tl", "\n")

        logger.debug(f"Translated: {f_name} | Time Taken: {time() - start:.2f}s")
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
        whisper_args = sj.cache["whisper_args"]
        export_format: str = sj.cache["export_format"]
        file_slice_start = (None if sj.cache["file_slice_start"] == "" else int(sj.cache["file_slice_start"]))
        file_slice_end = None if sj.cache["file_slice_end"] == "" else int(sj.cache["file_slice_end"])
        plot = False

        success, data = get_temperature(temperature)
        if not success:
            raise Exception(data)
        else:
            temperature = data

        # parse whisper_args
        data = parse_args_whisper_timestamped(sj.cache["whisper_args"])
        if not data.pop("success"):
            raise Exception(data["msg"])
        else:
            whisper_args = data
            assert isinstance(whisper_args, Dict)
            plot = whisper_args.pop("plot")
            threads = whisper_args.pop("threads")
            if threads:
                torch.set_num_threads(threads)
            if whisper_args.pop("debug"):
                logging.getLogger("WHISPER").setLevel(logging.DEBUG)

            whisper_args["temperature"] = temperature
            whisper_args["best_of"] = sj.cache["best_of"]
            whisper_args["beam_size"] = sj.cache["beam_size"]
            whisper_args["compression_ratio_threshold"] = sj.cache["compression_ratio_threshold"]
            whisper_args["logprob_threshold"] = sj.cache["logprob_threshold"]
            whisper_args["no_speech_threshold"] = sj.cache["no_speech_threshold"]
            whisper_args["suppress_tokens"] = sj.cache["suppress_tokens"]
            whisper_args["initial_prompt"] = sj.cache["initial_prompt"]
            whisper_args["condition_on_previous_text"] = sj.cache["condition_on_previous_text"]

        logger.debug(f"whisper_args: {whisper_args}")
        # assert whisper_args is an object
        if not isinstance(whisper_args, dict):
            raise Exception("whisper_args must be an object")

        # update button text
        gc.mw.btn_import_file.configure(text="Cancel")

        timerStart = time()
        taskname = "Transcribe & Translate" if transcribe and translate else "Transcribe" if transcribe else "Translate"
        language = f"from {lang_source} to {lang_target}" if translate else lang_source
        current_file_counter = 0

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
                    args=[file, lang_source, lang_target, model_name, engine, auto, save_name, plot],
                    kwargs=whisper_args,
                    daemon=True,
                )
            else:
                # will automatically check translate on or not depend on input
                # translate is called from here because other engine need to get transcribed text first if translating
                proc_thread = Thread(
                    target=cancellable_tc,
                    args=[
                        file, lang_source, lang_target, model_tc, model_tl, auto, transcribe, translate, engine, save_name,
                        plot
                    ],
                    kwargs=whisper_args,
                    daemon=True,
                )

            proc_thread.start()
            proc_thread.join()  # wait for thread to finish until continue to next file
            current_file_counter += 1

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
