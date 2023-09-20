from ast import literal_eval
from datetime import datetime, timedelta
from io import BytesIO
from os import remove
from platform import system
from shlex import quote
from threading import Lock, Thread
from time import gmtime, sleep, strftime, time
from tkinter import Toplevel, ttk
from typing import Dict, Literal
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
from speech_translate.globals import gc, sj
from speech_translate.utils.audio.device import auto_threshold, get_db, get_device_details

from ..helper import generate_temp_filename, nativeNotify
from ..whisper.helper import (append_dot_en, convert_str_options_to_dict, get_temperature, whisper_verbose_log)
from ..translate.translator import google_tl, libre_tl, memory_tl


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
                        last_sample += data  # type: ignore

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
    gc.enable_tl()

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
        gc.disable_tl()  # flag processing as done


def realtime_tl(
    text: str, lang_source: str, lang_target: str, engine: Literal["Google", "LibreTranslate", "MyMemoryTranslator"]
):
    """Translate the result of realtime_recording_thread using translation API"""
    assert gc.mw is not None
    gc.enable_tl()

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
        gc.disable_tl()  # flag processing as done
