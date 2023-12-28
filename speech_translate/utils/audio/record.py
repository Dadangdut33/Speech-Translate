# pylint: disable=global-variable-undefined
import os
from ast import literal_eval
from datetime import datetime, timedelta
from io import BytesIO
from platform import system
from shlex import quote
from threading import Lock, Thread
from time import gmtime, sleep, strftime, time
from tkinter import IntVar, Toplevel, ttk
from typing import Optional
from wave import Wave_read, Wave_write
from wave import open as w_open

import numpy as np
import requests
import scipy.io.wavfile as wav
import stable_whisper
import torch
import torchaudio
import webrtcvad
from whisper.tokenizer import TO_LANGUAGE_CODE

from speech_translate._constants import MAX_THRESHOLD, MIN_THRESHOLD, WHISPER_SR
from speech_translate._logging import logger
from speech_translate._path import dir_debug, dir_silero_vad, dir_temp, p_app_icon
from speech_translate.linker import bc, sj
from speech_translate.ui.custom.audio import AudioMeter
from speech_translate.ui.custom.checkbutton import CustomCheckButton
from speech_translate.ui.custom.label import LabelTitleText
from speech_translate.ui.custom.message import mbox
from speech_translate.ui.custom.spinbox import SpinboxNumOnly
from speech_translate.ui.custom.tooltip import tk_tooltip
from speech_translate.utils.audio.device import (
    get_db,
    get_device_details,
    get_frame_duration,
    get_speech_webrtc,
    resample_sr,
    to_silero,
)
from speech_translate.utils.translate.language import get_whisper_lang_name, get_whisper_lang_similar

from ..helper import cbtn_invoker, generate_temp_filename, get_proxies, native_notify, str_separator_to_html, unique_rec_list
from ..translate.translator import translate
from ..whisper.helper import (
    get_hallucination_filter,
    get_model,
    get_model_args,
    get_tc_args,
    model_values,
    remove_segments_by_str,
    stablets_verbose_log,
)

if system() == "Windows":
    import pyaudiowpatch as pyaudio  # type: ignore # pylint: disable=import-error
else:
    import pyaudio  # type: ignore # pylint: disable=import-error

ERROR_CON_NOTIFIED = False
ERROR_CON_NOFIFIED_AMOUNT = 0


