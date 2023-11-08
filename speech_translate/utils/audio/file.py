from os import path
import sys
from datetime import datetime
from threading import Thread
from time import gmtime, sleep, strftime, time
from tkinter import filedialog
from typing import List, Literal, Union, Dict

import stable_whisper  # https://github.com/jianfch/stable-ts # has no static annotation hence many type ignore
from whisper.tokenizer import TO_LANGUAGE_CODE

from speech_translate._path import dir_export, dir_alignment, dir_refinement, dir_translate
from speech_translate._logging import logger
from speech_translate.globals import gc, sj
from speech_translate.utils.translate.language import verify_language_in_key
from speech_translate.ui.custom.dialog import ModResultInputDialog, FileProcessDialog
from speech_translate.ui.custom.message import mbox

from ..helper import cbtn_invoker, get_proxies, native_notify, filename_only, start_file, up_first_case, get_list_of_dict, kill_thread
from ..whisper.helper import get_model, get_model_args, get_tc_args, save_output_stable_ts, model_values, to_language_name
from ..translate.translator import translate

# Global variable
# to track which file is processed
# index 0 (even) is the name of the file, index 1 (odd) is the status (True if success, False if failed)
processed_tc = []
processed_tl = []
global_file_import_counter = 0


def update_q_process(list_of_dict: List[dict], index: int, status: str) -> None:
    """
    Update the processed list of dict.
    """
    update = {
        "index": index,
        "status": status,
    }
    temp = get_list_of_dict(list_of_dict, "index", index)
    if temp is not None:
        list_of_dict[index] = update
    else:
        list_of_dict.append(update)


def run_whisper(func, audio: str, task: str, fail_status: List, **kwargs):
    """Run whisper function

    Args
    ----
    func : function
        The whisper function to run.
    fail_status : list
        To store the fail status, use list because it is passed by reference so it can be changed in thread.
    **kwargs
        The arguments to pass to the whisper function.

    Returns
    -------
    None
    """
    try:
        sys.stderr.write(f"Running Whisper {task}...\n")
        result = func(audio, task=task, **kwargs)
        gc.data_queue.put(result)
        sys.stderr.write(f"Whisper {task} done\n")
    except Exception as e:
        logger.exception(e)
        fail_status[0] = True
        if "The system cannot find the file specified" in str(e) and not gc.has_ffmpeg:
            logger.error("FFmpeg not found in system path. Please install FFmpeg and add it to system path")
            fail_status[1] = Exception("FFmpeg not found in system path. Please install FFmpeg and add it to system path")
        else:
            fail_status[1] = e


