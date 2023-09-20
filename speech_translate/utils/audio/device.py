from audioop import rms as calculate_rms
from math import ceil
from platform import system
from time import sleep, time
from typing import Literal

from numpy import log10

from speech_translate.custom_logging import logger

if system() == "Windows":
    import pyaudiowpatch as pyaudio
else:
    import pyaudio  # type: ignore


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


#TODO: FIX if threshold is already lower than the db, it will not adjust anymore
def auto_threshold(
    db: float,
    threshold: float,
    max: float,
    min: float,
    steps: int,
    recording_start: float,
    optimal: bool,
    recording: bool,
):
    # Check if the db value is above the threshold every 1 second
    if recording:
        if db > threshold:  # still speaking
            recording_start = time()
        else:
            # check again every 1 second wetber still recording or not
            if time() - recording_start > 1:
                # db < threshold = stop recording
                if db < threshold:
                    recording = False
                else:
                    recording_start = time()
                    # still recording? verify again
                    # increase the threshold to make sure that it is not a false positive
                    if optimal and threshold <= max:
                        if abs(abs(threshold) - ceil(abs(db))) > steps:
                            time()
                            prev = threshold
                            threshold += steps
                            # make sure that it is not a false positive
                            if threshold > db:
                                threshold = prev - steps

    else:
        # recording is false, check if db > threshold
        if db > threshold:
            # Start recording
            recording_start = time()
            recording = True
        else:
            # db < threshold = not picking up voice
            # adjust threshold
            if optimal and threshold >= min:
                if abs(abs(threshold) - abs(db)) > steps + 2:  # meaning steps + 2 away from the db
                    time()
                    prev = threshold
                    threshold -= steps
                    # make sure that it is not a false negative
                    if threshold < db:
                        threshold = prev + steps

    # Adjust the max min if needed
    if db < min:
        min = db
    elif db > max:
        max = db

    # first time
    # go until optimal
    if not optimal:
        # not speaking
        if db < threshold:
            # adjust threshold until near db
            if threshold >= min:
                if abs(abs(threshold) - ceil(abs(db))) > steps:
                    threshold -= steps
                else:
                    optimal = True

        # speaking
        elif db > threshold:
            # adjust threshold until near db
            if threshold <= max:
                if abs(abs(threshold) - abs(db)) > steps + 2:
                    threshold += steps  # increse
                else:
                    optimal = True

    return (threshold, max, min, recording_start, optimal, recording)


def get_device_average_threshold(device_type: Literal["mic", "speaker"], sj, duration: int = 5) -> float:
    """
    Function to get the average threshold of the device.

    Parameters
    ----
    deviceType: "mic" | "speaker"
        Device type
    sj: dict
        setting object
    duration: int
        Duration of recording in seconds

    Returns
    ----
    float
        Average threshold of the device
    """
    p = pyaudio.PyAudio()

    success, detail = get_device_details(device_type, sj, p)
    if not success:
        return 0

    # get data from device using pyaudio
    audio_data = b""

    def callback(in_data, frame_count, time_info, status):
        nonlocal audio_data
        audio_data += in_data
        return (in_data, pyaudio.paContinue)

    stream = p.open(
        format=pyaudio.paInt16,  # 16 bit audio
        channels=detail["num_of_channels"],
        rate=detail["sample_rate"],
        input=True,
        frames_per_buffer=detail["chunk_size"],
        input_device_index=int(detail["device_detail"]["index"]),
        stream_callback=callback,
    )

    # start recording
    stream.start_stream()

    sleep(duration)  # wait for 5 seconds

    stream.stop_stream()  # end
    stream.close()
    p.terminate()

    # get average threshold using RMS
    db = get_db(audio_data)

    return db


def get_device_details(device_type: Literal["speaker", "mic"], sj, p: pyaudio.PyAudio):
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
        id = device.split("[ID: ")[1]  # first get the id bracket
        id = id.split("]")[0]  # then get the id
        deviceIndex = id.split(",")[0]
        hostIndex = id.split(",")[1]

        device_detail = p.get_device_info_by_host_api_device_index(int(deviceIndex), int(hostIndex))
        if device_type == "speaker":
            device_detail = p.get_wasapi_loopback_analogue_by_dict(device_detail)  # type: ignore

        chunk_size = int(sj.cache[f"chunk_size_{device_type}"])
        if sj.cache[f"auto_sample_rate_{device_type}"]:
            sample_rate = int(device_detail["defaultSampleRate"])
        else:
            sample_rate = int(sj.cache[f"sample_rate_{device_type}"])

        if sj.cache[f"auto_channels_{device_type}"]:
            num_of_channels = int(device_detail["maxInputChannels"])
        else:
            num_of_channels = int(sj.cache[f"channels_{device_type}"])

        logger.debug(f"Device: ({device_detail['index']}) {device_detail['name']}")
        logger.debug(f"Sample Rate {sample_rate} | channels {num_of_channels} | chunk size {chunk_size}")
        logger.debug("Actual device detail:")
        logger.debug(device_detail)

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


def get_input_devices(hostAPI: str):
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
            if (hostAPI == current_api_info["name"]) or (hostAPI == ""):
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


def get_output_devices(hostAPI: str):
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
            if (hostAPI == current_api_info["name"]) or (hostAPI == ""):
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
    apis = []
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_host_api_count()):
            current_api_info = p.get_host_api_info_by_index(i)
            apis.append(f"{current_api_info['name']}")

        if len(apis) == 0:  # check if input empty or not
            apis = ["[WARNING] No host apis found."]
    except Exception as e:
        logger.error("Something went wrong while trying to get the host apis.")
        logger.exception(e)
        apis = ["[ERROR] Check the terminal/log for more information."]
    finally:
        p.terminate()
        return apis


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
        logger.error("Looks like WASAPI is not available on the system.")
        logger.exception(e)
        default_device = "Looks like WASAPI is not available on the system."
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
