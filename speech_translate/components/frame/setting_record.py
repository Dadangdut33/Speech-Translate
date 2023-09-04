import platform
import threading
import tkinter as tk
import numpy as np
from tkinter import ttk
from typing import Literal, Union

from speech_translate.globals import sj
from speech_translate.utils.helper import (
    max_number_float,
    number_only,
    max_number,
    cbtn_invoker,
    emoji_img,
    number_only_float,
    windows_os_only,
)
from speech_translate.utils.record import getDeviceAverageThreshold

from speech_translate.components.custom.countdown import CountdownWindow
from speech_translate.components.custom.message import mbox
from speech_translate.components.custom.tooltip import tk_tooltips, tk_tooltip


class SettingRecord:
    """
    Record tab in setting window.
    """

    def __init__(self, root: tk.Toplevel, master_frame: Union[ttk.Frame, tk.Frame]):
        self.root = root
        self.master = master_frame
        self.getting_threshold = False
        self.help_emoji = emoji_img(16, "❓")

        # ------------------ Record  ------------------
        self.lf_device = tk.LabelFrame(self.master, text="• Device Parameters")
        self.lf_device.pack(side="top", fill="x", padx=5, pady=5)

        self.f_device_1 = ttk.Frame(self.lf_device)
        self.f_device_1.pack(side="top", fill="x", pady=5, padx=5)

        self.lf_recording = tk.LabelFrame(self.master, text="• Recording Options")
        self.lf_recording.pack(side="top", fill="x", padx=5, pady=5)

        self.f_recording_1 = ttk.Frame(self.lf_recording)
        self.f_recording_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_recording_2 = ttk.Frame(self.lf_recording)
        self.f_recording_2.pack(side="top", fill="x", pady=5, padx=5)

        self.lf_result = tk.LabelFrame(self.master, text="• Result")
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
        self.spn_sr_mic = ttk.Spinbox(
            self.f_mic_device_1,
            from_=8_000,
            to=384_000,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
        )
        self.spn_sr_mic.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_sr_mic,
                8000,
                48000,
                lambda: sj.save_key("sample_rate_mic", int(self.spn_sr_mic.get())),
            ),
        )
        self.spn_sr_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_sr_mic, self.spn_sr_mic],
            "Set the sample rate for the audio recording. \n\nDefault value is 16000.",
        )

        self.lbl_chunk_size_mic = ttk.Label(self.f_mic_device_1, text="Chunk Size", width=14)
        self.lbl_chunk_size_mic.pack(side="left", padx=5)
        self.spn_chunk_size_mic = ttk.Spinbox(
            self.f_mic_device_1,
            from_=512,
            to=65536,
            validate="key",
            width=15,
            validatecommand=(self.root.register(number_only), "%P"),
        )
        self.spn_chunk_size_mic.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_chunk_size_mic,
                512,
                65536,
                lambda: sj.save_key("chunk_size_mic", int(self.spn_chunk_size_mic.get())),
            ),
        )
        self.spn_chunk_size_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_chunk_size_mic, self.spn_chunk_size_mic],
            "Set the chunk size for the audio recording. The lower it is, the more resources it will use."
            "\n\nDefault value is 1024.",
        )

        # 2
        self.lbl_channels_mic = ttk.Label(self.f_mic_device_2, text="Channels", width=14)
        self.lbl_channels_mic.pack(side="left", padx=5)
        self.spn_channels_mic = ttk.Spinbox(
            self.f_mic_device_2,
            from_=1,
            to=25,  # not sure what the limit is but we will just settle with 25
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
        )
        self.spn_channels_mic.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_channels_mic,
                1,
                25,
                lambda: sj.save_key("channels_mic", int(self.spn_channels_mic.get())),
            ),
        )
        self.spn_channels_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.spn_channels_mic, self.lbl_channels_mic],
            "Set the channels for the audio recording. \n\nDefault value is 1.",
        )

        # 3
        self.cbtn_auto_sr_mic = ttk.Checkbutton(self.f_mic_device_3, text="Auto sample rate", style="Switch.TCheckbutton")
        self.cbtn_auto_sr_mic.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_auto_sr_mic,
            "If checked, the sample rate will be automatically set based on the device's sample rate."
            "\n\nCheck this option if you are having issues.\n\nDefault is checked",
            wrapLength=400,
        )

        self.cbtn_auto_channels_mic = ttk.Checkbutton(
            self.f_mic_device_3, text="Auto channels value", style="Switch.TCheckbutton"
        )
        self.cbtn_auto_channels_mic.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_auto_channels_mic,
            "If checked, the channels value will be automatically set based on the device's channels amount."
            "\n\nCheck this option if you are having issues.\n\nDefault is checked",
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
        self.spn_sr_speaker = ttk.Spinbox(
            self.f_speaker_device_1,
            from_=8_000,
            to=384_000,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
        )
        self.spn_sr_speaker.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_sr_speaker,
                8000,
                48000,
                lambda: sj.save_key("sample_rate_speaker", int(self.spn_sr_speaker.get())),
            ),
        )
        self.spn_sr_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_sr_speaker, self.spn_sr_speaker],
            "Set the sample rate for the audio recording. \n\nDefault value is 41000.",
        )

        self.lbl_chunk_size_speaker = ttk.Label(self.f_speaker_device_1, text="Chunk Size", width=14)
        self.lbl_chunk_size_speaker.pack(side="left", padx=5)
        self.spn_chunk_size_speaker = ttk.Spinbox(
            self.f_speaker_device_1,
            from_=512,
            to=65536,
            validate="key",
            width=15,
            validatecommand=(self.root.register(number_only), "%P"),
        )
        self.spn_chunk_size_speaker.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_chunk_size_speaker,
                512,
                65536,
                lambda: sj.save_key("chunk_size_speaker", int(self.spn_chunk_size_speaker.get())),
            ),
        )
        self.spn_chunk_size_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_chunk_size_speaker, self.spn_chunk_size_speaker],
            "Set the chunk size for the audio recording. The lower it is, the more resources it will use."
            "\n\nDefault value is 1024.",
        )

        # 2
        self.lbl_channels_speaker = ttk.Label(self.f_speaker_device_2, text="Channels", width=14)
        self.lbl_channels_speaker.pack(side="left", padx=5)
        self.spn_channels_speaker = ttk.Spinbox(
            self.f_speaker_device_2, from_=1, to=25, validate="key", validatecommand=(self.root.register(number_only), "%P")
        )
        self.spn_channels_speaker.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_channels_speaker,
                1,
                25,
                lambda: sj.save_key("channels_speaker", int(self.spn_channels_speaker.get())),
            ),
        )
        self.spn_channels_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_channels_speaker, self.spn_channels_speaker],
            "Set the channels for the audio recording. \n\nDefault value is 2.",
        )

        # 3
        self.cbtn_auto_sr_speaker = ttk.Checkbutton(
            self.f_speaker_device_3, text="Auto sample rate", style="Switch.TCheckbutton"
        )
        self.cbtn_auto_sr_speaker.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_auto_sr_speaker,
            "If checked, the sample rate will be automatically set based on the device's sample rate."
            "\n\nCheck this option if you are having issues.\n\nDefault is checked",
            wrapLength=400,
        )

        self.cbtn_auto_channels_speaker = ttk.Checkbutton(
            self.f_speaker_device_3, text="Auto channels value", style="Switch.TCheckbutton"
        )
        self.cbtn_auto_channels_speaker.pack(side="left", padx=5)
        tk_tooltip(
            self.cbtn_auto_channels_speaker,
            "If checked, the channels value will be automatically set based on the device's channels amount."
            "\n\nCheck this option if you are having issues.\n\nDefault is checked",
            wrapLength=400,
        )

        # ------------------ Recording ------------------
        # ----- temp
        self.lf_temp = ttk.LabelFrame(self.f_recording_1, text="Temporary Files")
        self.lf_temp.pack(side="left", padx=5, fill="x", expand=True)

        self.f_temp_1 = ttk.Frame(self.lf_temp)
        self.f_temp_1.pack(side="top", fill="x", pady=5, padx=5)

        self.lbl_max_temp = ttk.Label(self.f_temp_1, text="Max Temp Files", width=14)
        self.lbl_max_temp.pack(side="left", padx=5, pady=5)
        self.spn_max_temp = ttk.Spinbox(
            self.f_temp_1, from_=50, to=1000, validate="key", validatecommand=(self.root.register(number_only), "%P")
        )
        self.spn_max_temp.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_max_temp,
                50,
                1000,
                lambda: sj.save_key("max_temp", int(self.spn_max_temp.get())),
            ),
        )
        self.spn_max_temp.pack(side="left", padx=5, pady=5)
        tk_tooltips(
            [self.spn_max_temp, self.lbl_max_temp],
            "Set max number of temporary files kept when recording from device that is not mono.\n\nDefault value is 200.",
        )

        self.cbtn_keep_temp = ttk.Checkbutton(self.f_temp_1, text="Keep temp files", style="Switch.TCheckbutton")
        self.cbtn_keep_temp.pack(side="left", padx=5, pady=5)
        tk_tooltip(
            self.cbtn_keep_temp,
            "If checked, will not delete temporary audio file that might be created by the program."
            "\n\nDefault value is unchecked.",
        )

        # ------ Mic
        self.lf_mic_recording = ttk.LabelFrame(self.f_recording_2, text="Microphone")
        self.lf_mic_recording.pack(side="left", padx=5, fill="x", expand=True)

        self.f_mic_recording_1 = ttk.Frame(self.lf_mic_recording)
        self.f_mic_recording_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_mic_recording_2 = ttk.Frame(self.lf_mic_recording)
        self.f_mic_recording_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_mic_recording_3 = ttk.Frame(self.lf_mic_recording)
        self.f_mic_recording_3.pack(side="top", fill="x", pady=5, padx=5)

        self.f_mic_recording_4 = ttk.Frame(self.lf_mic_recording)
        self.f_mic_recording_4.pack(side="top", fill="x", pady=5, padx=5)

        # 1
        self.lbl_buffer_mic = ttk.Label(self.f_mic_recording_1, text="Max buffer (s)", width=14)
        self.lbl_buffer_mic.pack(side="left", padx=5)
        self.spn_buffer_mic = ttk.Spinbox(
            self.f_mic_recording_1, from_=3, to=300, validate="key", validatecommand=(self.root.register(number_only), "%P")
        )
        self.spn_buffer_mic.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_buffer_mic,
                3,
                300,
                lambda: sj.save_key("max_buffer_mic", int(self.spn_buffer_mic.get())),
            ),
        )
        self.spn_buffer_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_buffer_mic, self.spn_buffer_mic],
            "Set the max buffer (in seconds) for microphone input.\n\nThe longer the buffer, the more time "
            "it will take to transcribe the audio. Not recommended to have very long buffer on low end PC."
            "\n\nDefault value is 10 seconds.",
        )

        self.lbl_hint_buffer_mic = ttk.Label(self.f_mic_recording_1, image=self.help_emoji, compound="left")
        self.lbl_hint_buffer_mic.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_hint_buffer_mic,
            "Max buffer is the maximum continous recording time. After it is reached buffer will be reset."
            "\n\nTips: Lower the buffer if your transcribe rate is low for a faster and more accurate result.",
        )

        # 2
        self.lbl_max_sentences_mic = ttk.Label(self.f_mic_recording_2, text="Max Sentences", width=14)
        self.lbl_max_sentences_mic.pack(side="left", padx=5)
        self.spn_max_sentences_mic = ttk.Spinbox(
            self.f_mic_recording_2, from_=1, to=250, validate="key", validatecommand=(self.root.register(number_only), "%P")
        )
        self.spn_max_sentences_mic.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_max_sentences_mic,
                1,
                30,
                lambda: sj.save_key("max_sentences_mic", int(self.spn_max_sentences_mic.get())),
            ),
        )
        self.spn_max_sentences_mic.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_max_sentences_mic, self.spn_max_sentences_mic],
            "Set max number of sentences kept between each buffer reset.\n\nOne sentence equals one max buffer. "
            "So if max buffer is 30 seconds, the words that are in those 30 seconds is the sentence."
            "\n\nDefault value is 5.",
        )

        # 3
        self.lbl_threshold_mic = ttk.Label(self.f_mic_recording_3, text="Threshold", width=14)
        self.lbl_threshold_mic.pack(side="left", padx=5)
        self.spn_threshold_mic = ttk.Spinbox(
            self.f_mic_recording_3,
            from_=0,
            to=100000,
            validate="key",
            validatecommand=(self.root.register(number_only_float), "%P"),
            width=12,
        )
        self.spn_threshold_mic.bind(
            "<KeyRelease>",
            lambda e: max_number_float(
                self.root,
                self.spn_threshold_mic,
                0,
                100000,
                lambda: sj.save_key("threshold_db_mic", float(self.spn_threshold_mic.get())),
            ),
        )
        self.spn_threshold_mic.pack(side="left", padx=5)

        self.btn_auto_threshold_mic = ttk.Button(
            self.f_mic_recording_3,
            text="Auto",
            command=lambda: self.mic_auto_threshold(),
            width=5,
        )
        self.btn_auto_threshold_mic.pack(side="left", padx=5)
        tk_tooltip(
            self.btn_auto_threshold_mic,
            "Try to auto calculate the mic threshold value. \n\n*Might not be accurate.",
        )

        self.lbl_hint_threshold_mic = ttk.Label(self.f_mic_recording_3, image=self.help_emoji, compound="left")
        self.lbl_hint_threshold_mic.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_hint_threshold_mic,
            "Minimum threshold is the minimum volume level that is needed for the audio to be recorded. "
            "If set correctly might help to reduce background noise.",
        )

        # 4
        self.cbtn_threshold_enable_mic = ttk.Checkbutton(
            self.f_mic_recording_4, text="Enable threshold", style="Switch.TCheckbutton"
        )
        self.cbtn_threshold_enable_mic.pack(side="left", padx=5, pady=2)

        # ------ Speaker
        self.lf_speaker_recording = ttk.LabelFrame(self.f_recording_2, text="Speaker")
        self.lf_speaker_recording.pack(side="left", padx=5, fill="x", expand=True)

        self.f_speaker_recording_1 = ttk.Frame(self.lf_speaker_recording)
        self.f_speaker_recording_1.pack(side="top", fill="x", pady=5, padx=5)

        self.f_speaker_recording_2 = ttk.Frame(self.lf_speaker_recording)
        self.f_speaker_recording_2.pack(side="top", fill="x", pady=5, padx=5)

        self.f_speaker_recording_3 = ttk.Frame(self.lf_speaker_recording)
        self.f_speaker_recording_3.pack(side="top", fill="x", pady=5, padx=5)

        self.f_speaker_recording_4 = ttk.Frame(self.lf_speaker_recording)
        self.f_speaker_recording_4.pack(side="top", fill="x", pady=5, padx=5)

        # 1
        self.lbl_buffer_speaker = ttk.Label(self.f_speaker_recording_1, text="Max buffer (s)", width=14)
        self.lbl_buffer_speaker.pack(side="left", padx=5)
        self.spn_buffer_speaker = ttk.Spinbox(
            self.f_speaker_recording_1,
            from_=3,
            to=300,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
        )
        self.spn_buffer_speaker.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_buffer_speaker,
                3,
                300,
                lambda: sj.save_key("max_buffer_speaker", int(self.spn_buffer_speaker.get())),
            ),
        )
        self.spn_buffer_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_buffer_speaker, self.spn_buffer_speaker],
            "Set the max buffer (in seconds) for speaker input.\n\nThe longer the buffer, the more time it will"
            "take to transcribe the audio. Not recommended to have very long buffer on low end PC."
            "\n\nDefault value is 10 seconds.\n\n*This Setting is only for Windows OS.",
        )

        self.lbl_hint_buffer_speaker = ttk.Label(self.f_speaker_recording_1, image=self.help_emoji, compound="left")
        self.lbl_hint_buffer_speaker.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_hint_buffer_speaker,
            "Max buffer is the maximum continous recording time. After it is reached buffer will be reset."
            "\n\nTips: Lower the buffer if your transcribe rate is low for a faster and more accurate result.",
        )

        # 2
        self.lbl_max_sentences_speaker = ttk.Label(self.f_speaker_recording_2, text="Max Sentences", width=14)
        self.lbl_max_sentences_speaker.pack(side="left", padx=5)
        self.spn_max_sentences_speaker = ttk.Spinbox(
            self.f_speaker_recording_2,
            from_=1,
            to=250,
            validate="key",
            validatecommand=(self.root.register(number_only), "%P"),
        )
        self.spn_max_sentences_speaker.bind(
            "<KeyRelease>",
            lambda e: max_number(
                self.root,
                self.spn_max_sentences_speaker,
                1,
                30,
                lambda: sj.save_key("max_sentences_speaker", int(self.spn_max_sentences_speaker.get())),
            ),
        )
        self.spn_max_sentences_speaker.pack(side="left", padx=5)
        tk_tooltips(
            [self.lbl_max_sentences_speaker, self.spn_max_sentences_speaker],
            "Set max number of sentences kept between each buffer reset.\n\nOne sentence equals one max buffer. "
            "So if max buffer is 30 seconds, the words that are in those 30 seconds is the sentence."
            "\n\nDefault value is 5.\n\n*This Setting is only for Windows OS.",
        )

        # 3
        self.lbl_threshold_speaker = ttk.Label(self.f_speaker_recording_3, text="Threshold", width=14)
        self.lbl_threshold_speaker.pack(side="left", padx=5)
        self.spn_threshold_speaker = ttk.Spinbox(
            self.f_speaker_recording_3,
            from_=0,
            to=100000,
            validate="key",
            validatecommand=(self.root.register(number_only_float), "%P"),
            width=12,
        )
        self.spn_threshold_speaker.bind(
            "<KeyRelease>",
            lambda e: max_number_float(
                self.root,
                self.spn_threshold_speaker,
                0,
                100000,
                lambda: sj.save_key(
                    "threshold_db_speaker",
                    float(self.spn_threshold_speaker.get()),
                ),
            ),
        )
        self.spn_threshold_speaker.pack(side="left", padx=5)

        self.btn_auto_threshold_speaker = ttk.Button(
            self.f_speaker_recording_3,
            text="Auto",
            command=lambda: self.speaker_auto_threshold(),
            width=5,
        )
        self.btn_auto_threshold_speaker.pack(side="left", padx=5)
        tk_tooltip(
            self.btn_auto_threshold_speaker,
            "Try to auto calculate the speaker threshold value. \n\n*Might not be accurate.",
        )

        self.lbl_hint_threshold_speaker = ttk.Label(self.f_speaker_recording_3, image=self.help_emoji, compound="left")
        self.lbl_hint_threshold_speaker.pack(side="left", padx=5)
        tk_tooltip(
            self.lbl_hint_threshold_speaker,
            "Minimum threshold is the minimum volume level that is needed for the audio to be recorded. "
            "If set correctly might help to reduce background noise.",
        )

        # 4
        self.cbtn_threshold_enable_speaker = ttk.Checkbutton(
            self.f_speaker_recording_4, text="Enable threshold", style="Switch.TCheckbutton"
        )
        self.cbtn_threshold_enable_speaker.pack(side="left", padx=5, pady=2)

        # ------------------ Result ------------------
        self.lbl_separator = ttk.Label(self.f_result_1, text="Text Separator", width=14)
        self.lbl_separator.pack(side="left", padx=5)
        self.entry_separator = ttk.Entry(self.f_result_1)
        self.entry_separator.pack(side="left", padx=5, fill="x", expand=True)
        self.entry_separator.bind(
            "<KeyRelease>",
            lambda e: sj.save_key("separate_with", self.entry_separator.get()),
        )
        tk_tooltips(
            [self.entry_separator, self.lbl_separator],
            "Set the separator for text that is transcribed or translated.\n\nDefault value \\n",
            wrapLength=400,
        )

        # --------------------------
        self.init_setting_once()

    # ------------------ Functions ------------------
    def init_setting_once(self):
        # Device pamaeters
        self.spn_sr_mic.set(sj.cache["sample_rate_mic"])
        self.spn_channels_mic.set(sj.cache["channels_mic"])
        self.spn_chunk_size_mic.set(sj.cache["chunk_size_mic"])
        cbtn_invoker(sj.cache["auto_sample_rate_mic"], self.cbtn_auto_sr_mic)
        cbtn_invoker(sj.cache["auto_channels_mic"], self.cbtn_auto_channels_mic)

        self.spn_sr_speaker.set(sj.cache["sample_rate_speaker"])
        self.spn_channels_speaker.set(sj.cache["channels_speaker"])
        self.spn_chunk_size_speaker.set(sj.cache["chunk_size_speaker"])
        cbtn_invoker(sj.cache["auto_sample_rate_speaker"], self.cbtn_auto_sr_speaker)
        cbtn_invoker(sj.cache["auto_channels_speaker"], self.cbtn_auto_channels_speaker)

        # recording options
        self.spn_max_temp.set(sj.cache["max_temp"])
        cbtn_invoker(sj.cache["keep_temp"], self.cbtn_keep_temp)

        self.spn_buffer_mic.set(sj.cache["max_buffer_mic"])
        self.spn_max_sentences_mic.set(sj.cache["max_sentences_mic"])
        self.spn_threshold_mic.set(sj.cache["threshold_db_mic"])
        cbtn_invoker(sj.cache["threshold_enable_mic"], self.cbtn_threshold_enable_mic)

        self.spn_buffer_speaker.set(sj.cache["max_buffer_speaker"])
        self.spn_max_sentences_speaker.set(sj.cache["max_sentences_speaker"])
        self.spn_threshold_speaker.set(sj.cache["threshold_db_speaker"])
        cbtn_invoker(sj.cache["threshold_enable_speaker"], self.cbtn_threshold_enable_speaker)

        # result
        self.entry_separator.delete(0, "end")
        self.entry_separator.insert(0, sj.cache["separate_with"])

        # disable
        windows_os_only(
            [
                self.lbl_sr_speaker,
                self.spn_sr_speaker,
                self.lbl_channels_speaker,
                self.spn_channels_speaker,
                self.lbl_chunk_size_speaker,
                self.spn_chunk_size_speaker,
                self.cbtn_auto_sr_speaker,
                self.cbtn_auto_channels_speaker,
                self.lbl_hint_buffer_speaker,
                self.lbl_buffer_speaker,
                self.spn_buffer_speaker,
                self.lbl_hint_threshold_speaker,
                self.lbl_threshold_speaker,
                self.spn_threshold_speaker,
                self.lbl_max_sentences_speaker,
                self.spn_max_sentences_speaker,
                self.cbtn_threshold_enable_speaker,
                self.btn_auto_threshold_speaker,
            ]
        )

        self.configure_commands()

    def configure_commands(self):
        """
        To prevent the command from being called multiple times, we need to configure the command just once after the setting is initialized
        """
        # Device parameters
        self.spn_sr_mic.configure(command=lambda: sj.save_key("sample_rate_mic", int(self.spn_sr_mic.get())))
        self.spn_channels_mic.configure(command=lambda: sj.save_key("channels_mic", int(self.spn_channels_mic.get())))
        self.spn_chunk_size_mic.configure(command=lambda: sj.save_key("chunk_size_mic", int(self.spn_chunk_size_mic.get())))
        self.cbtn_auto_sr_mic.configure(
            command=lambda: sj.save_key("auto_sample_rate_mic", self.cbtn_auto_sr_mic.instate(["selected"]))
            or self.toggle_sr("mic", self.cbtn_auto_sr_mic.instate(["selected"]))
        )
        self.cbtn_auto_channels_mic.configure(
            command=lambda: sj.save_key("auto_channels_mic", self.cbtn_auto_channels_mic.instate(["selected"]))
            or self.toggle_channels("mic", self.cbtn_auto_channels_mic.instate(["selected"]))
        )

        self.spn_sr_speaker.configure(command=lambda: sj.save_key("sample_rate_speaker", int(self.spn_sr_speaker.get())))
        self.spn_channels_speaker.configure(
            command=lambda: sj.save_key("channels_speaker", int(self.spn_channels_speaker.get()))
        )
        self.spn_chunk_size_speaker.configure(
            command=lambda: sj.save_key("chunk_size_speaker", int(self.spn_chunk_size_speaker.get()))
        )
        self.cbtn_auto_sr_speaker.configure(
            command=lambda: sj.save_key("auto_sample_rate_speaker", self.cbtn_auto_sr_speaker.instate(["selected"]))
            or self.toggle_sr("speaker", self.cbtn_auto_sr_speaker.instate(["selected"]))
        )
        self.cbtn_auto_channels_speaker.configure(
            command=lambda: sj.save_key("auto_channels_speaker", self.cbtn_auto_channels_speaker.instate(["selected"]))
            or self.toggle_channels("speaker", self.cbtn_auto_channels_speaker.instate(["selected"]))
        )

        # recording options
        self.spn_max_temp.configure(command=lambda: sj.save_key("max_temp", int(self.spn_max_temp.get())))
        self.cbtn_keep_temp.configure(command=lambda: sj.save_key("keep_temp", self.cbtn_keep_temp.instate(["selected"])))

        self.spn_buffer_mic.configure(command=lambda: sj.save_key("max_buffer_mic", int(self.spn_buffer_mic.get())))
        self.spn_max_sentences_mic.configure(
            command=lambda: sj.save_key("max_sentences_mic", int(self.spn_max_sentences_mic.get()))
        )
        self.spn_threshold_mic.configure(
            command=lambda: sj.save_key("threshold_db_mic", float(self.spn_threshold_mic.get()))
        )
        self.cbtn_threshold_enable_mic.configure(
            command=lambda: sj.save_key("threshold_enable_mic", self.cbtn_threshold_enable_mic.instate(["selected"]))
        )

        self.spn_buffer_speaker.configure(
            command=lambda: sj.save_key("max_buffer_speaker", int(self.spn_buffer_speaker.get()))
        )
        self.spn_max_sentences_speaker.configure(
            command=lambda: sj.save_key("max_sentences_speaker", int(self.spn_max_sentences_speaker.get()))
        )
        self.spn_threshold_speaker.configure(
            command=lambda: sj.save_key("threshold_db_speaker", float(self.spn_threshold_speaker.get()))
        )
        self.cbtn_threshold_enable_speaker.configure(
            command=lambda: sj.save_key(
                "threshold_enable_speaker",
                self.cbtn_threshold_enable_speaker.instate(["selected"]),
            )
        )

    def toggle_sr(self, device: Literal["mic", "speaker"], auto: bool) -> None:
        """
        Toggle sr spinner disabled or not depending on auto value
        """
        if device == "mic":
            self.spn_sr_mic.configure(state="disabled" if auto else "normal")
        elif device == "speaker":
            self.spn_sr_speaker.configure(state="disabled" if auto else "normal")

    def toggle_channels(self, device: Literal["mic", "speaker"], auto: bool) -> None:
        """
        Toggle channels spinner disabled or not depending on auto value
        """
        if device == "mic":
            self.spn_channels_mic.configure(state="disabled" if auto else "normal")
        elif device == "speaker":
            self.spn_channels_speaker.configure(state="disabled" if auto else "normal")

    def get_the_threshold(self, device: Literal["mic", "speaker"]) -> None:
        self.getting_threshold = True
        threshold = getDeviceAverageThreshold(device)
        if np.isnan(threshold):
            self.getting_threshold = False
            # ask user to try again
            if mbox(
                "Error",
                "Something went wrong while trying to get the threshold. Try again?",
                3,
                self.root,
            ):
                if device == "mic":
                    self.mic_threshold()
                elif device == "speaker":
                    self.speaker_threshold()
                return
            return

        if device == "mic":
            self.spn_threshold_mic.set(float(threshold))
        elif device == "speaker":
            self.spn_threshold_speaker.set(float(threshold))

        sj.save_key(f"threshold_db_{device}", float(threshold))
        self.getting_threshold = False

    def mic_threshold(self):
        # run in thread
        thread = threading.Thread(target=self.get_the_threshold, args=("mic",), daemon=True)
        thread.start()

        # show countdown window and wait for it to close
        CountdownWindow(self.root, 5, "Getting threshold...", "Getting threshold for mic")

    def mic_auto_threshold(self):
        """
        Prompt the user to record for 5 seconds and get the optimal threshold for the mic.
        """
        if self.getting_threshold:
            mbox(
                "Already getting threshold",
                "Please wait until the current threshold is calculated.",
                1,
            )
            return

        if mbox(
            "Auto Threshold - Mic",
            "After you press `yes` the program will record for 5 seconds and try to get the optimal threshold"
            "\n\nTry to keep the device silent to avoid inaccuracy\n\nSelected device: "
            f"{sj.cache['mic']}"
            "\n\n*Press no to cancel",
            3,
            self.root,
        ):
            self.mic_threshold()

    def speaker_threshold(self):
        # run in thread
        thread = threading.Thread(target=self.get_the_threshold, args=("speaker",), daemon=True)
        thread.start()

        # show countdown window and wait for it to close
        CountdownWindow(self.root, 5, "Getting threshold...", "Getting threshold for speaker")

    def speaker_auto_threshold(self):
        """
        Prompt the user to record for 5 seconds and get the optimal threshold for the speaker.
        """
        if platform.system() != "Windows":
            mbox(
                "Not supported",
                "This feature is only supported on Windows",
                1,
            )
            return

        if self.getting_threshold:
            mbox(
                "Already getting threshold",
                "Please wait until the current threshold is calculated.",
                1,
            )
            return

        if mbox(
            "Auto Threshold - Speaker",
            "After you press `yes` the program will record for 5 seconds and try to get the optimal threshold"
            "\n\nTry to keep the device silent to avoid inaccuracy\n\nSelected device: "
            f"{sj.cache['speaker']}"
            "\n\n*Press no to cancel",
            3,
            self.root,
        ):
            self.speaker_threshold()
