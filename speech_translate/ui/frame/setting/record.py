from platform import system
from threading import Thread
from time import sleep
from tkinter import Frame, IntVar, LabelFrame, StringVar, Toplevel, ttk
from typing import Literal, Union

import webrtcvad
from loguru import logger

from speech_translate._constants import MAX_THRESHOLD, MIN_THRESHOLD, WHISPER_SR
from speech_translate._path import dir_silero_vad
from speech_translate.linker import bc, sj
from speech_translate.ui.custom.audio import AudioMeter
from speech_translate.ui.custom.checkbutton import CustomCheckButton
from speech_translate.ui.custom.combobox import ComboboxTypeOnCustom
from speech_translate.ui.custom.spinbox import SpinboxNumOnly
from speech_translate.ui.custom.tooltip import tk_tooltip, tk_tooltips
from speech_translate.utils.audio.audio import get_db, get_frame_duration, get_speech_webrtc, resample_sr, to_silero
from speech_translate.utils.audio.device import get_device_details
from speech_translate.utils.helper import cbtn_invoker, windows_os_only

if system() == "Windows":
    import pyaudiowpatch as pyaudio  # type: ignore # pylint: disable=import-error
else:
    import pyaudio  # type: ignore # pylint: disable=import-error


class RecordingOptionsDevice:
    """
    Base class for recording options for device.
    """
    def __init__(
        self, root: Toplevel, master_frame: Union[ttk.Frame, Frame], device: Literal["speaker", "mic"],
        cb_sr: ComboboxTypeOnCustom, cb_channels: ComboboxTypeOnCustom
    ):
        import torch  # pylint: disable=import-outside-toplevel
        self.on_start = True
        self.root = root
        self.master = master_frame
        self.device: Literal["speaker", "mic"] = device
        self.long_device = "Microphone" if device == "mic" else "Speaker"
        self.cb_sr = cb_sr
        self.cb_channels = cb_channels
        self.vad_checked = False

        self.max_threshold = MAX_THRESHOLD
        self.min_threshold = MIN_THRESHOLD
        self.p = None
        self.device_detail = {}
        self.stream = None
        self.auto_threshold_disabled = False
        self.silero_disabled = False
        self.webrtcvad = webrtcvad.Vad()
        self.silerovad = None
        self.frame_duration = 10

        def load_silero_in_thread():
            self.silerovad, _ = torch.hub.load(repo_or_dir=dir_silero_vad, source="local", model="silero_vad", onnx=True)

        Thread(target=load_silero_in_thread, daemon=True).start()

        self.lf_device = ttk.LabelFrame(self.master, text=self.long_device)
        self.lf_device.pack(side="top", padx=5, fill="both", expand=True)

        self.f_device_1 = ttk.Frame(self.lf_device)
        self.f_device_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_device_2 = ttk.Frame(self.lf_device)
        self.f_device_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_device_3 = ttk.Frame(self.lf_device)
        self.f_device_3.pack(side="top", fill="x", pady=5, padx=5)

        self.f_device_4 = ttk.Frame(self.lf_device)
        self.f_device_4.pack(side="top", fill="x", pady=5, padx=5)

        self.f_device_5 = ttk.Frame(self.lf_device)
        self.f_device_5.pack(side="top", fill="x", pady=5, padx=5)

        self.f_device_6 = ttk.Frame(self.lf_device)
        self.f_device_6.pack(side="top", fill="x", pady=5, padx=5)

        # 1
        self.lbl_min_input = ttk.Label(self.f_device_1, text="Min Buffer (s)", width=14)
        self.lbl_min_input.pack(side="left", padx=5)
        self.spn_min_input = SpinboxNumOnly(
            self.root,
            self.f_device_1,
            0.1,
            10,
            lambda x: sj.save_key(f"min_input_length_{device}", float(x)),
            initial_value=sj.cache.get(f"min_input_length_{device}", 0.4),
            num_float=True,
            allow_empty=False,
            delay=10,
            width=10
        )
        self.spn_min_input.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_min_input, self.spn_min_input],
            f"Set the minimum buffer input length (in seconds) for the {self.long_device} " \
            "input to be considered as a valid input." \
            "\n\nThis means that the input must be at least x seconds long before being passed " \
            "to Whisper to get the result.\n\nDefault value is 0.4 seconds.",
        )

        # 1
        self.lbl_buffer = ttk.Label(self.f_device_1, text="Max buffer (s)", width=14)
        self.lbl_buffer.pack(side="left", padx=5)
        self.spn_buffer = SpinboxNumOnly(
            self.root,
            self.f_device_1,
            1,
            30,
            lambda x: sj.save_key(f"max_buffer_{device}", int(x)),
            initial_value=sj.cache.get(f"max_buffer_{device}", 10),
            width=10,
        )
        self.spn_buffer.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_buffer, self.spn_buffer],
            f"Set the max buffer (in seconds) for {self.long_device} input.\n\nThe longer the buffer, the more time "
            "it will take to transcribe the audio. Not recommended to have very long buffer on low end PC."
            "\n\nDefault value is 10 seconds.",
        )

        self.lbl_max_sentences = ttk.Label(self.f_device_2, text="Max Sentences", width=14)
        self.lbl_max_sentences.pack(side="left", padx=5)
        self.spn_max_sentences = SpinboxNumOnly(
            self.root,
            self.f_device_2,
            1,
            100,
            lambda x: sj.save_key(f"max_sentences_{device}", int(x)),
            initial_value=sj.cache.get(f"max_sentences_{device}", 5),
            width=10,
        )
        self.spn_max_sentences.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_max_sentences, self.spn_max_sentences],
            "Set max number of sentences to be saved in memory during the recording session,\n\n" \
            "one sentence equals to the length of the max buffer. "
            "So if max buffer is 10 seconds, the words that are in those 10 seconds is the sentence."
            "\n\nDefault value is 5.",
        )

        def toggle_no_limit(x, save=True):
            if save:
                sj.save_key(f"{device}_no_limit", x)
            if x:
                self.spn_max_sentences.configure(state="disabled")
            else:
                self.spn_max_sentences.configure(state="normal")

        self.cbtn_no_limit = CustomCheckButton(
            self.f_device_2,
            sj.cache.get(f"{device}_no_limit", False),
            toggle_no_limit,
            text="Set no limit to sentences",
            style="Switch.TCheckbutton"
        )
        self.cbtn_no_limit.pack(side="left", padx=5)
        toggle_no_limit(self.cbtn_no_limit.instate(["selected"]), save=False)
        tk_tooltip(
            self.cbtn_no_limit,
            "If checked, the number of sentences to be saved during the recording session will be limitless." \
            "\n\nYou can enable this if you want to have no limit to the transcribed text."
            "\n\nDefault is unchecked",
        )

        # 3
        self.hori_sep = ttk.Separator(self.f_device_3, orient="horizontal")
        self.hori_sep.pack(side="top", fill="x", pady=5, padx=5)

        # 4
        self.cbtn_threshold_enable = CustomCheckButton(
            self.f_device_4,
            sj.cache.get(f"threshold_enable_{device}", True),
            lambda x: sj.save_key(f"threshold_enable_{device}", x) or self.toggle_enable_threshold(),
            text="Enable threshold",
            style="Switch.TCheckbutton"
        )
        self.cbtn_threshold_enable.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_threshold_enable,
            "If checked, input will need to reach the threshold before it is considered as an input." \
            "\n\nDefault is checked",
        )

        self.cbtn_threshold_auto = CustomCheckButton(
            self.f_device_4,
            sj.cache.get(f"threshold_auto_{device}", True),
            lambda x: sj.save_key(f"threshold_auto_{device}", x) or self.toggle_auto_threshold(),
            text="Auto",
            style="Switch.TCheckbutton"
        )
        self.cbtn_threshold_auto.pack(side="left", padx=5)
        self.tooltip_cbtn_threshold_auto = tk_tooltip(
            self.cbtn_threshold_auto,
            f"Wether to use VAD or manual threshold for the {self.long_device} input.\n\nDefault is checked"
        )

        self.cbtn_auto_break_buffer = CustomCheckButton(
            self.f_device_4,
            sj.cache.get(f"auto_break_buffer_{device}", True),
            lambda x: sj.save_key(f"auto_break_buffer_{device}", x),
            text="Break buffer on silence",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_break_buffer.pack(side="left", padx=5)
        self.tooltip_cbtn_auto_break_buffer = tk_tooltip(
            self.cbtn_auto_break_buffer,
            "If checked, the buffer will be stopped and considered as 1 full sentence when there" \
            "is silence detected for more than 1 second. This could help in reducing the background noise." \
            "\n\nDefault is checked",
        )

        # 5
        # vad for auto
        self.lbl_sensitivity = ttk.Label(self.f_device_5, text="Filter Noise", width=10)
        self.lbl_sensitivity.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_sensitivity,
            "Set the sensitivity level for the voice activity detection (VAD). 0 is the least aggressive in filtering out" \
            " non-speech while 3 is the most aggressive.\n\nDefault value is 3.",
        )

        self.var_sensitivity = IntVar()
        self.radio_webrtc_sens_1 = ttk.Radiobutton(self.f_device_5, text="1", value=1, variable=self.var_sensitivity)
        self.radio_webrtc_sens_1.pack(side="left", padx=5)
        self.radio_webrtc_sens_2 = ttk.Radiobutton(self.f_device_5, text="2", value=2, variable=self.var_sensitivity)
        self.radio_webrtc_sens_2.pack(side="left", padx=5)
        self.radio_webrtc_sens_3 = ttk.Radiobutton(self.f_device_5, text="3", value=3, variable=self.var_sensitivity)
        self.radio_webrtc_sens_3.pack(side="left", padx=5)

        temp_map = {1: self.radio_webrtc_sens_1, 2: self.radio_webrtc_sens_2, 3: self.radio_webrtc_sens_3}
        self.var_sensitivity.set(sj.cache.get(f"threshold_auto_level_{device}", 3))
        cbtn_invoker(sj.cache.get(f"threshold_auto_{device}", True), temp_map[self.var_sensitivity.get()])
        self.radio_webrtc_sens_1.configure(
            command=lambda: sj.save_key(f"threshold_auto_level_{device}", 1) or self.webrtcvad.set_mode(1)
        )
        self.radio_webrtc_sens_2.configure(
            command=lambda: sj.save_key(f"threshold_auto_level_{device}", 2) or self.webrtcvad.set_mode(2)
        )
        self.radio_webrtc_sens_3.configure(
            command=lambda: sj.save_key(f"threshold_auto_level_{device}", 3) or self.webrtcvad.set_mode(3)
        )

        self.vert_sep = ttk.Separator(self.f_device_5, orient="vertical")
        self.vert_sep.pack(side="left", fill="y", padx=5)

        self.cbtn_threshold_auto_silero = CustomCheckButton(
            self.f_device_5,
            sj.cache.get(f"threshold_auto_silero_{device}", True),
            self.toggle_silero_vad,
            text="Use Silero",
            style="Switch.TCheckbutton"
        )
        self.cbtn_threshold_auto_silero.pack(side="left", padx=5)
        self.tooltip_cbtn_threshold_auto_silero = tk_tooltip(
            self.cbtn_threshold_auto_silero,
            "If checked, will use Silero-VAD alongside WebRTC-VAD for better noise filtering."
        )

        self.spn_silero_min = SpinboxNumOnly(
            self.root,
            self.f_device_5,
            0.1,
            1.0,
            lambda x: sj.save_key(f"threshold_silero_{device}_min", float(x)),
            initial_value=sj.cache.get(f"threshold_silero_{device}_min", 0.7),
            num_float=True,
            allow_empty=False,
            delay=10,
            increment=0.05,
            width=5
        )
        self.spn_silero_min.pack(side="left", padx=5)
        tk_tooltip(
            self.spn_silero_min,
            f"Set the minimum probability/confidence for Silero-VAD to consider your {self.long_device} " \
            "input as speech.\n\nDefault value is 0.7.",
        )

        # manual
        self.lbl_threshold_db = ttk.Label(self.f_device_5, text="Threshold (dB)", width=14)
        self.lbl_threshold_db.pack(side="left", padx=5)

        self.scale_threshold_db = ttk.Scale(self.f_device_5, from_=-60.0, to=0.0, orient="horizontal", length=300)
        self.scale_threshold_db.set(sj.cache.get(f"threshold_db_{device}", -30.0))
        self.scale_threshold_db.configure(command=self.slider_move)
        self.scale_threshold_db.bind(
            "<ButtonRelease-1>", lambda _: sj.save_key(f"threshold_db_{device}", float(self.scale_threshold_db.get()))
        )
        self.scale_threshold_db.pack(side="left", padx=5)

        self.lbl_threshold_db_value = ttk.Label(self.f_device_5, text="0 dB", width=8)
        self.lbl_threshold_db_value.configure(text=f"{self.scale_threshold_db.get():.2f} dB")
        self.lbl_threshold_db_value.pack(side="left", padx=5)

        # 6
        self.lbl_device_emoji = ttk.Label(self.f_device_6, image=bc.mic_emoji if device == "mic" else bc.speaker_emoji)
        self.lbl_device_emoji.pack(side="left", padx=5)

        self.audiometer = AudioMeter(self.f_device_6, self.master, True, MIN_THRESHOLD, MAX_THRESHOLD, height=30, width=300)
        self.audiometer.set_db(MIN_THRESHOLD)
        self.audiometer.pack(side="left", padx=5)

    def toggle_enable_threshold(self, open_stream=True):
        """
        Toggle the enable threshold checkbutton

        Parameters
        ----------
        open_stream : bool, optional
            open the stream or not, by default True
        """
        if "selected" in self.cbtn_threshold_enable.state():
            self.cbtn_threshold_auto.configure(state="normal")
            self.cbtn_auto_break_buffer.configure(state="normal")
            self.toggle_auto_threshold()
            self.call_set_meter(open_stream)
        else:
            self.cbtn_threshold_auto.configure(state="disabled")
            self.cbtn_auto_break_buffer.configure(state="disabled")
            self.toggle_auto_threshold()
            self.call_set_meter(open_stream)

    def toggle_auto_threshold(self):
        """
        Toggle the auto threshold checkbutton
        """
        if "selected" in self.cbtn_threshold_auto.state():
            self.audiometer.set_auto(True)
            self.audiometer.configure(height=10)
            self.scale_threshold_db.configure(state="disabled")

            self.lbl_threshold_db.pack_forget()
            self.scale_threshold_db.pack_forget()
            self.lbl_threshold_db_value.pack_forget()

            self.lbl_sensitivity.pack(side="left", padx=5)
            self.radio_webrtc_sens_1.pack(side="left", padx=5)
            self.radio_webrtc_sens_2.pack(side="left", padx=5)
            self.radio_webrtc_sens_3.pack(side="left", padx=5)
            self.vert_sep.pack(side="left", fill="y", padx=5)
            self.cbtn_threshold_auto_silero.pack(side="left", padx=5)
            self.toggle_silero_vad(self.cbtn_threshold_auto_silero.instate(["selected"]), save=False)
        else:
            self.audiometer.set_auto(False)
            self.audiometer.configure(height=30)
            self.scale_threshold_db.configure(state="normal")
            self.lbl_threshold_db_value.configure(text=f"{float(self.scale_threshold_db.get()):.2f} dB")

            self.lbl_sensitivity.pack_forget()
            self.radio_webrtc_sens_1.pack_forget()
            self.radio_webrtc_sens_2.pack_forget()
            self.radio_webrtc_sens_3.pack_forget()
            self.vert_sep.pack_forget()
            self.cbtn_threshold_auto_silero.pack_forget()
            self.toggle_silero_vad(False, save=False)

            self.lbl_threshold_db.pack(side="left", padx=5)
            self.scale_threshold_db.pack(side="left", padx=5)
            self.lbl_threshold_db_value.pack(side="left", padx=5)

    def set_meter(self, open_stream=True):
        """
        Open or close the speaker meter alongside the audio stream.
        This function also handle the UI changes when the meter is opened or closed

        Parameters
        ----------
        open_stream : bool, optional
            Whether to open the stream or not, by default True
        """
        if self.device == "speaker" and system() != "Windows":
            return

        try:
            if open_stream and sj.cache.get(f"threshold_enable_{self.device}", True):
                assert self.silerovad is not None, "SileroVAD is not loaded yet!"
                logger.debug(f"Opening {self.long_device} meter")
                self.possible_auto_threshold()
                self.possible_silerovad()
                self.silerovad.reset_states()
                self.f_device_5.pack(side="top", fill="x", pady=(10, 5), padx=5)
                self.f_device_6.pack(side="top", fill="x", pady=(0, 5), padx=5)
                self.audiometer.pack(side="left", padx=5)
                self.lbl_device_emoji.configure(
                    text="", image=bc.mic_emoji if self.device == "mic" else bc.speaker_emoji, width=10, foreground="black"
                )

                self.max_threshold = MAX_THRESHOLD
                self.min_threshold = MIN_THRESHOLD
                self.p = pyaudio.PyAudio()
                self.audiometer.set_threshold(sj.cache.get(f"threshold_db_{self.device}", -30.0))
                success, detail = get_device_details(self.device, sj, self.p, debug=False)
                if success:
                    self.device_detail = detail
                else:
                    raise Exception(f"Failed to get {self.long_device} details")

                self.frame_duration = get_frame_duration(self.device_detail["sample_rate"], self.device_detail["chunk_size"])
                self.stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=self.device_detail["num_of_channels"],
                    rate=self.device_detail["sample_rate"],
                    input=True,
                    frames_per_buffer=self.device_detail["chunk_size"],
                    input_device_index=self.device_detail["device_detail"]["index"],  # type: ignore
                    stream_callback=self.stream_cb,
                )
                self.stream.start_stream()
                self.audiometer.start()
            else:
                # STOP
                self.close_meter()

                self.f_device_5.pack_forget()
                self.f_device_6.pack_forget()
                self.audiometer.pack_forget()
        except Exception as e:
            if "main thread is not in main loop" not in str(e):  # on init sometimes it will throw this error
                logger.exception(e)

                # dont show the meter, show failed message
                try:
                    self.audiometer.pack_forget()
                    self.lbl_device_emoji.configure(
                        text="Failed to load device to open audio stream. Check log for details",
                        image="",
                        width=50,
                        foreground="red"
                    )
                except Exception:
                    pass

            self.close_meter()

    def close_meter(self):
        """
        Close the meter and the stream
        """
        if self.device == "speaker" and system() != "Windows":
            return

        try:
            if self.stream:
                if self.silerovad:
                    self.silerovad.reset_states()
                self.audiometer.stop()
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            if self.p is not None:
                self.p.terminate()
                self.p = None
        except Exception as e:
            logger.exception(e)
            logger.error(f"Failed to close {self.long_device} meter")

    def call_set_meter(self, open_stream=True):
        """
        Call the set meter function in a new thread
        It will close the meter first before opening it.

        Parameters
        ----------
        open_stream : bool, optional
            Whether to open the stream or not, by default True
        """
        if self.on_start:
            return

        if self.device == "speaker" and system() != "Windows":
            return

        self.close_meter()
        if not sj.cache["show_audio_visualizer_in_setting"]:
            return

        Thread(target=self.set_meter, args=[open_stream], daemon=True).start()

    def stream_cb(self, in_data, _frame_count, _time_info, _status):
        """
        Stream callback for the audio stream
        """
        try:
            assert self.silerovad is not None, "SileroVAD is not loaded yet!"
            resampled = resample_sr(in_data, self.device_detail["sample_rate"], WHISPER_SR)
            db = get_db(in_data)
            self.audiometer.set_db(db)

            if db > self.max_threshold:
                self.max_threshold = db
                self.audiometer.max = db
            if db < self.min_threshold:
                self.min_threshold = db
                self.audiometer.min = db

            if not self.vad_checked:  # check at least once so we know if silero is possible to use or not
                self.vad_checked = True
                logger.debug("Checking if webrtcvad is possible to use. You can ignore the error log if it fails!")
                get_speech_webrtc(resampled, WHISPER_SR, self.frame_duration, self.webrtcvad)
                logger.debug("Checking if silero is possible to use. You can ignore the error log if it fails!")
                self.silerovad(to_silero(resampled, self.device_detail["num_of_channels"]), WHISPER_SR)

            if sj.cache.get(f"threshold_enable_{self.device}", True) and not self.auto_threshold_disabled:
                is_speech = get_speech_webrtc(resampled, WHISPER_SR, self.frame_duration, self.webrtcvad)
                if is_speech and sj.cache.get(f"threshold_auto_silero_{self.device}", True) and not self.silero_disabled:
                    conf = self.silerovad(to_silero(resampled, self.device_detail["num_of_channels"]), WHISPER_SR)
                    is_speech = conf.item() >= sj.cache.get(f"threshold_silero_{self.device}_min", 0.7)
                self.audiometer.set_recording(is_speech)

            return (in_data, pyaudio.paContinue)
        except Exception as e:
            logger.exception(e)

            if "Error while processing frame" in str(e):
                logger.error("WEBRTC Error!")
                if self.frame_duration >= 20:
                    logger.warning(
                        f"Webrtc Fail to process frame for {self.long_device}, trying to lower frame duration." \
                        f"{self.frame_duration} -> {self.frame_duration - 10}"
                    )
                    self.frame_duration -= 10
                    self.vad_checked = False  # try again with new frame duration
                else:
                    self.disable_auto_threshold()
                logger.warning("Not possible to use Auto Threshold with the current device config! So it is now disabled")
            elif "Input audio chunk is too short" in str(e):
                logger.error("SileroVAD Error!")
                self.disable_silerovad()
                logger.warning("Not possible to use Silero VAD with the current device config! So it is now disabled")

            return (in_data, pyaudio.paContinue)

    def slider_move(self, event):
        """
        Slider move, update display
        """
        self.lbl_threshold_db_value.configure(text=f"{float(event):.2f} dB")
        self.audiometer.set_threshold(float(event))

    def possible_silerovad(self):
        """
        Check if silero vad is possible to use
        """
        self.cbtn_threshold_auto_silero.configure(state="normal")
        text = "If checked, will use Silero VAD alongside WebRTC VAD for better accuracy."
        self.tooltip_cbtn_threshold_auto_silero.text = text
        self.silero_disabled = False
        self.vad_checked = False

    def disable_silerovad(self):
        """
        Disable silero vad
        """
        disabled_text = "Silero VAD is unavailable on this current " \
                    "device configuration (check log for details)"
        if self.cbtn_threshold_auto_silero.instate(["selected"]):
            self.cbtn_threshold_auto_silero.invoke()
        self.cbtn_threshold_auto_silero.configure(state="disabled")
        self.tooltip_cbtn_threshold_auto_silero.text = disabled_text
        self.silero_disabled = True

    def possible_auto_threshold(self):
        """
        Enable auto threshold widget
        """
        text = "Wether to use VAD or manual threshold for the speaker input."
        self.cbtn_threshold_auto.configure(state="normal")
        self.tooltip_cbtn_threshold_auto.text = text
        self.cbtn_auto_break_buffer.configure(state="normal")

    def disable_auto_threshold(self):
        """
        Disable auto threshold widget
        """
        disabled_text = "Auto threshold is unavailable on this current device configuration. You can try to change the " \
                        "device configuration in the setting above"
        if self.cbtn_threshold_auto.instate(["selected"]):
            self.cbtn_threshold_auto.invoke()
        self.cbtn_threshold_auto.configure(state="disabled")
        self.tooltip_cbtn_threshold_auto.text = disabled_text
        self.auto_threshold_disabled = True

    def toggle_silero_vad(self, on, save=True):
        """
        Toggle the silero vad widget visibility
        """
        if save:
            sj.save_key(f"threshold_auto_silero_{self.device}", on)

        if on:
            self.spn_silero_min.pack(side="left", padx=5)
        else:
            self.spn_silero_min.pack_forget()

    def toggle_auto_sr(self, auto: bool):
        """
        Toggle sr spinner disabled or not depending on auto value
        """
        sj.save_key(f"auto_sample_rate_{self.device}", auto)
        self.cb_sr.toggle_disable(auto)

    def toggle_auto_channels(self, auto: bool):
        """
        Toggle channels spinner disabled or not depending on auto value
        """
        sj.save_key(f"auto_channels_{self.device}", auto)
        self.cb_channels.toggle_disable(auto)


