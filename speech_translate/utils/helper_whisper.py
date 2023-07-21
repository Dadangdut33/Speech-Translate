import re
from speech_translate.custom_logging import logger

modelSelectDict = {"Tiny (~32x speed)": "tiny", "Base (~16x speed)": "base", "Small (~6x speed)": "small", "Medium (~2x speed)": "medium", "Large (v1) (1x speed)": "large-v1", "Large (v2) (1x speed)": "large-v2"}
modelKeys = list(modelSelectDict.keys())
modelValues = list(modelSelectDict.values())

def append_dot_en(modelKey: str, src_english: bool):
    """
    Append .en to model name if src_english is True and model is not large (large does not have english version)

    Parameters
    ---
    modelKey: str
        The key of the model in modelSelectDict
    src_english: bool
        If the source language is english
    """
    logger.info("Checking model name")
    logger.debug(f"modelKey: {modelKey}, src_english: {src_english}")
    modelName = modelSelectDict[modelKey]
    if "large" not in modelName and src_english:
        modelName = modelName + ".en"

    logger.debug(f"modelName: {modelName}")
    return modelName

def str_to_union_str_list_int(string):
    """
    Convert a string to a Union[str, List[int]] can also be use for iterable of int (in this case the iterable is a list)
    :param string: string to convert
    :return: Union[str, List[int]]
    """
    # If string is a list of int, convert to list of int
    if string[0] == "[" and string[-1] == "]":
        string = string[1:-1]  # remove [ and ]
        string = string.split(",")  # split by ,
        string = [int(x) for x in string]  # convert to int

        return string

    return str(string)


def str_to_bool(string: str):
    """
    Convert a string to a bool
    :param string: string to convert
    :return: bool
    """
    if string.lower() == "true":
        return True
    elif string.lower() == "false":
        return False

    raise ValueError(f"Cannot convert {string} to bool")

def whisper_result_to_srt(result):
    """
    Generate SRT format from Whisper result
    from https://github.com/marferca/yt-whisper-demo/blob/5deef0ee0656cb6df54232c3dc62dbca1e7340c8/utils.py#L42
    """
    text = []
    for i, s in enumerate(result["segments"]):
        text.append(str(i + 1))

        time_start = s["start"]
        hours, minutes, seconds = int(time_start / 3600), (time_start / 60) % 60, (time_start) % 60
        timestamp_start = "%02d:%02d:%06.3f" % (hours, minutes, seconds)
        timestamp_start = timestamp_start.replace(".", ",")
        time_end = s["end"]

        hours, minutes, seconds = int(time_end / 3600), (time_end / 60) % 60, (time_end) % 60
        timestamp_end = "%02d:%02d:%06.3f" % (hours, minutes, seconds)
        timestamp_end = timestamp_end.replace(".", ",")
        text.append(timestamp_start + " --> " + timestamp_end)
        text.append(s["text"].strip() + "\n")

    return "\n".join(text)


def srt_whisper_to_txt_format(srt: str):
    """
    Convert SRT format to text format
    """
    text = []
    for line in srt.splitlines():
        if line.strip().isdigit():
            continue
        if "-->" in line:
            continue
        if line.strip() == "":
            continue
        text.append(line.strip())
    return "\n".join(text)

def srt_whisper_to_txt_format_stamps(srt: str):
    """
    Convert SRT format to text format, and return stamps
    """
    text = []
    stamps = []
    for line in srt.splitlines():
        if line.strip().isdigit():
            continue
        if "-->" in line:
            stamps.append(line)
            continue
        if line.strip() == "":
            continue
        text.append(line.strip())
    return "\n".join(text), stamps

def txt_to_srt_whisper_format_stamps(txt: str, stamps:list[str]):
    """
    Convert text format to SRT format, require list of stamps
    """
    srt = []
    for idx,(line,stamp) in enumerate(zip(txt.splitlines(),stamps)):
        srt.append(str(idx+1))
        srt.append(stamp.strip())
        srt.append(line.strip())
        srt.append("")
    return "\n".join(srt)


decodingDict = {
    "sample_len": int,
    "best_of": int,
    "beam_size": int,
    "patience": float,
    "length_penalty": float,
    "prompt": str_to_union_str_list_int,
    "prefix": str_to_union_str_list_int,
    "suppress_blank": str_to_bool,
    "suppress_tokens": str_to_union_str_list_int,
    "without_timestamps": str_to_bool,
    "max_initial_timestamp": float,
    "fp16": str_to_bool,
}

validDecodingOptions = decodingDict.keys()


def convert_str_options_to_dict(options):
    """
    Convert string options to dict
    :param options: string options
    :return: dict options
    """
    # Options are indicated by --option_name option_value
    # Example: --sample_len 1024
    # capture each option and its value
    result = {}
    success = False
    try:
        options = options.split("--")
        options = [option.strip() for option in options if option.strip() != ""]

        # convert to dict
        for option in options:
            option = option.split(" ")
            param = option[0]
            value = " ".join(option[1:])  # value rest of the string

            if param in validDecodingOptions:
                # add to dict but delete all " ' in value
                val = re.sub(r"['\"]", "", value)
                val = decodingDict[param](val)  # convert values

                result[param] = val

        success = True
    except Exception as e:
        logger.exception(e)
        result = str(e)
    finally:
        return success, result


def get_temperature(args):
    """
    Input must be a string of either a single float number (ex: 0.0) or tuple of floats number separated with commas (ex: 0.2, 0.3, 0.4 ...).
    """
    try:
        if "," in args:
            temperatures = [float(x) for x in args.split(",")]
            temperatures = tuple(temperatures)
        else:
            temperatures = float(args)

        return True, temperatures
    except Exception as e:
        logger.exception(e)
        return False, str(e)
