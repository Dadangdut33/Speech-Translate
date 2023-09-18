from ast import literal_eval
from datetime import datetime, timedelta
from io import BytesIO
from os import path, remove, sep
from platform import system
from shlex import quote
from textwrap import wrap
from threading import Lock, Thread
from time import gmtime, sleep, strftime, time
from tkinter import Toplevel, filedialog, ttk
from typing import Dict, List, Literal
from wave import Wave_read, Wave_write
from wave import open as w_open

import librosa
import numpy as np
import scipy.io.wavfile as wav
import whisper_timestamped as whisper

if system() == "Windows":
    import pyaudiowpatch as pyaudio
else:
    import pyaudio  # type: ignore

from speech_translate._constants import MAX_THRESHOLD, MIN_THRESHOLD, STEPS, WHISPER_SR
from speech_translate._path import app_icon, dir_debug, dir_temp
from speech_translate.components.custom.label import LabelTitleText
from speech_translate.components.custom.message import mbox
from speech_translate.custom_logging import logger
from speech_translate.globals import dir_export, gc, sj
from speech_translate.utils.device import auto_threshold, get_db, get_device_details

from .helper import cbtn_invoker, filename_only, generate_temp_filename, get_proxies, nativeNotify, start_file
from .helper_whisper import (
    append_dot_en, convert_str_options_to_dict, get_temperature, srt_whisper_to_txt_format, srt_whisper_to_txt_format_stamps,
    txt_to_srt_whisper_format_stamps, whisper_result_to_srt
)
from .translator import google_tl, libre_tl, memory_tl


def whisper_verbose_log(result):
    """
    This will log the result of the whisper engine in a verbose way.

    Parameters
    ----
    result:
        whisper result
    """
    logger.debug(f"Language: {result['language']}")
    logger.debug(f"Text: {result['text']}")
    logger.debug("Segments:")
    for index, segment in enumerate(result["segments"]):
        logger.debug(f"Segment {index}")
        logger.debug(f"ID: {segment['id']}")
        logger.debug(f"Seek: {segment['seek']}")
        logger.debug(f"Start: {segment['start']}")
        logger.debug(f"End: {segment['end']}")
        logger.debug(f"Text: {segment['text']}")
        logger.debug(f"Tokens: {segment['tokens']}")
        logger.debug(f"Temperature: {segment['temperature']}")
        logger.debug(f"Avg Logprob: {segment['avg_logprob']}")
        logger.debug(f"Compression Ratio: {segment['compression_ratio']}")
        logger.debug(f"No Speech Prob: {segment['no_speech_prob']}")
        logger.debug(f"Confidence: {segment['confidence']}")

        logger.debug("Words:")
        for index, words in enumerate(segment["words"]):
            logger.debug(f"Word {index}")
            logger.debug(f"Text: {words['text']}")
            logger.debug(f"Start: {words['start']}")
            logger.debug(f"End: {words['end']}")
            logger.debug(f"Confidence: {words['confidence']}")


