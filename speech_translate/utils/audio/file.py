import sys
import json
from os import path, makedirs
from datetime import datetime
from threading import Thread
from time import gmtime, sleep, strftime, time
from tkinter import filedialog
from typing import List, Literal, Union, Dict

import stable_whisper  # https://github.com/jianfch/stable-ts # has no static annotation hence many type ignore
from whisper.tokenizer import TO_LANGUAGE_CODE
from torch import cuda

from speech_translate._path import dir_export, dir_alignment, dir_refinement, dir_translate
from speech_translate._logging import logger
from speech_translate.linker import bc, sj
from speech_translate.utils.translate.language import get_whisper_lang_name, verify_language_in_key, get_whisper_lang_similar
from speech_translate.ui.custom.dialog import ModResultInputDialog, FileProcessDialog
from speech_translate.ui.custom.message import mbox

from ..helper import cbtn_invoker, get_proxies, native_notify, filename_only, start_file, up_first_case, get_list_of_dict, kill_thread
from ..whisper.helper import get_hallucination_filter, get_model, get_model_args, get_tc_args, save_output_stable_ts, model_values, to_language_name, get_task_format, split_res, remove_segments_by_str
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
        bc.data_queue.put(result)
        sys.stderr.write(f"Whisper {task} done\n")
    except Exception as e:
        logger.exception(e)
        fail_status[0] = True
        if "The system cannot find the file specified" in str(e) and not bc.has_ffmpeg:
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
        for s_index, segment in enumerate(query.segments):
            if len(result) == 0:
                logger.warning("Some part of the text might not be translated")
                return

            if isinstance(result, str):
                raise Exception(result)

            # dont forget to also add space back because its removed automatically in the api call
            segment.text = " " + str(result.pop(0))

            # because each word is taken from the text, we can replace the word with the translated text
            # but we first need to check the  of splitted translated text because sometimes its not the same length as the original
            temp_words = segment.text.split()
            translated_word_length = len(temp_words)
            if translated_word_length == len(segment.words):
                for word in segment.words:
                    word.word = " " + temp_words.pop(0)
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
                    for w_index, word in enumerate(temp_words):
                        nearest = nearest_array_index(segment.words, w_index)

                        # adding until hit the limit
                        if w_index < len(segment.words):
                            segment.words[nearest].word = " " + word
                        else:
                            # hit limit, just add the rest of the words
                            segment.words[nearest].word += f" {word}"
                # if tl word length < original word length, add until hit the limit (tl word length)
                # delete the rest of the words and then update the last word segment timing
                else:
                    logger.debug("TL word < Original word")
                    # get last word segment
                    last_word = segment.words[-1]

                    for w_index, word in enumerate(temp_words):
                        segment.words[w_index].word = " " + word

                    # delete the over boundary word that is probably not needed
                    segment.words = delete_elements_after_index(segment.words, translated_word_length - 1)

                    # now update the new one with last word segment timing
                    segment.words[-1].end = last_word.end

        sys.stderr.write(f"Translation with {engine} done\n")
    except Exception as e:
        logger.exception(e)
        fail_status[0] = True
        if "The system cannot find the file specified" in str(e) and not bc.has_ffmpeg:
            logger.error("FFmpeg not found in system path. Please install FFmpeg and add it to system path")
            fail_status[1] = Exception("FFmpeg not found in system path. Please install FFmpeg and add it to system path")
        elif "HTTPSConnectionPool" in str(e):
            logger.error("No internet or fail to reach host!")
            fail_status[1] = Exception("Fail to reach host! Might be because of no internet connection or host is down")
        else:
            fail_status[1] = e


