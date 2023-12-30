from platform import system
from typing import Literal

from loguru import logger

if system() == "Windows":
    import pyaudiowpatch as pyaudio  # type: ignore # pylint: disable=import-error
else:
    import pyaudio  # type: ignore # pylint: disable=import-error


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
            logger.exception(e)
            logger.warning("No input device found. Ignore this if you dont have a mic.")
            default_device = "No input device found."
        else:
            logger.exception(e)
            logger.error("Something went wrong while trying to get the default input device (mic).")
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
        if "object has no attribute" not in str(e):
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
        logger.exception(e)
        logger.error("Something went wrong while trying to get the default host api.")
        default_host_api = str(e)
    except Exception as e:
        logger.exception(e)
        logger.error("Something went wrong while trying to get the default host api.")
        default_host_api = str(e)
    finally:
        p.terminate()

    return sucess, default_host_api