# -------------------------------------------------------------------------------------------------------------------------
def record_realtime(
    lang_source: str,
    lang_target: str,
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"],
    modelKey: str,
    device: str,
    transcribe: bool,
    translate: bool,
    speaker: bool = False,
) -> None:
    """
    Function to record audio and translate it in real time. Speaker as input can only be used on Windows.
    Other OS need to use mic, speaker can be used only by using Loopback software such as PulseAudio, blackhole, etc.

    Parameters
    ----
    lang_source: str
        Source language
    lang_target: str
        Target language
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"]
        Translation engine
    modelKey: str
        The key of the model in modelSelectDict as the selected model to use
    device: str
        Device to use
    transcribe: bool
        Whether to transcribe the audio
    translate: bool
        Whether to translate the audio
    speaker: bool, optional
        Whether to use speaker diarization

    Returns
    ----
    None
    """
    assert gc.mw is not None
    master = gc.mw.root
    root = Toplevel(master)
    root.title("Loading...")
    root.transient(master)
    root.geometry("450x200")
    root.protocol("WM_DELETE_WINDOW", lambda: master.state("iconic"))  # minimize window when click close button
    root.geometry("+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))

    frame_lbl = ttk.Frame(root)
    frame_lbl.pack(side="top", fill="x", padx=5, pady=5, expand=True)

    frame_btn = ttk.Frame(root)
    frame_btn.pack(side="top", fill="x", padx=5, pady=5, expand=True)

    frame_lbl_1 = ttk.Frame(frame_lbl)
    frame_lbl_1.pack(side="top", fill="x")

    frame_lbl_2 = ttk.Frame(frame_lbl)
    frame_lbl_2.pack(side="top", fill="x")

    frame_lbl_3 = ttk.Frame(frame_lbl)
    frame_lbl_3.pack(side="top", fill="x")

    frame_lbl_4 = ttk.Frame(frame_lbl)
    frame_lbl_4.pack(side="top", fill="x")

    frame_lbl_5 = ttk.Frame(frame_lbl)
    frame_lbl_5.pack(side="top", fill="x")

    frame_lbl_6 = ttk.Frame(frame_lbl)
    frame_lbl_6.pack(side="top", fill="x")

    lbl_device = LabelTitleText(frame_lbl_1, "Device: ", device)
    lbl_device.pack(side="left", fill="x", padx=5, pady=5)

    lbl_sample_rate = LabelTitleText(frame_lbl_2, "Sample Rate: ", "⌛")
    lbl_sample_rate.pack(side="left", fill="x", padx=5, pady=5)

    lbl_channels = LabelTitleText(frame_lbl_2, "Channels: ", "⌛")
    lbl_channels.pack(side="left", fill="x", padx=5, pady=5)

    lbl_chunk_size = LabelTitleText(frame_lbl_2, "Chunk Size: ", "⌛")
    lbl_chunk_size.pack(side="left", fill="x", padx=5, pady=5)

    lbl_buffer = LabelTitleText(frame_lbl_3, "Buffer: ", "0/0 sec")
    lbl_buffer.pack(side="left", fill="x", padx=5, pady=5)

    progress_buffer = ttk.Progressbar(frame_lbl_4, orient="horizontal", length=200, mode="determinate")
    progress_buffer.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    lbl_timer = ttk.Label(frame_lbl_5, text="REC: 00:00:00")
    lbl_timer.pack(
        side="left",
        fill="x",
        padx=5,
        pady=5,
    )

    lbl_status = ttk.Label(frame_lbl_6, text="⌛ Setting up session...")
    lbl_status.pack(side="left", fill="x", padx=5, pady=5)

    btn_pause = ttk.Button(frame_btn, text="Pause", state="disabled")
    btn_pause.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    btn_stop = ttk.Button(frame_btn, text="Stop", style="Accent.TButton", state="disabled")
    btn_stop.pack(side="right", fill="x", padx=5, pady=5, expand=True)
    try:
        root.iconbitmap(app_icon)
    except Exception:
        pass

    modal_after = None
    try:
        src_english = lang_source == "english"
        auto = lang_source == "auto detect"
        whisperEngine = engine == "Whisper"
        modelName = append_dot_en(modelKey, src_english)

        # cannot transcribe concurrently. Will need to wait for the previous transcribe to finish
        if transcribe and whisperEngine:
            gc.tc_lock = Lock()

        # read from settings
        max_int16 = 2**15  # bit depth of 16 bit audio (32768)
        separator = literal_eval(quote(sj.cache["separate_with"]))
        use_temp = sj.cache["use_temp"]
        temperature = sj.cache["temperature"]
        whisper_args = sj.cache["whisper_extra_args"]

        success, data = get_temperature(temperature)
        if not success:
            raise Exception(data)
        else:
            temperature = data

        # assert temperature is not string
        if isinstance(temperature, str):
            raise Exception("temperature must be a floating point number")

        # parse whisper_extra_args
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

        # if only translate to english using whisper engine
        task = "translate" if whisperEngine and translate and not transcribe else "transcribe"

        # load model
        model: whisper.Whisper = whisper.load_model(modelName)

        # stop loadbar
        gc.mw.stop_loadBar("mic" if not speaker else "speaker")

        # ----------------- Get device -----------------
        logger.info("-" * 50)
        logger.info(f"Task: {task}")
        logger.info(f"Modelname: {modelName}")
        logger.info(f"Engine: {engine}")
        logger.info(f"Auto mode: {auto}")
        logger.info(f"Source Languange: {lang_source}")
        if translate:
            logger.info(f"Target Language: {lang_target}")

        p = pyaudio.PyAudio()
        success, detail = get_device_details("speaker" if speaker else "mic", sj, p)

        if not success:
            raise Exception("Failed to get device details")
        else:
            device_detail = detail["device_detail"]
            sample_rate = detail["sample_rate"]
            num_of_channels = detail["num_of_channels"]
            chunk_size = detail["chunk_size"]

        # ----------------- Start modal -----------------
        # window to show progress
        root.title("Recording")

        timerStart = time()
        paused = False
        duration_seconds = 0
        modal_update_rate = 300
        gc.current_rec_status = "💤 Idle"
        gc.auto_detected_lang = "~"
        language = f"{lang_source} → {lang_target}" if translate else lang_source

        def stop_recording():
            gc.recording = False  # only set flag to false because cleanup is handled directly down below
            btn_stop.configure(state="disabled", text="Stopping...")  # disable btn
            btn_pause.configure(state="disabled")

        def toggle_pause():
            nonlocal paused
            paused = not paused
            if paused:
                if gc.stream:
                    gc.stream.stop_stream()
                btn_pause.configure(text="Resume")
                root.title(f"Recording {rec_type} (Paused)")
                gc.current_rec_status = "⏸️ Paused"
                update_status_lbl()
            else:
                if gc.stream:
                    gc.stream.start_stream()
                btn_pause.configure(text="Pause")
                root.title(f"Recording {rec_type}")
                update_modal_ui()

        def update_status_lbl():
            lbl_status.configure(text=gc.current_rec_status)

        def update_modal_ui():
            nonlocal timerStart, paused, modal_after
            if gc.recording and not paused:
                timer = strftime("%H:%M:%S", gmtime(time() - timerStart))
                data_queue_size = gc.data_queue.qsize() * chunk_size / 1024  # approx buffer size in kb

                lbl_timer.configure(
                    text=f"REC: {timer} | "
                    f"{language if not auto else language.replace('auto detect', f'auto detect ({gc.auto_detected_lang})')}"
                )
                lbl_buffer.set_text(
                    f"{round(duration_seconds, 2)}/{round(max_record_time, 2)} sec ({round(data_queue_size, 2)} kb)"
                )
                # update progress / buffer percentage
                progress_buffer["value"] = duration_seconds / max_record_time * 100
                update_status_lbl()

                modal_after = root.after(modal_update_rate, update_modal_ui)

        transcribe_rate = timedelta(seconds=sj.cache["transcribe_rate"] / 1000)
        max_record_time = int(sj.cache["max_buffer_speaker"]) if speaker else int(sj.cache["max_buffer_mic"])
        max_sentences = int(sj.cache["max_sentences_speaker"]) if speaker else int(sj.cache["max_sentences_mic"])

        lbl_sample_rate.set_text(sample_rate)
        lbl_channels.set_text(num_of_channels)
        lbl_chunk_size.set_text(chunk_size)
        lbl_buffer.set_text(f"0/{round(max_record_time, 2)} sec")
        lbl_timer.configure(text=f"REC: 00:00:00 | {language}")
        lbl_status.configure(text="▶️ Recording")
        btn_pause.configure(state="normal", command=toggle_pause)
        btn_stop.configure(state="normal", command=stop_recording)
        update_modal_ui()

        # ----------------- Start recording -----------------
        # recording session init
        global prev_tl_text, sentences_tl, threshold, rec_type, max, min, t_start, optimal, recording
        tempList = []
        sentences_tc = []
        sentences_tl = []
        prev_tc_text = ""
        prev_tl_text = ""
        next_transcribe_time = None
        last_sample = bytes()

        # threshold
        threshold = 0
        rec_type = "speaker" if speaker else "mic"
        max = MAX_THRESHOLD
        min = MIN_THRESHOLD
        t_start = time()
        optimal = False
        recording = False
        gc.stream = p.open(
            format=pyaudio.paInt16,  # 16 bit audio
            channels=num_of_channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size,
            input_device_index=int(device_detail["index"]),
            stream_callback=record_callback,
        )

        logger.debug("Record Session Started")

        # transcribing loop
        while gc.recording:
            if paused:
                continue

            if not gc.data_queue.empty():
                now = datetime.utcnow()

                # Set next_transcribe_time for the first time.
                if not next_transcribe_time:
                    next_transcribe_time = now + transcribe_rate

                # Run transcription based on transcribe rate that is set by user.
                # The more delay it have the more it will reduces stress on the GPU / CPU (if using cpu).
                if now > next_transcribe_time:
                    next_transcribe_time = now + transcribe_rate

                    # Getting the stream data from the queue.
                    while not gc.data_queue.empty():
                        data = gc.data_queue.get()
                        last_sample += data

                    if sj.cache["debug_realtime_record"] == 1:
                        logger.info("Processing Audio")

                    # When not using temp file, we need to convert the audio to numpy array. To do that
                    # We use librosa to resample to 16k because whisper only accept 16k hz audio and
                    # when we use numpy array we need to convert it ourselves
                    if not use_temp and sample_rate != WHISPER_SR:
                        audio_as_np_int16 = np.frombuffer(last_sample,
                                                          dtype=np.int16).flatten()  # read as numpy array of int16
                        audio_as_np_float32 = audio_as_np_int16.astype(np.float32)  # convert to float32
                        resampled_audio = librosa.resample(audio_as_np_float32, orig_sr=sample_rate, target_sr=WHISPER_SR)
                        audio_bytes = resampled_audio.astype(np.int16).tobytes()  # Convert the resampled audio back to bytes
                    else:
                        audio_bytes = last_sample

                    # Write out raw frames as a wave file.
                    wf = BytesIO()
                    wav_writer: Wave_write = w_open(wf, "wb")
                    wav_writer.setframerate(WHISPER_SR if not use_temp else sample_rate)
                    wav_writer.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                    wav_writer.setnchannels(num_of_channels)
                    wav_writer.writeframes(audio_bytes)  # get the audio data from the buffer.
                    wav_writer.close()

                    # Read the audio data
                    wf.seek(0)
                    wav_reader: Wave_read = w_open(wf)
                    samples = wav_reader.getnframes()
                    audio_bytes = wav_reader.readframes(samples)
                    duration_seconds = samples / WHISPER_SR  # 2 bytes per sample for int16
                    wav_reader.close()

                    if not use_temp:
                        # Convert the wave data straight to a numpy array for the model.
                        if num_of_channels == 1:
                            audio_as_np_int16 = np.frombuffer(audio_bytes, dtype=np.int16).flatten()
                            audio_as_np_float32 = audio_as_np_int16.astype(np.float32)
                            audio_target = audio_as_np_float32 / max_int16  # normalized as Numpy array
                        else:
                            # Samples are interleaved, so for a stereo stream with left channel
                            # of [L0, L1, L2, ...] and right channel of [R0, R1, R2, ...], the output
                            # is ordered as [[L0, R0], [L1, R1], [L2, R2], ...
                            audio_as_np_int16 = np.frombuffer(audio_bytes, dtype=np.int16).flatten()
                            audio_as_np_float32 = audio_as_np_int16.astype(np.float32)

                            chunk_length = len(audio_as_np_float32) / num_of_channels
                            assert chunk_length == int(chunk_length)
                            audio_reshaped = np.reshape(audio_as_np_float32, (int(chunk_length), num_of_channels))
                            audio_target = audio_reshaped[:, 0] / max_int16  # take left channel only

                        if sj.cache["debug_recorded_audio"] == 1:
                            wav.write(generate_temp_filename(dir_debug), WHISPER_SR, audio_target)
                    else:
                        # Using temp file
                        audio_target = generate_temp_filename(dir_temp)
                        tempList.append(audio_target)  # add to the temp list to delete later

                        # block until the file is written
                        timeNow = time()
                        with open(audio_target, "wb") as f:
                            f.write(wf.getvalue())  # write it

                        if sj.cache["debug_realtime_record"] == 1:
                            logger.debug(f"File Write Time: {time() - timeNow}")

                        # delete the oldest file if the temp list is too long
                        if len(tempList) > sj.cache["max_temp"] and not sj.cache["keep_temp"]:
                            remove(tempList[0])
                            tempList.pop(0)

                    # DEBUG
                    if sj.cache["debug_realtime_record"] == 1:
                        logger.info("Transcribing")

                    # Transcribe the audio
                    gc.current_rec_status = "▶️ Recording ⟳ Transcribing"
                    if translate and whisperEngine:
                        assert gc.tc_lock is not None
                        gc.tc_lock.acquire()

                        whisper.load_audio

                    result = whisper.transcribe(
                        model,
                        audio_target,
                        language=lang_source if not auto else None,
                        task=task,
                        **whisper_args,
                    )

                    if translate and whisperEngine:
                        assert gc.tc_lock is not None
                        gc.tc_lock.release()

                    text = str(result["text"]).strip()
                    gc.auto_detected_lang = str(result["language"])

                    if len(text) > 0:
                        prev_tc_text = text
                        if transcribe:
                            if sj.cache["debug_realtime_record"] == 1:
                                if sj.cache["verbose"]:
                                    logger.debug(whisper_verbose_log(result))
                                else:
                                    logger.debug(f"New text: {text}")

                            # Clear the textbox first, then insert the new text.
                            gc.clear_mw_tc()
                            gc.clear_ex_tc()
                            to_ex_tc = ""

                            # insert previous sentences first if there are any
                            for sentence in sentences_tc:
                                gc.insert_result_mw(sentence, "tc")
                                to_ex_tc += sentence + separator

                            # insert the current sentence after previous sentences
                            gc.insert_result_mw(text, "tc")
                            gc.insert_result_ex(to_ex_tc + text, "tc")
                        if translate:
                            # Start translate thread
                            gc.current_rec_status = "▶️ Recording ⟳ Translating"

                            # Using whisper engine
                            if whisperEngine:
                                tlThread = Thread(
                                    target=whisper_realtime_tl,
                                    args=[
                                        audio_target,
                                        lang_source,
                                        auto,
                                        model,
                                    ],
                                    kwargs=whisper_args,
                                    daemon=True,
                                )
                                tlThread.start()
                            # Using translation API
                            else:
                                tlThread = Thread(
                                    target=realtime_tl, args=[text, lang_source, lang_target, engine], daemon=True
                                )
                                tlThread.start()

                    # break up the buffer If we've reached max recording time
                    if duration_seconds > max_record_time:
                        last_sample = bytes()

                        if transcribe:
                            sentences_tc.append(prev_tc_text)
                            if len(sentences_tc) >= max_sentences:
                                sentences_tc.pop(0)

                        if translate:
                            sentences_tl.append(prev_tl_text)
                            if len(sentences_tl) >= max_sentences:
                                sentences_tl.pop(0)

                    gc.current_rec_status = "▶️ Recording"  # reset status

            sleep(0.1)
        else:
            logger.debug("Record Session ended")

            gc.current_rec_status = "⚠️ Stopping stream"
            update_status_lbl()
            logger.info("-" * 50)
            logger.info("Stopping stream")
            gc.stream.stop_stream()
            gc.stream.close()

            gc.current_rec_status = "⚠️ Terminating pyaudio"
            update_status_lbl()
            logger.info("Terminating pyaudio")
            p.terminate()

            # empty the queue
            gc.current_rec_status = "⚠️ Emptying queue"
            update_status_lbl()
            logger.info("Emptying queue")
            while not gc.data_queue.empty():
                gc.data_queue.get()

            if not sj.cache["keep_temp"]:
                gc.current_rec_status = "⚠️ Cleaning up audioFiles (if any)"
                update_status_lbl()
                logger.info("Cleaning up audioFiles (if any)")
                for audio in tempList:
                    try:
                        remove(audio)
                    except FileNotFoundError:
                        pass
                logger.info("Done!")

            gc.current_rec_status = "⏹️ Stopped"
            update_status_lbl()
            gc.mw.after_rec_stop()
            if modal_after:
                root.after_cancel(modal_after)
            if root.winfo_exists():
                root.destroy()  # close if not destroyed

            logger.info("Modal closed")
            logger.info("-" * 50)
    except Exception as e:
        logger.error("Error in record session")
        logger.exception(e)
        assert gc.mw is not None
        mbox("Error in record session", f"{str(e)}", 2, gc.mw.root)
        gc.mw.rec_stop()
        gc.mw.after_rec_stop()
        if modal_after:
            root.after_cancel(modal_after)
        if root.winfo_exists():
            root.destroy()  # close if not destroyed


def record_callback(in_data, frame_count, time_info, status):
    """Record Audio From stream buffer and save it to a queue"""
    global threshold, rec_type, max, min, t_start, optimal, recording

    # TODO: show db meter in the modal, idle status, auto breakup buffer
    if not sj.cache[f"threshold_enable_{rec_type}"]:
        # store chunks of audio in queue
        # record regardless of db
        gc.data_queue.put(in_data)
    else:
        # only record if db is above threshold
        db = get_db(in_data)
        if sj.cache[f"threshold_auto_{rec_type}"]:
            threshold, max, min, t_start, optimal, recording = auto_threshold(
                db, threshold, max, min, STEPS, t_start, optimal, recording
            )

            if recording:
                gc.data_queue.put(in_data)
            else:
                gc.current_rec_status = "💤 Idle"
        else:
            if db > sj.cache[f"threshold_db_{rec_type}"]:
                gc.data_queue.put(in_data)
            else:
                gc.current_rec_status = "💤 Idle"

    return (in_data, pyaudio.paContinue)


def whisper_realtime_tl(
    audio_normalised,
    lang_source: str,
    auto: bool,
    model: whisper.Whisper,
    **whisper_args,
):
    """Translate the result of realtime_recording_thread using whisper model"""
    assert gc.mw is not None
    gc.enableTranslating()

    global prev_tl_text, sentences_tl
    try:
        separator = literal_eval(quote(sj.cache["separate_with"]))

        assert gc.tc_lock is not None
        gc.tc_lock.acquire()
        result = whisper.transcribe(
            model,
            audio_normalised,
            language=lang_source if not auto else None,
            task="translate",
            **whisper_args,
        )
        gc.tc_lock.release()
        text = str(result["text"]).strip()
        gc.auto_detected_lang = str(result["language"])

        if len(text) > 0:
            prev_tl_text = text

            if sj.cache["debug_realtime_record"] == 1:
                logger.debug("New translated text (Whisper)")
                if sj.cache["verbose"]:
                    logger.debug(whisper_verbose_log(result))
                else:
                    logger.debug(f"{text}")

            # Clear the textbox first, then insert the new text.
            gc.clear_mw_tl()
            gc.clear_ex_tl()
            to_ex_tb = ""

            # insert previous sentences if there are any
            for sentence in sentences_tl:
                gc.insert_result_mw(sentence, "tl")
                to_ex_tb += sentence + separator

            # insert the current sentence after previous sentences
            gc.insert_result_mw(text, "tl")
            gc.insert_result_ex(to_ex_tb + text, "tl")

    except Exception as e:
        logger.exception(e)
        nativeNotify("Error: translating failed", str(e))
    finally:
        gc.disableTranslating()  # flag processing as done


def realtime_tl(
    text: str, lang_source: str, lang_target: str, engine: Literal["Google", "LibreTranslate", "MyMemoryTranslator"]
):
    """Translate the result of realtime_recording_thread using translation API"""
    assert gc.mw is not None
    gc.enableTranslating()

    try:
        global prev_tl_text, sentences_tl
        separator = literal_eval(quote(sj.cache["separate_with"]))
        tl_res = ""
        debug_log = sj.cache["debug_translate"]

        if engine == "Google":
            success, tl_res = google_tl(text, lang_source, lang_target, debug_log)
            if not success:
                nativeNotify("Error: translation with google failed", tl_res)

        elif engine == "LibreTranslate":
            success, tl_res = libre_tl(
                text,
                lang_source,
                lang_target,
                sj.cache["libre_https"],
                sj.cache["libre_host"],
                sj.cache["libre_port"],
                sj.cache["libre_api_key"],
                debug_log,
            )
            if not success:
                nativeNotify("Error: translation with libre failed", tl_res)

        elif engine == "MyMemoryTranslator":
            success, tl_res = memory_tl(text, lang_source, lang_target, debug_log)
            if not success:
                nativeNotify("Error: translation with mymemory failed", str(tl_res))

        tl_res = tl_res.strip()
        if len(tl_res) > 0:
            prev_tl_text = tl_res
            # Clear the textbox first, then insert the new text.
            gc.clear_mw_tl()
            gc.clear_ex_tl()
            to_ex_tb = ""

            # insert previous sentences if there are any
            for sentence in sentences_tl:
                gc.insert_result_mw(sentence, "tl")
                to_ex_tb += sentence + separator

            # insert the current sentence after previous sentences
            gc.insert_result_mw(tl_res, "tl")
            gc.insert_result_ex(to_ex_tb + tl_res, "tl")

    except Exception as e:
        logger.exception(e)
        nativeNotify("Error: translating failed", str(e))
    finally:
        gc.disableTranslating()  # flag processing as done


# -------------------------------------------------------------------------------------------------------------------------
# run in threaded environment with queue and exception to cancel
def cancellable_tl(
    query: str,
    lang_source: str,
    lang_target: str,
    model_name: str,
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"],
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
    model_name: str
        name of the whisper model
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"]
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
    gc.enableTranslating()
    gc.mw.start_loadBar()
    logger.debug("Translating...")

    try:
        separator = literal_eval(quote(sj.cache["separate_with"]))
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]
        save_name = save_name.replace("{task}", "translate")
        save_name = save_name.replace("{task-short}", "tl")

        if engine == "Whisper":
            try:
                # verify audio file exists
                if not path.isfile(query):
                    logger.warning("Audio file does not exist")
                    gc.disableTranslating()
                    return

                logger.debug("Translating with whisper")
                logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")
                model = whisper.load_model(model_name)

                def run_threaded():
                    result = whisper.transcribe(
                        model,
                        query,
                        task="translate",
                        language=lang_source if not auto else None,
                        **whisper_args,
                    )
                    gc.data_queue.put(result)

                thread = Thread(target=run_threaded, daemon=True)
                thread.start()

                while thread.is_alive():
                    if not gc.translating:
                        logger.debug("Cancelling translation")
                        raise Exception("Cancelled")
                    sleep(0.1)

                result_Tl_whisper = gc.data_queue.get()

            except Exception as e:
                gc.disableTranslating()  # flag processing as done if error
                gc.mw.stop_loadBar()
                if str(e) == "Cancelled":
                    logger.info("Translation cancelled")
                else:
                    logger.exception(e)
                    nativeNotify("Error: translating with whisper failed", str(e))
                return

            # if whisper, sended text (toTranslate) is the audio file path
            resultsTxt = result_Tl_whisper["text"].strip()

            if len(resultsTxt) > 0:
                gc.file_tled_counter += 1
                resultSrt = whisper_result_to_srt(result_Tl_whisper)

                with open(path.join(export_to, f"{save_name}.txt"), "w", encoding="utf-8") as f:
                    f.write(resultsTxt)

                with open(path.join(export_to, f"{save_name}.srt"), "w", encoding="utf-8") as f:
                    f.write(resultSrt)

                gc.insert_result_mw(f"translated {save_name} and saved to .txt and .srt" + separator, "tl")
            else:
                gc.insert_result_mw(f"Fail to save file {save_name}. It is empty (no text get from transcription)", "tl")
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
            proxies = get_proxies(sj.cache["proxy_http"], sj.cache["proxy_https"])

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

                result = txt_to_srt_whisper_format_stamps(result, timestamp)
                result_Tl.append(result)

            for i, results in enumerate(result_Tl):
                # sended text (toTranslate parameter) is sended in srt format
                # so the result that we got from translation is as srt
                resultSrt = results
                resultTxt = srt_whisper_to_txt_format(resultSrt)  # format it back to txt

                if len(resultSrt) > 0:
                    gc.file_tled_counter += 1
                    save_name_part = f"{save_name}_pt{i + 1}" if len(result_Tl) > 1 else save_name

                    with open(path.join(export_to, f"{save_name_part}.txt"), "w", encoding="utf-8") as f:
                        f.write(resultTxt)

                    with open(path.join(export_to, f"{save_name_part}.srt"), "w", encoding="utf-8") as f:
                        f.write(resultSrt)

                    gc.insert_result_mw(f"Translated {save_name_part} and saved to .txt and .srt", "tl")
                else:
                    gc.insert_result_mw(
                        f"Translated file {save_name} is empty (no text get from transcription) so it's not saved", "tl"
                    )
                    logger.warning("Translated Text is empty")

    except Exception as e:
        logger.exception(e)
        nativeNotify("Error: translating failed", str(e))
        return
    finally:
        gc.disableTranslating()  # flag processing as done. No need to check for transcription because it is done before this
        gc.mw.stop_loadBar()


def cancellable_tc(
    audio_name: str,
    lang_source: str,
    lang_target: str,
    modelName: str,
    auto: bool,
    transcribe: bool,
    translate: bool,
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"],
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
    modelName: str
        name of the model to use
    auto: bool
        if True, source language will be auto detected
    transcribe: bool
        if True, transcribe the audio
    translate: bool
        if True, translate the transcription
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"]
        engine to use for translation
    **whisper_args:
        whisper parameter

    Returns
    -------
    None
    """
    assert gc.mw is not None
    gc.enableTranscribing()
    gc.mw.start_loadBar()

    # Transcribe
    logger.info("-" * 50)
    logger.info(f"Transcribing Audio: {audio_name.split(sep)[-1]}")

    # verify audio file exists
    if not path.isfile(audio_name):
        logger.warning("Audio file does not exist")
        gc.disableTranslating()
        gc.mw.stop_loadBar()
        return

    try:
        result_Tc = ""
        save_name = save_name.replace("{task}", "transcribe")
        save_name = save_name.replace("{task-short}", "tc")

        logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")
        model: whisper.Whisper = whisper.load_model(modelName)

        def run_threaded():
            result = whisper.transcribe(
                model,
                audio_name,
                task="transcribe",
                language=lang_source if not auto else None,
                **whisper_args,
            )
            gc.data_queue.put(result)

        thread = Thread(target=run_threaded, daemon=True)
        thread.start()

        while thread.is_alive():
            if not gc.transcribing:
                logger.debug("Cancelling transcription")
                raise Exception("Cancelled")
            sleep(0.1)

        result_Tc = gc.data_queue.get()

        # export to file
        name_only = filename_only(audio_name)
        name_only = name_only[:100]  # limit length of file name to 100 characters
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]

        # export if transcribe mode is on
        if transcribe:
            logger.debug(result_Tc)

            resultTxt = result_Tc["text"].strip()

            if len(resultTxt) > 0:
                gc.file_tced_counter += 1
                resultSrt = whisper_result_to_srt(result_Tc)

                with open(path.join(export_to, f"{save_name}.txt"), "w", encoding="utf-8") as f:
                    f.write(resultTxt)

                with open(path.join(export_to, f"{save_name}.srt"), "w", encoding="utf-8") as f:
                    f.write(resultSrt)

                gc.insert_result_mw(f"Transcribed File {name_only} saved to {save_name} .txt and .srt", "tc")
            else:
                gc.insert_result_mw(
                    f"Transcribed File {name_only} is empty (no text get from transcription) so it's not saved", "tc"
                )
                logger.warning("Transcribed Text is empty")

        # start translation thread if translate mode is on
        if translate:
            # send result as srt if not using whisper because it will be send to translation API.
            # If using whisper translation will be done using whisper model
            toTranslate = whisper_result_to_srt(result_Tc) if engine != "Whisper" else audio_name
            translateThread = Thread(
                target=cancellable_tl,
                args=[
                    toTranslate,
                    lang_source,
                    lang_target,
                    modelName,
                    engine,
                    auto,
                    save_name,
                ],
                kwargs=whisper_args,
                daemon=True,
            )

            translateThread.start()  # Start translation in a new thread to prevent blocking

    except Exception as e:
        if str(e) == "Cancelled":
            logger.info("Transcribing cancelled")
        else:
            logger.exception(e)
            nativeNotify("Error: Transcribing Audio", str(e))
    finally:
        gc.disableTranscribing()
        gc.mw.stop_loadBar()


def file_input(
    files: List[str], modelKey: str, lang_source: str, lang_target: str, transcribe: bool, translate: bool, engine: str
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
    frame_lbl.pack(side="top", fill="x", padx=5, pady=5, expand=True)

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

        src_english = lang_source == "english"
        auto = lang_source == "auto detect"
        whisperEngine = engine == "Whisper"
        model_name = append_dot_en(modelKey, src_english)

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

            logger.debug("save_name: " + save_name)

            if translate and whisperEngine and not transcribe:  # if only translating and using the whisper engine
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
                        model_name,
                        auto,
                        transcribe,
                        translate,
                        engine,
                        save_name,
                    ],
                    kwargs=whisper_args,
                    daemon=True,
                )
            start = time()
            logger.debug(f"Starting process for {file}")
            proc_thread.start()
            proc_thread.join()  # wait for thread to finish until continue to next file
            logger.debug(f"Finished process for {file} in {round(time() - start, 2)}s")

        # destroy progress window
        if root.winfo_exists():
            root.after(1000, root.destroy)

        logger.info(f"End process (FILE) [Total time: {time() - startProc:.2f}s]")
        # open folder
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]
        if gc.file_tced_counter > 0 or gc.file_tled_counter > 0:
            if sj.cache["auto_open_dir_export"]:
                start_file(export_to)

            resultMsg = (
                f"Transcribed {gc.file_tced_counter} file(s) and Translated {gc.file_tled_counter} file(s)"
                if transcribe and translate else
                f"Transcribed {gc.file_tced_counter} file(s)" if transcribe else f"Translated {gc.file_tled_counter} file(s)"
            )
            mbox(f"File {taskname} Done", resultMsg, 0)

        # turn off loadbar
        gc.mw.stop_loadBar("file")
        gc.disableRecording()  # update flag
    except Exception as e:
        logger.error("Error occured while processing file(s)")
        logger.exception(e)
        assert gc.mw is not None
        mbox("Error occured while processing file(s)", f"{str(e)}", 2, gc.mw.root)
        gc.mw.from_file_stop(prompt=False, notify=False)

        if root.winfo_exists():
            root.after(1000, root.destroy)  # destroy progress window
