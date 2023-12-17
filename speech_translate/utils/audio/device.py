# pylint: disable=deprecated-module
from audioop import rms as calculate_rms
from io import BytesIO
from platform import system
from typing import Literal
from wave import Wave_read, Wave_write
from wave import open as w_open

import numpy as np
import torch
from loguru import logger
from numpy import float32, frombuffer, int16, log10
from scipy.signal import butter, filtfilt, resample_poly
from webrtcvad import Vad

from speech_translate._constants import WHISPER_SR

if system() == "Windows":
    import pyaudiowpatch as pyaudio  # type: ignore # pylint: disable=import-error
else:
    import pyaudio  # type: ignore # pylint: disable=import-error


class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, _bytes, timestamp, duration):
        self.bytes = _bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate, get_only_first_frame=False):
    """Generates audio frames from PCM audio data.

    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.

    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n
        if get_only_first_frame:
            break


def resample_sr(data: bytes, sample_rate: int, target_sample_rate: int) -> bytes:
    """
    This function resamples the audio data from a given sample rate to a target sample rate.
    The function is used when the sample rate of the audio is not 16kHz.

    If by chance the sample rate is already 16kHz, the function will return the original audio data.

    Parameters
    ----------
    data : bytes
        chunk of audio data from pyaudio input stream in bytes
    sample_rate : int
        sample rate of the audio data
    target_sample_rate : int
        target sample rate

    Returns
    -------
    bytes
    """
    if sample_rate == target_sample_rate:
        return data

    audio_as_np_int16 = frombuffer(data, dtype=int16)  # read as numpy array of int16
    audio_as_np_float32 = audio_as_np_int16.astype(float32)  # convert to float32

    # Filter the audio with a anti aliasing filter
    nyquist = 0.5 * sample_rate  # nyquist frequency / folding frequency
    cutoff = 0.9 * nyquist  # Adjust the cutoff frequency as needed

    # Use a butterworth filter with order of 4
    filter_order = 4
    b, a = butter(filter_order, cutoff / nyquist, btype='lowpass')

    # Filter the audio using filtfilt (zero-phase filtering)
    filtered_audio = filtfilt(b, a, audio_as_np_float32)

    # Resample the filtered audio with zero-padding
    resampled = resample_poly(filtered_audio, target_sample_rate, sample_rate, window=('kaiser', 5.0))

    return resampled.astype(int16).tobytes()  # convert back to int16 and bytes


def get_db(audio_data: bytes) -> float:
    """Get the db value of the audio data.

    Parameters
    ----------
    audio_data : bytes
        chunk of audio data from pyaudio input stream in bytes

    Returns
    -------
    float
        db value of the audio data
    """
    rms: float = calculate_rms(audio_data, 2) / 32767
    if rms == 0.0:
        return 0.0
    else:
        return 20 * log10(rms)  # convert to db


def get_speech_webrtc(
    data: bytes, sample_rate: int, frame_duration_ms: int, vad: Vad, get_only_first_frame: bool = True
) -> bool:
    frames = list(frame_generator(frame_duration_ms, data, sample_rate, get_only_first_frame=get_only_first_frame))
    data_to_check = data if len(frames) == 0 else frames[0].bytes
    is_speech: bool = vad.is_speech(data_to_check, sample_rate)
    return is_speech


def to_silero(sound_bytes: bytes, num_of_channels: int, samp_width: int = 2):
    """Converts a byte array to a 32-bit float tensor.

    Parameters
    ----------
    sound_bytes : byte array
        A byte array representing a sound file.
    num_of_channels : int
        The number of channels in the sound file.
    samp_width : int, optional
        The sample width of the sound file, by default 2 (16-bit)

    Returns
    -------
    torch tensor
        A tensor representing the sound file data.
    """
    if num_of_channels == 1:
        audio_as_np_int16 = np.frombuffer(sound_bytes, dtype=np.int16).flatten()
        abs_max = np.abs(audio_as_np_int16).max()
        np_buf = audio_as_np_int16.astype('float32')
        if abs_max > 0:
            np_buf *= 1 / abs_max
    else:
        # need to make temp in memory to make sure the audio will be read properly
        wf = BytesIO()
        wav_writer: Wave_write = w_open(wf, "wb")
        wav_writer.setframerate(WHISPER_SR)
        wav_writer.setsampwidth(samp_width)
        wav_writer.setnchannels(num_of_channels)
        wav_writer.writeframes(sound_bytes)
        wav_writer.close()
        wf.seek(0)

        wav_reader: Wave_read = w_open(wf)
        samples = wav_reader.getnframes()
        audio_bytes = wav_reader.readframes(samples)

        audio_as_np_int16 = np.frombuffer(audio_bytes, dtype=np.int16).flatten()
        audio_as_np_float32 = audio_as_np_int16.astype(np.float32)
        chunk_length = len(audio_as_np_float32) / num_of_channels
        audio_reshaped = np.reshape(audio_as_np_float32, (int(chunk_length), num_of_channels))
        np_buf = audio_reshaped[:, 0] / np.iinfo(np.int16).max  # take left channel only

    torch_float32 = torch.from_numpy(np_buf.squeeze())
    return torch_float32


def get_frame_duration(sample_rate: int, chunk_size: int) -> int:
    """
    Get the frame duration to be used in the frame generator.
    Value return is either 10, 20, or 30 ms.

    Parameters
    ----------
    sample_rate : int
        sample rate of the audio data
    chunk_size : int
        chunk size of the audio data

    Returns
    -------
    int
        frame duration in ms
    """
    ms_per_read = int((chunk_size / sample_rate) * 1000)

    if ms_per_read >= 30:
        return 30
    elif ms_per_read >= 20:
        return 20
    else:
        return 10


def get_channel_int(channel_string: str):
    if channel_string.isdigit():
        return int(channel_string)
    elif channel_string.lower() == "mono":
        return 1
    elif channel_string.lower() == "stereo":
        return 2
    else:
        raise ValueError("Invalid channel string")


def get_device_details(device_type: Literal["speaker", "mic"], sj, p: pyaudio.PyAudio, debug: bool = True):
    """
    Function to get the device detail, chunk size, sample rate, and number of channels.

    Parameters
    ----
    deviceType: "mic" | "speaker"
        Device type
    sj: dict
        setting object
    p: pyaudio.PyAudio
        PyAudio object

    Returns
    ----
    bool
        True if success, False if failed
    dict
        device detail, chunk size, sample rate, and number of channels
    """
    try:
        device = sj.cache[device_type]

        # get the id in device string [ID: deviceIndex,hostIndex]
        device_id = device.split("[ID: ")[1]  # first get the id bracket
        device_id = device_id.split("]")[0]  # then get the id
        device_index = device_id.split(",")[0]
        host_index = device_id.split(",")[1]

        device_detail = p.get_device_info_by_host_api_device_index(int(device_index), int(host_index))
        if device_type == "speaker":
            # device_detail = p.get_wasapi_loopback_analogue_by_dict(device_detail)
            if not device_detail["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():  # type: ignore
                    # Try to find loopback device with same name(and [Loopback suffix]).
                    if device_detail["name"] in loopback["name"]:
                        device_detail = loopback
                        break
                else:
                    logger.error("Fail to find loopback device with same name.")
                    return False, {
                        "device_detail": {},
                        "chunk_size": 0,
                        "sample_rate": 0,
                        "num_of_channels": 0,
                    }

        chunk_size = int(sj.cache[f"chunk_size_{device_type}"])
        if sj.cache[f"auto_sample_rate_{device_type}"]:
            sample_rate = int(device_detail["defaultSampleRate"])
        else:
            sample_rate = int(sj.cache[f"sample_rate_{device_type}"])

        if sj.cache[f"auto_channels_{device_type}"]:
            num_of_channels = str(device_detail["maxInputChannels"])
        else:
            num_of_channels = str(sj.cache[f"channels_{device_type}"])

        num_of_channels = get_channel_int(num_of_channels)

        if debug:
            logger.debug(f"Device: ({device_detail['index']}) {device_detail['name']}" \
                f"Sample Rate {sample_rate} | channels {num_of_channels} | chunk size {chunk_size}" \
                f"Actual device detail: {device_detail}")

        return True, {
            "device_detail": device_detail,
            "chunk_size": chunk_size,
            "sample_rate": sample_rate,
            "num_of_channels": num_of_channels,
        }
    except Exception as e:
        logger.error(f"Something went wrong while trying to get the {device_type} device details.")
        logger.exception(e)
        return False, {
            "device_detail": {},
            "chunk_size": 0,
            "sample_rate": 0,
            "num_of_channels": 0,
        }


def get_input_devices(host_api: str):
    """
    Get the input devices (mic) from the specified hostAPI.
    """
    devices = []
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_host_api_count()):
            current_api_info = p.get_host_api_info_by_index(i)
            # This will ccheck hostAPI parameter
            # If it is empty, get all devices. If specified, get only the devices from the specified hostAPI
            if (host_api == current_api_info["name"]) or (host_api == ""):
                for j in range(int(current_api_info["deviceCount"])):
                    device = p.get_device_info_by_host_api_device_index(i, j)  # get device info by host api device index
                    if int(device["maxInputChannels"]) > 0:
                        devices.append(f"[ID: {i},{j}] | {device['name']}")  # j is the device index in the host api

        if len(devices) == 0:  # check if input empty or not
            devices = ["[WARNING] No input devices found."]
    except Exception as e:
        logger.error("Something went wrong while trying to get the input devices (mic).")
        logger.exception(e)
        devices = ["[ERROR] Check the terminal/log for more information."]
    finally:
        p.terminate()

    return devices


def get_output_devices(host_api: str):
    """
    Get the output devices (speaker) from the specified hostAPI.
    """
    devices = []
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_host_api_count()):
            current_api_info = p.get_host_api_info_by_index(i)
            # This will check hostAPI parameter
            # If it is empty, get all devices. If specified, get only the devices from the specified hostAPI
            if (host_api == current_api_info["name"]) or (host_api == ""):
                for j in range(int(current_api_info["deviceCount"])):
                    device = p.get_device_info_by_host_api_device_index(i, j)  # get device info by host api device index
                    if int(device["maxOutputChannels"]) > 0:
                        devices.append(f"[ID: {i},{j}] | {device['name']}")  # j is the device index in the host api

        if len(devices) == 0:  # check if input empty or not
            devices = ["[WARNING] No ouput devices (speaker) found."]
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
    host_apis = []
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_host_api_count()):
            current_api_info = p.get_host_api_info_by_index(i)
            host_apis.append(f"{current_api_info['name']}")

        if len(host_apis) == 0:  # check if input empty or not
            host_apis = ["[WARNING] No host apis found."]
    except Exception as e:
        logger.error("Something went wrong while trying to get the host apis.")
        logger.exception(e)
        host_apis = ["[ERROR] Check the terminal/log for more information."]
    finally:
        p.terminate()

    return host_apis


def get_default_input_device():
    """Get the default input device (mic).

    Returns
    -------
    bool
        True if success, False if failed
    str | dict
        Default input device detail. If failed, return the error message (str).
    """
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
    """Get the default output device (mic).

    Returns
    -------
    bool
        True if success, False if failed
    str | dict
        Default output device detail. If failed, return the error message (str).
    """
    p = pyaudio.PyAudio()
    sucess = False
    default_device = None
    try:
        # Get default WASAPI info
        default_device = p.get_default_wasapi_loopback()  # type: ignore
        sucess = True
    except OSError as e:
        logger.exception(e)
        logger.error("Looks like WASAPI is not available on the system.")
        default_device = "Looks like WASAPI is not available on the system."
    except Exception as e:
        if "AttributeError: 'PyAudio' object has no attribute 'get_default_wasapi_loopback'" not in str(e):
            logger.exception(e)
            logger.error("Something went wrong while trying to get the default output device (speaker).")
            default_device = str(e)
        else:
            logger.exception(e)
            logger.error("Speaker as input is not available on the system.")
            default_device = "Speaker as input is not available on the system."
    finally:
        p.terminate()

    return sucess, default_device


def get_default_host_api():
    """Get the default host api.

    Returns
    -------
    bool
        True if success, False if failed
    str | dict
        Default host api detail. If failed, return the error message (str).
    """
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
