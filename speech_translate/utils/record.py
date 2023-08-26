import io
import math
import os
import platform
import threading
import ast
import shlex
import numpy
import tkinter as tk
import time as t
from tkinter import ttk, filedialog
from textwrap import wrap
from datetime import datetime, timedelta
from time import sleep, time
from typing import Literal, List, Union, Dict

import whisper_timestamped as whisper
import audioop
import wave

if platform.system() == "Windows":
    import pyaudiowpatch as pyaudio
else:
    import pyaudio  # type: ignore

from speech_translate._path import app_icon
from speech_translate.globals import dir_temp, sj, gc, dir_export
from speech_translate.custom_logging import logger
from speech_translate.components.custom.label import LabelTitleText
from speech_translate.components.custom.message import mbox

from .helper import cbtn_invoker, nativeNotify, start_file, filename_only
from .helper_whisper import (
    get_temperature,
    convert_str_options_to_dict,
    whisper_result_to_srt,
    srt_whisper_to_txt_format,
    srt_whisper_to_txt_format_stamps,
    txt_to_srt_whisper_format_stamps,
    append_dot_en,
)
from .translator import google_tl, libre_tl, memory_tl


def get_input_devices(hostAPI: str):
    """
    Get the input devices (mic) from the specified hostAPI.
    Format: [ID: {device['index']}] | {device['name']}
    """
    devices = []
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_host_api_count()):
            current_api_info = p.get_host_api_info_by_index(i)
            if (hostAPI == current_api_info["name"]) or (
                hostAPI == ""
            ):  # if hostAPI is empty, get all devices. else, get only the devices from the specified hostAPI
                for j in range(int(current_api_info["deviceCount"])):
                    device = p.get_device_info_by_host_api_device_index(i, j)  # get device info by host api device index
                    if int(device["maxInputChannels"]) > 0:
                        devices.append(f"[ID: {i},{j}] | {device['name']}")  # j is the device index in the host api

        # check if input empty or not
        if len(devices) == 0:
            devices = ["[ERROR] No input devices found."]
    except Exception as e:
        logger.error("Something went wrong while trying to get the input devices (mic).")
        logger.exception(e)
        devices = ["[ERROR] Check the terminal/log for more information."]
    finally:
        p.terminate()
        return devices


def get_output_devices(hostAPI: str):
    """
    Get the output devices (speaker) from the specified hostAPI.
    Format: [ID: {device['index']}] | {device['name']}
    """
    devices = []
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_host_api_count()):
            current_api_info = p.get_host_api_info_by_index(i)
            if (hostAPI == current_api_info["name"]) or (
                hostAPI == ""
            ):  # if hostAPI is empty, get all devices. else, get only the devices from the specified hostAPI
                for j in range(int(current_api_info["deviceCount"])):
                    device = p.get_device_info_by_host_api_device_index(i, j)  # get device info by host api device index
                    if int(device["maxOutputChannels"]) > 0:
                        devices.append(f"[ID: {i},{j}] | {device['name']}")  # j is the device index in the host api

        # check if input empty or not
        if len(devices) == 0:
            devices = ["[ERROR] No ouput devices (speaker) found."]
    except Exception as e:
        logger.error("Something went wrong while trying to get the output devices (speaker).")
        logger.exception(e)
        devices = ["[ERROR] Check the terminal/log for more information."]
    finally:
        p.terminate()
        return devices


def get_host_apis():
    """
    Get the host apis from the system.
    """
    apis = []
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_host_api_count()):
            current_api_info = p.get_host_api_info_by_index(i)
            apis.append(f"{current_api_info['name']}")

        # check if input empty or not
        if len(apis) == 0:
            apis = ["[ERROR] No host apis found."]
    except Exception as e:
        logger.error("Something went wrong while trying to get the host apis.")
        logger.exception(e)
        apis = ["[ERROR] Check the terminal/log for more information."]
    finally:
        p.terminate()
        return apis