class SettingRecord:
    """
    Record tab in setting window.
    """
    def __init__(self, root: Toplevel, master_frame: Union[ttk.Frame, Frame]):
        self.root = root
        self.master = master_frame
        self.on_start = True

        # ------------------ Record  ------------------
        self.lf_device = LabelFrame(self.master, text="• Device Parameters (Advanced Setting ⚠️)")
        self.lf_device.pack(side="top", fill="x", padx=5, pady=5)

        tk_tooltip(
            self.lf_device, "This is advanced settings, you should not change this unless you know what you are doing."
            "\n\nChanging this option might cause the program to fail to record!",
            delay=50
        )

        self.f_device_1 = ttk.Frame(self.lf_device)
        self.f_device_1.pack(side="top", fill="x", pady=5, padx=5)

        self.lf_recording = LabelFrame(self.master, text="• Recording Options")
        self.lf_recording.pack(side="top", fill="x", padx=5, pady=5)

        self.f_recording_0 = ttk.Frame(self.lf_recording)
        self.f_recording_0.pack(side="top", fill="x", pady=5, padx=5)

        self.f_recording_1 = ttk.Frame(self.lf_recording)
        self.f_recording_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_recording_2 = ttk.Frame(self.lf_recording)
        self.f_recording_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_recording_2_l = ttk.Frame(self.f_recording_2)
        self.f_recording_2_l.pack(side="left", fill="both", expand=True)

        self.f_recording_2_r = ttk.Frame(self.f_recording_2)
        self.f_recording_2_r.pack(side="left", fill="both", expand=True)

        self.lf_result = LabelFrame(self.master, text="• Result")
        self.lf_result.pack(side="top", fill="x", padx=5, pady=5)

        self.f_result_1 = ttk.Frame(self.lf_result)
        self.f_result_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_result_2 = ttk.Frame(self.lf_result)
        self.f_result_2.pack(side="top", fill="x", pady=5, padx=5)

        # ------------------ Device ------------------
        # --------- MIC
        self.lf_mic_device = ttk.LabelFrame(self.f_device_1, text="Microphone")
        self.lf_mic_device.pack(side="left", padx=5, fill="x", expand=True)

        self.f_mic_device_1 = ttk.Frame(self.lf_mic_device)
        self.f_mic_device_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_mic_device_2 = ttk.Frame(self.lf_mic_device)
        self.f_mic_device_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_mic_device_3 = ttk.Frame(self.lf_mic_device)
        self.f_mic_device_3.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_sr_mic = ttk.Label(self.f_mic_device_1, text="Sample Rate", width=14)
        self.lbl_sr_mic.pack(side="left", padx=5)
        self.cb_sr_mic = ComboboxTypeOnCustom(
            self.root, self.f_mic_device_1, ["8000", "16000", "22050", "44100", "48000"], "4000", "384000",
            lambda x: self.set_sr("mic", int(x)), sj.cache["sample_rate_mic"]
        )
        self.cb_sr_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_sr_mic, self.cb_sr_mic],
            "Set the sample rate for the audio recording. \n\nDefault value is 16000 if not auto.",
        )

        self.lbl_chunk_size_mic = ttk.Label(self.f_mic_device_1, text="Chunk Size", width=10)
        self.lbl_chunk_size_mic.pack(side="left", padx=5)
        self.cb_chunk_size_mic = ComboboxTypeOnCustom(
            self.root, self.f_mic_device_1, ["320", "480", "640", "800", "960", "1024", "1280"], "320", "1280",
            lambda x: self.set_chunk_size("mic", int(x)), sj.cache["chunk_size_mic"]
        )
        self.cb_chunk_size_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_chunk_size_mic, self.cb_chunk_size_mic],
            "Set the chunk size for the audio recording. Bigger chunk size means that more audio data is processed"
            " at once, which can lead to higher CPU usage"
            "\n\nDefault value is 1024.",
        )

        # 2
        self.lbl_channels_mic = ttk.Label(self.f_mic_device_2, text="Channels", width=14)
        self.lbl_channels_mic.pack(side="left", padx=5)
        self.cb_channels_mic = ComboboxTypeOnCustom(
            self.root, self.f_mic_device_2, ["Mono", "Stereo"], "1", "25", lambda x: self.set_channels("mic", str(x)),
            sj.cache["channels_mic"]
        )
        self.cb_channels_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.cb_channels_mic, self.lbl_channels_mic],
            "Set the channels for the audio recording.\n\n*The program might fail to record properly if you set " \
            "channels to more than stereo (2), But if you insist on setting it to more than stereo, you can try " \
            "to use the temporary wav file option in the conversion option below." \
            "\n\nDefault value is Mono (1) for mic input if not auto.",
            wrap_len=400,
        )

        # 3
        self.cbtn_auto_sr_mic = CustomCheckButton(
            self.f_mic_device_3,
            sj.cache["auto_sample_rate_mic"],
            lambda x: self.__toggle_auto_sr("mic", x),
            text="Auto sample rate",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_sr_mic.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_auto_sr_mic,
            "If checked, the sample rate will be automatically set based on the device's sample rate."
            "\n\nInvalid value will cause the program to fail to record, it is better to leave it checked if you are having"
            " issues\n\nDefault is checked",
            wrap_len=400,
        )

        self.cbtn_auto_channels_mic = CustomCheckButton(
            self.f_mic_device_3,
            sj.cache["auto_channels_mic"],
            lambda x: self.__toggle_auto_channels("mic", x),
            text="Auto channels value",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_channels_mic.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_auto_channels_mic,
            "If checked, the channels value will be automatically set based on the device's channels amount."
            "\n\nInvalid value will cause the program to fail to record, it is better to leave it checked if you are having"
            " issues\n\nDefault is checked",
            wrap_len=400,
        )

        # --------- Speaker
        self.lf_speaker_device = ttk.LabelFrame(self.f_device_1, text="Speaker")
        self.lf_speaker_device.pack(side="left", padx=5, fill="x", expand=True)

        self.f_speaker_device_1 = ttk.Frame(self.lf_speaker_device)
        self.f_speaker_device_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_speaker_device_2 = ttk.Frame(self.lf_speaker_device)
        self.f_speaker_device_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_speaker_device_3 = ttk.Frame(self.lf_speaker_device)
        self.f_speaker_device_3.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_sr_speaker = ttk.Label(self.f_speaker_device_1, text="Sample Rate", width=14)
        self.lbl_sr_speaker.pack(side="left", padx=5)
        self.cb_sr_speaker = ComboboxTypeOnCustom(
            self.root, self.f_speaker_device_1, ["8000", "16000", "22050", "44100", "48000"], "4000", "384000",
            lambda x: self.set_sr("speaker", int(x)), sj.cache["sample_rate_speaker"]
        )
        self.cb_sr_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_sr_speaker, self.cb_sr_speaker],
            "Set the sample rate for the audio recording. \n\nDefault value is 41000 if not auto.",
        )

        self.lbl_chunk_size_speaker = ttk.Label(self.f_speaker_device_1, text="Chunk Size", width=10)
        self.lbl_chunk_size_speaker.pack(side="left", padx=5)
        self.cb_chunk_size_speaker = ComboboxTypeOnCustom(
            self.root, self.f_speaker_device_1, ["320", "480", "640", "800", "960", "1024", "1280"], "320", "1280",
            lambda x: self.set_chunk_size("speaker", int(x)), sj.cache["chunk_size_speaker"]
        )
        self.cb_chunk_size_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_chunk_size_speaker, self.cb_chunk_size_speaker],
            "Set the chunk size for the audio recording. Bigger chunk size means that more audio data is processed"
            " at once, which can lead to higher CPU usage"
            "\n\nDefault value is 1024.",
        )

        # 2
        self.lbl_channels_speaker = ttk.Label(self.f_speaker_device_2, text="Channels", width=14)
        self.lbl_channels_speaker.pack(side="left", padx=5)
        self.cb_channels_speaker = ComboboxTypeOnCustom(
            self.root, self.f_speaker_device_2, ["Mono", "Stereo"], "1", "25",
            lambda x: self.set_channels("speaker", str(x)), sj.cache["channels_speaker"]
        )
        self.cb_channels_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.cb_channels_speaker, self.lbl_channels_speaker],
            "Set the channels for the audio recording.\n\n*The program might fail to record properly if you set " \
            "channels to more than stereo (2), But if you insist on setting it to more than stereo, you can try " \
            "to use the temporary wav file option in the conversion option below." \
            "\n\nDefault value is Stereo (2) for speaker input if not auto.",
            wrap_len=400,
        )

        # 3
        self.cbtn_auto_sr_speaker = CustomCheckButton(
            self.f_speaker_device_3,
            sj.cache["auto_sample_rate_speaker"],
            lambda x: self.__toggle_auto_sr("speaker", x),
            text="Auto sample rate",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_sr_speaker.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_auto_sr_speaker,
            "If checked, the sample rate will be automatically set based on the device's sample rate."
            "\n\nInvalid value will cause the program to fail to record, it is better to leave it checked if you are having"
            " issues\n\nDefault is checked",
            wrap_len=400,
        )

        self.cbtn_auto_channels_speaker = CustomCheckButton(
            self.f_speaker_device_3,
            sj.cache["auto_channels_speaker"],
            lambda x: self.__toggle_auto_channels("speaker", x),
            text="Auto channels value",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_channels_speaker.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_auto_channels_speaker,
            "If checked, the channels value will be automatically set based on the device's channels amount."
            "\n\nInvalid value will cause the program to fail to record, it is better to leave it checked if you are having"
            " issues\n\nDefault is checked",
            wrap_len=400,
        )

        # ------------------ Recording ------------------
        self.lbl_tc_rate = ttk.Label(self.f_recording_0, text="Transcribe Rate (ms)", width=18)
        self.lbl_tc_rate.pack(side="left", padx=5)
        self.spn_tc_rate = SpinboxNumOnly(
            self.root,
            self.f_recording_0,
            1,
            1000,
            lambda x: sj.save_key("transcribe_rate", int(x)),
            initial_value=sj.cache["transcribe_rate"]
        )
        self.spn_tc_rate.pack(side="left", padx=5)
        tk_tooltips(
            [self.spn_tc_rate, self.lbl_tc_rate],
            "Set the transcribe rate or the time between each transcribe check."
            "\n\nFor more real time experience you can lower it more. The lower the value, the more resource it will use."
            "\n\nIf you lower the transcribe rate, you should also lower the max buffer for a better experience."
            "\n\nDefault value is 300ms.",
            wrap_len=350,
        )

        # ----- procesing
        self.lf_processing = ttk.LabelFrame(self.f_recording_1, text="Audio Processing")
        self.lf_processing.pack(side="top", padx=5, fill="x", expand=True)

        self.f_processing_1 = ttk.Frame(self.lf_processing)
        self.f_processing_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_processing_2 = ttk.Frame(self.lf_processing)
        self.f_processing_2.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_conversion_method = ttk.Label(self.f_processing_1, text="Conversion", width=14)
        self.lbl_conversion_method.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_conversion_method,
            "Set the method used to convert the audio before feeding it to the model."
            "\n\nDefault value is numpy array.",
        )

        self.var_conversion = StringVar()
        self.radio_numpy_array = ttk.Radiobutton(
            self.f_processing_1, text="Numpy Array", value="numpy", variable=self.var_conversion
        )
        self.radio_numpy_array.pack(side="left", padx=5)
        tk_tooltip(
            self.radio_numpy_array,
            "The default and recommended method to process the audio. "
            "This will make the process faster because of no I/O process of file."
            "\n\nDefault value is checked.",
            wrap_len=380,
        )

        self.radio_temp_file = ttk.Radiobutton(
            self.f_processing_1, text="Temporary wav File", value="temp", variable=self.var_conversion
        )
        self.radio_temp_file.pack(side="left", padx=5)
        tk_tooltip(
            self.radio_temp_file,
            "If checked, will use temporary created wav files to fed the audio to the Whisper model " \
            "instead of using numpy arrays.\n\nUsing this might help to fix error related to device " \
            "or conversion in record session (which rarely happens), but it could slow down the process " \
            "especially if the buffer is long. When both VAD and Demucs are enabled in record session, " \
            "this option will be used automatically..\n\nDefault value is unchecked.",
            wrap_len=400,
        )

        self.var_conversion.set("temp" if sj.cache["use_temp"] else "numpy")
        self.radio_numpy_array.configure(command=lambda: sj.save_key("use_temp", False) or self.toggle_use_temp(False))
        self.radio_temp_file.configure(command=lambda: sj.save_key("use_temp", True) or self.toggle_use_temp(True))

        self.lbl_hint_conversion = ttk.Label(self.f_processing_1, image=bc.question_emoji, compound="left")
        self.lbl_hint_conversion.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_hint_conversion,
            "Convert method is the method used to process the audio before feeding it to the model." \
            "\n\nNumpy array is the default and recommended method. It is faster and more efficient. " \
            "If there are any errors related to device or conversion in the record session, try using " \
            "the temporary wav file.\n\nTemporary wav file is slower and less efficient but might be more " \
            "accurate in some cases. When using wav file, the I/O process of the recorded wav file might " \
            "slow down the performance of the app significantly, especially on long buffers." \
            "\n\nBoth setting will resample the audio to a 16k hz sample rate. Difference is, numpy array " \
            "uses scipy to resample the audio while temporary wav file uses ffmpeg.",
            wrap_len=400,
        )

        self.cbtn_keep_temp = CustomCheckButton(
            self.f_processing_2,
            sj.cache["keep_temp"],
            lambda x: sj.save_key("keep_temp", x),
            text="Keep temp files",
            style="Switch.TCheckbutton"
        )
        self.cbtn_keep_temp.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_keep_temp,
            "If checked, will not delete the audio file that is fed into the transcribers."
            "\n\nDefault value is unchecked.",
        )

        # ------ MIC and Speaker recording
        self.mic_rec_option = RecordingOptionsDevice(
            self.root,
            self.f_recording_2_l,
            "mic",
            self.cb_sr_mic,
            self.cb_channels_mic,
        )
        self.speaker_rec_option = RecordingOptionsDevice(
            self.root,
            self.f_recording_2_r,
            "speaker",
            self.cb_sr_speaker,
            self.cb_channels_speaker,
        )

        # ------------------ Result ------------------
        self.lbl_separator = ttk.Label(self.f_result_1, text="Text Separator", width=14)
        self.lbl_separator.pack(side="left", padx=5)
        self.entry_separator = ttk.Entry(self.f_result_1)
        self.entry_separator.insert(0, sj.cache["separate_with"])
        self.entry_separator.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_separator.bind(
            "<KeyRelease>",
            lambda e: sj.save_key("separate_with", self.entry_separator.get()),
        )
        tk_tooltips(
            [self.entry_separator, self.lbl_separator],
            "Set the separator for text resulted from the record session.\n\nDefault value \\n",
            wrap_len=400,
        )

        # --------------------------
        self.__init_setting_once()

    # ------------------ Functions ------------------
    def __init_setting_once(self):
        """Initialize the setting once"""
        # toggle
        self.toggle_use_temp(self.radio_temp_file.instate(["selected"]))
        self.cb_sr_mic.toggle_disable(self.cbtn_auto_sr_mic.instate(["selected"]))
        self.cb_channels_mic.toggle_disable(self.cbtn_auto_channels_mic.instate(["selected"]))
        self.cb_sr_speaker.toggle_disable(self.cbtn_auto_sr_speaker.instate(["selected"]))
        self.cb_channels_speaker.toggle_disable(self.cbtn_auto_channels_speaker.instate(["selected"]))
        self.mic_rec_option.toggle_enable_threshold(False)  # not open on start
        self.speaker_rec_option.toggle_enable_threshold(False)  # not open on start

        # disable
        windows_os_only(
            [
                self.lbl_sr_speaker, self.cb_sr_speaker, self.lbl_channels_speaker, self.cb_channels_speaker,
                self.lbl_chunk_size_speaker, self.cb_chunk_size_speaker, self.cbtn_auto_sr_speaker,
                self.cbtn_auto_channels_speaker, self.speaker_rec_option.lbl_min_input,
                self.speaker_rec_option.spn_min_input, self.speaker_rec_option.lbl_buffer,
                self.speaker_rec_option.lbl_buffer, self.speaker_rec_option.spn_buffer,
                self.speaker_rec_option.lbl_max_sentences, self.speaker_rec_option.spn_max_sentences,
                self.speaker_rec_option.cbtn_no_limit, self.speaker_rec_option.cbtn_threshold_enable,
                self.speaker_rec_option.cbtn_threshold_auto, self.speaker_rec_option.cbtn_threshold_auto,
                self.speaker_rec_option.spn_silero_min, self.speaker_rec_option.cbtn_auto_break_buffer,
                self.speaker_rec_option.scale_threshold_db, self.speaker_rec_option.lbl_threshold_db_value,
                self.speaker_rec_option.lbl_threshold_db, self.speaker_rec_option.lbl_sensitivity,
                self.speaker_rec_option.radio_webrtc_sens_1, self.speaker_rec_option.radio_webrtc_sens_2,
                self.speaker_rec_option.radio_webrtc_sens_3, self.speaker_rec_option.cbtn_threshold_auto_silero
            ]
        )

        if system() != "Windows":
            self.speaker_rec_option.cbtn_threshold_auto.configure(state="disabled")
            self.speaker_rec_option.cbtn_auto_break_buffer.configure(state="disabled")

        self.on_start = False
        self.mic_rec_option.on_start = False
        self.speaker_rec_option.on_start = False

    def toggle_use_temp(self, state: bool) -> None:
        """
        Toggle the use temp checkbutton
        """
        if state:
            self.f_processing_2.pack(side="top", fill="x", pady=5, padx=5)
            self.lbl_conversion_method.pack_configure(pady=0)
            self.radio_numpy_array.pack_configure(pady=0)
            self.radio_temp_file.pack_configure(pady=0)
            self.lbl_hint_conversion.pack_configure(pady=0)
        else:
            self.lbl_conversion_method.pack_configure(pady=(0, 5))
            self.radio_numpy_array.pack_configure(pady=(0, 5))
            self.radio_temp_file.pack_configure(pady=(0, 5))
            self.lbl_hint_conversion.pack_configure(pady=(0, 5))
            self.f_processing_2.pack_forget()

    def set_sr(self, device: Literal["mic", "speaker"], value: int) -> None:
        """
        Set the sample rate for the device
        """
        sj.save_key(f"sample_rate_{device}", value)
        if device == "mic":
            self.mic_rec_option.toggle_enable_threshold()
        elif device == "speaker":
            self.speaker_rec_option.toggle_enable_threshold()

    def set_chunk_size(self, device: Literal["mic", "speaker"], value: int) -> None:
        """
        Set the chunk size for the device
        """
        sj.save_key(f"chunk_size_{device}", value)
        if device == "mic":
            self.mic_rec_option.toggle_enable_threshold()
        elif device == "speaker":
            self.speaker_rec_option.toggle_enable_threshold()

    def set_channels(self, device: Literal["mic", "speaker"], value: str) -> None:
        """
        Set the channels for the device
        """
        sj.save_key(f"channels_{device}", value)
        if device == "mic":
            self.mic_rec_option.toggle_enable_threshold()
        elif device == "speaker":
            self.speaker_rec_option.toggle_enable_threshold()

    def __toggle_auto_sr(self, device: Literal["mic", "speaker"], auto: bool) -> None:
        """
        Toggle sr spinner disabled or not depending on auto value
        """
        sj.save_key(f"auto_sample_rate_{device}", auto)
        if device == "mic":
            self.cb_sr_mic.toggle_disable(auto)
            self.mic_rec_option.toggle_enable_threshold()
        elif device == "speaker":
            self.cb_sr_speaker.toggle_disable(auto)
            self.speaker_rec_option.toggle_enable_threshold()

    def __toggle_auto_channels(self, device: Literal["mic", "speaker"], auto: bool) -> None:
        """
        Toggle channels spinner disabled or not depending on auto value
        """
        sj.save_key(f"auto_channels_{device}", auto)
        if device == "mic":
            self.cb_channels_mic.toggle_disable(auto)
            self.mic_rec_option.toggle_enable_threshold()
        elif device == "speaker":
            self.cb_channels_speaker.toggle_disable(auto)
            self.speaker_rec_option.toggle_enable_threshold()

    def call_both_with_wait(self, open_stream=True):
        if self.on_start:
            return

        if open_stream:
            logger.debug("Opening both meter")

        if not sj.cache["show_audio_visualizer_in_setting"]:
            self.mic_rec_option.close_meter()
        else:
            mic = Thread(target=self.mic_rec_option.call_set_meter, daemon=True, args=[open_stream])
            mic.start()
            mic.join()

        if system() == "Windows":
            # for some reason, if the speaker is called right after the mic, it will not work properly
            # it will fail to catch any loopback and will crash the program completely
            # so we wait for 1 second to prevent error
            sleep(1)

            if not sj.cache["show_audio_visualizer_in_setting"]:
                self.speaker_rec_option.close_meter()
            else:
                speaker = Thread(target=self.speaker_rec_option.call_set_meter, daemon=True, args=[open_stream])
                speaker.start()
                speaker.join()
