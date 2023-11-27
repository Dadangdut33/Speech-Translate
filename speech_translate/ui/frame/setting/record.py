from platform import system
from threading import Thread
from time import sleep
from tkinter import ttk, Toplevel, Frame, LabelFrame, StringVar, IntVar
from typing import Literal, Union

from loguru import logger
from webrtcvad import Vad
from speech_translate.ui.custom.checkbutton import CustomCheckButton
from speech_translate.ui.custom.combobox import ComboboxTypeOnCustom
from speech_translate.ui.custom.spinbox import SpinboxNumOnly
if system() == "Windows":
    import pyaudiowpatch as pyaudio
else:
    import pyaudio  # type: ignore

from speech_translate.linker import sj, bc
from speech_translate._constants import MIN_THRESHOLD, MAX_THRESHOLD, WHISPER_SR
from speech_translate.utils.audio.device import get_db, get_device_details, get_frame_duration, get_speech, resample_sr
from speech_translate.utils.helper import get_channel_int, cbtn_invoker, windows_os_only
from speech_translate.ui.custom.audio import AudioMeter
from speech_translate.ui.custom.tooltip import tk_tooltips, tk_tooltip


class SettingRecord:
    """
    Record tab in setting window.
    """
    def __init__(self, root: Toplevel, master_frame: Union[ttk.Frame, Frame]):
        self.root = root
        self.master = master_frame
        self.getting_threshold = False
        self.on_start = True

        self.max_mic = MAX_THRESHOLD
        self.min_mic = MIN_THRESHOLD
        self.p_mic = None
        self.detail_mic = None
        self.stream_mic = None
        self.mic_stopped = False
        self.thread_mic = None
        self.vad_mic = Vad()
        self.frame_duration_mic = 10

        self.max_speaker = MAX_THRESHOLD
        self.min_speaker = MIN_THRESHOLD
        self.p_speaker = None
        self.detail_speaker = None
        self.stream_speaker = None
        self.speaker_stopped = False
        self.thread_speaker = None
        self.vad_speaker = Vad()
        self.frame_duration_speaker = 10

        # ------------------ Record  ------------------
        self.lf_device = LabelFrame(self.master, text="• Device Parameters")
        self.lf_device.pack(side="top", fill="x", padx=5, pady=5)

        self.f_device_1 = ttk.Frame(self.lf_device)
        self.f_device_1.pack(side="top", fill="x", pady=5, padx=5)

        self.lf_recording = LabelFrame(self.master, text="• Recording Options")
        self.lf_recording.pack(side="top", fill="x", padx=5, pady=5)

        self.f_recording_0 = ttk.Frame(self.lf_recording)
        self.f_recording_0.pack(side="top", fill="x", pady=5, padx=5)

        self.f_recording_1 = ttk.Frame(self.lf_recording)
        self.f_recording_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_recording_1_l = ttk.Frame(self.f_recording_1)
        self.f_recording_1_l.pack(side="left", fill="x")

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
            self.root,
            self.f_mic_device_1,
            ["8000", "16000", "22050", "44100", "48000"],
            "4000",
            "384000",
            lambda x: sj.save_key("sample_rate_mic", int(x)),
            sj.cache["sample_rate_mic"],
        )
        self.cb_sr_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_sr_mic, self.cb_sr_mic],
            "Set the sample rate for the audio recording. \n\nDefault value is 16000.",
        )

        self.lbl_chunk_size_mic = ttk.Label(self.f_mic_device_1, text="Chunk Size", width=10)
        self.lbl_chunk_size_mic.pack(side="left", padx=5)
        self.cb_chunk_size_mic = ComboboxTypeOnCustom(
            self.root, self.f_mic_device_1, ["160", "320", "480", "640", "800", "960", "1024", "1280"], "160", "1280",
            lambda x: sj.save_key("chunk_size_mic", int(x)), sj.cache["chunk_size_mic"]
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
            self.root, self.f_mic_device_2, ["Mono", "Stereo"], "1", "25", lambda x: sj.save_key("channels_mic", x),
            sj.cache["channels_mic"]
        )
        self.cb_channels_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.cb_channels_mic, self.lbl_channels_mic],
            "Set the channels for the audio recording. \n\nDefault value is Mono (1).",
        )

        # 3
        self.cbtn_auto_sr_mic = CustomCheckButton(
            self.f_mic_device_3,
            sj.cache["auto_sample_rate_mic"],
            lambda x: sj.save_key("auto_sample_rate_mic", x) or self.toggle_sr("mic", x),
            text="Auto sample rate",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_sr_mic.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_auto_sr_mic,
            "If checked, the sample rate will be automatically set based on the device's sample rate."
            "\n\nInvalid value will cause the program to fail to record, it is better to leave it checked if you are having"
            " issues\n\nDefault is checked",
            wrapLength=400,
        )

        self.cbtn_auto_channels_mic = CustomCheckButton(
            self.f_mic_device_3,
            sj.cache["auto_channels_mic"],
            lambda x: sj.save_key("auto_channels_mic", x) or self.toggle_channels("mic", x),
            text="Auto channels value",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_channels_mic.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_auto_channels_mic,
            "If checked, the channels value will be automatically set based on the device's channels amount."
            "\n\nInvalid value will cause the program to fail to record, it is better to leave it checked if you are having"
            " issues\n\nDefault is checked",
            wrapLength=400,
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
            lambda x: sj.save_key("sample_rate_speaker", int(x)), sj.cache["sample_rate_speaker"]
        )
        self.cb_sr_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_sr_speaker, self.cb_sr_speaker],
            "Set the sample rate for the audio recording. \n\nDefault value is 41000.",
        )

        self.lbl_chunk_size_speaker = ttk.Label(self.f_speaker_device_1, text="Chunk Size", width=10)
        self.lbl_chunk_size_speaker.pack(side="left", padx=5)
        self.cb_chunk_size_speaker = ComboboxTypeOnCustom(
            self.root, self.f_speaker_device_1, ["160", "320", "480", "640", "800", "960", "1024", "1280"], "160", "1280",
            lambda x: sj.save_key("chunk_size_speaker", int(x)), sj.cache["chunk_size_speaker"]
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
            self.root, self.f_speaker_device_2, ["Mono", "Stereo"], "1", "25", lambda x: sj.save_key("channels_speaker", x),
            sj.cache["channels_speaker"]
        )
        self.cb_channels_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.cb_channels_speaker, self.lbl_channels_speaker],
            "Set the channels for the audio recording. \n\nDefault value is Stereo (2).",
        )

        # 3
        self.cbtn_auto_sr_speaker = CustomCheckButton(
            self.f_speaker_device_3,
            sj.cache["auto_sample_rate_speaker"],
            lambda x: sj.save_key("auto_sample_rate_speaker", x) or self.toggle_sr("speaker", x),
            text="Auto sample rate",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_sr_speaker.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_auto_sr_speaker,
            "If checked, the sample rate will be automatically set based on the device's sample rate."
            "\n\nInvalid value will cause the program to fail to record, it is better to leave it checked if you are having"
            " issues\n\nDefault is checked",
            wrapLength=400,
        )

        self.cbtn_auto_channels_speaker = CustomCheckButton(
            self.f_speaker_device_3,
            sj.cache["auto_channels_speaker"],
            lambda x: sj.save_key("auto_channels_speaker", x) or self.toggle_channels("speaker", x),
            text="Auto channels value",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_channels_speaker.pack(side="left", padx=5, pady=(0, 5))
        tk_tooltip(
            self.cbtn_auto_channels_speaker,
            "If checked, the channels value will be automatically set based on the device's channels amount."
            "\n\nInvalid value will cause the program to fail to record, it is better to leave it checked if you are having"
            " issues\n\nDefault is checked",
            wrapLength=400,
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
            wrapLength=350,
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
            wrapLength=380,
        )

        self.radio_temp_file = ttk.Radiobutton(
            self.f_processing_1, text="Temporary wav File", value="temp", variable=self.var_conversion
        )
        self.radio_temp_file.pack(side="left", padx=5)
        tk_tooltip(
            self.radio_temp_file,
            "If checked, will use temporary created wav files to fed the audio to the Whisper model "
            "instead of using numpy arrays.\n\nUsing this might help to fix error related to device or conversion in record session (which rarely happens), "
            "but it could slow down the process especially if the buffer is long. When both VAD and Demucs are enabled in record session, this option will be used automatically."
            ".\n\nDefault value is unchecked.",
            wrapLength=400,
        )

        self.var_conversion.set("temp" if sj.cache["use_temp"] else "numpy")
        self.radio_numpy_array.configure(command=lambda: sj.save_key("use_temp", False) or self.toggle_use_temp(False))
        self.radio_temp_file.configure(command=lambda: sj.save_key("use_temp", True) or self.toggle_use_temp(True))

        self.lbl_hint_conversion = ttk.Label(self.f_processing_1, image=bc.help_emoji, compound="left")
        self.lbl_hint_conversion.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_hint_conversion,
            "Convert method is the method used to process the audio before feeding it to the model."
            "\n\nNumpy array is the default and recommended method. It is faster and more efficient. "
            "If there are any errors related to device or conversion in the record session, try using the temporary wav file."
            "\n\nTemporary wav file is slower and less efficient but might be more accurate in some cases. "
            "When using wav file, the I/O process of the recorded wav file might slow down the performance "
            "of the app significantly, especially on long buffers."
            "\n\nBoth setting will resample the audio to a 16k hz sample rate. Difference is, numpy array "
            "uses scipy to resample the audio while temporary wav file uses ffmpeg.",
            wrapLength=400,
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

        # ------ Mic
        self.lf_mic_recording = ttk.LabelFrame(self.f_recording_2_l, text="Microphone")
        self.lf_mic_recording.pack(side="top", padx=5, fill="both", expand=True)

        self.f_mic_recording_1 = ttk.Frame(self.lf_mic_recording)
        self.f_mic_recording_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_mic_recording_2 = ttk.Frame(self.lf_mic_recording)
        self.f_mic_recording_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_mic_recording_3 = ttk.Frame(self.lf_mic_recording)
        self.f_mic_recording_3.pack(side="top", fill="x", pady=(5, 3), padx=5)

        self.f_mic_recording_4 = ttk.Frame(self.lf_mic_recording)
        self.f_mic_recording_4.pack(side="top", fill="x", pady=(10, 5), padx=5)

        self.f_mic_recording_5 = ttk.Frame(self.lf_mic_recording)
        self.f_mic_recording_5.pack(side="top", fill="x", pady=(0, 5), padx=5)

        # 1
        self.lbl_buffer_mic = ttk.Label(self.f_mic_recording_1, text="Max buffer", width=14)
        self.lbl_buffer_mic.pack(side="left", padx=5)
        self.spn_buffer_mic = SpinboxNumOnly(
            self.root,
            self.f_mic_recording_1,
            1,
            30,
            lambda x: sj.save_key("max_buffer_mic", int(x)),
            initial_value=sj.cache["max_buffer_mic"]
        )
        self.spn_buffer_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_buffer_mic, self.spn_buffer_mic],
            "Set the max buffer (in seconds) for microphone input.\n\nThe longer the buffer, the more time "
            "it will take to transcribe the audio. Not recommended to have very long buffer on low end PC."
            "\n\nDefault value is 10 seconds.",
        )

        self.lbl_hint_buffer_mic = ttk.Label(self.f_mic_recording_1, image=bc.help_emoji, compound="left")
        self.lbl_hint_buffer_mic.pack(side="left", padx=5)

        # 2
        self.lbl_max_sentences_mic = ttk.Label(self.f_mic_recording_2, text="Max Sentences", width=14)
        self.lbl_max_sentences_mic.pack(side="left", padx=5)
        self.spn_max_sentences_mic = SpinboxNumOnly(
            self.root,
            self.f_mic_recording_2,
            1,
            100,
            lambda x: sj.save_key("max_sentences_mic", int(x)),
            initial_value=sj.cache["max_sentences_mic"]
        )
        self.spn_max_sentences_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_max_sentences_mic, self.spn_max_sentences_mic],
            "Set max number of sentences, \n\none sentence equals one buffer. "
            "So if max buffer is 10 seconds, the words that are in those 10 seconds is the sentence."
            "\n\nDefault value is 5.",
        )

        # 3
        self.cbtn_threshold_enable_mic = CustomCheckButton(
            self.f_mic_recording_3,
            sj.cache["threshold_enable_mic"],
            lambda x: sj.save_key("threshold_enable_mic", x) or self.toggle_enable_threshold_mic(),
            text="Enable threshold",
            style="Switch.TCheckbutton"
        )
        self.cbtn_threshold_enable_mic.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_threshold_enable_mic,
            "If checked, input will need to reach the threshold before it is considered as an input."
            "\n\nDefault is checked",
        )

        self.cbtn_threshold_auto_mic = CustomCheckButton(
            self.f_mic_recording_3,
            sj.cache["threshold_auto_mic"],
            lambda x: sj.save_key("threshold_auto_mic", x) or self.toggle_auto_threshold_mic(),
            text="Auto",
            style="Switch.TCheckbutton"
        )
        self.cbtn_threshold_auto_mic.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_threshold_auto_mic,
            "Wether to use VAD or manual threshold for the speaker input.\n\nDefault is checked"
        )

        self.cbtn_auto_break_buffer_mic = CustomCheckButton(
            self.f_mic_recording_3,
            sj.cache["auto_break_buffer_mic"],
            lambda x: sj.save_key("auto_break_buffer_mic", x),
            text="Break buffer on silence",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_break_buffer_mic.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_auto_break_buffer_mic,
            "If checked, the buffer will be stopped and considered as 1 full sentence when there is silence detected for more than 1 second. "
            "This could help in reducing the background noise."
            "\n\nDefault is checked",
        )

        self.lbl_hint_threshold_mic = ttk.Label(self.f_mic_recording_3, image=bc.help_emoji, compound="left")
        self.lbl_hint_threshold_mic.pack(side="left", padx=5)

        # 4
        # vad for auto
        self.lbl_sensitivity_microphone = ttk.Label(self.f_mic_recording_4, text="Filter Noise", width=10)
        self.lbl_sensitivity_microphone.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_sensitivity_microphone,
            "Set the sensitivity level for the voice activity detection (VAD). 0 is the least aggressive in filtering out"
            " non-speech while 3 is the most aggressive"
            "\n\nDefault value is 2.",
        )

        self.var_sensitivity_microphone = IntVar()
        self.radio_vad_mic_1 = ttk.Radiobutton(
            self.f_mic_recording_4, text="1", value=1, variable=self.var_sensitivity_microphone
        )
        self.radio_vad_mic_1.pack(side="left", padx=5)
        self.radio_vad_mic_2 = ttk.Radiobutton(
            self.f_mic_recording_4, text="2", value=2, variable=self.var_sensitivity_microphone
        )
        self.radio_vad_mic_2.pack(side="left", padx=5)
        self.radio_vad_mic_3 = ttk.Radiobutton(
            self.f_mic_recording_4, text="3", value=3, variable=self.var_sensitivity_microphone
        )
        self.radio_vad_mic_3.pack(side="left", padx=5)

        temp_map = {1: self.radio_vad_mic_1, 2: self.radio_vad_mic_2, 3: self.radio_vad_mic_3}
        cbtn_invoker(sj.cache["threshold_auto_mic"], temp_map[sj.cache["threshold_auto_mode_mic"]])
        self.vad_mic.set_mode(sj.cache["threshold_auto_mode_mic"])
        self.radio_vad_mic_1.configure(command=lambda: sj.save_key("threshold_auto_mode_mic", 1) or self.vad_mic.set_mode(1))
        self.radio_vad_mic_2.configure(command=lambda: sj.save_key("threshold_auto_mode_mic", 2) or self.vad_mic.set_mode(2))
        self.radio_vad_mic_3.configure(command=lambda: sj.save_key("threshold_auto_mode_mic", 3) or self.vad_mic.set_mode(3))

        # threshold for manual
        self.lbl_threshold_mic = ttk.Label(self.f_mic_recording_4, text="Threshold", width=10)
        self.lbl_threshold_mic.pack(side="left", padx=5)

        self.scale_threshold_mic = ttk.Scale(self.f_mic_recording_4, from_=-60.0, to=0.0, orient="horizontal", length=300)
        self.scale_threshold_mic.set(sj.cache["threshold_db_mic"])
        self.scale_threshold_mic.configure(command=self.slider_mic_move)
        self.scale_threshold_mic.bind(
            "<ButtonRelease-1>", lambda e: sj.save_key("threshold_db_mic", float(self.scale_threshold_mic.get()))
        )
        self.scale_threshold_mic.pack(side="left", padx=5)

        self.lbl_threshold_db_mic = ttk.Label(self.f_mic_recording_4, text="0 dB", width=8)
        self.lbl_threshold_db_mic.configure(text=f"{float(sj.cache['threshold_db_mic']):.2f} dB")
        self.lbl_threshold_db_mic.pack(side="left", padx=5)

        # 5
        self.hidden_padder_mic = ttk.Label(self.f_mic_recording_5, text="", width=10)  # hidden padder
        self.hidden_padder_mic.pack(side="left", padx=5)

        self.audiometer_mic = AudioMeter(
            self.f_mic_recording_5, self.master, True, MIN_THRESHOLD, MAX_THRESHOLD, height=30, width=300
        )
        self.audiometer_mic.set_db(MIN_THRESHOLD)
        self.audiometer_mic.pack(side="left", padx=5, fill="x")

        # ------ Speaker
        self.lf_speaker_recording = ttk.LabelFrame(self.f_recording_2_r, text="Speaker")
        self.lf_speaker_recording.pack(side="top", padx=5, fill="both", expand=True)

        self.f_speaker_recording_1 = ttk.Frame(self.lf_speaker_recording)
        self.f_speaker_recording_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_speaker_recording_2 = ttk.Frame(self.lf_speaker_recording)
        self.f_speaker_recording_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_speaker_recording_3 = ttk.Frame(self.lf_speaker_recording)
        self.f_speaker_recording_3.pack(side="top", fill="x", pady=(5, 3), padx=5)

        self.f_speaker_recording_4 = ttk.Frame(self.lf_speaker_recording)
        self.f_speaker_recording_4.pack(side="top", fill="x", pady=(10, 5), padx=5)

        self.f_speaker_recording_5 = ttk.Frame(self.lf_speaker_recording)
        self.f_speaker_recording_5.pack(side="top", fill="x", pady=(0, 5), padx=5)

        # 1
        self.lbl_buffer_speaker = ttk.Label(self.f_speaker_recording_1, text="Max buffer (s)", width=14)
        self.lbl_buffer_speaker.pack(side="left", padx=5)
        self.spn_buffer_speaker = SpinboxNumOnly(
            self.root,
            self.f_speaker_recording_1,
            1,
            30,
            lambda x: sj.save_key("max_buffer_speaker", int(x)),
            initial_value=sj.cache["max_buffer_speaker"]
        )
        self.spn_buffer_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_buffer_speaker, self.spn_buffer_speaker],
            "Set the max buffer (in seconds) for speaker input.\n\nThe longer the buffer, the more time "
            "it will take to transcribe the audio. Not recommended to have very long buffer on low end PC."
            "\n\nDefault value is 10 seconds.",
        )

        self.lbl_hint_buffer_speaker = ttk.Label(self.f_speaker_recording_1, image=bc.help_emoji, compound="left")
        self.lbl_hint_buffer_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_hint_buffer_mic, self.lbl_hint_buffer_speaker],
            "Buffer is the recorded audio that is kept in memory before being transcribed. "
            'Each buffer will act as "one sentence". So if max buffer is 10 seconds, '
            "the words that are in those 10 seconds is the sentence. ",
            wrapLength=400,
        )

        # 2
        self.lbl_max_sentences_speaker = ttk.Label(self.f_speaker_recording_2, text="Max Sentences", width=14)
        self.lbl_max_sentences_speaker.pack(side="left", padx=5)
        self.spn_max_sentences_speaker = SpinboxNumOnly(
            self.root,
            self.f_speaker_recording_2,
            1,
            100,
            lambda x: sj.save_key("max_sentences_speaker", int(x)),
            initial_value=sj.cache["max_sentences_speaker"]
        )
        self.spn_max_sentences_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_max_sentences_speaker, self.spn_max_sentences_speaker],
            "Set max number of sentences, \n\nOne sentence equals one buffer. "
            "So if max buffer is 10 seconds, the words that are in those 10 seconds is the sentence."
            "\n\nDefault value is 5.",
        )

        # 3
        self.cbtn_threshold_enable_speaker = CustomCheckButton(
            self.f_speaker_recording_3,
            sj.cache["threshold_enable_speaker"],
            lambda x: sj.save_key("threshold_enable_speaker", x) or self.toggle_enable_threshold_speaker(),
            text="Enable threshold",
            style="Switch.TCheckbutton"
        )
        self.cbtn_threshold_enable_speaker.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_threshold_enable_speaker,
            "If checked, input will need to reach the threshold before it is considered as an input."
            "\n\nDefault is checked",
        )

        self.cbtn_threshold_auto_speaker = CustomCheckButton(
            self.f_speaker_recording_3,
            sj.cache["threshold_auto_speaker"],
            lambda x: sj.save_key("threshold_auto_speaker", x) or self.toggle_auto_threshold_speaker(),
            text="Auto",
            style="Switch.TCheckbutton"
        )
        self.cbtn_threshold_auto_speaker.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_threshold_auto_speaker,
            "Wether to use VAD or manual threshold for the speaker input.\n\nDefault is checked"
        )

        self.cbtn_auto_break_buffer_speaker = CustomCheckButton(
            self.f_speaker_recording_3,
            sj.cache["auto_break_buffer_speaker"],
            lambda x: sj.save_key("auto_break_buffer_speaker", x),
            text="Break buffer on silence",
            style="Switch.TCheckbutton"
        )
        self.cbtn_auto_break_buffer_speaker.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_auto_break_buffer_speaker,
            "If checked, the buffer will be stopped and considered as 1 full sentence when there is silence detected for more than 1 second. "
            "This could help in reducing the background noise."
            "\n\nDefault is checked",
        )

        self.lbl_hint_threshold_speaker = ttk.Label(self.f_speaker_recording_3, image=bc.help_emoji, compound="left")
        self.lbl_hint_threshold_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_hint_threshold_mic, self.lbl_hint_threshold_speaker],
            "Threshold is the minimum volume level that is needed for the audio to be recorded. "
            "If set correctly might help to reduce background noise.\n\n"
            "The bar below is the audio meter. The green bar is the current volume level "
            "and the red line is the threshold level.\n\n"
            "If you set threshold to auto, you won't see the red line. "
            "Instead you will see only green bar when the audio is loud enough to be recorded.\n\n"
            "If threshold is not auto, there will be a red line. If the green bar is above the red line, "
            "it means that the audio is loud enough to be recorded.",
            wrapLength=400,
        )

        # 4
        # vad for auto
        self.lbl_sensitivity_speaker = ttk.Label(self.f_speaker_recording_4, text="Filter Noise", width=10)
        self.lbl_sensitivity_speaker.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_sensitivity_speaker,
            "Set the sensitivity level for the voice activity detection (VAD). 0 is the least aggressive in filtering out"
            " non-speech while 3 is the most aggressive"
            "\n\nDefault value is 2.",
        )

        self.var_sensitivity_speaker = IntVar()
        self.radio_vad_speaker_1 = ttk.Radiobutton(
            self.f_speaker_recording_4, text="1", value=1, variable=self.var_sensitivity_speaker
        )
        self.radio_vad_speaker_1.pack(side="left", padx=5)
        self.radio_vad_speaker_2 = ttk.Radiobutton(
            self.f_speaker_recording_4, text="2", value=2, variable=self.var_sensitivity_speaker
        )
        self.radio_vad_speaker_2.pack(side="left", padx=5)
        self.radio_vad_speaker_3 = ttk.Radiobutton(
            self.f_speaker_recording_4, text="3", value=3, variable=self.var_sensitivity_speaker
        )
        self.radio_vad_speaker_3.pack(side="left", padx=5)

        temp_map = {1: self.radio_vad_speaker_1, 2: self.radio_vad_speaker_2, 3: self.radio_vad_speaker_3}
        cbtn_invoker(sj.cache["threshold_auto_speaker"], temp_map[sj.cache["threshold_auto_mode_speaker"]])
        self.vad_speaker.set_mode(sj.cache["threshold_auto_mode_speaker"])

        self.radio_vad_speaker_1.configure(
            command=lambda: sj.save_key("threshold_auto_mode_speaker", 1) or self.vad_speaker.set_mode(1)
        )
        self.radio_vad_speaker_2.configure(
            command=lambda: sj.save_key("threshold_auto_mode_speaker", 2) or self.vad_speaker.set_mode(2)
        )
        self.radio_vad_speaker_3.configure(
            command=lambda: sj.save_key("threshold_auto_mode_speaker", 3) or self.vad_speaker.set_mode(3)
        )

        # threshold for manual
        self.lbl_threshold_speaker = ttk.Label(self.f_speaker_recording_4, text="Threshold", width=10)
        self.lbl_threshold_speaker.pack(side="left", padx=5)

        self.scale_threshold_speaker = ttk.Scale(
            self.f_speaker_recording_4, from_=-60.0, to=0.0, orient="horizontal", length=300
        )
        self.scale_threshold_speaker.set(sj.cache["threshold_db_speaker"])
        self.scale_threshold_speaker.configure(command=self.slider_speaker_move)
        self.scale_threshold_speaker.bind(
            "<ButtonRelease-1>", lambda e: sj.save_key("threshold_db_speaker", float(self.scale_threshold_speaker.get()))
        )
        self.scale_threshold_speaker.pack(side="left", padx=5)

        self.lbl_threshold_db_speaker = ttk.Label(self.f_speaker_recording_4, text="0 dB", width=8)
        self.lbl_threshold_db_speaker.configure(text=f"{float(sj.cache['threshold_db_speaker']):.2f} dB")
        self.lbl_threshold_db_speaker.pack(side="left", padx=5)

        # 5
        self.hidden_padder_speaker = ttk.Label(self.f_speaker_recording_5, text="", width=10)  # hidden padder
        self.hidden_padder_speaker.pack(side="left", padx=5)

        self.audiometer_speaker = AudioMeter(
            self.f_speaker_recording_5, self.master, True, MIN_THRESHOLD, MAX_THRESHOLD, height=30, width=300
        )
        self.audiometer_speaker.pack(side="left", padx=5, fill="x")

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
            wrapLength=400,
        )

        # --------------------------
        self.init_setting_once()

    # ------------------ Functions ------------------
    def init_setting_once(self):
        """Initialize the setting once"""
        # disable
        windows_os_only(
            [
                self.lbl_sr_speaker, self.cb_sr_speaker, self.lbl_channels_speaker, self.cb_channels_speaker,
                self.lbl_chunk_size_speaker, self.cb_chunk_size_speaker, self.cbtn_auto_sr_speaker,
                self.cbtn_auto_channels_speaker, self.lbl_hint_buffer_speaker, self.lbl_buffer_speaker,
                self.spn_buffer_speaker, self.lbl_max_sentences_speaker, self.spn_max_sentences_speaker,
                self.cbtn_threshold_enable_speaker, self.cbtn_threshold_auto_speaker, self.cbtn_auto_break_buffer_speaker,
                self.lbl_hint_threshold_speaker, self.scale_threshold_speaker
            ]
        )

        # toggle
        self.toggle_sr("mic", self.cbtn_auto_sr_mic.instate(["selected"]))
        self.toggle_channels("mic", self.cbtn_auto_channels_mic.instate(["selected"]))
        self.toggle_sr("speaker", self.cbtn_auto_sr_speaker.instate(["selected"]))
        self.toggle_channels("speaker", self.cbtn_auto_channels_speaker.instate(["selected"]))
        self.toggle_use_temp(self.radio_temp_file.instate(["selected"]))

        self.toggle_enable_threshold_mic(False)  # not open on start
        self.toggle_enable_threshold_speaker(False)  # not open on start
        self.on_start = False

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

    def toggle_sr(self, device: Literal["mic", "speaker"], auto: bool) -> None:
        """
        Toggle sr spinner disabled or not depending on auto value
        """
        if device == "mic":
            self.cb_sr_mic.toggle_disable(auto)
        elif device == "speaker":
            self.cb_sr_speaker.toggle_disable(auto)

    def toggle_channels(self, device: Literal["mic", "speaker"], auto: bool) -> None:
        """
        Toggle channels spinner disabled or not depending on auto value
        """
        if device == "mic":
            self.cb_channels_mic.toggle_disable(auto)
        elif device == "speaker":
            self.cb_channels_speaker.toggle_disable(auto)

    def call_both_with_wait(self, open=True):
        if self.on_start:
            return

        if not sj.cache["show_audio_visualizer_in_setting"]:
            self.close_meter_mic()
        else:
            mic = Thread(target=self.call_set_meter_mic, daemon=True, args=[open])
            mic.start()
            mic.join()

        if system() == "Windows":
            # for some reason, if the speaker is called right after the mic, it will not work properly
            # it will fail to catch any loopback and will crash the program completely
            # so we wait for 1 second to prevent error
            sleep(1)

            if not sj.cache["show_audio_visualizer_in_setting"]:
                self.close_meter_speaker()
            else:
                speaker = Thread(target=self.call_set_meter_speaker, daemon=True, args=[open])
                speaker.start()
                speaker.join()

    # ---- Mic & Speaker ----
    def slider_mic_move(self, event):
        """
        When the slider is moved, change the threshold value and save it to the settings
        """
        self.lbl_threshold_db_mic.configure(text=f"{float(event):.2f} dB")
        self.audiometer_mic.set_threshold(float(event))

    def slider_speaker_move(self, event):
        """
        When the slider is moved, change the threshold value and save it to the settings
        """
        if system() != "Windows":
            return

        self.lbl_threshold_db_speaker.configure(text=f"{float(event):.2f} dB")
        self.audiometer_speaker.set_threshold(float(event))

    def mic_meter(self, in_data, frame_count, time_info, status):
        """
        Start the mic meter
        """
        assert self.detail_mic is not None
        resampled = resample_sr(in_data, self.detail_mic["sample_rate"], WHISPER_SR)
        db = get_db(in_data)
        self.audiometer_mic.set_db(db)

        if db > self.max_mic:
            self.max_mic = db
            self.audiometer_mic.max = db
        elif db < self.min_mic:
            self.min_mic = db
            self.audiometer_mic.min = db

        if sj.cache["threshold_auto_mic"]:
            self.audiometer_mic.set_recording(get_speech(resampled, WHISPER_SR, self.frame_duration_mic, self.vad_mic))

        return (in_data, pyaudio.paContinue)

    def speaker_meter(self, in_data, frame_count, time_info, status):
        """
        Start the speaker meter
        """
        assert self.detail_speaker is not None
        resampled = resample_sr(in_data, self.detail_speaker["sample_rate"], WHISPER_SR)
        db = get_db(in_data)
        self.audiometer_speaker.set_db(db)

        if db > self.max_speaker:
            self.max_speaker = db
            self.audiometer_speaker.max = db
        elif db < self.min_speaker:
            self.min_speaker = db
            self.audiometer_speaker.min = db

        if sj.cache["threshold_auto_speaker"]:
            self.audiometer_speaker.set_recording(
                get_speech(resampled, WHISPER_SR, self.frame_duration_speaker, self.vad_speaker)
            )

        return (in_data, pyaudio.paContinue)

    def call_set_meter_mic(self, open=True):
        if self.on_start:
            return

        if not sj.cache["show_audio_visualizer_in_setting"]:
            self.close_meter_mic()
            return

        Thread(target=self.set_meter_mic, daemon=True, args=[open]).start()

    def close_meter_mic(self):
        self.audiometer_mic.stop()
        try:
            if self.stream_mic:
                self.stream_mic.stop_stream()
                self.stream_mic.close()
                self.stream_mic = None

            if self.p_mic:
                self.p_mic.terminate()
                self.p_mic = None
        except Exception as e:
            logger.exception(e)

    def set_meter_mic(self, open=True):
        try:
            self.hidden_padder_mic.configure(text="", width=10, foreground="black")
            # must be enable and not in auto mode
            if open and sj.cache["threshold_enable_mic"]:
                self.f_mic_recording_4.pack(side="top", fill="x", pady=(10, 5), padx=5)
                self.f_mic_recording_5.pack(side="top", fill="x", pady=(0, 5), padx=5)
                self.audiometer_mic.pack(side="left", padx=5)

                self.max_mic = MAX_THRESHOLD
                self.min_mic = MIN_THRESHOLD
                self.p_mic = pyaudio.PyAudio()
                self.audiometer_mic.set_threshold(sj.cache["threshold_db_mic"])
                logger.debug("getting mic device details")
                success, detail = get_device_details("mic", sj, self.p_mic)
                if success:
                    self.detail_mic = detail
                else:
                    raise Exception("Failed to get mic device details")

                logger.debug(f"mic detail: {self.detail_mic}")

                self.frame_duration_mic = get_frame_duration(self.detail_mic["sample_rate"], self.detail_mic["chunk_size"])
                self.stream_mic = self.p_mic.open(
                    format=pyaudio.paInt16,
                    channels=get_channel_int(self.detail_mic["num_of_channels"]),
                    rate=self.detail_mic["sample_rate"],
                    input=True,
                    frames_per_buffer=self.detail_mic["chunk_size"],
                    input_device_index=self.detail_mic["device_detail"]["index"],  # type: ignore
                    stream_callback=self.mic_meter,
                )

                self.audiometer_mic.start()
            else:
                # STOP
                self.close_meter_mic()

                self.f_mic_recording_4.pack_forget()
                self.f_mic_recording_5.pack_forget()
                self.audiometer_mic.pack_forget()
        except Exception as e:
            if "main thread is not in main loop" not in str(e):  # on init sometimes it will throw this error
                logger.exception(e)

            # fail because probably no device
            self.close_meter_mic()

            # ddont show the meter, show failed message
            try:
                self.audiometer_mic.pack_forget()
                self.hidden_padder_mic.configure(text="Fail to load device. Check log", width=30, foreground="red")
            except Exception as e:
                pass

    def call_set_meter_speaker(self, open=True):
        if system() == "Windows" and not self.on_start:
            if not sj.cache["show_audio_visualizer_in_setting"]:
                self.close_meter_speaker()
                return

            Thread(target=self.set_meter_speaker, daemon=True, args=[open]).start()

    def close_meter_speaker(self):
        if system() != "Windows":
            return
        self.audiometer_speaker.stop()
        try:
            if self.stream_speaker:
                self.stream_speaker.stop_stream()
                self.stream_speaker.close()
                self.stream_speaker = None

            if self.p_speaker:
                self.p_speaker.terminate()
                self.p_speaker = None
        except Exception as e:
            logger.exception(e)

    def set_meter_speaker(self, open=True):
        if system() != "Windows":
            return

        try:
            self.hidden_padder_speaker.configure(text="", width=10, foreground="black")
            # must be enable and not in auto mode
            if open and sj.cache["threshold_enable_speaker"]:
                self.f_speaker_recording_4.pack(side="top", fill="x", pady=(10, 5), padx=5)
                self.f_speaker_recording_5.pack(side="top", fill="x", pady=(0, 5), padx=5)
                self.audiometer_speaker.pack(side="left", padx=5)

                self.max_speaker = MAX_THRESHOLD
                self.min_speaker = MIN_THRESHOLD
                self.p_speaker = pyaudio.PyAudio()
                self.audiometer_speaker.set_threshold(sj.cache["threshold_db_speaker"])
                success, detail = get_device_details("speaker", sj, self.p_speaker)
                if success:
                    self.detail_speaker = detail
                else:
                    raise Exception("Failed to get speaker device details")

                self.frame_duration_speaker = get_frame_duration(
                    self.detail_speaker["sample_rate"], self.detail_speaker["chunk_size"]
                )
                self.stream_speaker = self.p_speaker.open(
                    format=pyaudio.paInt16,
                    channels=get_channel_int(self.detail_speaker["num_of_channels"]),
                    rate=self.detail_speaker["sample_rate"],
                    input=True,
                    frames_per_buffer=self.detail_speaker["chunk_size"],
                    input_device_index=self.detail_speaker["device_detail"]["index"],  # type: ignore
                    stream_callback=self.speaker_meter,
                )
                self.stream_speaker.start_stream()
                self.audiometer_speaker.start()
            else:
                # STOP
                self.close_meter_speaker()

                self.f_speaker_recording_4.pack_forget()
                self.f_speaker_recording_5.pack_forget()
                self.audiometer_speaker.pack_forget()
        except Exception as e:
            if "main thread is not in main loop" not in str(e):  # on init sometimes it will throw this error
                logger.exception(e)

            self.close_meter_speaker()

            # dont show the meter, show failed message
            try:
                self.audiometer_speaker.pack_forget()
                self.hidden_padder_speaker.configure(text="Fail to load device. Check log", width=30, foreground="red")
            except Exception as e:
                pass

    def toggle_enable_threshold_mic(self, open=True):
        if "selected" in self.cbtn_threshold_enable_mic.state():
            self.cbtn_threshold_auto_mic.configure(state="normal")
            self.cbtn_auto_break_buffer_mic.configure(state="normal")
            self.toggle_auto_threshold_mic()
            self.call_set_meter_mic(open)
        else:
            self.cbtn_threshold_auto_mic.configure(state="disabled")
            self.cbtn_auto_break_buffer_mic.configure(state="disabled")
            self.toggle_auto_threshold_mic()
            self.call_set_meter_mic(False)

    def toggle_enable_threshold_speaker(self, open=True):
        if system() != "Windows":
            return

        if "selected" in self.cbtn_threshold_enable_speaker.state():
            self.cbtn_threshold_auto_speaker.configure(state="normal")
            self.cbtn_auto_break_buffer_speaker.configure(state="normal")
            self.toggle_auto_threshold_speaker()
            self.call_set_meter_speaker(open)
        else:
            self.cbtn_threshold_auto_speaker.configure(state="disabled")
            self.cbtn_auto_break_buffer_speaker.configure(state="disabled")
            self.toggle_auto_threshold_speaker()
            self.call_set_meter_speaker(False)

    def toggle_auto_threshold_mic(self):
        if "selected" in self.cbtn_threshold_auto_mic.state():
            self.audiometer_mic.set_auto(True)
            self.audiometer_mic.configure(height=10)

            self.lbl_threshold_mic.pack_forget()
            self.scale_threshold_mic.pack_forget()
            self.lbl_threshold_db_mic.pack_forget()

            self.lbl_sensitivity_microphone.pack(side="left", padx=5)
            self.radio_vad_mic_1.pack(side="left", padx=5)
            self.radio_vad_mic_2.pack(side="left", padx=5)
            self.radio_vad_mic_3.pack(side="left", padx=5)
        else:
            self.audiometer_mic.set_auto(False)
            self.lbl_threshold_db_mic.configure(text=f"{float(sj.cache['threshold_db_mic']):.2f} dB")
            self.audiometer_mic.configure(height=30)

            self.lbl_sensitivity_microphone.pack_forget()
            self.radio_vad_mic_1.pack_forget()
            self.radio_vad_mic_2.pack_forget()
            self.radio_vad_mic_3.pack_forget()

            self.lbl_threshold_mic.pack(side="left", padx=5)
            self.scale_threshold_mic.pack(side="left", padx=5)
            self.lbl_threshold_db_mic.pack(side="left", padx=5)

    def toggle_auto_threshold_speaker(self):
        pass
        if system() != "Windows":
            return

        if "selected" in self.cbtn_threshold_auto_speaker.state():
            self.audiometer_speaker.set_auto(True)
            self.audiometer_speaker.configure(height=10)
            self.scale_threshold_speaker.configure(state="disabled")

            self.lbl_threshold_speaker.pack_forget()
            self.scale_threshold_speaker.pack_forget()
            self.lbl_threshold_db_speaker.pack_forget()

            self.lbl_sensitivity_speaker.pack(side="left", padx=5)
            self.radio_vad_speaker_1.pack(side="left", padx=5)
            self.radio_vad_speaker_2.pack(side="left", padx=5)
            self.radio_vad_speaker_3.pack(side="left", padx=5)
        else:
            self.audiometer_speaker.set_auto(False)
            self.audiometer_speaker.configure(height=30)
            self.scale_threshold_speaker.configure(state="normal")
            self.lbl_threshold_db_speaker.configure(text=f"{float(sj.cache['threshold_db_speaker']):.2f} dB")

            self.lbl_sensitivity_speaker.pack_forget()
            self.radio_vad_speaker_1.pack_forget()
            self.radio_vad_speaker_2.pack_forget()
            self.radio_vad_speaker_3.pack_forget()

            self.lbl_threshold_speaker.pack(side="left", padx=5)
            self.scale_threshold_speaker.pack(side="left", padx=5)
            self.lbl_threshold_db_speaker.pack(side="left", padx=5)
