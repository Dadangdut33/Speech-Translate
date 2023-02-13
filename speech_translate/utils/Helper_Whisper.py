import re

validDecodingOptions = [
    "temperature",
    "sample_len",
    "best_of",
    "beam_size",
    "patience",
    "length_penalty",
    "prompt",
    "prefix",
    "suppress_blank",
    "suppress_tokens",
    "without_timestamps",
    "max_initial_timestamp",
    "fp16",
]


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
            result[param] = re.sub(r"['\"]", "", value)

    return result


# DEBUG
if __name__ == "__main__":
    # Example of a valid option string: (This is only an example, value is just gibberish)
    # options = '--temperature 0.7 --sample_len 1024 --best_of 3 --beam_size 5 --patience 5 --length_penalty 1.0 --prompt "Hello, my name is" --prefix "Hello, my name is" --suppress_blank 1 --suppress_tokens "Hello, my name is" --without_timestamps 1 --max_initial_timestamp 0.0 --fp16 1'
    options = "1 adas d asd asdasd as --temperature 0.7 --test tust"
    options = convert_str_options_to_dict(options)
    print(options)
