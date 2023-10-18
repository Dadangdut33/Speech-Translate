import argparse
import os
import csv
import json
from typing import Literal, List, Union
from re import sub

import torch
from whisper.utils import str2bool, optional_float, optional_int, get_writer

from speech_translate.custom_logging import logger

model_select_dict = {
    "Tiny (~32x speed)": "tiny",
    "Base (~16x speed)": "base",
    "Small (~6x speed)": "small",
    "Medium (~2x speed)": "medium",
    "Large (v1) (1x speed)": "large-v1",
    "Large (v2) (1x speed)": "large-v2",
}
model_keys = list(model_select_dict.keys())
model_values = list(model_select_dict.values())
USE_EFFICIENT_BY_DEFAULT = True
TRUST_WHISPER_TIMESTAMP_BY_DEFAULT = True


class ActionSetAccurate(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        assert nargs is None
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, "best_of", 5)
        setattr(namespace, "beam_size", 5)
        setattr(namespace, "temperature_increment_on_fallback", 0.2)


class ActionSetEfficient(argparse.Action):
    """
    Set the default options to be efficient (disable beam search and options that requires to sample several times)
    """
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        assert nargs is None
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, "best_of", None)
        setattr(namespace, "beam_size", None)
        setattr(namespace, "temperature_increment_on_fallback", None)


def parse_args_whisper_timestamped(arguments: str, temperature):
    parser = argparse.ArgumentParser()
    args = {"success": True, "msg": ""}
    try:
        # ruff: noqa: E501
        # yapf: disable
        parser.add_argument('--vad', default=False, help="whether to run Voice Activity Detection (VAD) to remove non-speech segment before applying Whisper model (removes hallucinations)", type=str2bool)
        parser.add_argument('--detect_disfluencies', default=False, help="whether to try to detect disfluencies, marking them as special words [*]", type=str2bool)
        parser.add_argument('--recompute_all_timestamps', default=not TRUST_WHISPER_TIMESTAMP_BY_DEFAULT, help="Do not rely at all on Whisper timestamps (Experimental option: did not bring any improvement, but could be useful in cases where Whipser segment timestamp are wrong by more than 0.5 seconds)", type=str2bool)
        parser.add_argument("--punctuations_with_words", default=True, help="whether to include punctuations in the words", type=str2bool)

        # parser.add_argument("--temperature", default=0.0, help="temperature to use for sampling", type=float)
        # parser.add_argument("--best_of", type=optional_int, default=None if USE_EFFICIENT_BY_DEFAULT else 5, help="number of candidates when sampling with non-zero temperature")
        # parser.add_argument("--beam_size", type=optional_int, default=None if USE_EFFICIENT_BY_DEFAULT else 5, help="number of beams in beam search, only applicable when temperature is zero")
        parser.add_argument("--patience", type=float, default=None, help="optional patience value to use in beam decoding, as in https://arxiv.org/abs/2204.05424, the default (1.0) is equivalent to conventional beam search")
        parser.add_argument("--length_penalty", type=float, default=None, help="optional token length penalty coefficient (alpha) as in https://arxiv.org/abs/1609.08144, uses simple length normalization by default")

        # parser.add_argument("--suppress_tokens", default="-1", help="comma-separated list of token ids to suppress during sampling; '-1' will suppress most special characters except common punctuations", type=str)
        # parser.add_argument("--initial_prompt", default=None, help="optional text to provide as a prompt for the first window.", type=str)
        # parser.add_argument("--condition_on_previous_text", default=True, help="if True, provide the previous output of the model as a prompt for the next window; disabling may make the text inconsistent across windows, but the model becomes less prone to getting stuck in a failure loop", type=str2bool)
        parser.add_argument("--fp16", default=None, help="whether to perform inference in fp16; Automatic by default (True if GPU available, False otherwise)", type=str2bool)

        # parser.add_argument("--temperature_increment_on_fallback", default=0.0 if USE_EFFICIENT_BY_DEFAULT else 0.2, help="Temperature to increase when falling back when the decoding fails to meet either of the thresholds below", type=optional_float)
        parser.add_argument("--compression_ratio_threshold", default=2.4, help="if the gzip compression ratio is higher than this value, treat the decoding as failed", type=optional_float)
        parser.add_argument("--logprob_threshold", default=-1.0, help="if the average log probability is lower than this value, treat the decoding as failed", type=optional_float)
        parser.add_argument("--no_speech_threshold", default=0.6, help="if the probability of the <|nospeech|> token is higher than this value AND the decoding has failed due to `logprob_threshold`, consider the segment as silence", type=optional_float)
        parser.add_argument("--threads", default=0, help="number of threads used by torch for CPU inference; supercedes MKL_NUM_THREADS/OMP_NUM_THREADS", type=optional_int)

        parser.add_argument("--compute_confidence", default=True, help="whether to compute confidence scores for words", type=str2bool)
        parser.add_argument("--verbose", type=str2bool, default=False, help="whether to print out the progress and debug messages of Whisper")
        parser.add_argument('--plot', help="plot word alignments (save the figures if an --output_dir is specified, otherwhise just show figures that have to be closed to continue)", default=False, action="store_true")
        parser.add_argument('--debug', help="print some debug information about word alignement", default=False, action="store_true")

        # parser.add_argument('--accurate', help="Shortcut to use the same default option as in Whisper (best_of=5, beam_search=5, temperature_increment_on_fallback=0.2)", action=ActionSetAccurate)

        # parser.add_argument('--efficient', help="Shortcut to disable beam size and options that requires to sample several times, for an efficient decoding", action=ActionSetEfficient)

        parser.add_argument('--naive', help="use naive approach, doing inference twice (once to get the transcription, once to get word timestamps and confidence scores).", default=False, action="store_true")
        # yapf: enable

        args = parser.parse_args(arguments.split()).__dict__
        args.pop("accurate")
        args.pop("efficient")

        # temperature_increment_on_fallback = args.pop("temperature_increment_on_fallback")
        # if temperature_increment_on_fallback:
        #     temperature = tuple(np.arange(temperature, 1.0 + 1e-6, temperature_increment_on_fallback))
        # else:
        #     temperature = [temperature]

        threads = args.pop("threads")
        if threads:
            torch.set_num_threads(threads)
    except Exception as e:
        logger.exception(e)
        args["success"] = False
        args["msg"] = str(e)
    finally:
        return args