def run_translate_api(
    query: stable_whisper.WhisperResult, engine: str, lang_source: str, lang_target: str, proxies: Dict, debug_log: bool,
    fail_status: List, **kwargs
):
    """Run translation API

    Parameters
    ----------
    query : stable_whisper.WhisperResult
        The result of whisper process.
    engine : str
        The engine to use for translation.
    lang_source : str
        The source language.
    lang_target : str
        The target language.
    proxies : str
        The proxies to use.
    debug_log : bool
        Whether to log the debug.
    fail_status : List
        To store the fail status, use list because it is passed by reference so it can be changed in thread.

    Raises
    ------
    Exception
        _description_
    """
    try:
        sys.stderr.write(f"Running Translation with {engine}...\n")
        # translate every text and words in each segments, replace it
        segment_texts = [segment.text for segment in query.segments]

        query.language = lang_target  # now its the target language
        # tl text in that segment
        success, result = translate(engine, segment_texts, lang_source, lang_target, proxies, debug_log, **kwargs)

        # replace
        for index, segment in enumerate(query.segments):
            if len(result) == 0:
                logger.warning("Some part of the text might not be translated")
                return

            # dont forget to also add space back because its removed automatically in the api call
            segment.text = result.pop(0) + " "

            # because each word is taken from the text, we can replace the word with the translated text
            # but we first need to check the  of splitted translated text because sometimes its not the same length as the original
            temp = segment.text.split()
            translated_word_length = len(temp)
            if translated_word_length == len(segment.words):
                for word in segment.words:
                    word.word = temp.pop(0) + " "
            else:
                # This is somewhat brute force but it should work just fine. Keep in mind that the timing might be a bit off
                # considering that we are replacing the words in the segment without knowing the previous value
                logger.warning(
                    "Translated text words is not the same length as the words in the segment. Attempting to replace words..."
                )
                logger.warning(
                    f"Translated Words Length: {translated_word_length} | Original Words Length: {len(segment.words)}"
                )

                def nearest_array_index(array, value):
                    if value > len(array) - 1:
                        return len(array) - 1
                    else:
                        return value

                def delete_elements_after_index(my_list, index_to_keep):
                    new_list = my_list[:index_to_keep + 1]
                    return new_list

                # if tl word length > original word length, add until hit the limit.
                # if hit limit, just add the rest of the words to the last word in the segment
                if translated_word_length > len(segment.words):
                    logger.debug("TL word > Original word")
                    for index, word in enumerate(temp):
                        nearest = nearest_array_index(segment.words, index)

                        # adding until hit the limit
                        if index < len(segment.words):
                            segment.words[nearest].word = word + " "
                        else:
                            # hit limit, just add the rest of the words
                            segment.words[nearest].word += f"{word} "
                # if tl word length < original word length, add until hit the limit (tl word length)
                # delete the rest of the words and then update the last word segment timing
                else:
                    logger.debug("TL word < Original word")
                    # get last word segment
                    last_word = segment.words[-1]

                    for index, word in enumerate(temp):
                        segment.words[index].word = word + " "

                    # delete the over boundary word that is probably not needed
                    segment.words = delete_elements_after_index(segment.words, translated_word_length - 1)

                    # now update the new one with last word segment timing while removing the trailing space
                    segment.words[-1].end = last_word.end

            # remove trailing space in last word
            segment.words[-1].word = segment.words[-1].word.rstrip()

        sys.stderr.write(f"Translation with {engine} done\n")
    except Exception as e:
        logger.exception(e)
        fail_status[0] = True
        if "The system cannot find the file specified" in str(e) and not gc.has_ffmpeg:
            logger.error("FFmpeg not found in system path. Please install FFmpeg and add it to system path")
            fail_status[1] = Exception("FFmpeg not found in system path. Please install FFmpeg and add it to system path")
        else:
            fail_status[1] = e


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
    tracker_index: int,
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
    stable_tc
        whisper function for transcribing
    stable_tl
        whisper function for translating
    auto: bool
        if True, source language will be auto detected
    transcribe: bool
        if True, transcribe the audio
    translate: bool
        if True, translate the transcription
    engine: str
        engine to use for translation
    tracker_index: int
        index to track the progress
    **whisper_args:
        whisper parameter

    Returns
    -------
    None
    """
    assert gc.mw is not None
    global global_file_import_counter, processed_tc
    start = time()

    try:
        update_q_process(processed_tc, tracker_index, "Transcribing please wait...")
        f_name = save_name.replace("{task}", "transcribe")
        f_name = f_name.replace("{task-short}", "tc")

        logger.info("-" * 50)
        logger.info("Transcribing")
        logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")

        fail_status = [False, ""]
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]

        thread = Thread(
            target=run_whisper, args=[stable_tc, audio_name, "transcribe", fail_status], kwargs=whisper_args, daemon=True
        )
        thread.start()

        while thread.is_alive():
            if not gc.transcribing:
                logger.debug("Cancelling transcription")
                kill_thread(thread)
                raise Exception("Cancelled")
            sleep(0.1)

        if fail_status[0]:
            raise Exception(fail_status[1])

        result_tc: stable_whisper.WhisperResult = gc.data_queue.get()

        # export if transcribe mode is on
        if transcribe:
            result_text = result_tc.text.strip()

            if len(result_text) > 0:
                gc.file_tced_counter += 1
                save_output_stable_ts(result_tc, path.join(export_to, f_name), sj.cache["export_to"], sj)
            else:
                logger.warning("Transcribed Text is empty")
                update_q_process(processed_tc, tracker_index, "TC Fail! Got empty transcribed text")

        update_q_process(processed_tc, tracker_index, "Transcribed")
        logger.debug(f"Transcribing Audio: {f_name} | Time Taken: {time() - start:.2f}s")

        # start translation thread if translate mode is on
        if translate:
            # send result as srt if not using whisper because it will be send to translation API.
            # If using whisper translation will be done using whisper model
            to_tl = result_tc if engine not in model_values else audio_name
            translateThread = Thread(
                target=cancellable_tl,
                args=[to_tl, lang_source, lang_target, stable_tl, engine, auto, save_name, tracker_index],
                kwargs=whisper_args,
                daemon=True,
            )

            translateThread.start()  # Start translation in a new thread to prevent blocking
    except Exception as e:
        update_q_process(processed_tc, tracker_index, "Failed to transcribe")
        if str(e) == "Cancelled":
            logger.info("Transcribing cancelled")
        else:
            logger.exception(e)
            native_notify("Error: Transcribing Audio", str(e))
    finally:
        global_file_import_counter += 1


def cancellable_tl(
    query: Union[str, stable_whisper.WhisperResult],
    lang_source: str,
    lang_target: str,
    stable_tl,
    engine: str,
    auto: bool,
    save_name: str,
    tracker_index: int,
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
    stable_tl
        whisper function for translating
    engine: str
        engine to use
    auto: bool
        whether to use auto language detection
    save_name: str
        name of the file to save the translation to
    tracker_index: int
        index to track the progress
    **whisper_args:
        whisper parameter

    Returns
    -------
    None
    """
    assert gc.mw is not None
    global global_file_import_counter, processed_tl
    start = time()

    try:
        update_q_process(processed_tl, tracker_index, "Translating please wait...")
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]
        f_name = save_name.replace("{task}", "translate")
        f_name = f_name.replace("{task-short}", "tl")

        logger.info("-" * 50)
        logger.info("Translating")

        if engine in model_values:
            logger.debug("Translating with whisper")
            logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")

            fail_status = [False, ""]
            thread = Thread(
                target=run_whisper, args=[stable_tl, query, "translate", fail_status], kwargs=whisper_args, daemon=True
            )
            thread.start()

            while thread.is_alive():
                if not gc.translating:
                    logger.debug("Cancelling translation")
                    kill_thread(thread)
                    raise Exception("Cancelled")
                sleep(0.1)

            if fail_status[0]:
                raise Exception(fail_status[1])

            result_tl: stable_whisper.WhisperResult = gc.data_queue.get()

            # if whisper, sended text (toTranslate) is the audio file path
            resultTxt = result_tl.text.strip()

            if len(resultTxt) == 0:
                logger.warning("Translated Text is empty")
                update_q_process(processed_tl, tracker_index, "TL Fail! Got empty translated text")
                return

            gc.file_tled_counter += 1
            save_output_stable_ts(result_tl, path.join(export_to, f_name), sj.cache["export_to"], sj)
        else:
            assert isinstance(query, stable_whisper.WhisperResult)
            if len(query.text.strip()) == 0:
                logger.warning("Translated Text is empty")
                update_q_process(processed_tl, tracker_index, "TL Fail! Got empty translated text")
                return

            debug_log = sj.cache["debug_translate"]
            proxies = get_proxies(sj.cache["http_proxy"], sj.cache["https_proxy"])
            kwargs = {}
            if engine == "LibreTranslate":
                kwargs["libre_https"] = sj.cache["libre_https"]
                kwargs["libre_host"] = sj.cache["libre_host"]
                kwargs["libre_port"] = sj.cache["libre_port"]
                kwargs["libre_api_key"] = sj.cache["libre_api_key"]

            fail_status = [False, ""]
            thread = Thread(
                target=run_translate_api,
                args=[query, engine, lang_source, lang_target, proxies, debug_log, fail_status],
                kwargs=kwargs,
                daemon=True
            )
            thread.start()

            while thread.is_alive():
                if not gc.translating:
                    logger.debug("Cancelling translation")
                    kill_thread(thread)
                    raise Exception("Cancelled")
                sleep(0.1)

            if fail_status[0]:
                raise Exception(fail_status[1])

            gc.file_tled_counter += 1
            save_output_stable_ts(query, path.join(export_to, f_name), sj.cache["export_to"], sj)

        update_q_process(processed_tl, tracker_index, "Translated")
        logger.debug(f"Translated: {f_name} | Time Taken: {time() - start:.2f}s")
    except Exception as e:
        update_q_process(processed_tl, tracker_index, "Failed to translate")
        if str(e) == "Cancelled":
            logger.info("Translation cancelled")
        else:
            logger.exception(e)
            native_notify(f"Error: translation with {engine} failed", str(e))
    finally:
        global_file_import_counter += 1