def get_default_input_device():
    p = pyaudio.PyAudio()
    sucess = False
    default_device = None
    try:
        default_device = p.get_default_input_device_info()
        sucess = True
    except Exception as e:
        if "Error querying device -1" in str(e):
            logger.warning("No input device found. Ignore this if you dont have a mic. Err details below:")
            logger.exception(e)
            default_device = "No input device found."
        else:
            logger.error("Something went wrong while trying to get the default input device (mic).")
            logger.exception(e)
            default_device = str(e)
    finally:
        p.terminate()
        return sucess, default_device


def get_default_output_device():
    p = pyaudio.PyAudio()
    sucess = False
    default_device = None
    try:
        # Get default WASAPI info
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_device = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])  # type: ignore
        sucess = True
    except OSError as e:
        logger.error("Looks like WASAPI is not available on the system.")
        logger.exception(e)
        default_device = "Looks like WASAPI is not available on the system."
    finally:
        p.terminate()
        return sucess, default_device


def get_default_host_api():
    p = pyaudio.PyAudio()
    sucess = False
    default_host_api = None
    try:
        default_host_api = p.get_default_host_api_info()
        sucess = True
    except OSError as e:
        logger.error("Something went wrong while trying to get the default host api.")
        logger.exception(e)
        default_host_api = str(e)
    finally:
        p.terminate()
        return sucess, default_host_api


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
    logger.debug(f"Segments:")
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

        logger.debug(f"Words:")
        for index, words in enumerate(segment["words"]):
            logger.debug(f"Word {index}")
            logger.debug(f"Text: {words['text']}")
            logger.debug(f"Start: {words['start']}")
            logger.debug(f"End: {words['end']}")
            logger.debug(f"Confidence: {words['confidence']}")


# --------------------------------------------------------------------------------------------------------------------------------------
def getDeviceAverageThreshold(deviceType: Literal["mic", "speaker"], duration: int = 5) -> float:
    """
    Function to get the average threshold of the device.

    Parameters
    ----
    deviceType: "mic" | "speaker"
        Device type
    duration: int
        Duration of recording in seconds

    Returns
    ----
    float
        Average threshold of the device
    """
    p = pyaudio.PyAudio()

    if deviceType == "speaker":
        device = sj.cache["speaker"]

        # get the id in [ID: deviceIndex,hostIndex]
        id = device.split("[ID: ")[1]  # first get the id bracket
        id = id.split("]")[0]  # then get the id
        deviceIndex = id.split(",")[0]
        hostIndex = id.split(",")[1]

        # Get device detail
        device_detail = p.get_device_info_by_host_api_device_index(int(deviceIndex), int(hostIndex))

        if not device_detail["isLoopbackDevice"]:
            for loopback in p.get_loopback_device_info_generator():  # type: ignore
                """
                Try to find loopback device with same name(and [Loopback suffix]).
                Unfortunately, this is the most adequate way at the moment.
                """
                if device_detail["name"] in loopback["name"]:
                    device_detail = loopback
                    break
            else:
                # raise exception
                raise Exception("Loopback device not found")

        # speaker will automatically use the max sample rate and channels, because it won't work if not set like this
        num_of_channels = int(device_detail["maxInputChannels"])
        sample_rate = int(device_detail["defaultSampleRate"])
    else:
        device = sj.cache["mic"]

        # get the id in [ID: deviceIndex,hostIndex]
        id = device.split("[ID: ")[1]  # first get the id bracket
        id = id.split("]")[0]  # then get the id
        deviceIndex = id.split(",")[0]
        hostIndex = id.split(",")[1]

        # Get device detail
        device_detail = p.get_device_info_by_host_api_device_index(int(deviceIndex), int(hostIndex))

        sample_rate = sj.cache["sample_rate"]
        num_of_channels = 1

        # check if user set auto for sample rate and channels
        if sj.cache["auto_sample_rate"]:
            sample_rate = int(device_detail["defaultSampleRate"])
        if sj.cache["auto_channels_value"]:
            num_of_channels = int(device_detail["maxInputChannels"])
            if num_of_channels == 0:
                num_of_channels = 1

    logger.debug(f"Device: ({device_detail['index']}) {device_detail['name']}")
    logger.debug(f"Sample Rate {sample_rate} | channels {num_of_channels}")
    logger.debug(device_detail)

    # get data from device using pyaudio
    data = b""

    def callback(in_data, frame_count, time_info, status):
        nonlocal data
        data += in_data
        return (in_data, pyaudio.paContinue)

    chunk_size = sj.cache["chunk_size"]
    stream = p.open(
        format=pyaudio.paInt16,  # 16 bit audio
        channels=num_of_channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk_size,
        input_device_index=int(device_detail["index"]),
        stream_callback=callback,
    )

    stream.start_stream()

    while stream.is_active():
        sleep(0.1)
        if len(data) > sample_rate * duration * 2:
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

    # get average threshold
    # we use rms to get the "loudness" of the audio
    avg_threshold = audioop.rms(data, 2) + 200  # add 200 to make sure it is above average

    # Set the reference level based on the maximum amplitude for 16-bit audio
    reference = 32767

    # Calculate the dB value
    db = 20 * math.log10(avg_threshold / reference)

    logger.debug(f"Average threshold energy: {avg_threshold}")
    logger.debug(f"Average threshold in dB: {db}")

    return avg_threshold