# -------------------------------------------------------------------------------------------------------------------------
def record_session(
    lang_source: str,
    lang_target: str,
    engine: str,
    model_name_tc: str,
    device: str,
    is_tc: bool,
    is_tl: bool,
    speaker: bool = False,
) -> None:
    """
    Function to record audio and translate it in real time / live. Speaker as input can only be used on Windows.
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
    is_tc: bool
        Whether to transcribe the audio
    is_tl: bool
        Whether to translate the audio
    speaker: bool, optional
        Device is speaker or not

    Returns
    ----
    None
    """
    rec_type = "speaker" if speaker else "mic"
    assert bc.mw is not None
    master = bc.mw.root
    root = None

    # ----------------- Get device -----------------
    try:
        global sr_ori, frame_duration_ms, threshold_enable, threshold_db, threshold_auto, use_silero, \
            silero_min_conf, vad_checked, num_of_channels, prev_tc_res, prev_tl_res, max_db, min_db, \
            is_silence, was_recording, t_silence, samp_width, webrtc_vad, silero_vad, use_temp, \
            disable_silerovad, disable_auto_threshold, silero_disabled, ERROR_CON_NOTIFIED, \
            ERROR_CON_NOFIFIED_AMOUNT

        ERROR_CON_NOTIFIED = False
        ERROR_CON_NOFIFIED_AMOUNT = 0
        p = pyaudio.PyAudio()
        success, detail = get_device_details(rec_type, sj, p)

        if not success:
            raise Exception("Failed to get device details")

        device_detail = detail["device_detail"]
        sr_ori = detail["sample_rate"]
        num_of_channels = detail["num_of_channels"]
        chunk_size = detail["chunk_size"]
        transcribe_rate = timedelta(seconds=sj.cache["transcribe_rate"] / 1000)
        max_buffer_s = int(sj.cache.get(f"max_buffer_{rec_type}", 10))
        max_sentences = int(sj.cache.get(f"max_sentences_{rec_type}", 5))
        sentence_limitless = sj.cache.get(f"{rec_type}_no_limit", False)
        tl_engine_whisper = engine in model_values

        taskname = "Transcribe & Translate" if is_tc and is_tl else "Transcribe" if is_tc else "Translate"
        more_information = f"\n> Language: {lang_source} → {lang_target}" if is_tl else f"\n> Language: {lang_source}"
        more_information += f"\n> {taskname} using {model_name_tc}"
        if is_tl and (model_name_tc != engine):
            more_information += f" → {engine}"

        # ask confirmation first if enabled
        # show the selected device and recording type
        bc.mw.stop_lb()
        if sj.cache["rec_ask_confirmation_first"]:
            if not mbox(
                "Record Confirmation",
                f"> Device: {device} ({'Speaker' if speaker else 'Mic'})" \
                f"\n> Sample Rate: {sr_ori} | Channels: {num_of_channels} | Chunk Size: {chunk_size}" \
                f"{more_information}\n\nContinue?",
                3,
                master,
            ):
                bc.mw.rec_stop()
                bc.mw.after_rec_stop()
                return

        # warn user if sample_rate is more than 48000
        if not sj.cache["supress_record_warning"]:
            if sr_ori > 48000 and not mbox(
                    "Warning",
                    f"Sample rate is more than 48000 Hz ({sr_ori} Hz). This might cause some issues (audio " \
                    "might not get picked up). If this happen you can try to change sample rate or change the " \
                    "conversion method. (You can turn off this warning in setting->general->suppress record warning)" \
                    "\n\nDo you want to continue?",
                    3,
                    master,
                ):
                bc.mw.rec_stop()
                bc.mw.after_rec_stop()
                return

            if is_tl and not tl_engine_whisper:
                # check connection first
                try:
                    logger.info("Checking for internet connection")
                    requests.get("https://www.google.com/", timeout=5)
                except Exception as e:
                    logger.exception(e)
                    if not mbox(
                        "Warning",
                        "Failed to check for internet connection. Translation might not work. " \
                        "(You can turn off this warning in setting->general->suppress record warning)" \
                        "\n\nDo you want to continue?",
                        3,
                        master,
                    ):
                        bc.mw.rec_stop()
                        bc.mw.after_rec_stop()
                        return

        bc.mw.start_lb()

        vad_checked = False
        frame_duration_ms = get_frame_duration(sr_ori, chunk_size)
        threshold_enable = sj.cache.get(f"threshold_enable_{rec_type}", True)
        threshold_db = sj.cache.get(f"threshold_db_{rec_type}", -20)
        threshold_auto = sj.cache.get(f"threshold_auto_{rec_type}", True)
        use_silero = sj.cache.get(f"threshold_auto_silero_{rec_type}", True)
        silero_disabled = False
        silero_min_conf = sj.cache.get(f"threshold_silero_{rec_type}_min", 0.75)
        auto_break_buffer = sj.cache.get(f"auto_break_buffer_{rec_type}", True)

        auto = lang_source.lower() == "auto detect"
        use_temp = sj.cache["use_temp"]
        language = f"{lang_source} → {lang_target}" if is_tl else lang_source

        # ----------------- Modal window -----------------
        root = Toplevel(master)
        root.title("Loading...")
        root.transient(master)
        root.geometry("450x275")
        root.protocol("WM_DELETE_WINDOW", lambda: master.state("iconic"))  # minimize window when click close button
        root.geometry(f"+{master.winfo_rootx() + 50}+{master.winfo_rooty() + 50}")
        root.maxsize(600, 325)
        root.minsize(400, 225)

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
        lbl_sample_rate.set_text(sr_ori)

        lbl_channels = LabelTitleText(frame_lbl_2, "Channels: ", "⌛")
        lbl_channels.pack(side="left", fill="x", padx=5, pady=5)
        lbl_channels.set_text(num_of_channels)

        lbl_chunk_size = LabelTitleText(frame_lbl_2, "Chunk Size: ", "⌛")
        lbl_chunk_size.pack(side="left", fill="x", padx=5, pady=5)
        lbl_chunk_size.set_text(chunk_size)

        # 3
        lbl_buffer = LabelTitleText(frame_lbl_3, "Buffer: ", "0/0 sec")
        lbl_buffer.pack(side="left", fill="x", padx=5, pady=5)
        lbl_buffer.set_text(f"0/{round(max_buffer_s, 2)} sec")

        lbl_sentences = LabelTitleText(frame_lbl_3, "Sentences: ", "0/0")
        lbl_sentences.pack(side="left", fill="x", padx=5, pady=5)

        # 4
        progress_buffer = ttk.Progressbar(frame_lbl_4, orient="horizontal", length=200, mode="determinate")
        progress_buffer.pack(side="left", fill="x", padx=5, pady=5, expand=True)

        # 5
        lbl_timer = ttk.Label(frame_lbl_5, text="REC: 00:00:00")
        lbl_timer.pack(side="left", fill="x", padx=5, pady=5)
        lbl_timer.configure(text=f"REC: 00:00:00 | {language}")

        lbl_status = ttk.Label(frame_lbl_5, text="⌛ Setting up session...")
        lbl_status.pack(side="right", fill="x", padx=5, pady=5)

        # 6
        cbtn_enable_threshold = CustomCheckButton(
            frame_lbl_6,
            threshold_enable,
            lambda x: set_treshold(x) or toggle_enable_threshold(),
            text="Enable Threshold",
            state="disabled"
        )
        cbtn_enable_threshold.pack(side="left", fill="x", padx=5, pady=5)

        cbtn_auto_threshold = CustomCheckButton(
            frame_lbl_6,
            threshold_auto,
            lambda x: set_threshold_auto(x) or toggle_auto_threshold(),
            text="Auto Threshold",
            state="disabled"
        )
        cbtn_auto_threshold.pack(side="left", fill="x", padx=5, pady=5)

        cbtn_break_buffer_on_silence = CustomCheckButton(
            frame_lbl_6,
            auto_break_buffer,
            lambda x: set_threshold_auto_break_buffer(x),  # pylint: disable=unnecessary-lambda
            text="Break buffer on silence",
            state="disabled"
        )
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

        vert_sep = ttk.Separator(frame_lbl_7, orient="vertical")
        vert_sep.pack(side="left", fill="y", padx=5, pady=5)

        cbtn_enable_silero = CustomCheckButton(
            frame_lbl_7,
            use_silero,
            lambda x: set_use_silero(x),  # pylint: disable=unnecessary-lambda
            text="Use Silero",
            state="disabled"
        )
        cbtn_enable_silero.pack(side="left", fill="x", padx=5, pady=5)
        tooltip_cbtn_silero = tk_tooltip(
            cbtn_enable_silero,
            "Use Silero VAD for more accurate VAD alongside WebRTC VAD"
            " (Silero will be automatically disabled if it failed on usage)",
        )

        spn_silero_min_conf = SpinboxNumOnly(
            root,
            frame_lbl_7,
            0.1,
            1.0,
            lambda x: set_silero_min_conf(float(x)),
            initial_value=sj.cache.get(f"threshold_silero_{rec_type}_min", 0.75),
            num_float=True,
            allow_empty=False,
            delay=10,
            increment=0.05,
        )
        spn_silero_min_conf.configure(state="disabled")
        spn_silero_min_conf.pack(side="left", fill="x", padx=5, pady=5)
        tk_tooltip(
            spn_silero_min_conf, "Set the minimum confidence for your input to be considered as speech when using Silero VAD"
        )

        lbl_threshold = ttk.Label(frame_lbl_7, text="Threshold")
        lbl_threshold.pack(side="left", fill="x", padx=5, pady=5)

        scale_threshold = ttk.Scale(frame_lbl_7, from_=-60.0, to=0.0, orient="horizontal", state="disabled")
        scale_threshold.pack(side="left", fill="x", padx=5, pady=5, expand=True)
        scale_threshold.set(sj.cache.get(f"threshold_db_{rec_type}", -20))

        lbl_threshold_db = ttk.Label(frame_lbl_7, text="0.0 dB")
        lbl_threshold_db.pack(side="left", fill="x", padx=5, pady=5)
        lbl_threshold_db.configure(text=f"{sj.cache.get(f'threshold_db_{rec_type}'):.2f} dB")

        # 8
        global audiometer
        lbl_mic = ttk.Label(frame_lbl_8, image=bc.mic_emoji if not speaker else bc.speaker_emoji)
        lbl_mic.pack(side="left", fill="x", padx=(5, 0), pady=0)

        audiometer = AudioMeter(frame_lbl_8, root, True, MIN_THRESHOLD, MAX_THRESHOLD, height=10)
        audiometer.pack(side="left", fill="x", padx=5, pady=0, expand=True)
        audiometer.set_disabled(not sj.cache["show_audio_visualizer_in_record"])
        audiometer.set_threshold(sj.cache.get(f"threshold_db_{rec_type}"))

        # btn
        btn_pause = ttk.Button(frame_btn, text="Pause", state="disabled")
        btn_pause.pack(side="left", fill="x", padx=5, expand=True)

        btn_stop = ttk.Button(frame_btn, text="Stop", style="Accent.TButton")
        btn_stop.pack(side="right", fill="x", padx=5, expand=True)
        try:
            root.iconbitmap(p_app_icon)
        except Exception:
            pass

        # ----------------- Vars that is load after window to show loading -----------------
        max_int16 = np.iinfo(np.int16).max  # bit depth of 16 bit audio (32768)
        separator = str_separator_to_html(literal_eval(quote(sj.cache["separate_with"])))
        webrtc_vad = webrtcvad.Vad(sj.cache.get(f"threshold_auto_mode_{rec_type}", 3))
        torchaudio.set_audio_backend("soundfile")
        silero_vad, _ = torch.hub.load(repo_or_dir=dir_silero_vad, source="local", model="silero_vad", onnx=True)
        silero_vad.reset_states()

        # cannot transcribe and translate concurrently. Will need to wait for the previous transcribe to finish
        if is_tc and is_tl and tl_engine_whisper:
            bc.tc_lock = Lock()
        else:
            bc.tc_lock = None

        # ---- load model -----
        model_args = get_model_args(sj.cache)
        _model_tc, _model_tl, stable_tc, stable_tl, to_args = get_model(
            is_tc, is_tl, tl_engine_whisper, model_name_tc, engine, sj.cache, **model_args
        )
        whisper_args = get_tc_args(to_args, sj.cache)
        whisper_args["verbose"] = None  # set to none so no printing of the progress to stdout
        whisper_lang = get_whisper_lang_similar(lang_source) if not auto else None
        whisper_args["language"] = TO_LANGUAGE_CODE[whisper_lang] if whisper_lang else None

        if sj.cache["use_faster_whisper"] and not use_temp:
            whisper_args["input_sr"] = WHISPER_SR  # when using numpy array as input, will need to set input_sr

        # ! if both demucs and vad is enabled, use file instead of numpy array to avoid error
        if whisper_args["demucs"] and whisper_args["vad"]:
            logger.info("Both demucs and vad is enabled. Force using file instead of numpy array")
            use_temp = True

        cuda_device = model_args["device"]

        # ---- load hallucination filter -----
        if sj.cache["filter_rec"]:
            hallucination_filters = get_hallucination_filter('rec', sj.cache["path_filter_rec"])
        else:
            hallucination_filters = {}

        bc.mw.stop_lb(rec_type)
        logger.info("-" * 50)
        logger.info(f"Taskname: {taskname}")
        logger.info(f"TC: {is_tc}")
        logger.info(f"TL: {is_tl}")
        logger.info(f"Model: {model_name_tc}")
        logger.info(f"Engine: {engine}")
        logger.info(f"CUDA: {cuda_device}")
        logger.info(f"Auto mode: {auto}")
        logger.info(f"Whisper Lang/Key: {whisper_lang}/{whisper_args['language']}")
        logger.info(f"Source Languange: {lang_source}")
        if is_tl:
            logger.info(f"Target Language: {lang_target}")
        logger.info(f"Model Args: {model_args}")
        logger.info(f"Process Args: {whisper_args}")

        # ----------------- Start modal -----------------
        # window to show progress
        root.title("Recording")

        t_start = time()
        paused = False
        duration_seconds = 0
        bc.current_rec_status = "💤 Idle"
        bc.auto_detected_lang = "~"

        def stop_recording():
            bc.recording = False  # only set flag to false because cleanup is handled directly down below
            btn_stop.configure(state="disabled", text="Stopping...")  # disable btn
            btn_pause.configure(state="disabled")

        def toggle_pause():
            nonlocal paused
            paused = not paused
            if paused:
                if bc.stream:
                    bc.stream.stop_stream()
                btn_pause.configure(text="Resume")
                root.title(f"Recording {rec_type} (Paused)")
                bc.current_rec_status = "⏸️ Paused"
                update_status_lbl()
                silero_vad.reset_states()
            else:
                if bc.stream:
                    bc.stream.start_stream()
                btn_pause.configure(text="Pause")
                root.title(f"Recording {rec_type}")

        def toggle_enable_threshold():
            val = cbtn_enable_threshold.instate(["selected"])
            sj.save_key(f"threshold_enable_{rec_type}", val)
            if val:
                cbtn_auto_threshold.configure(state="normal")
                cbtn_break_buffer_on_silence.configure(state="normal")
                frame_lbl_7.pack(side="top", fill="x")
                frame_lbl_8.pack(side="top", fill="x", expand=True)

                audiometer.start()
            else:
                cbtn_auto_threshold.configure(state="disabled")
                cbtn_break_buffer_on_silence.configure(state="disabled")
                frame_lbl_7.pack_forget()
                frame_lbl_8.pack_forget()

                audiometer.stop()
            toggle_auto_threshold()

        def toggle_auto_threshold():
            val = cbtn_auto_threshold.instate(["selected"])
            sj.save_key(f"threshold_auto_{rec_type}", val)
            if val:
                audiometer.set_auto(True)
                audiometer.configure(height=10)

                lbl_threshold.pack_forget()
                scale_threshold.pack_forget()
                lbl_threshold_db.pack_forget()

                lbl_sensitivity.pack(side="left", fill="x", padx=5, pady=5)
                radio_vad_1.pack(side="left", fill="x", padx=5, pady=5)
                radio_vad_2.pack(side="left", fill="x", padx=5, pady=5)
                radio_vad_3.pack(side="left", fill="x", padx=5, pady=5)
                cbtn_enable_silero.pack(side="left", fill="x", padx=5, pady=5)
                if use_silero:
                    spn_silero_min_conf.pack(side="left", fill="x", padx=5, pady=5)
            else:
                audiometer.set_auto(False)
                audiometer.configure(height=20)

                lbl_sensitivity.pack_forget()
                radio_vad_1.pack_forget()
                radio_vad_2.pack_forget()
                radio_vad_3.pack_forget()
                vert_sep.pack_forget()
                cbtn_enable_silero.pack_forget()
                spn_silero_min_conf.pack_forget()

                lbl_threshold.pack(side="left", fill="x", padx=5, pady=5)
                scale_threshold.pack(side="left", fill="x", padx=5, pady=5, expand=True)
                lbl_threshold_db.pack(side="left", fill="x", padx=5, pady=5)

        def slider_move(event):
            global threshold_db
            threshold_db = float(event)
            lbl_threshold_db.configure(text=f"{threshold_db:.2f} dB")
            audiometer.set_threshold(threshold_db)
            sj.save_key(f"threshold_db_{rec_type}", threshold_db)

        def set_treshold(state: bool):
            global threshold_enable
            threshold_enable = state

        def set_threshold_auto(state: bool):
            global threshold_auto
            threshold_auto = state

        def set_use_silero(state: bool):
            global use_silero
            use_silero = state
            logger.info(f"Silero VAD is {'enabled' if state else 'disabled'}")
            sj.save_key(f"threshold_auto_silero_{rec_type}", state)
            silero_vad.reset_states()
            if state:
                spn_silero_min_conf.pack(side="left", fill="x", padx=5, pady=5)
            else:
                spn_silero_min_conf.pack_forget()

        def set_silero_min_conf(state: float):
            global silero_min_conf
            sj.save_key(f"threshold_silero_{rec_type}_min", state)
            silero_min_conf = state

        def set_webrtc_level(mode: int):
            webrtc_vad.set_mode(mode)

        def set_threshold_auto_break_buffer(state: bool):
            nonlocal auto_break_buffer
            auto_break_buffer = state

        def disable_silerovad():
            """
            Disable silero when not possible to use it
            """
            global silero_disabled
            if cbtn_enable_silero.instate(["selected"]):
                cbtn_enable_silero.invoke()
            silero_disabled = True
            cbtn_enable_silero.configure(state="disabled")
            tooltip_cbtn_silero.text = "Silero VAD is unavailable on this current " \
                                    "device configuration (check log for details)"

        def disable_auto_threshold():  # pylint: disable=unused-variable
            """
            Disable auto threshold when not possible to use it
            """
            if cbtn_auto_threshold.instate(["selected"]):
                cbtn_auto_threshold.invoke()
            cbtn_auto_threshold.configure(state="disabled")
            tk_tooltip(
                cbtn_auto_threshold,
                "Auto threshold is unavailable on this current device configuration (check log for details)"
            )
            disable_silerovad()

        def update_status_lbl():
            lbl_status.configure(text=bc.current_rec_status)

        def update_modal_ui():
            nonlocal t_start, paused
            while bc.recording:
                if paused:
                    sleep(0.1)
                    continue
                try:
                    timer = strftime("%H:%M:%S", gmtime(time() - t_start))
                    data_queue_size = (bc.data_queue.qsize() * chunk_size) / 1024  # approx buffer size in kb
                    lbl_timer.configure(
                        text=f"REC: {timer} | "
                        f"{language.replace('auto detect', f'auto detect ({bc.auto_detected_lang})') if auto else language}"
                    )
                    lbl_buffer.set_text(
                        f"{round(duration_seconds, 2)}/{round(max_buffer_s, 2)} sec (~{round(data_queue_size, 2)} kb)"
                    )
                    sentence_text = f"{len(bc.tc_sentences) or len(bc.tl_sentences) or '0'}"
                    if not sentence_limitless:
                        sentence_text += f"/{max_sentences}"
                    lbl_sentences.set_text(sentence_text)

                    progress_buffer["value"] = duration_seconds / max_buffer_s * 100
                    update_status_lbl()
                    sleep(0.1)
                except Exception as e:
                    if "invalid command name" not in str(e):
                        logger.exception(e)
                        logger.warning("Failed to update modal ui | Ignore if already closed")
                        break

        cbtn_enable_threshold.configure(state="normal")
        cbtn_auto_threshold.configure(state="normal")
        cbtn_break_buffer_on_silence.configure(state="normal")
        cbtn_enable_silero.configure(state="normal")
        spn_silero_min_conf.configure(state="normal")
        btn_pause.configure(state="normal", command=toggle_pause)
        btn_stop.configure(state="normal", command=stop_recording)
        scale_threshold.configure(command=slider_move, state="normal")
        temp_map = {1: radio_vad_1, 2: radio_vad_2, 3: radio_vad_3}
        radio_vad_1.configure(command=lambda: set_webrtc_level(1), state="normal")
        radio_vad_2.configure(command=lambda: set_webrtc_level(2), state="normal")
        radio_vad_3.configure(command=lambda: set_webrtc_level(3), state="normal")
        cbtn_invoker(threshold_auto, temp_map[sj.cache.get(f"threshold_auto_level_{rec_type}", 3)])
        if not use_silero:
            spn_silero_min_conf.pack_forget()
        toggle_enable_threshold()
        update_ui_thread = Thread(target=update_modal_ui, daemon=True)
        update_ui_thread.start()

        # ----------------- Start recording -----------------
        lbl_status.configure(text="▶️ Recording")
        # recording session init
        bc.tc_sentences = []
        bc.tl_sentences = []
        temp_list = []
        prev_tc_res = ""
        prev_tl_res = ""
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
        bc.stream = p.open(
            format=pyaudio.paInt16,  # 16 bit audio
            channels=num_of_channels,
            rate=sr_ori,
            input=True,
            frames_per_buffer=chunk_size,
            input_device_index=int(device_detail["index"]),
            stream_callback=record_cb,
        )

        logger.debug("Recording session started")

        def break_buffer_store_update():
            """
            Break the buffer (last_sample). Resetting the buffer means that the buffer will be cleared and
            it will be stored in the currently transcribed or translated text.
            """
            nonlocal last_sample, duration_seconds
            last_sample = bytes()
            duration_seconds = 0

            # append if there is any text
            # remove text that is exactly the same because some dupe might accidentally happened
            # update only if there is any text
            if is_tc:
                if prev_tc_res:
                    bc.tc_sentences.append(prev_tc_res)
                bc.tc_sentences = unique_rec_list(bc.tc_sentences)
                if not sentence_limitless and len(bc.tc_sentences) > max_sentences:
                    bc.tc_sentences.pop(0)
                if len(bc.tc_sentences) > 0:
                    bc.update_tc(None, separator)
            if is_tl:
                if prev_tl_res:
                    bc.tl_sentences.append(prev_tl_res)
                bc.tl_sentences = unique_rec_list(bc.tl_sentences)
                if not sentence_limitless and len(bc.tl_sentences) > max_sentences:
                    bc.tl_sentences.pop(0)
                if len(bc.tl_sentences) > 0:
                    bc.update_tl(None, separator)

        # transcribing loop
        while bc.recording:
            if paused:
                sleep(0.1)
                continue

            if bc.data_queue.empty():
                # no audio is being recorded, Could be because threshold is not met or because device is paused
                # in case of speaker device, it will pause the stream  when the speaker is not playing anything
                if auto_break_buffer:
                    # if silence has been detected for more than 1 second, break the buffer (last_sample)
                    if is_silence and time() - t_silence > 1:
                        is_silence = False
                        break_buffer_store_update()
                        bc.current_rec_status = "💤 Idle (Buffer Cleared)"
                        if sj.cache["debug_realtime_record"]:
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
            while not bc.data_queue.empty():
                data = bc.data_queue.get()
                last_sample += data

            if sj.cache["debug_realtime_record"]:
                logger.info("Processing Audio")

            # need to make temp in memory to make sure the audio will be read properly
            wf = BytesIO()
            wav_writer: Wave_write = w_open(wf, "wb")
            wav_writer.setframerate(WHISPER_SR if not use_temp else sr_ori)
            wav_writer.setsampwidth(samp_width)
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
                audio_as_np_int16 = np.frombuffer(audio_bytes, dtype=np.int16).flatten()
                audio_as_np_float32 = audio_as_np_int16.astype(np.float32)
                if num_of_channels == 1:
                    audio_np = audio_as_np_float32 / max_int16  # normalized as Numpy array
                    if whisper_args["demucs"]:
                        audio_target = torch.from_numpy(audio_np).to(cuda_device)  # convert to torch tensor
                    else:
                        audio_target = audio_np
                else:
                    # Samples are interleaved, so for a stereo stream with left channel
                    # of [L0, L1, L2, ...] and right channel of [R0, R1, R2, ...]
                    # the output is ordered as [[L0, R0], [L1, R1], [L2, R2], ...
                    chunk_length = len(audio_as_np_float32) / num_of_channels
                    audio_reshaped = np.reshape(audio_as_np_float32, (int(chunk_length), num_of_channels))
                    audio_np = audio_reshaped[:, 0] / max_int16  # take left channel only
                    if whisper_args["demucs"]:
                        audio_target = torch.from_numpy(audio_np).to(cuda_device)  # convert to torch tensor
                    else:
                        audio_target = audio_np

                if sj.cache["debug_recorded_audio"]:
                    wav.write(generate_temp_filename(dir_debug), WHISPER_SR, audio_np)
            else:
                # add to the temp list to delete later
                audio_target = generate_temp_filename(dir_temp)
                temp_list.append(audio_target)

                # block until the file is written
                t_start_write = time()
                with open(audio_target, "wb") as f:
                    f.write(wf.getvalue())

                if sj.cache["debug_realtime_record"]:
                    logger.debug(f"File Write Time: {time() - t_start_write}")

            # if duration is < 0.4 seconds, skip. Wait until more context is available
            if duration_seconds < sj.cache.get(f"min_input_length_{rec_type}", 0.4):
                if sj.cache["debug_realtime_record"]:
                    logger.debug(f"Duration is {duration_seconds} seconds. Skipping")
                continue

            # If only translating and its using whisper engine
            if is_tl and tl_engine_whisper and not is_tc:
                if sj.cache["debug_realtime_record"]:
                    logger.info("Translating")
                bc.current_rec_status = "▶️ Recording ⟳ Translating Audio"
                bc.rec_tl_thread = Thread(
                    target=run_whisper_tl,
                    args=[audio_target, stable_tl, separator, False, hallucination_filters],
                    kwargs=whisper_args,
                    daemon=True
                )
                bc.rec_tl_thread.start()
            else:
                # will automatically check translate on or not depend on input
                # translate is called from here because other engine need to get transcribed text first if translating
                if sj.cache["debug_realtime_record"]:
                    logger.info("Transcribing")

                bc.current_rec_status = "▶️ Recording ⟳ Transcribing Audio"
                result: Optional[stable_whisper.WhisperResult] = None

                def run_tc():
                    nonlocal result
                    if bc.tc_lock is not None:
                        with bc.tc_lock:
                            result = stable_tc(  # type: ignore
                                audio_target, task="transcribe", **whisper_args
                            )
                    else:
                        result = stable_tc(  # type: ignore
                            audio_target, task="transcribe", **whisper_args
                        )

                # def run_tc
                bc.rec_tc_thread = Thread(target=run_tc, args=[], daemon=True)
                bc.rec_tc_thread.start()
                bc.rec_tc_thread.join()

                if result is None:
                    logger.warning("Transcribing failed, check log for details!")
                    continue

                if sj.cache["filter_rec"]:
                    try:
                        result = remove_segments_by_str(
                            result,
                            hallucination_filters[get_whisper_lang_name(result.language) \
                                                  if auto else whisper_lang],
                            sj.cache["filter_rec_case_sensitive"],
                            sj.cache["filter_rec_strip"],
                            sj.cache["filter_rec_ignore_punctuations"],
                            sj.cache["filter_rec_exact_match"],
                            sj.cache["filter_rec_similarity"],
                            sj.cache["debug_realtime_record"],
                        )
                    except Exception as e:
                        logger.exception(e)
                        logger.error("Error in filtering hallucination")

                text = result.text.strip()
                bc.auto_detected_lang = result.language or "~"

                if len(text) > 0:
                    if sj.cache["debug_realtime_record"]:
                        logger.debug("New text (Whisper)")
                        if sj.cache["verbose_record"]:
                            stablets_verbose_log(result)
                        else:
                            logger.debug(f"{text}")

                    prev_tc_res = result
                    bc.update_tc(result, separator)

                    if is_tl:
                        bc.current_rec_status = "▶️ Recording ⟳ Translating text"
                        if tl_engine_whisper:
                            bc.rec_tl_thread = Thread(
                                target=run_whisper_tl,
                                args=[audio_target, stable_tl, separator, True, hallucination_filters],
                                kwargs=whisper_args,
                                daemon=True
                            )
                        else:
                            bc.rec_tl_thread = Thread(
                                target=tl_api, args=[text, lang_source, lang_target, engine, separator], daemon=True
                            )

                        bc.rec_tl_thread.start()
                        bc.rec_tl_thread.join()

            if use_temp and not sj.cache["keep_temp"]:
                os.remove(audio_target)  # type: ignore
                temp_list.remove(audio_target)

            # break up the buffer If we've reached max recording time
            if duration_seconds > max_buffer_s:
                break_buffer_store_update()

            bc.current_rec_status = "▶️ Recording"  # reset status

        # ----------------- End recording -----------------
        logger.debug("Stopping Record Session")

        bc.current_rec_status = "⚠️ Stopping stream"
        update_status_lbl()
        logger.info("-" * 50)
        logger.info("Stopping stream")
        bc.stream.stop_stream()
        bc.stream.close()
        bc.stream = None
        bc.rec_tc_thread = None
        bc.rec_tl_thread = None

        bc.current_rec_status = "⚠️ Terminating pyaudio"
        update_status_lbl()
        logger.info("Terminating pyaudio")
        p.terminate()
        p = None

        # empty the queue
        bc.current_rec_status = "⚠️ Emptying queue"
        update_status_lbl()
        logger.info("Emptying queue")
        while not bc.data_queue.empty():
            bc.data_queue.get()

        if not sj.cache["keep_temp"]:
            bc.current_rec_status = "⚠️ Cleaning up audioFiles (if any)"
            update_status_lbl()
            logger.info("Cleaning up audioFiles (if any)")
            for audio in temp_list:
                try:
                    os.remove(audio)
                except Exception:
                    pass
            logger.info("Done!")

        bc.current_rec_status = "⏹️ Stopped"

        del _model_tc, _model_tl

        update_status_lbl()
        audiometer.stop()
        bc.mw.after_rec_stop()
        if root.winfo_exists():
            root.destroy()

        logger.info("Modal closed")
        logger.info("-" * 50)
    except Exception as e:
        logger.exception(e)
        logger.error("Error in record session")
        if "The system cannot find the file specified" in str(e) and not bc.has_ffmpeg:
            logger.error("FFmpeg not found in system path. Please install FFmpeg and add it to system path")
            e = Exception("FFmpeg not found in system path. Please install FFmpeg and add it to system path")

        assert bc.mw is not None
        mbox("Error in record session", f"{str(e)}", 2, bc.mw.root)
        bc.mw.rec_stop()
        bc.mw.after_rec_stop()
        if root and root.winfo_exists():
            root.destroy()  # close if not destroyed
    finally:
        torch.cuda.empty_cache()
        logger.info("Record session ended")


