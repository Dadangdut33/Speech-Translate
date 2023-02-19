import re
from speech_translate.Logging import logger


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