# --------------------------------------------------------------------------------------------------------------------------------------
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
    root = tk.Toplevel(master)
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

    lbl_buffer = LabelTitleText(frame_lbl_3, "Buffer: ", f"0/0 sec")
    lbl_buffer.pack(side="left", fill="x", padx=5, pady=5)

    progress_buffer = ttk.Progressbar(frame_lbl_4, orient="horizontal", length=200, mode="determinate")
    progress_buffer.pack(side="left", fill="x", padx=5, pady=5, expand=True)

    lbl_timer = ttk.Label(frame_lbl_5, text=f"REC: 00:00:00")
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
    except:
        pass

    try:
        src_english = lang_source == "english"
        auto = lang_source == "auto detect"
        whisperEngine = engine == "Whisper"
        modelName = append_dot_en(modelKey, src_english)

        # cannot transcribe concurrently. Will need to wait for the previous transcribe to finish
        if transcribe and whisperEngine:
            gc.tc_lock = threading.Lock()

        # read from settings
        sample_rate = int(sj.cache["sample_rate"])
        chunk_size = int(sj.cache["chunk_size"])
        max_sentences = int(sj.cache["max_sentences"])
        max_int16 = 2**15  # bit depth of 16 bit audio (32768)
        separator = ast.literal_eval(shlex.quote(sj.cache["separate_with"]))

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

        # recording session init
        global prev_tl_text, sentences_tl
        tempList = []
        sentences_tc = []
        sentences_tl = []
        prev_tc_text = ""
        prev_tl_text = ""
        next_transcribe_time = None
        last_sample = bytes()
        transcribe_rate = timedelta(seconds=sj.cache["transcribe_rate"] / 1000)
        max_record_time = int(sj.cache["max_buffer_speaker"]) if speaker else int(sj.cache["max_buffer_mic"])
        # if only translate to english using whisper engine
        task = "translate" if whisperEngine and translate and not transcribe else "transcribe"

        # load model
        model: whisper.Whisper = whisper.load_model(modelName)

        # stop loadbar
        gc.mw.stop_loadBar("mic" if not speaker else "speaker")

        # ----------------- Start recording -----------------
        logger.info("-" * 50)
        logger.info(f"Task: {task}")
        logger.info(f"Modelname: {modelName}")
        logger.info(f"Engine: {engine}")
        logger.info(f"Auto mode: {auto}")
        logger.info(f"Source Languange: {lang_source}")
        if translate:
            logger.info(f"Target Language: {lang_target}")

        # pyaudio
        p = pyaudio.PyAudio()

        if speaker:
            # get the id in [ID: deviceIndex,hostIndex]
            id = device.split("[ID: ")[1]  # first get the id bracket
            id = id.split("]")[0]  # then get the id
            deviceIndex = id.split(",")[0]
            hostIndex = id.split(",")[1]

            # Get device detail
            device_detail = p.get_device_info_by_host_api_device_index(int(deviceIndex), int(hostIndex))

            if not device_detail["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():  # type: ignore
                    """
                    Try to find loopback device with same name(and [Loopback suffix]).
                    Unfortunately, this is the most adequate way at the moment.
                    """
                    if device_detail["name"] in loopback["name"]:
                        device_detail = loopback
                        break
                else:
                    # raise exception
                    raise Exception("Loopback device not found")

            # speaker will automatically use the max sample rate and channels, because it won't work if not set like this
            num_of_channels = int(device_detail["maxInputChannels"])
            sample_rate = int(device_detail["defaultSampleRate"])
        else:
            # get the id in [ID: deviceIndex,hostIndex]
            id = device.split("[ID: ")[1]  # first get the id bracket
            id = id.split("]")[0]  # then get the id
            deviceIndex = id.split(",")[0]
            hostIndex = id.split(",")[1]

            # Get device detail
            device_detail = p.get_device_info_by_host_api_device_index(int(deviceIndex), int(hostIndex))
            num_of_channels = 1

            # check if user set auto for sample rate and channels
            if sj.cache["auto_sample_rate"]:
                sample_rate = int(device_detail["defaultSampleRate"])
            if sj.cache["auto_channels_value"]:
                num_of_channels = int(device_detail["maxInputChannels"])
                if num_of_channels == 0:
                    num_of_channels = 1

        logger.debug(device_detail)
        logger.debug(f"Device: ({device_detail['index']}) {device_detail['name']}")
        logger.debug(f"Sample Rate {sample_rate} | channels {num_of_channels} | chunk size {chunk_size}")

        rec_type = "speaker" if speaker else "mic"
        gc.stream = p.open(
            format=pyaudio.paInt16,  # 16 bit audio
            channels=num_of_channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size,
            input_device_index=int(device_detail["index"]),
        )
        record_thread = threading.Thread(target=realtime_recording_thread, args=[chunk_size, rec_type], daemon=True)
        record_thread.start()

        logger.debug(f"Record Session Started")

        # ----------------- Start modal -----------------
        # window to show progress
        root.title("Recording")

        timerStart = time()
        paused = False
        audio_length_in_seconds = 0
        gc.current_rec_status = f"▶️ Recording"
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
                btn_pause.configure(text="Resume")
                root.title(f"Recording {rec_type} (Paused)")
                gc.current_rec_status = f"⏸️ Paused"
                update_status_lbl()
            else:
                btn_pause.configure(text="Pause")
                root.title(f"Recording {rec_type}")
                update_modal_ui()

        def update_status_lbl():
            lbl_status.configure(text=gc.current_rec_status)

        def update_modal_ui():
            nonlocal timerStart, paused
            if gc.recording:
                if not paused:
                    timer = t.strftime("%H:%M:%S", t.gmtime(time() - timerStart))
                    data_queue_size = gc.data_queue.qsize() * chunk_size / 1024  # approx buffer size in kb

                    lbl_timer.configure(
                        text=f"REC: {timer} | {language if not auto else language.replace('auto detect', f'auto detect ({gc.auto_detected_lang})')}"
                    )
                    lbl_buffer.set_text(
                        f"{round(audio_length_in_seconds, 2)}/{round(max_record_time, 2)} sec ({round(data_queue_size, 2)} kb)"
                    )
                    # update progress / buffer percentage
                    progress_buffer["value"] = audio_length_in_seconds / max_record_time * 100
                    update_status_lbl()

                    root.after(1000, update_modal_ui)

        lbl_sample_rate.set_text(sample_rate)
        lbl_channels.set_text(num_of_channels)
        lbl_chunk_size.set_text(chunk_size)
        lbl_buffer.set_text(f"0/{round(max_record_time, 2)} sec")
        lbl_timer.configure(text=f"REC: 00:00:00 | {language}")
        lbl_status.configure(text="▶️ Recording")
        btn_pause.configure(state="normal", command=toggle_pause)
        btn_stop.configure(state="normal", command=stop_recording)
        update_modal_ui()

        # transcribing thread
        while gc.recording:
            if paused:
                continue

            if not gc.data_queue.empty():
                now = datetime.utcnow()

                # Set next_transcribe_time for the first time.
                if not next_transcribe_time:
                    next_transcribe_time = now + transcribe_rate

                # Run transcription based on transcribe rate that is set by user. The more delay it have the more it will reduces stress on the GPU / CPU (if using cpu).
                # Transcriptions will be more accurate as they go because they will have more audio context to work with (Limit on the audio context or buffer is set in the setting).
                if now > next_transcribe_time:
                    next_transcribe_time = now + transcribe_rate

                    # Getting the stream data from the queue.
                    while not gc.data_queue.empty():
                        data = gc.data_queue.get()
                        last_sample += data

                    # Write out raw frames as a wave file.
                    wav_file = io.BytesIO()
                    wav_writer: wave.Wave_write = wave.open(wav_file, "wb")
                    wav_writer.setframerate(sample_rate)
                    wav_writer.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                    wav_writer.setnchannels(num_of_channels)
                    wav_writer.writeframes(last_sample)  # get the audio data from the buffer.
                    wav_writer.close()

                    # Read the audio data
                    wav_file.seek(0)
                    wav_reader: wave.Wave_read = wave.open(wav_file)
                    samples = wav_reader.getnframes()
                    audio = wav_reader.readframes(samples)
                    wav_reader.close()

                    # DEBUG
                    if sj.cache["debug_realtime_record"] == 1:
                        logger.info(f"Processing Audio")

                    # TODO: FIX this make sure that the conversion is correct so we can use the fast method
                    if num_of_channels > 1:
                        # If not mono, the fast method does not work so we have to resort to using the old, a little slower, but working method
                        # which is to save the audio file and read it directly to the whisper model
                        audio_target = os.path.join(dir_temp, datetime.now().strftime("%Y-%m-%d %H_%M_%S_%f")) + ".wav"
                        tempList.append(audio_target)  # add to the temp list to delete later

                        # block until the file is written
                        timeNow = time()
                        with open(audio_target, "wb") as f:
                            f.write(wav_file.getvalue())  # write it

                        if sj.cache["debug_realtime_record"] == 1:
                            logger.debug(f"File Write Time: {time() - timeNow}")

                        # delete the oldest file if the temp list is too long
                        if len(tempList) > sj.cache["max_temp"] and not sj.cache["keep_temp"]:
                            os.remove(tempList[0])
                            tempList.pop(0)
                    else:
                        # Convert the wave data straight to a numpy array for the model.
                        # https://stackoverflow.com/a/62298670

                        # get audio format and bit depth
                        audio_format = p.get_format_from_width(wav_reader.getsampwidth())

                        audio_as_np_int16 = numpy.frombuffer(audio, dtype=numpy.int16)
                        audio_as_np_float32 = audio_as_np_int16.astype(numpy.float32)
                        audio_target = audio_as_np_float32 / max_int16  # normalized as Numpy array

                    # DEBUG
                    if sj.cache["debug_realtime_record"] == 1:
                        logger.info(f"Transcribing")

                    # Transcribe the audio
                    gc.current_rec_status = "▶️ Recording ⟳ Transcribing"
                    if translate and whisperEngine:
                        assert gc.tc_lock is not None
                        gc.tc_lock.acquire()

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

                    if len(text) > 0 and text != prev_tc_text:
                        prev_tc_text = text
                        if transcribe:
                            if sj.cache["debug_realtime_record"] == 1:
                                logger.info(f"New transcribed text")
                                if sj.cache["verbose"]:
                                    logger.debug(whisper_verbose_log(result))
                                else:
                                    logger.debug(f"{text}")

                            # this works like this:
                            # clear the textbox first, then insert the text. The text inserted is a continuation of the previous text.
                            # the longer it is the clearer the transcribed text will be, because of more context.
                            gc.clearMwTc()
                            gc.clearExTc()
                            toExTc = ""

                            # insert previous sentences if there are any
                            for sentence in sentences_tc:
                                gc.insertMwTbTc(sentence + separator, str(result["language"]))
                                toExTc += sentence + separator

                            # insert the current sentence after previous sentences
                            gc.insertMwTbTc(text + separator, str(result["language"]))
                            toExTc += text + separator
                            gc.insertExTbTc(toExTc, str(result["language"]))

                        if translate:
                            # Start translate thread
                            gc.current_rec_status = "▶️ Recording ⟳ Translating"

                            # Using whisper engine
                            if whisperEngine:
                                tlThread = threading.Thread(
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
                                tlThread = threading.Thread(
                                    target=realtime_tl, args=[text, lang_source, lang_target, engine], daemon=True
                                )
                                tlThread.start()

                    # break up the buffer If we've reached max recording time
                    audio_length_in_seconds = samples / float(sample_rate)
                    if sj.cache["debug_realtime_record"] == 1:
                        logger.debug(f"Audio length: {audio_length_in_seconds}")

                    if audio_length_in_seconds > max_record_time:
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
            logger.debug(f"Record Session ended")

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

            if num_of_channels > 1 and not sj.cache["keep_temp"]:
                gc.current_rec_status = "⚠️ Cleaning up audioFiles"
                update_status_lbl()
                logger.info("Cleaning up audioFiles")
                for audio in tempList:
                    try:
                        os.remove(audio)
                    except FileNotFoundError:
                        pass
                logger.info("Done!")

            gc.current_rec_status = "⏹️ Stopped"
            update_status_lbl()
            gc.mw.after_rec_stop()
            if root.winfo_exists():
                root.destroy()  # close if not destroyed
    except Exception as e:
        logger.error(f"Error in record session")
        logger.exception(e)
        assert gc.mw is not None
        mbox("Error in record session", f"{str(e)}", 2, gc.mw.root)
        gc.mw.rec_stop()
        gc.mw.after_rec_stop()
        if root.winfo_exists():
            root.destroy()  # close if not destroyed


def realtime_recording_thread(chunk_size: int, rec_type: Literal["mic", "speaker"]):
    """Record Audio From stream buffer and save it to a queue"""
    assert gc.stream is not None
    while gc.recording:  # Record in a thread at a fast rate.
        if gc.paused:
            sleep(0.1)
            continue

        data = gc.stream.read(chunk_size)
        gc.current_energy = audioop.rms(data, 2)

        if sj.cache["debug_energy"]:
            logger.debug(f"energy: {gc.current_energy}")

        # store chunks of audio in queue
        if not sj.cache["enable_threshold"]:  # record regardless of energy
            gc.data_queue.put(data)
        elif (
            sj.cache["enable_threshold"] and gc.current_energy > sj.cache[f"{rec_type}_energy_threshold"]
        ):  # only record if energy is above threshold
            gc.data_queue.put(data)


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
        separator = ast.literal_eval(shlex.quote(sj.cache["separate_with"]))

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

        if len(text) > 0 and text != prev_tl_text:
            prev_tl_text = text

            if sj.cache["debug_realtime_record"] == 1:
                logger.debug(f"New translated text (Whisper)")
                if sj.cache["verbose"]:
                    logger.debug(whisper_verbose_log(result))
                else:
                    logger.debug(f"{text}")

            # this works like this:
            # clear the textbox first, then insert the text. The text inserted is a continuation of the previous text.
            # the longer it is the clearer the transcribed text will be, because of more context.
            gc.clearMwTl()
            gc.clearExTl()
            toExTb = ""

            # insert previous sentences if there are any
            for sentence in sentences_tl:
                gc.insertMwTbTl(sentence + separator, str(result["language"]))
                toExTb += sentence + separator

            # insert the current sentence after previous sentences
            gc.insertMwTbTl(text + separator, str(result["language"]))
            toExTb += text + separator
            gc.insertExTbTl(toExTb, str(result["language"]))

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
        separator = ast.literal_eval(shlex.quote(sj.cache["separate_with"]))
        result_Tl = ""
        debug_log = sj.cache["debug_translate"]

        if engine == "Google":
            success, result_Tl = google_tl(text, lang_source, lang_target, debug_log)
            if not success:
                nativeNotify("Error: translation with google failed", result_Tl)

        elif engine == "LibreTranslate":
            success, result_Tl = libre_tl(
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
                nativeNotify("Error: translation with libre failed", result_Tl)

        elif engine == "MyMemoryTranslator":
            success, result_Tl = memory_tl(text, lang_source, lang_target, debug_log)
            if not success:
                nativeNotify("Error: translation with mymemory failed", str(result_Tl))

        result_Tl = result_Tl.strip()
        if len(result_Tl) > 0 and result_Tl != prev_tl_text:
            prev_tl_text = result_Tl
            # this works like this:
            # clear the textbox first, then insert the text. The text inserted is a continuation of the previous text.
            # the longer it is the clearer the transcribed text will be, because of more context.
            gc.clearMwTl()
            gc.clearExTl()
            toExTb = ""

            # insert previous sentences if there are any
            for sentence in sentences_tl:
                gc.insertMwTbTl(sentence + separator, lang_target)
                toExTb += sentence + separator

            # insert the current sentence after previous sentences
            gc.insertMwTbTl(result_Tl + separator, lang_target)
            toExTb += result_Tl + separator
            gc.insertExTbTl(toExTb, lang_target)

    except Exception as e:
        logger.exception(e)
        nativeNotify("Error: translating failed", str(e))
    finally:
        gc.disableTranslating()  # flag processing as done


# --------------------------------------------------------------------------------------------------------------------------------------
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
    This function is cancellable with the cancel flag that is set by the cancel button and will be checked periodically every 0.1 seconds
    If the cancel flag is set, the function will raise an exception to stop the thread

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
    logger.debug(f"Translating...")

    try:
        separator = ast.literal_eval(shlex.quote(sj.cache["separate_with"]))
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]
        save_name = save_name.replace("{task}", "translate")
        save_name = save_name.replace("{task-short}", "tl")

        if engine == "Whisper":
            try:
                # verify audio file exists
                if not os.path.isfile(query):
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

                thread = threading.Thread(target=run_threaded, daemon=True)
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

                with open(os.path.join(export_to, f"{save_name}.txt"), "w", encoding="utf-8") as f:
                    f.write(resultsTxt)

                with open(os.path.join(export_to, f"{save_name}.srt"), "w", encoding="utf-8") as f:
                    f.write(resultSrt)

                gc.insertMwTbTl(
                    f"translated {save_name} and saved to .txt and .srt" + separator, str(result_Tl_whisper["language"])
                )
            else:
                gc.insertMwTbTl(
                    f"Fail to save file {save_name}. It is empty (no text get from transcription)" + separator,
                    str(result_Tl_whisper["language"]),
                )
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

            if sj.cache["proxy_http"] != "" or sj.cache["proxy_https"] != "":
                proxies = {}

                if sj.cache["proxy_http"] != "":
                    proxies["http"] = sj.cache["proxy_http"]

                if sj.cache["proxy_https"] != "":
                    proxies["https"] = sj.cache["proxy_https"]
            else:
                proxies = None

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
                # sended text (toTranslate parameter) is sended in srt format so the result that we got from translation is as srt
                resultSrt = results
                resultTxt = srt_whisper_to_txt_format(resultSrt)  # format it back to txt

                if len(resultSrt) > 0:
                    gc.file_tled_counter += 1
                    save_name_part = f"{save_name}_pt{i + 1}" if len(result_Tl) > 1 else save_name

                    with open(os.path.join(export_to, f"{save_name_part}.txt"), "w", encoding="utf-8") as f:
                        f.write(resultTxt)

                    with open(os.path.join(export_to, f"{save_name_part}.srt"), "w", encoding="utf-8") as f:
                        f.write(resultSrt)

                    gc.insertMwTbTl(f"Translated {save_name_part} and saved to .txt and .srt" + separator, lang_target)
                else:
                    gc.insertMwTbTl(
                        f"Translated file {save_name} is empty (no text get from transcription) so it's not saved"
                        + separator,
                        lang_target,
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
    logger.info(f"Transcribing Audio: {audio_name.split(os.sep)[-1]}")

    # verify audio file exists
    if not os.path.isfile(audio_name):
        logger.warning("Audio file does not exist")
        gc.disableTranslating()
        gc.mw.stop_loadBar()
        return

    try:
        result_Tc = ""
        separator = ast.literal_eval(shlex.quote(sj.cache["separate_with"]))
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

        thread = threading.Thread(target=run_threaded, daemon=True)
        thread.start()

        while thread.is_alive():
            if not gc.transcribing:
                logger.debug("Cancelling transcription")
                raise Exception("Cancelled")
            sleep(0.1)

        result_Tc = gc.data_queue.get()

        # export to file
        audioNameOnly = filename_only(audio_name)
        audioNameOnly = audioNameOnly[:100]  # limit length of file name to 100 characters
        export_to = dir_export if sj.cache["dir_export"] == "auto" else sj.cache["dir_export"]

        # export if transcribe mode is on
        if transcribe:
            resultTxt = result_Tc["text"].strip()

            if len(resultTxt) > 0:
                gc.file_tced_counter += 1
                resultSrt = whisper_result_to_srt(result_Tc)

                with open(os.path.join(export_to, f"{save_name}.txt"), "w", encoding="utf-8") as f:
                    f.write(resultTxt)

                with open(os.path.join(export_to, f"{save_name}.srt"), "w", encoding="utf-8") as f:
                    f.write(resultSrt)

                gc.insertMwTbTc(
                    f"Transcribed File {audioNameOnly} saved to {save_name} .txt and .srt" + separator,
                    str(result_Tc["language"]),
                )
            else:
                gc.insertMwTbTc(
                    f"Transcribed File {audioNameOnly} is empty (no text get from transcription) so it's not saved"
                    + separator,
                    str(result_Tc["language"]),
                )
                logger.warning("Transcribed Text is empty")

        # start translation thread if translate mode is on
        if translate:
            # send result as srt if not using whisper because it will be send to translation API. If using whisper translation will be done using whisper model
            toTranslate = whisper_result_to_srt(result_Tc) if engine != "Whisper" else audio_name
            translateThread = threading.Thread(
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
    root = tk.Toplevel(master)
    root.title("File Import Progress")
    root.transient(master)
    root.geometry("450x225")
    root.protocol("WM_DELETE_WINDOW", lambda: master.state("iconic"))  # minimize window when click close button
    root.geometry("+{}+{}".format(master.winfo_rootx() + 50, master.winfo_rooty() + 50))
    try:
        root.iconbitmap(app_icon)
    except:
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

    lbl_elapsed = LabelTitleText(frame_lbl_4, "Elapsed: ", f"0s")
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
        logger.info(f"Start Process (FILE)")
        gc.file_tced_counter = 0
        gc.file_tled_counter = 0

        src_english = lang_source == "english"
        auto = lang_source == "auto detect"
        whisperEngine = engine == "Whisper"
        model_name = append_dot_en(modelKey, src_english)

        temperature = sj.cache["temperature"]
        whisper_args = sj.cache["whisper_extra_args"]
        export_format: str = sj.cache["export_format"]
        file_slice_start: Union[None, int] = (
            None if sj.cache["file_slice_start"] == "" else int(sj.cache["file_slice_start"])
        )
        file_slice_end: Union[None, int] = None if sj.cache["file_slice_end"] == "" else int(sj.cache["file_slice_end"])

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
                lbl_elapsed.set_text(text=f"{t.strftime('%H:%M:%S', t.gmtime(time() - timerStart))}")

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
                proc_thread = threading.Thread(
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
                proc_thread = threading.Thread(
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
                if transcribe and translate
                else f"Transcribed {gc.file_tced_counter} file(s)"
                if transcribe
                else f"Translated {gc.file_tled_counter} file(s)"
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