def process_file(
    data_files: List[str], model_name_tc: str, lang_source: str, lang_target: str, transcribe: bool, translate: bool,
    engine: str
) -> None:
    """Function to transcribe and translate from audio/video files.

    Args
    ----
    data_files (list[str])
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
    try:
        gc.mw.disable_interactions()
        master = gc.mw.root
        fp = FileProcessDialog(master, "File Import Progress", "export", ["Audio / Video File", "Status"], sj)

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
        _, _, stable_tc, stable_tl, to_args = get_model(
            transcribe, translate, tl_engine_whisper, model_name_tc, engine, sj.cache, **model_args
        )
        whisper_args = get_tc_args(to_args, sj.cache)
        whisper_args["language"] = TO_LANGUAGE_CODE[lang_source.lower()] if not auto else None

        # update button text
        gc.mw.btn_import_file.configure(text="Cancel")

        t_start = time()
        adding = False
        taskname = "Transcribe & Translate" if transcribe and translate else "Transcribe" if transcribe else "Translate"
        language = f"from {lang_source} to {lang_target}" if translate else lang_source
        logger.info(f"Model Args: {model_args}")
        logger.info(f"Process Args: {whisper_args}")
        local_file_import_counter = 0

        global processed_tc, processed_tl, global_file_import_counter
        processed_tc = []
        processed_tl = []
        global_file_import_counter = 0
        all_done = False

        def get_queue_data():
            nonlocal data_files, transcribe, translate
            show = []
            for index, file in enumerate(data_files):
                status = ""
                if transcribe:
                    temp = get_list_of_dict(processed_tc, "index", index)
                    if temp is not None:
                        status += f"{temp['status']}"
                    else:
                        status += "Waiting"

                if translate:
                    if transcribe:
                        status += ", "

                    temp = get_list_of_dict(processed_tl, "index", index)
                    if temp is not None:
                        status += f"{temp['status']}"
                    else:
                        status += "Waiting"

                show.append([file, status])

            # check if there is any still in process
            found_in_process = False
            for item in show:
                if "Waiting" in item[1] or "Translating" in item[1] or "Transcribing" in item[1]:
                    found_in_process = True
                    break

            if not found_in_process:
                nonlocal all_done
                all_done = True

            return show

        def add_to_files():
            nonlocal data_files, adding
            adding = True
            to_add = filedialog.askopenfilenames(
                title="Select a file",
                filetypes=(
                    ("Audio files", "*.wav *.mp3 *.ogg *.flac *.aac *.wma *.m4a"),
                    ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
                    ("All files", "*.*"),
                ),
            )

            if len(to_add) > 0:
                if transcribe:
                    current_file_counter = gc.file_tced_counter
                else:
                    current_file_counter = gc.file_tled_counter
                data_files.extend(list(to_add))
                fp.lbl_files.set_text(text=f"{current_file_counter}/{len(data_files)}")

            adding = False

        canceled = False

        def cancel():
            nonlocal canceled
            # confirm
            if mbox("Cancel confirmation", "Are you sure you want to cancel file process?", 3, master):
                assert gc.mw is not None
                canceled = True
                gc.mw.from_file_stop(prompt=False, notify=True)

        def update_modal_ui():
            nonlocal t_start, local_file_import_counter
            if gc.file_processing:

                fp.lbl_files.set_text(text=f"{local_file_import_counter}/{len(data_files)}")
                fp.lbl_elapsed.set_text(text=f"{strftime('%H:%M:%S', gmtime(time() - t_start))}")

                if local_file_import_counter > 0:
                    fp.lbl_files.set_text(
                        text=
                        f"{local_file_import_counter}/{len(data_files)} ({filename_only(data_files[local_file_import_counter - 1])})"
                    )
                else:
                    fp.lbl_files.set_text(
                        text=
                        f"{local_file_import_counter}/{len(data_files)} ({filename_only(data_files[local_file_import_counter])})"
                    )

                processed = ""
                if transcribe:
                    processed += f"{gc.file_tced_counter} Transcribed"
                if translate:
                    if transcribe:
                        processed += ", "
                    processed += f"{gc.file_tled_counter} Translated"
                fp.lbl_processed.set_text(text=processed)

                # update progressbar
                # times 2 if:
                # - either transcribe and translating
                # - or, only translating but not using whisper engine (which means it must get transcribed first, making the process twice)
                if (transcribe and translate) or (not transcribe and translate and not tl_engine_whisper):
                    prog_file_len = len(data_files) * 2
                else:
                    prog_file_len = len(data_files)

                fp.progress_bar["value"] = (global_file_import_counter / prog_file_len * 100)
                fp.queue_window.update_sheet(get_queue_data())
                fp.root.after(1000, update_modal_ui)

        # widgets
        fp.lbl_task_name.configure(text=f"Task: {taskname} {language} with {model_name_tc} model")
        fp.lbl_elapsed.set_text(f"{round(time() - t_start, 2)}s")
        fp.cbtn_open_folder.configure(state="normal")
        cbtn_invoker(sj.cache["auto_open_dir_export"], fp.cbtn_open_folder)
        fp.btn_add.configure(state="normal", command=add_to_files)
        fp.btn_cancel.configure(state="normal", command=cancel)

        update_modal_ui()
        gc.mw.start_loadBar()
        gc.enable_tc()
        gc.enable_tl()

        for file in data_files:
            if not gc.file_processing:  # if cancel button is pressed
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
            logger.debug("Save_name: " + save_name)

            if visualize_suppression:
                stable_whisper.visualize_suppression(
                    file,
                    path.join(
                        dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"],
                        f"{save_name.replace('{task}', 'visualized')}.png"
                    )
                )

            # if only translating and using the whisper engine
            if translate and tl_engine_whisper and not transcribe:
                proc_thread = Thread(
                    target=cancellable_tl,
                    args=[file, lang_source, lang_target, stable_tl, engine, auto, save_name, global_file_import_counter],
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
                        global_file_import_counter
                    ],
                    kwargs=whisper_args,
                    daemon=True,
                )

            proc_thread.start()
            proc_thread.join()  # wait for thread to finish until continue to next file
            local_file_import_counter += 1

            while adding:
                sleep(0.5)

        # making sure that all file is processed
        # when all_done is True, it means that all file is processed
        # translation is not waited in the tc thread
        while not all_done:
            sleep(0.5)

        gc.disable_tc()
        gc.disable_tl()

        # destroy progress window
        if fp.root.winfo_exists():
            fp.root.after(100, fp.root.destroy)

        logger.info(f"End process (FILE) [Total time: {time() - t_start:.2f}s]")

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

        if not canceled:
            mbox(f"File {taskname} Done", resultMsg, 0, master)
    except Exception as e:
        logger.error("Error occured while processing file(s)")
        logger.exception(e)
        mbox("Error occured while processing file(s)", f"{str(e)}", 2, gc.mw.root)
        gc.mw.from_file_stop(prompt=False, notify=False)

        try:
            if fp and fp.root.winfo_exists():  # type: ignore
                fp.root.after(1000, fp.root.destroy)  # destroy progress window
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to destroy progress window")
    finally:
        gc.disable_rec()  # update flag
        gc.mw.enable_interactions()
        # reset processed list
        processed_tc = []
        processed_tl = []


def mod_result(data_files: List, model_name_tc: str, mode: Literal["refinement", "alignment"]):
    """Function to modify the result of whisper process.
    To modify these results we use the refine or align function from stable whisper.

    The ui is from the import_file function, modify to fit the refine and align process.

    Alignment can take result from faster whisper json because it does not check for token null or not, bui
    refinement needs the token to be not null. Which means that if the program fail to refine because found null token,
    the program will try to transcribe the audio again and try to refine again.

    Parameters
    ----------
    data_files : List
        List of data files
        When mode is refinement, the list should be [(source_file, mode_file), ...]
        When mode is alignment, the list should be [(source_file, mode_file, lang), ...]

    model_name_tc : str
        _description_

    mode : Literal[&quot;refinement&quot;, &quot;alignment&quot;]
        _description_
    """

    assert gc.mw is not None
    try:
        gc.mw.disable_interactions()
        master = gc.mw.root
        fp = FileProcessDialog(master, f"File {up_first_case(mode)} Progress", mode, ["Audio/Video File", "Status"], sj)
        task_short = {"refinement": "rf", "alignment": "al"}

        logger.info("Start Process (MOD FILE)")
        gc.mod_file_counter = 0
        adding = False
        action_name = "Refined" if mode == "refinement" else "Aligned"
        export_format: str = sj.cache["export_format"]
        file_slice_start = (None if sj.cache["file_slice_start"] == "" else int(sj.cache["file_slice_start"]))
        file_slice_end = None if sj.cache["file_slice_end"] == "" else int(sj.cache["file_slice_end"])

        # load model
        model_args = get_model_args(sj.cache)
        model = stable_whisper.load_model(model_name_tc, **model_args)
        mod_dict = {"refinement": model.refine, "alignment": model.align}
        mod_function = mod_dict[mode]
        mod_args = get_tc_args(mod_function, sj.cache, mode="refine" if mode == "refinement" else "align")

        t_start = time()
        logger.info(f"Model Args: {model_args}")
        logger.info(f"Process Args: {mod_args}")

        processed = []

        def get_queue_data():
            nonlocal data_files, processed
            show = []
            for index, file in enumerate(data_files):
                status = ""
                temp = get_list_of_dict(processed, "index", index)
                if temp is not None:
                    status += f"{temp['status']}"
                else:
                    status += "Waiting"

                show.append([file[0], status])  # file[0] is the directory of the source file

            return show

        def add_to_files():
            nonlocal data_files, adding
            if adding:  # add check because of custom window does not stop interaction in main window
                return

            adding = True
            source_f, mod_f, lang = ModResultInputDialog(
                fp.root, "Add File Pair", up_first_case(mode), with_lang=True if mode == "alignment" else False
            ).get_input()

            # if still processing file and user select / add files
            if source_f and mod_f:
                if mode == "alignment":
                    data_files.extend((source_f, mod_f, lang))
                else:
                    data_files.extend((source_f, mod_f))

                fp.lbl_files.set_text(text=f"{gc.mod_file_counter}/{len(data_files)}")

            adding = False

        def cancel():
            assert gc.mw is not None
            if mode == "refinement":
                gc.mw.refinement_stop(prompt=True, notify=True, master=fp.root)
            else:
                gc.mw.alignment_stop(prompt=True, notify=True, master=fp.root)

        def update_modal_ui():
            nonlocal t_start
            if gc.file_processing:

                fp.lbl_files.set_text(text=f"{gc.mod_file_counter}/{len(data_files)}")
                fp.lbl_elapsed.set_text(text=f"{strftime('%H:%M:%S', gmtime(time() - t_start))}")

                if gc.mod_file_counter > 0:
                    fp.lbl_files.set_text(
                        text=
                        f"{gc.mod_file_counter}/{len(data_files)} ({filename_only(data_files[gc.mod_file_counter - 1][0])})"
                    )
                else:
                    fp.lbl_files.set_text(
                        text=f"{gc.mod_file_counter}/{len(data_files)} ({filename_only(data_files[gc.mod_file_counter][0])})"
                    )

                fp.lbl_processed.set_text(text=f"{gc.mod_file_counter}")

                # update progressbar
                prog_file_len = len(data_files)
                fp.progress_bar["value"] = (gc.mod_file_counter / prog_file_len * 100)

                fp.queue_window.update_sheet(get_queue_data())
                fp.root.after(1000, update_modal_ui)

        def read_txt(file):
            with open(file, "r", encoding="utf-8") as f:
                return f.read()

        # widgets
        fp.lbl_task_name.configure(text=f"Task {mode} with {model_name_tc} model")
        fp.lbl_elapsed.set_text(f"{round(time() - t_start, 2)}s")
        fp.cbtn_open_folder.configure(state="normal")
        cbtn_invoker(sj.cache.get(f"auto_open_dir_{mode}", True), fp.cbtn_open_folder)
        fp.btn_add.configure(state="normal", command=add_to_files)
        fp.btn_cancel.configure(state="normal", command=cancel)

        update_modal_ui()
        gc.mw.start_loadBar()

        if mode == "refinement":
            export_to = dir_refinement if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"] + "/refinement"
        else:
            export_to = dir_alignment if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"] + "/alignment"

        for file in data_files:
            # file = (source_file, mode_file, lang) -> lang is only present if mode is alignment
            fail = False
            fail_msg = ""

            if not gc.file_processing:  # if cancel button is pressed
                return

            # name and get data
            logger.debug(f"PROCESSING: {file}")
            file_name = filename_only(file[0])
            save_name = datetime.now().strftime(export_format)
            save_name = save_name.replace("{file}", file_name[file_slice_start:file_slice_end])
            save_name = save_name.replace("{lang-source}", "")
            save_name = save_name.replace("{lang-target}", "")
            save_name = save_name.replace("{model}", model_name_tc)
            save_name = save_name.replace("{engine}", "")
            save_name = save_name.replace("{task}", mode)
            save_name = save_name.replace("{task-short}", task_short[mode])
            logger.debug("Save_name: " + save_name)

            audio = file[0]
            try:
                mod_source = stable_whisper.WhisperResult(file[1]) if file[1].endswith(".json") else read_txt(file[1])
            except Exception as e:
                logger.exception(e)
                logger.warning("Program failed to parse or read file, please make sure that the input is a valid file")
                fail = True
                fail_msg = e
                update_q_process(processed, gc.mod_file_counter, "Failed to parse or read file (check log)")
                continue  # continue to next file

            if mode == "alignment":
                mod_args["language"] = TO_LANGUAGE_CODE[file[2].lower()] if file[2] is not None else None

            def run_mod():
                nonlocal mod_source, processed
                try:
                    update_q_process(processed, gc.mod_file_counter, f"Processing {mode}")
                    result = mod_function(audio, mod_source, **mod_args)
                    gc.data_queue.put(result)
                    update_q_process(processed, gc.mod_file_counter, f"{action_name}")
                except Exception as e:
                    nonlocal fail, fail_msg
                    if "'NoneType' object is not iterable" in str(e):
                        # if refinement and found null token, try to transcribe the audio again and try to refine again
                        if mode == "refinement":
                            logger.warning("Found null token, now trying to re-transcribe with whisper model")
                            update_q_process(
                                processed, gc.mod_file_counter,
                                "Found null token, now trying to re-transcribe with whisper model"
                            )
                            transcribe_args = get_tc_args(model.transcribe, sj.cache)
                            logger.info(f"Process Args: {transcribe_args}")
                            result = model.transcribe(audio, **transcribe_args)
                            update_q_process(
                                processed, gc.mod_file_counter, "Transcribed successfully, now trying to refine again"
                            )
                            result = mod_function(audio, result, **mod_args)
                            update_q_process(processed, gc.mod_file_counter, "Refined")
                            gc.data_queue.put(result)
                        else:
                            fail = True
                            fail_msg = e
                            update_q_process(processed, gc.mod_file_counter, f"Failed to do {mode} (check log)")
                    else:
                        logger.exception(e)
                        fail = True
                        if "The system cannot find the file specified" in str(fail_msg) and not gc.has_ffmpeg:
                            logger.error("FFmpeg not found in system path. Please install FFmpeg and add it to system path")
                            fail_msg = Exception(
                                "FFmpeg not found in system path. Please install FFmpeg and add it to system path"
                            )
                        else:
                            fail_msg = e

                        update_q_process(processed, gc.mod_file_counter, f"Failed to do {mode} (check log)")

            thread = Thread(target=run_mod, daemon=True)
            thread.start()

            while thread.is_alive():
                if not gc.file_processing:
                    logger.debug(f"Cancelling {mode}")
                    kill_thread(thread)
                    raise Exception("Cancelled")
                sleep(0.1)

            if fail:
                native_notify(f"Error: {mode} failed", str(fail_msg))
                continue

            result: stable_whisper.WhisperResult = gc.data_queue.get()
            save_output_stable_ts(result, path.join(export_to, save_name), sj.cache["export_to"], sj)
            gc.mod_file_counter += 1

            while adding:
                sleep(0.3)

        # destroy progress window
        if fp.root.winfo_exists():
            fp.root.after(100, fp.root.destroy)

        logger.info(f"End process ({mode}) [Total time: {time() - t_start:.2f}s]")

        # turn off loadbar
        gc.mw.stop_loadBar()

        if gc.mod_file_counter > 0:
            # open folder
            if sj.cache["auto_open_dir_export"]:
                start_file(export_to)

        mbox(f"File {mode} Done", f"{action_name} {gc.mod_file_counter} file(s)", 0)
        # done, interaction is re enabled in main
    except Exception as e:
        if str(e) != "Cancelled":
            logger.error(f"Error occured while doing {mode}")
            logger.exception(e)
            assert gc.mw is not None
            mbox(f"Error occured while doing {mode}", f"{str(e)}", 2, gc.mw.root)

            if mode == "refinement":
                gc.mw.refinement_stop(prompt=False, notify=False)
            else:
                gc.mw.alignment_stop(prompt=False, notify=False)
        else:
            logger.info(f"{mode} cancelled")

        try:
            if fp and fp.root.winfo_exists():  # type: ignore
                fp.root.after(1000, fp.root.destroy)  # destroy progress window
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to destroy progress window")
    finally:
        gc.disable_rec()  # making sure
        gc.mw.enable_interactions()


def translate_result(data_files: List, engine: str, lang_target: str):
    """Function to translate the result of whisper process.

    Parameters
    ----------
    data_files : List
        List of data files
        The list should be [(source_file, lang_target), ...]
    engine : str
        Translation engine to use
    lang_target : str
        Language to translate to
    """

    assert gc.mw is not None
    try:
        gc.mw.disable_interactions()
        master = gc.mw.root
        fp = FileProcessDialog(master, "File Translate Progress", "translate", ["Source File", "Status"], sj)

        logger.info("Start Process (MOD FILE)")
        gc.mod_file_counter = 0
        adding = False
        export_format: str = sj.cache["export_format"]
        file_slice_start = (None if sj.cache["file_slice_start"] == "" else int(sj.cache["file_slice_start"]))
        file_slice_end = None if sj.cache["file_slice_end"] == "" else int(sj.cache["file_slice_end"])
        fail_status = [False, ""]
        export_to = dir_translate if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"] + "/translate"

        tl_args = {
            "proxies": get_proxies(sj.cache["http_proxy"], sj.cache["https_proxy"]),
            "engine": engine,
            "lang_target": lang_target.lower(),
            "debug_log": sj.cache["debug_translate"],
            "fail_status": fail_status
        }
        if engine == "LibreTranslate":
            tl_args["libre_https"] = sj.cache["libre_https"]
            tl_args["libre_host"] = sj.cache["libre_host"]
            tl_args["libre_port"] = sj.cache["libre_port"]
            tl_args["libre_api_key"] = sj.cache["libre_api_key"]

        t_start = time()
        logger.info(f"Process Args: {tl_args}")

        processed = []

        def get_queue_data():
            nonlocal data_files, processed
            show = []
            for index, file in enumerate(data_files):
                status = ""
                temp = get_list_of_dict(processed, "index", index)
                if temp is not None:
                    status += f"{temp['status']}"
                else:
                    status += "Waiting"

                show.append([file, status])  # file[0] is the directory of the source file

            return show

        def add_to_files():
            nonlocal data_files, adding
            adding = True
            to_add = filedialog.askopenfilenames(
                title="Select a file",
                filetypes=(("JSON (Whisper Result)", "*.json"), ),
            )

            if len(to_add) > 0:
                data_files.extend(list(to_add))
                fp.lbl_files.set_text(text=f"{gc.mod_file_counter}/{len(data_files)}")

            adding = False

        def cancel():
            assert gc.mw is not None
            gc.mw.translate_stop(prompt=True, notify=True, master=fp.root)

        def update_modal_ui():
            nonlocal t_start
            if gc.file_processing:

                fp.lbl_files.set_text(text=f"{gc.mod_file_counter}/{len(data_files)}")
                fp.lbl_elapsed.set_text(text=f"{strftime('%H:%M:%S', gmtime(time() - t_start))}")

                if gc.mod_file_counter > 0:
                    fp.lbl_files.set_text(
                        text=f"{gc.mod_file_counter}/{len(data_files)} ({filename_only(data_files[gc.mod_file_counter - 1])})"
                    )
                else:
                    fp.lbl_files.set_text(
                        text=f"{gc.mod_file_counter}/{len(data_files)} ({filename_only(data_files[gc.mod_file_counter])})"
                    )

                fp.lbl_processed.set_text(text=f"{gc.mod_file_counter}")

                # update progressbar
                prog_file_len = len(data_files)
                fp.progress_bar["value"] = (gc.mod_file_counter / prog_file_len * 100)

                fp.queue_window.update_sheet(get_queue_data())
                fp.root.after(1000, update_modal_ui)

        # widgets
        fp.lbl_task_name.configure(text=f"Task Translate with {engine} engine")
        fp.lbl_elapsed.set_text(f"{round(time() - t_start, 2)}s")
        fp.cbtn_open_folder.configure(state="normal")
        cbtn_invoker(sj.cache["auto_open_dir_translate"], fp.cbtn_open_folder)
        fp.btn_add.configure(state="normal", command=add_to_files)
        fp.btn_cancel.configure(state="normal", command=cancel)

        update_modal_ui()
        gc.mw.start_loadBar()

        for file in data_files:
            if not gc.file_processing:  # cancel button is pressed
                return

            # name and get data
            update_q_process(processed, gc.mod_file_counter, "Processing")
            try:
                result = stable_whisper.WhisperResult(file)
            except Exception as e:
                logger.exception(e)
                logger.warning("Program failed to parse or read file, please make sure that the input is a valid file")
                fail_status[0] = True
                fail_status[1] = e
                update_q_process(processed, gc.mod_file_counter, "Failed to parse or read file (check log)")
                continue

            lang_source = to_language_name(result.language)  # type: ignore
            tl_args["lang_source"] = lang_source  # convert from lang code to language name
            if not verify_language_in_key(lang_source, engine):
                logger.warning(
                    f"Language {lang_source} is not supported by {engine} engine. Will try to use auto and it might not work out the way its supposed to"
                )

            logger.debug(f"PROCESSING: {file}")
            logger.debug(f"Lang source: {lang_source}")
            file_name = filename_only(file)
            save_name = datetime.now().strftime(export_format)
            save_name = save_name.replace("{file}", file_name[file_slice_start:file_slice_end])
            save_name = save_name.replace("{lang-source}", lang_source)
            save_name = save_name.replace("{lang-target}", lang_target)
            save_name = save_name.replace("{model}", "")
            save_name = save_name.replace("{engine}", engine)
            save_name = save_name.replace("{task}", "translate")
            save_name = save_name.replace("{task-short}", "tl")
            logger.debug("Save_name: " + save_name)

            thread = Thread(target=run_translate_api, args=[result], kwargs=tl_args, daemon=True)
            thread.start()

            while thread.is_alive():
                if not gc.file_processing:
                    logger.debug("Cancelling translation")
                    kill_thread(thread)
                    raise Exception("Cancelled")
                sleep(0.1)

            if fail_status[0]:
                update_q_process(processed, gc.mod_file_counter, "Failed to translate (check log)")
                native_notify("Error: Translate failed", str(fail_status[1]))
                continue  # continue to next file

            gc.mod_file_counter += 1
            save_output_stable_ts(result, path.join(export_to, save_name), sj.cache["export_to"], sj)

            while adding:
                sleep(0.3)

        # destroy progress window
        if fp.root.winfo_exists():
            fp.root.after(100, fp.root.destroy)

        logger.info(f"End process (Translate result) [Total time: {time() - t_start:.2f}s]")

        # turn off loadbar
        gc.mw.stop_loadBar()

        if gc.mod_file_counter > 0:
            # open folder
            if sj.cache["auto_open_dir_translate"]:
                start_file(export_to)

        mbox("File Translate Done", f"Translated {gc.mod_file_counter} file(s)", 0)
    except Exception as e:
        if str(e) != "Cancelled":
            logger.error("Error occured while translating file(s)")
            logger.exception(e)
            assert gc.mw is not None
            mbox("Error occured while processing file(s)", f"{str(e)}", 2, gc.mw.root)
            gc.mw.translate_stop(prompt=False, notify=False)
        else:
            logger.debug("Cancelled translate")

        try:
            if fp and fp.root.winfo_exists():  # type: ignore
                fp.root.after(1000, fp.root.destroy)  # destroy progress window
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to destroy progress window")
    finally:
        gc.disable_rec()  # update flag
        gc.mw.enable_interactions()
