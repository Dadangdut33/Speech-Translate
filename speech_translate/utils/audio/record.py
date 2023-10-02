import sys
from ast import literal_eval
from datetime import datetime, timedelta
from io import BytesIO
from os import remove
from platform import system
from shlex import quote
from threading import Lock, Thread
from time import gmtime, strftime, time, sleep
from tkinter import IntVar, Toplevel, ttk
from typing import Dict
from wave import Wave_read, Wave_write
from wave import open as w_open

import numpy as np
import scipy.io.wavfile as wav
import whisper_timestamped as whisper

from speech_translate.components.custom.audio import AudioMeter
if system() == "Windows":
    import pyaudiowpatch as pyaudio
else:
    import pyaudio  # type: ignore
from webrtcvad import Vad

from speech_translate._constants import MAX_THRESHOLD, MIN_THRESHOLD, WHISPER_SR
from speech_translate._path import app_icon, dir_debug, dir_temp
from speech_translate.components.custom.label import LabelTitleText
from speech_translate.components.custom.message import mbox
from speech_translate.custom_logging import logger
from speech_translate.globals import gc, sj
from speech_translate.utils.audio.device import get_db, get_device_details, get_frame_duration, get_speech, resample_sr

from ..helper import cbtn_invoker, generate_temp_filename, get_channel_int, nativeNotify
from ..whisper.helper import convert_str_options_to_dict, get_temperature, whisper_verbose_log, model_values
from ..translate.translator import google_tl, libre_tl, memory_tl


# -------------------------------------------------------------------------------------------------------------------------
class NullIO:
    def write(self, s):
        pass


# store original stdout
original_stdout = sys.stdout