# run in threaded environment with queue and exception to cancel
def cancellable_tc(
    audio_name: str,
    lang_source: str,
    lang_target: str,
    model_name_tc: str,
    stable_tc,
    stable_tl,
    auto: bool,
    transcribe: bool,
    translate: bool,
    engine: str,
    save_name: str,
    save_meta: str,
    tracker_index: int,
    hallucination_filters: Dict,
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
    save_name: str
        name of the file to save the transcription to
    save_meta: str
        name of the file to save the metadata to
    tracker_index: int
        index to track the progress
    **whisper_args:
        whisper parameter

    Returns
    -------
    None
    """
    assert bc.mw is not None
    global global_file_import_counter, processed_tc
    start = time()

    try:
        update_q_process(processed_tc, tracker_index, "Transcribing please wait...")
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]
        format_dict = get_task_format(
            "transcribed", f"transcribed {lang_source}", f"transcribed with {model_name_tc}",
            f"transcribed {lang_source} with {model_name_tc}"
        )
        format_dict.update(
            get_task_format(
                "tc",
                f"tc {lang_source}",
                f"tc with {model_name_tc}",
                f"tc {lang_source} with {model_name_tc}",
                short_only=True
            )
        )
        f_name = save_name
        for fmt, value in format_dict.items():
            f_name = f_name.replace(fmt, value)

        logger.info("-" * 50)
        logger.info("Transcribing")
        logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")

        fail_status = [False, ""]

        thread = Thread(
            target=run_whisper, args=[stable_tc, audio_name, "transcribe", fail_status], kwargs=whisper_args, daemon=True
        )
        thread.start()

        while thread.is_alive():
            if not bc.transcribing_file:
                logger.debug("Cancelling transcription")
                kill_thread(thread)
                raise Exception("Cancelled")
            sleep(0.1)

        if fail_status[0]:
            raise Exception(fail_status[1])

        result_tc: stable_whisper.WhisperResult = bc.data_queue.get()
        if sj.cache["filter_file_import"]:
            try:
                assert result_tc.language is not None, "Language is None"
                result_tc = remove_segments_by_str(
                    result_tc, hallucination_filters[get_whisper_lang_name(result_tc.language) if auto else lang_source],
                    sj.cache["filter_file_import_case_sensitive"], sj.cache["filter_file_import_strip"],
                    sj.cache["filter_file_import_ignore_punctuations"]
                )
            except Exception as e:
                logger.exception(e)
                logger.error("Error in filtering hallucination")

        if sj.cache["remove_repetition_file_import"]:
            result_tc = result_tc.remove_repetition(sj.cache["remove_repetition_amount"])

        # export if transcribe mode is on
        if transcribe:
            result_tc_save = stable_whisper.WhisperResult(result_tc.to_dict())
            result_tc_save = split_res(result_tc_save, sj.cache)
            result_text = result_tc.text.strip()

            if len(result_text) > 0:
                bc.file_tced_counter += 1
                save_output_stable_ts(result_tc_save, path.join(export_to, f_name), sj.cache["export_to"], sj)
            else:
                logger.warning("Transcribed Text is empty")
                update_q_process(processed_tc, tracker_index, "TC Fail! Got empty transcribed text")

        update_q_process(processed_tc, tracker_index, "Transcribed")
        taken = time() - start
        logger.debug(f"Transcribing Audio: {f_name} | Time Taken: {taken:.2f}s")

        try:
            meta = {}
            p = path.join(export_to, save_meta + ".json")
            makedirs(path.dirname(p), exist_ok=True)
            with open(p, "r", encoding="utf-8") as f:
                meta = json.load(f)
                meta["transcribe_time"] = taken
                meta["transcribe_success"] = True

            with open(p, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=4)
            logger.debug("Updated tc metadata")
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to update metadata")

        # start translation thread if translate mode is on
        if translate:
            # send result as srt if not using whisper because it will be send to translation API.
            # If using whisper translation will be done using whisper model
            res_to_tl = result_tc if engine not in model_values else audio_name
            translateThread = Thread(
                target=cancellable_tl,
                args=[
                    res_to_tl, lang_source, lang_target, stable_tl, engine, auto, save_name, save_meta, tracker_index,
                    hallucination_filters
                ],
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
    save_meta: str,
    tracker_index: int,
    hallucination_filters: Dict,
    **whisper_args,
):
    """
    Translate the result of file input using either whisper model or translation API
    This function is cancellable with the cancel flag that is set by the cancel button and will be checked periodically every
    0.1 seconds. If the cancel flag is set, the function will raise an exception to stop the thread

    Args
    ----
    query: str or stable_whisper.WhisperResult
        audio file path if engine is whisper, result of whisper process if engine is not whisper
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
    save_meta: str
        name of the file to save the metadata to
    tracker_index: int
        index to track the progress
    **whisper_args:
        whisper parameter

    Returns
    -------
    None
    """
    assert bc.mw is not None
    global global_file_import_counter, processed_tl
    start = time()

    try:
        update_q_process(processed_tl, tracker_index, "Translating please wait...")
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]
        format_dict = get_task_format(
            "translated",
            f"translated {lang_source} to {lang_target}",
            f"translated with {engine}",
            f"translated {lang_source} to {lang_target} with {engine}",
        )
        format_dict.update(
            get_task_format(
                "tl",
                f"tl {lang_source} to {lang_target}",
                f"tl with {engine}",
                f"tl {lang_source} to {lang_target} with {engine}",
                short_only=True
            )
        )
        f_name = save_name
        for fmt, value in format_dict.items():
            f_name = f_name.replace(fmt, value)

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
                if not bc.translating_file:
                    logger.debug("Cancelling translation")
                    kill_thread(thread)
                    raise Exception("Cancelled")
                sleep(0.1)

            if fail_status[0]:
                raise Exception(fail_status[1])

            result_tl: stable_whisper.WhisperResult = bc.data_queue.get()
            if sj.cache["filter_file_import"]:
                try:
                    assert result_tl.language is not None, "Language is None"
                    result_tl = remove_segments_by_str(
                        result_tl, hallucination_filters[get_whisper_lang_name(result_tl.language) if auto else lang_source],
                        sj.cache["filter_file_import_case_sensitive"], sj.cache["filter_file_import_strip"],
                        sj.cache["filter_file_import_ignore_punctuations"]
                    )
                except Exception as e:
                    logger.exception(e)
                    logger.error("Error in filtering hallucination")

            if sj.cache["remove_repetition_file_import"]:
                result_tl = result_tl.remove_repetition(sj.cache["remove_repetition_amount"])

            # if whisper, sended text (toTranslate) is the audio file path
            resultTxt = result_tl.text.strip()

            if len(resultTxt) == 0:
                logger.warning("Translated Text is empty")
                update_q_process(processed_tl, tracker_index, "TL Fail! Got empty translated text")
                return

            result_tl = split_res(result_tl, sj.cache)
            bc.file_tled_counter += 1
            save_output_stable_ts(result_tl, path.join(export_to, f_name), sj.cache["export_to"], sj)
        else:
            # when using TL API, query is the result of whisper process
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
                if not bc.translating_file:
                    logger.debug("Cancelling translation")
                    kill_thread(thread)
                    raise Exception("Cancelled")
                sleep(0.1)

            if fail_status[0]:
                raise Exception(fail_status[1])

            bc.file_tled_counter += 1
            query = split_res(query, sj.cache)
            save_output_stable_ts(query, path.join(export_to, f_name), sj.cache["export_to"], sj)

        update_q_process(processed_tl, tracker_index, "Translated")
        taken = time() - start
        logger.debug(f"Translated: {f_name} | Time Taken: {taken:.2f}s")

        try:
            meta = {}
            p = path.join(export_to, save_meta + ".json")
            makedirs(path.dirname(p), exist_ok=True)
            with open(p, "r", encoding="utf-8") as f:
                meta = json.load(f)
                meta["translate_time"] = taken
                meta["translate_success"] = True

            with open(p, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=4)

            logger.debug("Updated tl metadata")
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to update metadata")
    except Exception as e:
        update_q_process(processed_tl, tracker_index, "Failed to translate")
        if str(e) == "Cancelled":
            logger.info("Translation cancelled")
        else:
            logger.exception(e)
            native_notify(f"Error: translation with {engine} failed ", str(e) + " Check log for details")
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
    assert bc.mw is not None
    try:
        bc.mw.disable_interactions()
        master = bc.mw.root
        fp = FileProcessDialog(master, "File Import Progress", "export", ["Audio / Video File", "Status"], sj)

        logger.info("Start Process (FILE)")
        bc.file_tced_counter = 0
        bc.file_tled_counter = 0

        auto = lang_source == "auto detect"
        tl_engine_whisper = engine in model_values

        export_format: str = sj.cache["export_format"]
        file_slice_start = (None if sj.cache["file_slice_start"] == "" else int(sj.cache["file_slice_start"]))
        file_slice_end = None if sj.cache["file_slice_end"] == "" else int(sj.cache["file_slice_end"])
        visualize_suppression = sj.cache["visualize_suppression"]

        # load model
        model_args = get_model_args(sj.cache)
        _model_tc, _model_tl, stable_tc, stable_tl, to_args = get_model(
            transcribe, translate, tl_engine_whisper, model_name_tc, engine, sj.cache, **model_args
        )
        whisper_args = get_tc_args(to_args, sj.cache)
        whisper_args["language"] = TO_LANGUAGE_CODE[get_whisper_lang_similar(lang_source)] if not auto else None
        if sj.cache["filter_file_import"]:
            hallucination_filters = get_hallucination_filter('file', sj.cache["path_filter_file_import"])
        else:
            hallucination_filters = {}

        # update button text
        bc.mw.btn_import_file.configure(text="Cancel")

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
                    current_file_counter = bc.file_tced_counter
                else:
                    current_file_counter = bc.file_tled_counter
                data_files.extend(list(to_add))
                fp.lbl_files.set_text(text=f"{current_file_counter}/{len(data_files)}")

            adding = False

        canceled = False

        def cancel():
            nonlocal canceled
            # confirm
            if mbox("Cancel confirmation", "Are you sure you want to cancel file process?", 3, master):
                assert bc.mw is not None
                canceled = True
                bc.mw.from_file_stop(prompt=False, notify=True)

        def update_modal_ui():
            nonlocal t_start, local_file_import_counter
            prev_q_data = []
            while bc.file_processing:
                try:
                    fp.lbl_elapsed.set_text(text=f"{strftime('%H:%M:%S', gmtime(time() - t_start))}")

                    if local_file_import_counter > 0:
                        cur_file = f"{local_file_import_counter}/{len(data_files)} ({filename_only(data_files[local_file_import_counter - 1])})"
                    else:
                        cur_file = f"{local_file_import_counter}/{len(data_files)} ({filename_only(data_files[local_file_import_counter])})"
                    fp.lbl_files.set_text(text=cur_file)

                    processed = ""
                    if transcribe:
                        processed += f"{bc.file_tced_counter} Transcribed"
                    if translate:
                        if transcribe:
                            processed += ", "
                        processed += f"{bc.file_tled_counter} Translated"
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
                    new = get_queue_data()
                    if new != prev_q_data:
                        prev_q_data = new
                        fp.queue_window.update_sheet(new)

                    sleep(1)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)
                        logger.warning("Failed to update modal ui | Ignore if already closed")
                        break

        # widgets
        fp.lbl_task_name.configure(text=f"Task: {taskname} {language} with {model_name_tc} model")
        fp.lbl_elapsed.set_text(f"{round(time() - t_start, 2)}s")
        fp.cbtn_open_folder.configure(state="normal")
        cbtn_invoker(sj.cache["auto_open_dir_export"], fp.cbtn_open_folder)
        fp.btn_add.configure(state="normal", command=add_to_files)
        fp.btn_cancel.configure(state="normal", command=cancel)

        update_ui_thread = Thread(target=update_modal_ui, daemon=True)
        update_ui_thread.start()

        bc.mw.start_loadBar()
        bc.enable_file_tc()
        bc.enable_file_tl()

        for file in data_files:
            if not bc.file_processing:  # if cancel button is pressed
                return

            # Proccess it
            logger.debug("FILE PROCESSING: " + file)
            file_name = filename_only(file)
            save_name = datetime.now().strftime(export_format)
            save_name = save_name.replace("{file}", file_name[file_slice_start:file_slice_end])
            save_name = save_name.replace("{lang-source}", lang_source)
            save_name = save_name.replace("{lang-target}", lang_target)
            save_name = save_name.replace("{transcribe-with}", model_name_tc)
            save_name = save_name.replace("{translate-with}", engine)
            logger.debug("Save_name: " + save_name)
            export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]

            save_meta = save_name
            format_dict = get_task_format("metadata", "metadata", "metadata", "metadata", both=True)
            for fmt, value in format_dict.items():
                save_meta = save_meta.replace(fmt, value)

            p = path.join(export_to, save_meta + ".json")
            makedirs(path.dirname(p), exist_ok=True)
            if visualize_suppression:
                save_visual = save_name
                format_dict = get_task_format(
                    "visualized supression",
                    "visualized supression",
                    f"visualized supression with vad {whisper_args['vad']}",
                    f"visualized supression with vad {whisper_args['vad']}",
                    both=True
                )
                for fmt, value in format_dict.items():
                    save_visual = save_visual.replace(fmt, value)

                stable_whisper.visualize_suppression(
                    file, path.join(export_to, save_visual + ".png"), vad=whisper_args["vad"]
                )
                logger.debug("saved visualized suppression")

            with open(p, "w", encoding="utf-8") as f:
                meta = {
                    "meta_written_at": str(datetime.now()),
                    "task": taskname,
                    "filename": file_name,
                    "transcribe": transcribe,
                    "translate": translate,
                    "model": model_name_tc if transcribe or tl_engine_whisper else "",
                    "using_faster_whisper": sj.cache["use_faster_whisper"],
                    "engine": engine if translate else "",
                    "source_language": lang_source,
                    "target_language": lang_target if translate else "",
                    "visualize_supression": visualize_suppression,
                    "segment_level": sj.cache["segment_level"],
                    "word_level": sj.cache["word_level"],
                    "segment_limit": {
                        "segment_max_words": sj.cache["segment_max_words"],
                        "segment_max_chars": sj.cache["segment_max_chars"],
                        "segment_split_or_newline": sj.cache["segment_split_or_newline"],
                        "segment_even_split": sj.cache["segment_even_split"],
                    },
                    "model_args": model_args,
                    "whisper_args": whisper_args,
                }
                f.write(json.dumps(meta, ensure_ascii=False, indent=4))
                logger.debug("saved metadata")

            # if only translating and using the whisper engine
            if translate and not transcribe and tl_engine_whisper:
                proc_thread = Thread(
                    target=cancellable_tl,
                    args=[
                        file, lang_source, lang_target, stable_tl, engine, auto, save_name, save_meta,
                        global_file_import_counter, hallucination_filters
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
                        file, lang_source, lang_target, model_name_tc, stable_tc, stable_tl, auto, transcribe, translate,
                        engine, save_name, save_meta, global_file_import_counter, hallucination_filters
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

        bc.disable_file_tc()
        bc.disable_file_tl()

        # destroy progress window
        if fp.root.winfo_exists():
            fp.root.after(100, fp.root.destroy)

        logger.info(f"End process (FILE) [Total time: {time() - t_start:.2f}s]")

        del _model_tc, _model_tl, stable_tc, stable_tl, to_args, whisper_args
        # turn off loadbar
        bc.mw.stop_loadBar("file")
        bc.disable_file_process()  # update flag

        if bc.file_tced_counter > 0 or bc.file_tled_counter > 0:
            # open folder
            if sj.cache["auto_open_dir_export"]:
                export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]
                start_file(export_to)

        resultMsg = (
            f"Transcribed {bc.file_tced_counter} file(s) and Translated {bc.file_tled_counter} file(s)"
            if transcribe and translate else
            f"Transcribed {bc.file_tced_counter} file(s)" if transcribe else f"Translated {bc.file_tled_counter} file(s)"
        )

        if not canceled:
            mbox(f"File {taskname} Done", resultMsg, 0, master)
    except Exception as e:
        bc.disable_file_process()
        bc.disable_file_tc()
        bc.disable_file_tl()
        logger.error("Error occured while processing file(s)")
        logger.exception(e)
        mbox("Error occured while processing file(s)", f"{str(e)}", 2, bc.mw.root)

        try:
            if fp and fp.root.winfo_exists():  # type: ignore
                fp.root.after(1000, fp.root.destroy)  # destroy progress window
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to destroy progress window")
    finally:
        cuda.empty_cache()
        bc.mw.from_file_stop(prompt=False, notify=False)
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

    assert bc.mw is not None
    try:
        bc.mw.disable_interactions()
        master = bc.mw.root
        fp = FileProcessDialog(master, f"File {up_first_case(mode)} Progress", mode, ["Audio/Video File", "Status"], sj)
        task_short = {"refinement": "rf", "alignment": "al"}

        logger.info("Start Process (MOD FILE)")
        bc.mod_file_counter = 0
        adding = False
        action_name = "Refined" if mode == "refinement" else "Aligned"
        export_format: str = sj.cache["export_format"]
        file_slice_start = (None if sj.cache["file_slice_start"] == "" else int(sj.cache["file_slice_start"]))
        file_slice_end = None if sj.cache["file_slice_end"] == "" else int(sj.cache["file_slice_end"])

        # load model
        model_args = get_model_args(sj.cache)
        # alignment is possible using faster whisper model with stable whisper
        if mode == "alignment" and sj.cache["use_faster_whisper"]:
            model = stable_whisper.load_faster_whisper(model_name_tc, **model_args)
        else:
            model = stable_whisper.load_model(model_name_tc, **model_args)
        mod_function = model.refine if mode == "refinement" else model.align  # type: ignore
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

                fp.lbl_files.set_text(text=f"{bc.mod_file_counter}/{len(data_files)}")

            adding = False

        def cancel():
            assert bc.mw is not None
            if mode == "refinement":
                bc.mw.refinement_stop(prompt=True, notify=True, master=fp.root)
            else:
                bc.mw.alignment_stop(prompt=True, notify=True, master=fp.root)

        def update_modal_ui():
            nonlocal t_start
            prev_q_data = []
            while bc.file_processing:
                try:
                    fp.lbl_elapsed.set_text(text=f"{strftime('%H:%M:%S', gmtime(time() - t_start))}")

                    if bc.mod_file_counter > 0:
                        cur_file = f"{bc.mod_file_counter}/{len(data_files)} ({filename_only(data_files[bc.mod_file_counter - 1][0])})"
                    else:
                        cur_file = f"{bc.mod_file_counter}/{len(data_files)} ({filename_only(data_files[bc.mod_file_counter][0])})"
                    fp.lbl_files.set_text(text=cur_file)

                    fp.lbl_processed.set_text(text=f"{bc.mod_file_counter}")
                    # update progressbar
                    prog_file_len = len(data_files)
                    fp.progress_bar["value"] = (bc.mod_file_counter / prog_file_len * 100)
                    new = get_queue_data()
                    if new != prev_q_data:
                        prev_q_data = new
                        fp.queue_window.update_sheet(new)

                    sleep(1)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)
                        logger.warning("Failed to update modal ui | Ignore if already closed")
                        break

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

        update_ui_thread = Thread(target=update_modal_ui, daemon=True)
        update_ui_thread.start()
        bc.mw.start_loadBar()

        if mode == "refinement":
            export_to = dir_refinement if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"] + "/@refined"
        else:
            export_to = dir_alignment if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"] + "/@aligned"

        for file in data_files:
            # file = (source_file, mod_file, lang) -> lang is only present if mode is alignment
            fail = False
            fail_msg = ""

            if not bc.file_processing:  # if cancel button is pressed
                return

            # name and get data
            start = time()
            logger.debug(f"PROCESSING: {file}")
            file_name = filename_only(file[0])
            save_name = datetime.now().strftime(export_format)
            save_name = save_name.replace("{file}", file_name[file_slice_start:file_slice_end])
            save_name = save_name.replace("{lang-source}", "")
            save_name = save_name.replace("{lang-target}", "")
            save_name = save_name.replace("{transcribe-with}", model_name_tc)
            save_name = save_name.replace("{translate-with}", "")

            save_meta = save_name
            format_dict = get_task_format("metadata", "metadata", "metadata", "metadata", both=True)
            for fmt, value in format_dict.items():
                save_meta = save_meta.replace(fmt, value)

            format_dict = get_task_format(
                action_name, action_name, f"{action_name} with {model_name_tc}", f"{action_name} with {model_name_tc}"
            )
            format_dict.update(
                get_task_format(
                    task_short[mode],
                    task_short[mode],
                    f"{task_short[mode]} with {model_name_tc}",
                    f"{task_short[mode]} with {model_name_tc}",
                    short_only=True
                )
            )
            for fmt, value in format_dict.items():
                save_name = save_name.replace(fmt, value)

            logger.debug("Save_name: " + save_name)

            audio = file[0]
            try:
                mod_source = stable_whisper.WhisperResult(file[1]) if file[1].endswith(".json") else read_txt(file[1])
            except Exception as e:
                logger.exception(e)
                logger.warning("Program failed to parse or read file, please make sure that the input is a valid file")
                fail = True
                fail_msg = e
                update_q_process(processed, bc.mod_file_counter, "Failed to parse or read file (check log)")
                continue  # continue to next file

            if mode == "alignment":
                l_code = file[2].lower()
                # if > 3, means that it is a language name, not a language code
                if l_code is not None and len(l_code) > 3:
                    l_code = TO_LANGUAGE_CODE[get_whisper_lang_similar(l_code)]

                mod_args["language"] = l_code

            def run_mod():
                nonlocal mod_source, processed, model, mod_function
                try:
                    update_q_process(processed, bc.mod_file_counter, f"Processing {mode}")
                    result = mod_function(audio, mod_source, **mod_args)
                    bc.data_queue.put(result)
                    update_q_process(processed, bc.mod_file_counter, f"{action_name}")
                except Exception as e:
                    nonlocal fail, fail_msg
                    if "'NoneType' object is not iterable" in str(e):
                        # if refinement and found null token, try to transcribe the audio again and try to refine again
                        if mode == "refinement":
                            logger.warning("Found null token, now trying to re-transcribe with whisper model")
                            update_q_process(
                                processed, bc.mod_file_counter,
                                "Found null token, now trying to re-transcribe with whisper model"
                            )
                            try:
                                transcribe_args = get_tc_args(model.transcribe, sj.cache)
                                logger.info(f"Process Args: {transcribe_args}")
                                result = model.transcribe(audio, **transcribe_args)
                                update_q_process(
                                    processed, bc.mod_file_counter, "Transcribed successfully, now trying to refine again"
                                )
                                result = mod_function(audio, result, **mod_args)
                                update_q_process(processed, bc.mod_file_counter, "Refined")
                                bc.data_queue.put(result)
                            except Exception as e:
                                logger.exception(e)
                                fail = True
                                fail_msg = e
                                update_q_process(
                                    processed, bc.mod_file_counter, f"Failed to do {mode} on re-transcribe (check log)"
                                )
                        else:
                            fail = True
                            fail_msg = e
                            update_q_process(processed, bc.mod_file_counter, f"Failed to do {mode} (check log)")
                    else:
                        logger.exception(e)
                        fail = True
                        if "The system cannot find the file specified" in str(fail_msg) and not bc.has_ffmpeg:
                            logger.error("FFmpeg not found in system path. Please install FFmpeg and add it to system path")
                            fail_msg = Exception(
                                "FFmpeg not found in system path. Please install FFmpeg and add it to system path"
                            )
                        else:
                            fail_msg = e

                        update_q_process(processed, bc.mod_file_counter, f"Failed to do {mode} (check log)")

            thread = Thread(target=run_mod, daemon=True)
            thread.start()

            while thread.is_alive():
                if not bc.file_processing:
                    logger.debug(f"Cancelling {mode}")
                    kill_thread(thread)
                    raise Exception("Cancelled")
                sleep(0.1)

            if fail:
                native_notify(f"Error: {mode} failed", str(fail_msg) + " Check log for details")
                continue

            result: stable_whisper.WhisperResult = bc.data_queue.get()
            if sj.cache.get(f"remove_repetition_result_{mode}", False):
                result = result.remove_repetition(sj.cache["remove_repetition_amount"])
            result = split_res(result, sj.cache)
            if result.language is None:  # it could result to None when using faster whisper on alignment
                if mod_args["language"] is not None:
                    result.language = mod_args["language"]
                else:
                    result.language = "auto"

            save_output_stable_ts(result, path.join(export_to, save_name), sj.cache["export_to"], sj)
            bc.mod_file_counter += 1

            p = path.join(export_to, save_meta + ".json")
            makedirs(path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                meta = {
                    "meta_written_at": str(datetime.now()),
                    "task": "Mod Result (Refinement)" if mode == "refinement" else "Mod Result (Alignment)",
                    "filename": file_name,
                    "model": model_name_tc,
                    "using_faster_whisper": sj.cache["use_faster_whisper"],
                    "time": time() - start,
                    "model_args": model_args,
                    "whisper_args": mod_args,
                }
                f.write(json.dumps(meta, ensure_ascii=False, indent=4))
                logger.debug("saved metadata")

            while adding:
                sleep(0.3)

        # destroy progress window
        if fp.root.winfo_exists():
            fp.root.after(100, fp.root.destroy)

        logger.info(f"End process ({mode}) [Total time: {time() - t_start:.2f}s]")

        del model, mod_function
        # turn off loadbar
        bc.mw.stop_loadBar()

        if bc.mod_file_counter > 0:
            # open folder
            if sj.cache["auto_open_dir_export"]:
                start_file(export_to)

        mbox(f"File {mode} Done", f"{action_name} {bc.mod_file_counter} file(s)", 0)
        # done, interaction is re enabled in main
    except Exception as e:
        bc.disable_file_process()
        if str(e) != "Cancelled":
            logger.error(f"Error occured while doing {mode}")
            logger.exception(e)
            assert bc.mw is not None
            mbox(f"Error occured while doing {mode}", f"{str(e)}", 2, bc.mw.root)
        else:
            logger.info(f"{mode} cancelled")

        try:
            if fp and fp.root.winfo_exists():  # type: ignore
                fp.root.after(1000, fp.root.destroy)  # destroy progress window
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to destroy progress window")
    finally:
        cuda.empty_cache()
        if mode == "refinement":
            bc.mw.refinement_stop(prompt=False, notify=False)
        else:
            bc.mw.alignment_stop(prompt=False, notify=False)


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

    assert bc.mw is not None
    try:
        bc.mw.disable_interactions()
        master = bc.mw.root
        fp = FileProcessDialog(master, "Result File Translation Progress", "translate", ["Source File", "Status"], sj)

        logger.info("Start Process (MOD FILE)")
        bc.mod_file_counter = 0
        adding = False
        export_format: str = sj.cache["export_format"]
        file_slice_start = (None if sj.cache["file_slice_start"] == "" else int(sj.cache["file_slice_start"]))
        file_slice_end = None if sj.cache["file_slice_end"] == "" else int(sj.cache["file_slice_end"])
        fail_status = [False, ""]
        export_to = dir_translate if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"] + "/@translated"

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
                fp.lbl_files.set_text(text=f"{bc.mod_file_counter}/{len(data_files)}")

            adding = False

        def cancel():
            assert bc.mw is not None
            bc.mw.translate_stop(prompt=True, notify=True, master=fp.root)

        def update_modal_ui():
            nonlocal t_start
            prev_q_data = []
            while bc.file_processing:
                try:
                    fp.lbl_elapsed.set_text(text=f"{strftime('%H:%M:%S', gmtime(time() - t_start))}")

                    if bc.mod_file_counter > 0:
                        cur_file = f"{bc.mod_file_counter}/{len(data_files)} ({filename_only(data_files[bc.mod_file_counter - 1][0])})"
                    else:
                        cur_file = f"{bc.mod_file_counter}/{len(data_files)} ({filename_only(data_files[bc.mod_file_counter][0])})"
                    fp.lbl_files.set_text(text=cur_file)

                    fp.lbl_processed.set_text(text=f"{bc.mod_file_counter}")
                    # update progressbar
                    prog_file_len = len(data_files)
                    fp.progress_bar["value"] = (bc.mod_file_counter / prog_file_len * 100)
                    new = get_queue_data()
                    if new != prev_q_data:
                        prev_q_data = new
                        fp.queue_window.update_sheet(new)

                    sleep(1)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)
                        logger.warning("Failed to update modal ui | Ignore if already closed")
                        break

        # widgets
        fp.lbl_task_name.configure(text=f"Task Translate with {engine} engine")
        fp.lbl_elapsed.set_text(f"{round(time() - t_start, 2)}s")
        fp.cbtn_open_folder.configure(state="normal")
        cbtn_invoker(sj.cache["auto_open_dir_translate"], fp.cbtn_open_folder)
        fp.btn_add.configure(state="normal", command=add_to_files)
        fp.btn_cancel.configure(state="normal", command=cancel)

        update_ui_thread = Thread(target=update_modal_ui, daemon=True)
        update_ui_thread.start()
        bc.mw.start_loadBar()

        for file in data_files:
            if not bc.file_processing:  # cancel button is pressed
                return

            # name and get data
            update_q_process(processed, bc.mod_file_counter, "Processing")
            try:
                result = stable_whisper.WhisperResult(file)
            except Exception as e:
                logger.exception(e)
                logger.warning("Program failed to parse or read file, please make sure that the input is a valid file")
                fail_status[0] = True
                fail_status[1] = e
                update_q_process(processed, bc.mod_file_counter, "Failed to parse or read file (check log)")
                continue

            lang_source = to_language_name(result.language) or "auto"  # type: ignore
            tl_args["lang_source"] = lang_source  # convert from lang code to language name
            if not verify_language_in_key(lang_source, engine):
                logger.warning(
                    f"Language {lang_source} is not supported by {engine} engine. Will try to use auto and it might not work out the way its supposed to"
                )

            start = time()
            logger.debug(f"PROCESSING: {file}")
            logger.debug(f"Lang source: {lang_source} | Lang target: {lang_target}")
            file_name = filename_only(file)
            save_name = datetime.now().strftime(export_format)
            save_name = save_name.replace("{file}", file_name[file_slice_start:file_slice_end])
            save_name = save_name.replace("{lang-source}", lang_source or "")
            save_name = save_name.replace("{lang-target}", lang_target)
            save_name = save_name.replace("{transcribe-with}", "")
            save_name = save_name.replace("{translate-with}", engine)

            save_meta = save_name
            format_dict = get_task_format("metadata", "metadata", "metadata", "metadata", both=True)
            for fmt, value in format_dict.items():
                save_meta = save_meta.replace(fmt, value)

            format_dict = get_task_format(
                "translated result",
                f"translated result from {lang_source} to {lang_target}",
                f"translated result with {engine}",
                f"translated result from {lang_source} to {lang_target} with {engine}",
            )
            format_dict.update(
                get_task_format(
                    "tl res",
                    f"tl res from {lang_source} to {lang_target}",
                    f"tl res with {engine}",
                    f"tl res from {lang_source} to {lang_target} with {engine}",
                    short_only=True
                )
            )
            for fmt, value in format_dict.items():
                save_name = save_name.replace(fmt, value)

            logger.debug("Save_name: " + save_name)

            thread = Thread(target=run_translate_api, args=[result], kwargs=tl_args, daemon=True)
            thread.start()

            while thread.is_alive():
                if not bc.file_processing:
                    logger.debug("Cancelling translation")
                    kill_thread(thread)
                    raise Exception("Cancelled")
                sleep(0.1)

            if fail_status[0]:
                update_q_process(processed, bc.mod_file_counter, "Failed to translate (check log)")
                native_notify("Error: Translate failed", str(fail_status[1]) + " Check log for details")
                continue  # continue to next file

            save_output_stable_ts(result, path.join(export_to, save_name), sj.cache["export_to"], sj)
            bc.mod_file_counter += 1

            p = path.join(export_to, save_meta + ".json")
            makedirs(path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                meta = {
                    "meta_written_at": str(datetime.now()),
                    "task": "Translate Whisper Result",
                    "filename": file_name,
                    "engine": engine,
                    "source_language": lang_source,
                    "target_language": lang_target,
                    "time": time() - start,
                }
                f.write(json.dumps(meta, ensure_ascii=False, indent=4))
                logger.debug("saved metadata")

            while adding:
                sleep(0.3)

        # destroy progress window
        if fp.root.winfo_exists():
            fp.root.after(100, fp.root.destroy)

        logger.info(f"End process (Translate result) [Total time: {time() - t_start:.2f}s]")

        # turn off loadbar
        bc.mw.stop_loadBar()

        if bc.mod_file_counter > 0:
            # open folder
            if sj.cache["auto_open_dir_translate"]:
                start_file(export_to)

        mbox("File Translate Done", f"Translated {bc.mod_file_counter} file(s)", 0)
    except Exception as e:
        bc.disable_file_process()
        if str(e) != "Cancelled":
            logger.error("Error occured while translating file(s)")
            logger.exception(e)
            assert bc.mw is not None
            mbox("Error occured while processing file(s)", f"{str(e)}", 2, bc.mw.root)
        else:
            logger.debug("Cancelled translate")

        try:
            if fp and fp.root.winfo_exists():  # type: ignore
                fp.root.after(1000, fp.root.destroy)  # destroy progress window
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to destroy progress window")
    finally:
        bc.mw.translate_stop(prompt=False, notify=False)