def record_cb(in_data, _frame_count, _time_info, _status):
    """
    Record Audio From stream buffer and save it to queue in global class
    Will also check for sample rate and threshold setting 
    """
    global frame_duration_ms, max_db, min_db, is_silence, t_silence, was_recording, vad_checked

    try:
        # Run resample and use resampled audio if not using temp file
        resampled = resample_sr(in_data, sr_ori, WHISPER_SR)
        if not use_temp:  # when use_temp will use the original audio
            in_data = resampled

        # run vad at least once to check if it is possible to use with current device config
        if not vad_checked:
            vad_checked = True
            logger.debug("Checking if webrtcvad is possible to use. You can ignore the error log if it fails!")
            get_speech_webrtc(resampled, WHISPER_SR, frame_duration_ms, webrtc_vad)
            logger.debug("Checking if silero is possible to use. You can ignore the error log if it fails!")
            silero_vad(to_silero(resampled, num_of_channels, samp_width), WHISPER_SR)

        if not threshold_enable:
            bc.data_queue.put(in_data)  # record regardless of db
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

            # using vad
            if threshold_auto:
                is_speech = get_speech_webrtc(resampled, WHISPER_SR, frame_duration_ms, webrtc_vad)
                if use_silero and is_speech and not silero_disabled:  # double check with silero if enabled
                    conf: torch.Tensor = silero_vad(to_silero(resampled, num_of_channels, samp_width), WHISPER_SR)
                    is_speech = conf.item() >= silero_min_conf

                audiometer.set_recording(is_speech)
            else:
                is_speech = db > threshold_db

            if is_speech:
                bc.data_queue.put(in_data)
                was_recording = True
            else:
                bc.current_rec_status = "💤 Idle"
                if was_recording:
                    was_recording = False
                    if not is_silence:  # mark as silence if not already marked
                        is_silence = True
                        t_silence = time()

        return (in_data, pyaudio.paContinue)
    except Exception as e:
        logger.exception(e)
        logger.error("Error in record_cb")
        if "Error while processing frame" in str(e):
            logger.error("WEBRTC Error!")
            if frame_duration_ms >= 20:
                logger.warning(
                    "Webrtc Fail to process frame, trying to lower frame duration." \
                    f"{frame_duration_ms} -> {frame_duration_ms - 10}"
                )
                frame_duration_ms -= 10
                vad_checked = False  # try again with new frame duration
            else:
                disable_auto_threshold()  # pylint: disable=undefined-variable
                logger.warning("Not possible to use Auto Threshold with the current device config! So it is now disabled")

        elif "Input audio chunk is too short" in str(e):
            logger.error("SileroVAD Error!")
            disable_silerovad()  # pylint: disable=undefined-variable
            logger.warning("Not possible to use Silero VAD with the current device config! So it is now disabled")

        return (in_data, pyaudio.paContinue)