def record_realtime(
    lang_source: str,
    lang_target: str,
    engine: str,
    model_name_tc: str,
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
    engine: str
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
        Device is speaker or not

    Returns
    ----
    None
    """
    assert gc.mw is not None
    master = gc.mw.root
    root = Toplevel(master)
    root.title("Loading...")
    root.transient(master)
    root.geometry("450x250")
    root.protocol("WM_DELETE_WINDOW", lambda: master.state("iconic"))  # minimize window when click close button
    root.geometry("+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))
    root.maxsize(600, 325)

    frame_lbl = ttk.Frame(root)
    frame_lbl.pack(side="top", fill="both", padx=5, pady=5, expand=True)

    frame_btn = ttk.Frame(root)
    frame_btn.pack(side="top", fill="x", padx=5, pady=(0, 5), expand=True)

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

    frame_lbl_7 = ttk.Frame(frame_lbl)
    frame_lbl_7.pack(side="top", fill="x")

    frame_lbl_8 = ttk.Frame(frame_lbl)
    frame_lbl_8.pack(side="top", fill="x", expand=True)

    # 1
    lbl_device = LabelTitleText(frame_lbl_1, "Device: ", device)
    lbl_device.pack(side="left", fill="x", padx=5, pady=5)

    # 2
    lbl_sample_rate = LabelTitleText(frame_lbl_2, "Sample Rate: ", "⌛")
    lbl_sample_rate.pack(side="left", fill="x", padx=5, pady=5)

    lbl_channels = LabelTitleText(frame_lbl_2, "Channels: ", "⌛")
    lbl_channels.pack(side="left", fill="x", padx=5, pady=5)

    lbl_chunk_size = LabelTitleText(frame_lbl_2, "Chunk Size: ", "⌛")
    lbl_chunk_size.pack(side="left", fill="x", padx=5, pady=5)

    # 3
    lbl_buffer = LabelTitleText(frame_lbl_3, "Buffer: ", "0/0 sec")
    lbl_buffer.pack(side="left", fill="x", padx=5, pady=5)

    # 4
    progress_buffer = ttk.Progressbar(frame_lbl_4, orient="horizontal", length=200, mode="determinate")
    progress_buffer.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    # 5
    lbl_timer = ttk.Label(frame_lbl_5, text="REC: 00:00:00")
    lbl_timer.pack(side="left", fill="x", padx=5, pady=5)

    lbl_status = ttk.Label(frame_lbl_5, text="⌛ Setting up session...")
    lbl_status.pack(side="right", fill="x", padx=5, pady=5)

    # 6
    cbtn_enable_threshold = ttk.Checkbutton(frame_lbl_6, text="Enable Threshold", state="disabled")
    cbtn_enable_threshold.pack(side="left", fill="x", padx=5, pady=5)

    cbtn_auto_threshold = ttk.Checkbutton(frame_lbl_6, text="Auto Threshold", state="disabled")
    cbtn_auto_threshold.pack(side="left", fill="x", padx=5, pady=5)

    cbtn_break_buffer_on_silence = ttk.Checkbutton(frame_lbl_6, text="Break buffer on silence", state="disabled")
    cbtn_break_buffer_on_silence.pack(side="left", fill="x", padx=5, pady=5)

    # 7
    lbl_sensitivity = ttk.Label(frame_lbl_7, text="Filter Noise")
    lbl_sensitivity.pack(side="left", fill="x", padx=5, pady=5)

    var_sensitivity = IntVar()
    radio_vad_1 = ttk.Radiobutton(frame_lbl_7, text="1", variable=var_sensitivity, value=1, state="disabled")
    radio_vad_1.pack(side="left", fill="x", padx=5, pady=5)
    radio_vad_2 = ttk.Radiobutton(frame_lbl_7, text="2", variable=var_sensitivity, value=2, state="disabled")
    radio_vad_2.pack(side="left", fill="x", padx=5, pady=5)
    radio_vad_3 = ttk.Radiobutton(frame_lbl_7, text="3", variable=var_sensitivity, value=3, state="disabled")
    radio_vad_3.pack(side="left", fill="x", padx=5, pady=5)

    lbl_threshold = ttk.Label(frame_lbl_7, text="Threshold")
    lbl_threshold.pack(side="left", fill="x", padx=5, pady=5)

    scale_threshold = ttk.Scale(frame_lbl_7, from_=-60.0, to=0.0, orient="horizontal", state="disabled")
    scale_threshold.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    lbl_threshold_db = ttk.Label(frame_lbl_7, text="0.0 dB")
    lbl_threshold_db.pack(side="left", fill="x", padx=5, pady=5)

    # 8
    global audiometer
    audiometer = AudioMeter(frame_lbl_8, root, True, MIN_THRESHOLD, MAX_THRESHOLD, height=10)
    audiometer.pack(side="left", fill="x", padx=5, pady=0, expand=True)

    # btn
    btn_pause = ttk.Button(frame_btn, text="Pause", state="disabled")
    btn_pause.pack(side="left", fill="x", padx=5, expand=True)

    btn_stop = ttk.Button(frame_btn, text="Stop", style="Accent.TButton", state="disabled")
    btn_stop.pack(side="right", fill="x", padx=5, expand=True)
    try:
        root.iconbitmap(app_icon)
    except Exception:
        pass

    modal_after = None
    try:
        global vad, use_temp
        auto = lang_source == "auto detect"
        tl_engine_whisper = engine in model_values
        rec_type = "speaker" if speaker else "mic"
        vad = Vad(sj.cache[f"threshold_auto_mode_{rec_type}"])

        logger.debug(tl_engine_whisper)

        # cannot transcribe and translate concurrently. Will need to wait for the previous transcribe to finish
        if translate and tl_engine_whisper:
            gc.tc_lock = Lock()

        if auto:
            # temporary disable print functon from the library | Logger is not affected
            sys.stdout = NullIO()

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
        task = "translate" if tl_engine_whisper and translate and not transcribe else "transcribe"

        # load model
        model_tc = whisper.load_model(model_name_tc)
        model_tl = whisper.load_model(engine) if tl_engine_whisper else None

        gc.mw.stop_loadBar(rec_type)
        # ----------------- Get device -----------------
        logger.info("-" * 50)
        logger.info(f"Task: {task}")
        logger.info(f"TC model: {model_name_tc}")
        logger.info(f"Engine: {engine}")
        logger.info(f"Auto mode: {auto}")
        logger.info(f"Source Languange: {lang_source}")
        if translate:
            logger.info(f"Target Language: {lang_target}")

        p = pyaudio.PyAudio()
        success, detail = get_device_details(rec_type, sj, p)

        if not success:
            raise Exception("Failed to get device details")

        global sr_ori, frame_duration_ms, threshold_enable, threshold_db, threshold_auto_mode
        device_detail = detail["device_detail"]
        sr_ori = detail["sample_rate"]
        num_of_channels = get_channel_int(detail["num_of_channels"])
        chunk_size = detail["chunk_size"]
        frame_duration_ms = get_frame_duration(chunk_size, sr_ori)
        threshold_enable = sj.cache[f"threshold_enable_{rec_type}"]
        threshold_db = sj.cache[f"threshold_db_{rec_type}"]
        threshold_auto_mode = sj.cache[f"threshold_auto_mode_{rec_type}"]
        auto_break_buffer = sj.cache[f"auto_break_buffer_{rec_type}"]

        # ----------------- Start modal -----------------
        # window to show progress
        root.title("Recording")

        timerStart = time()
        paused = False
        duration_seconds = 0
        modal_update_rate = 100
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

        def toggle_enable_threshold():
            if "selected" in cbtn_enable_threshold.state():
                cbtn_auto_threshold.configure(state="normal")
                cbtn_break_buffer_on_silence.configure(state="normal")
                frame_lbl_7.pack(side="top", fill="x")
                frame_lbl_8.pack(side="top", fill="x", expand=True)

                toggle_auto_threshold()
                audiometer.start()
            else:
                cbtn_auto_threshold.configure(state="disabled")
                cbtn_break_buffer_on_silence.configure(state="disabled")
                frame_lbl_7.pack_forget()
                frame_lbl_8.pack_forget()

                toggle_auto_threshold()
                audiometer.stop()

        def toggle_auto_threshold():
            if "selected" in cbtn_auto_threshold.state():
                audiometer.set_auto(True)
                audiometer.configure(height=10)

                lbl_threshold.pack_forget()
                scale_threshold.pack_forget()
                lbl_threshold_db.pack_forget()

                lbl_sensitivity.pack(side="left", fill="x", padx=5, pady=5)
                radio_vad_1.pack(side="left", fill="x", padx=5, pady=5)
                radio_vad_2.pack(side="left", fill="x", padx=5, pady=5)
                radio_vad_3.pack(side="left", fill="x", padx=5, pady=5)
            else:
                audiometer.set_auto(False)
                audiometer.configure(height=20)

                lbl_sensitivity.pack_forget()
                radio_vad_1.pack_forget()
                radio_vad_2.pack_forget()
                radio_vad_3.pack_forget()

                lbl_threshold.pack(side="left", fill="x", padx=5, pady=5)
                scale_threshold.pack(side="left", fill="x", padx=5, pady=5, expand=True)
                lbl_threshold_db.pack(side="left", fill="x", padx=5, pady=5)

        def slider_move(event):
            global threshold_db
            lbl_threshold_db.configure(text=f"{float(event):.2f} dB")
            audiometer.set_threshold(float(event))
            threshold_db = float(event)

        def set_auto_mode(mode):
            global threshold_auto_mode
            threshold_auto_mode = mode
            vad.set_mode(mode)

        def set_treshold_state(state):
            global threshold_enable
            threshold_enable = state

        def set_threshold_auto(state):
            global threshold_auto_mode
            threshold_auto_mode = state

        def set_threshold_auto_break_buffer(state):
            global auto_break_buffer
            auto_break_buffer = state

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

        lbl_sample_rate.set_text(sr_ori)
        lbl_channels.set_text(num_of_channels)
        lbl_chunk_size.set_text(chunk_size)
        lbl_buffer.set_text(f"0/{round(max_record_time, 2)} sec")
        lbl_timer.configure(text=f"REC: 00:00:00 | {language}")
        lbl_status.configure(text="▶️ Recording")

        cbtn_enable_threshold.configure(state="normal")
        cbtn_auto_threshold.configure(state="normal")
        cbtn_break_buffer_on_silence.configure(state="normal")
        scale_threshold.set(sj.cache[f"threshold_db_{rec_type}"])
        scale_threshold.configure(command=slider_move, state="normal")
        lbl_threshold_db.configure(text=f"{sj.cache[f'threshold_db_{rec_type}']:.2f} dB")
        temp_map = {1: radio_vad_1, 2: radio_vad_2, 3: radio_vad_3}
        radio_vad_1.configure(command=lambda: set_auto_mode(1), state="normal")
        radio_vad_2.configure(command=lambda: set_auto_mode(2), state="normal")
        radio_vad_3.configure(command=lambda: set_auto_mode(3), state="normal")
        cbtn_invoker(sj.cache[f"threshold_enable_{rec_type}"], cbtn_enable_threshold)
        cbtn_invoker(sj.cache[f"threshold_auto_{rec_type}"], cbtn_auto_threshold)
        cbtn_invoker(sj.cache[f"auto_break_buffer_{rec_type}"], cbtn_break_buffer_on_silence)
        cbtn_invoker(sj.cache[f"threshold_auto_mode_{rec_type}"], temp_map[sj.cache[f"threshold_auto_mode_{rec_type}"]])
        cbtn_enable_threshold.configure(
            command=lambda: set_treshold_state(cbtn_enable_threshold.instate(["selected"])) or toggle_enable_threshold()
        )
        cbtn_auto_threshold.configure(
            command=lambda: set_threshold_auto(cbtn_auto_threshold.instate(["selected"])) or toggle_auto_threshold()
        )
        cbtn_break_buffer_on_silence.configure(
            command=lambda: set_threshold_auto_break_buffer(cbtn_break_buffer_on_silence.instate(["selected"]))
        )
        btn_pause.configure(state="normal", command=toggle_pause)
        btn_stop.configure(state="normal", command=stop_recording)
        audiometer.set_threshold(sj.cache[f"threshold_db_{rec_type}"])
        toggle_enable_threshold()
        update_modal_ui()

        # ----------------- Start recording -----------------
        # recording session init
        global prev_tc_text, prev_tl_text, sentences_tc, sentences_tl, max_db, min_db, is_silence, was_recording, t_silence
        temp_list = []
        sentences_tc = []
        sentences_tl = []
        prev_tc_text = ""
        prev_tl_text = ""
        next_transcribe_time = None
        last_sample = bytes()
        samp_width = p.get_sample_size(pyaudio.paInt16)
        sr_divider = WHISPER_SR if not use_temp else sr_ori

        # threshold
        is_silence = False
        was_recording = False
        t_silence = time()
        max_db = MAX_THRESHOLD
        min_db = MIN_THRESHOLD
        gc.stream = p.open(
            format=pyaudio.paInt16,  # 16 bit audio
            channels=num_of_channels,
            rate=sr_ori,
            input=True,
            frames_per_buffer=chunk_size,
            input_device_index=int(device_detail["index"]),
            stream_callback=record_callback,
        )

        logger.debug("Record Session Started")

        def break_buffer():
            global sentences_tc, sentences_tl, prev_tc_text, prev_tl_text
            nonlocal last_sample, duration_seconds
            last_sample = bytes()
            duration_seconds = 0

            # append and remove text that is exactly the same same
            # Some dupe might accidentally happened so we need to remove it
            if transcribe:
                sentences_tc.append(prev_tc_text)
                sentences_tc = list(dict.fromkeys(sentences_tc))
                if len(sentences_tc) >= max_sentences:
                    sentences_tc.pop(0)

            if translate:
                sentences_tl.append(prev_tl_text)
                sentences_tl = list(dict.fromkeys(sentences_tl))
                if len(sentences_tl) >= max_sentences:
                    sentences_tl.pop(0)

        # transcribing loop
        while gc.recording:
            if paused:
                sleep(0.1)
                continue

            if gc.data_queue.empty():
                # no audio is being recorded, Could be because threshold is not met or because device is paused
                # in case of speaker device, it will pause the stream  when the speaker is not playing anything
                if auto_break_buffer:
                    # if silence has been detected for more than 1 second, break the buffer (last_sample)
                    if is_silence and time() - t_silence > 1:
                        is_silence = False
                        break_buffer()
                        gc.current_rec_status = "💤 Idle (Buffer Cleared)"
                        if sj.cache["debug_realtime_record"] == 1:
                            logger.debug("Silence found for more than 1 second. Buffer reseted")
                continue

            # update now if there is audio being recorded
            now = datetime.utcnow()

            # Set next_transcribe_time for the first time.
            if not next_transcribe_time:  # run only once
                next_transcribe_time = now + transcribe_rate

            # Run transcription based on transcribe rate that is set by user.
            # The more delay it have the more it will reduces stress on the GPU / CPU (if using cpu).
            if next_transcribe_time > now:
                continue

            # update next_transcribe_time
            next_transcribe_time = now + transcribe_rate

            # Getting the stream data from the queue while also clearing the queue.
            while not gc.data_queue.empty():
                data = gc.data_queue.get()
                last_sample += data

            if sj.cache["debug_realtime_record"] == 1:
                logger.info("Processing Audio")

            # need to make temp in memory to make sure the audio will be read properly
            wf = BytesIO()
            wav_writer: Wave_write = w_open(wf, "wb")
            wav_writer.setframerate(WHISPER_SR if not use_temp else sr_ori)
            wav_writer.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wav_writer.setnchannels(num_of_channels)
            wav_writer.writeframes(last_sample)
            wav_writer.close()
            wf.seek(0)

            duration_seconds = len(last_sample) / (samp_width * sr_divider)
            if not use_temp:
                # Read the audio data
                wav_reader: Wave_read = w_open(wf)
                samples = wav_reader.getnframes()
                audio_bytes = wav_reader.readframes(samples)
                wav_reader.close()

                # Convert the wave data straight to a numpy array for the model.
                if num_of_channels == 1:
                    audio_as_np_int16 = np.frombuffer(audio_bytes, dtype=np.int16).flatten()
                    audio_as_np_float32 = audio_as_np_int16.astype(np.float32)
                    audio_target = audio_as_np_float32 / max_int16  # normalized as Numpy array
                else:
                    # Samples are interleaved, so for a stereo stream with left channel
                    # of [L0, L1, L2, ...] and right channel of [R0, R1, R2, ...]
                    # the output is ordered as [[L0, R0], [L1, R1], [L2, R2], ...
                    audio_as_np_int16 = np.frombuffer(audio_bytes, dtype=np.int16).flatten()
                    audio_as_np_float32 = audio_as_np_int16.astype(np.float32)

                    chunk_length = len(audio_as_np_float32) / num_of_channels
                    assert chunk_length == int(chunk_length)
                    audio_reshaped = np.reshape(audio_as_np_float32, (int(chunk_length), num_of_channels))
                    audio_target = audio_reshaped[:, 0] / max_int16  # take left channel only

                if sj.cache["debug_recorded_audio"] == 1:
                    wav.write(generate_temp_filename(dir_debug), WHISPER_SR, audio_target)
            else:
                # add to the temp list to delete later
                audio_target = generate_temp_filename(dir_temp)
                temp_list.append(audio_target)

                # block until the file is written
                timeNow = time()
                with open(audio_target, "wb") as f:
                    f.write(wf.getvalue())

                if sj.cache["debug_realtime_record"] == 1:
                    logger.debug(f"File Write Time: {time() - timeNow}")

                # delete the oldest file if the temp list is too long
                if len(temp_list) > sj.cache["max_temp"] and not sj.cache["keep_temp"]:
                    remove(temp_list[0])
                    temp_list.pop(0)

            if sj.cache["debug_realtime_record"] == 1:
                logger.info("Transcribing")

            # Transcribe the audio
            gc.current_rec_status = "▶️ Recording ⟳ Transcribing"
            if translate and tl_engine_whisper:
                assert gc.tc_lock is not None
                gc.tc_lock.acquire()

            result = whisper.transcribe(
                model_tc, audio_target, language=lang_source if not auto else None, task=task, **whisper_args
            )

            if translate and tl_engine_whisper:
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
                    if tl_engine_whisper:
                        tl_thread = Thread(
                            target=whisper_realtime_tl,
                            args=[audio_target, lang_source, auto, model_tl],
                            kwargs=whisper_args,
                            daemon=True
                        )
                    # Using translation API
                    else:
                        tl_thread = Thread(target=realtime_tl, args=[text, lang_source, lang_target, engine], daemon=True)

                    tl_thread.start()

            # break up the buffer If we've reached max recording time
            if duration_seconds > max_record_time:
                break_buffer()

            gc.current_rec_status = "▶️ Recording"  # reset status
        else:
            logger.debug("Record Session ended")

            if auto:
                # re-enable print
                sys.stdout = original_stdout

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
                for audio in temp_list:
                    try:
                        remove(audio)
                    except FileNotFoundError:
                        pass
                logger.info("Done!")

            gc.current_rec_status = "⏹️ Stopped"
            update_status_lbl()
            audiometer.stop()
            gc.mw.after_rec_stop()
            if modal_after:
                root.after_cancel(modal_after)
            if root.winfo_exists():
                root.destroy()

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
    """
    Record Audio From stream buffer and save it to queue in global class
    Will also check for sample rate and threshold setting 
    """
    global max_db, min_db, vad, sr_ori, audiometer, frame_duration_ms
    global use_temp, is_silence, t_silence, was_recording, threshold_enable, threshold_db, threshold_auto_mode

    # Run resample and use resampled audio if not using temp file
    resampled = resample_sr(in_data, sr_ori, WHISPER_SR)
    if not use_temp:
        in_data = resampled

    if not threshold_enable:
        gc.data_queue.put(in_data)  # record regardless of db
    else:
        # only record if db is above threshold
        db = get_db(in_data)
        audiometer.set_db(db)

        if db > max_db:
            max_db = db
            audiometer.set_max(db)
        elif db < min_db:
            min_db = db
            audiometer.set_min(db)

        if threshold_auto_mode:
            is_speech = get_speech(resampled, WHISPER_SR, frame_duration_ms, vad, get_only_first_frame=True)
            audiometer.set_recording(is_speech)

            if is_speech:
                gc.data_queue.put(in_data)
                was_recording = True
            else:
                gc.current_rec_status = "💤 Idle"
                # toggle only once
                if was_recording:
                    was_recording = False
                    if not is_silence:
                        is_silence = True
                        t_silence = time()
        else:
            if db > threshold_db:
                gc.data_queue.put(in_data)
                was_recording = True
            else:
                gc.current_rec_status = "💤 Idle"
                # toggle only once
                if was_recording:
                    was_recording = False
                    if not is_silence:
                        is_silence = True
                        t_silence = time()

    return (in_data, pyaudio.paContinue)


def whisper_realtime_tl(
    audio,
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
            model, audio, language=lang_source if not auto else None, task="translate", **whisper_args
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


def realtime_tl(text: str, lang_source: str, lang_target: str, engine: str):
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
