import re


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
    "temperature": float,
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
    # Example: --temperature 0.7 --sample_len 1024
    # capture each option and its value
    options = options.split("--")
    options = [option.strip() for option in options if option.strip() != ""]

    # convert to dict
    result = {}
    for i, option in enumerate(options):
        option = option.split(" ")
        param = option[0]
        value = " ".join(option[1:])  # value rest of the string

        if param in validDecodingOptions:
            # add to dict but delete all " ' in value
            val = re.sub(r"['\"]", "", value)
            val = decodingDict[param](val) # convert values

            result[param] = val

    return result


# DEBUG
if __name__ == "__main__":
    # Example of a valid option string: (This is only an example, value is just gibberish)
    # options = '--temperature 0.7 --sample_len 1024 --best_of 3 --beam_size 5 --patience 5 --length_penalty 1.0 --prompt "Hello, my name is" --prefix "Hello, my name is" --suppress_blank 1 --suppress_tokens "Hello, my name is" --without_timestamps 1 --max_initial_timestamp 0.0 --fp16 1'
    options = '--prompt "hello world" --prefix 0 --suppress_tokens "[hello world"'
    # options = "1 adas d asd asdasd as --temperature 0.7 --test tust"
    options = convert_str_options_to_dict(options)
    print(options)