def flatten(list_of_lists, key=None):
    for sublist in list_of_lists:
        for item in sublist.get(key, []) if key else sublist:
            yield item


def remove_keys(list_of_dicts, key):
    for d in list_of_dicts:
        yield {k: d[k] for k in d.keys() - {key}}


def write_csv(transcript, file, sep=",", text_first=True, format_timestamps=None, header=False):
    writer = csv.writer(file, delimiter=sep)
    if format_timestamps is None:
        format_timestamps = lambda x: x  # noqa
    if header is True:
        header = ["text", "start", "end"] if text_first else ["start", "end", "text"]
    if header:
        writer.writerow(header)
    if text_first:
        writer.writerows(
            [
                [segment["text"].strip(),
                 format_timestamps(segment["start"]),
                 format_timestamps(segment["end"])] for segment in transcript
            ]
        )
    else:
        writer.writerows(
            [
                [format_timestamps(segment["start"]),
                 format_timestamps(segment["end"]), segment["text"].strip()] for segment in transcript
            ]
        )


def do_write(transcript, file, output_format):
    writer = get_writer(output_format, os.path.curdir)
    try:
        return writer.write_result({"segments": transcript}, file)
    except TypeError:
        # Version > 20230314
        return writer.write_result(
            {"segments": list(transcript)}, file, {
                "highlight_words": False,
                "max_line_width": None,
                "max_line_count": None,
            }
        )


def save_output(
    result, outname, output_formats: List[Union[Literal["json"], Literal["csv"], Literal["txt"], Literal["vtt"],
                                                Literal["srt"], Literal["tsv"]]]
):
    for format in output_formats:
        if format == "json":
            # Save JSON
            with open(outname + ".words.json", "w", encoding="utf-8") as js:
                json.dump(result, js, indent=2, ensure_ascii=False)
        elif format == "csv":
            # Save CSV
            with open(outname + ".csv", "w", encoding="utf-8") as csv:
                write_csv(result["segments"], file=csv)
            if ".words" in output_formats:
                with open(outname + ".words.csv", "w", encoding="utf-8") as csv:
                    write_csv(flatten(result["segments"], "words"), file=csv)
        else:

            def get_writer_func(output_format):
                return lambda transcript, file: do_write(transcript, file, output_format)

            writers = {format: get_writer_func(format) for format in output_formats}
            writer = writers.get(format)
            if writer is None:
                raise ValueError(f"Unknown output format: {format}")

            if format == "txt":
                with open(f"{outname}.txt", "w", encoding="utf-8") as f:
                    writer(result["segments"], file=f)
            elif format == "vtt" or "srt":
                with open(f"{outname}.{format}", "w", encoding="utf-8") as f:
                    writer(remove_keys(result["segments"], "words"), file=f)
                if ".words" in output_formats:
                    with open(f"{outname}.words.{format}", "w", encoding="utf-8") as f:
                        writer(flatten(result["segments"], "words"), file=f)
            else:
                with open(f"{outname}.{format}", "w", encoding="utf-8") as f:
                    writer(result["segments"], file=f)
                if ".words" in output_formats:
                    with open(f"{outname}.words.{format}", "w", encoding="utf-8") as f:
                        writer(flatten(result["segments"], "words"), file=f)


def append_dot_en(model_key: str, src_english: bool):
    """
    Append .en to model name if src_english is True and model is not large (large does not have english version)

    Parameters
    ----------
    modelKey: str
        The key of the model in modelSelectDict
    src_english: bool
        If the source language is english
    """
    logger.info("Checking model name")
    logger.debug(f"modelKey: {model_key}, src_english: {src_english}")
    name = model_select_dict[model_key]
    if "large" not in name and src_english:
        name = name + ".en"

    logger.debug(f"modelName: {name}")
    return name


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
    logger.debug("Segments:")
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

        logger.debug("Words:")
        for index, words in enumerate(segment["words"]):
            logger.debug(f"Word {index}")
            logger.debug(f"Text: {words['text']}")
            logger.debug(f"Start: {words['start']}")
            logger.debug(f"End: {words['end']}")
            logger.debug(f"Confidence: {words['confidence']}")


def str_to_union_str_list_int(string):
    """
    Convert a string to a Union[str, List[int]] can also be use for iterable of int (in this case the iterable is a list)

    Parameters
    ----------
    string: str
        string to convert

    return
    ------
    Union[str, List[int]]
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

    Parameters
    ----------
    string: str
        string to convert

    return
    ------
    bool
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


def txt_to_srt_whisper_format_stamps(txt: str, stamps: list[str]):
    """
    Convert text format to SRT format, require list of stamps
    """
    srt = []
    for idx, (line, stamp) in enumerate(zip(txt.splitlines(), stamps)):
        srt.append(str(idx + 1))
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
                val = sub(r"['\"]", "", value)
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
    Input must be a string of either a single float number (ex: 0.0) or tuple of floats number separated with commas
    (ex: 0.2, 0.3, 0.4 ...).
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