def run_whisper_tl(audio, stable_tl, separator: str, with_lock, hallucination_filters, **whisper_args):
    """Run Translate"""
    assert bc.mw is not None
    global prev_tl_res
    if with_lock:
        with bc.tc_lock:  # type: ignore
            result: stable_whisper.WhisperResult = stable_tl(audio, task="translate", **whisper_args)
    else:
        result: stable_whisper.WhisperResult = stable_tl(audio, task="translate", **whisper_args)

    if sj.cache["filter_rec"]:
        try:
            result = remove_segments_by_str(
                result, hallucination_filters["english"], sj.cache["filter_rec_case_sensitive"],
                sj.cache["filter_rec_strip"], sj.cache["filter_rec_ignore_punctuations"], sj.cache["filter_rec_exact_match"],
                sj.cache["filter_rec_similarity"], sj.cache["debug_realtime_record"]
            )
        except Exception as e:
            logger.exception(e)
            logger.error("Error in filtering hallucination")

    text = result.text.strip()
    bc.auto_detected_lang = result.language or "~"

    if len(text) > 0:
        if sj.cache["debug_realtime_record"]:
            logger.debug("New translated text (Whisper)")
            if sj.cache["verbose_record"]:
                stablets_verbose_log(result)
            else:
                logger.debug(f"{text}")

        prev_tl_res = result
        bc.update_tl(result, separator)


def tl_api(text: str, lang_source: str, lang_target: str, engine: str, separator: str):
    """Translate the result of realtime_recording_thread using translation API"""
    assert bc.mw is not None
    global prev_tl_res

    try:
        debug_log = sj.cache["debug_translate"]
        proxies = get_proxies(sj.cache["http_proxy"], sj.cache["https_proxy"])
        q = [text]
        kwargs = {"live_input": True}
        if engine == "LibreTranslate":
            kwargs["libre_link"] = sj.cache["libre_link"]  # type: ignore
            kwargs["libre_api_key"] = sj.cache["libre_api_key"]  # type: ignore

        success, result = translate(engine, q, lang_source, lang_target, proxies, debug_log, **kwargs)
        if not success:
            raise Exception(result)

        result = result[0]
        if result is not None and len(result) > 0:
            prev_tl_res = result.strip()
            bc.update_tl(result.strip(), separator)
    except Exception as e:
        logger.exception(e)
        global ERROR_CON_NOTIFIED, ERROR_CON_NOFIFIED_AMOUNT
        if not ERROR_CON_NOTIFIED:
            native_notify(f"Error: translation with {engine} failed", str(e))
            ERROR_CON_NOFIFIED_AMOUNT += 1
            if ERROR_CON_NOFIFIED_AMOUNT > 3:  # after 3 times, stop notifying
                ERROR_CON_NOTIFIED = True
