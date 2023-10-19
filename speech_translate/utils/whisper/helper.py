import argparse
import os
import csv
import json
from typing import List

from whisper.utils import str2bool, optional_int, get_writer

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


def parse_args_whisper_timestamped(arguments: str):
    parser = argparse.ArgumentParser()
    args = {}
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
        # parser.add_argument("--compression_ratio_threshold", default=2.4, help="if the gzip compression ratio is higher than this value, treat the decoding as failed", type=optional_float)
        # parser.add_argument("--logprob_threshold", default=-1.0, help="if the average log probability is lower than this value, treat the decoding as failed", type=optional_float)
        # parser.add_argument("--no_speech_threshold", default=0.6, help="if the probability of the <|nospeech|> token is higher than this value AND the decoding has failed due to `logprob_threshold`, consider the segment as silence", type=optional_float)
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
        args["naive_approach"] = args.pop("naive")
        args["remove_punctuation_from_words"] = not args.pop("punctuations_with_words")
        args["compute_word_confidence"] = args.pop("compute_confidence")
        args["trust_whisper_timestamps"] = not args.pop("recompute_all_timestamps")
        args["success"] = True
    except Exception as e:
        logger.exception(e)
        args["success"] = False
        args["msg"] = str(e)
    finally:
        if args == {}:
            args["success"] = False
            args["msg"] = "Fail to parse arguments, please check again"

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
    return writer.write_result({"segments": transcript}, file)


def fname_dupe_check(filename: str, extension: str):
    # check if file already exists
    if os.path.exists(filename + extension):
        # add (2) to the filename, but if that already exists, add (3) and so on
        i = 2
        while os.path.exists(filename + f" ({i})"):
            i += 1

        filename += f" ({i})"

    return filename


def save_output(result, outname, output_formats: List[str]):
    for format in output_formats:
        # check if the current format have its "format.words" counterpart
        per_word = output_formats.count(format + ".words") > 0
        if ".words" in format:
            continue

        if format == "json":
            # Save JSON
            with open(fname_dupe_check(outname, format) + ".words.json", "w", encoding="utf-8") as js:
                json.dump(result, js, indent=2, ensure_ascii=False)
        elif format == "csv":
            # Save CSV
            with open(fname_dupe_check(outname, format) + ".csv", "w", encoding="utf-8") as csv:
                write_csv(result["segments"], file=csv)
            if per_word:
                with open(fname_dupe_check(outname, format) + ".words.csv", "w", encoding="utf-8") as csv:
                    write_csv(flatten(result["segments"], "words"), file=csv)
        else:

            def get_writer_func(output_format):
                return lambda transcript, file: do_write(transcript, file, output_format)

            writers = {format: get_writer_func(format) for format in output_formats}
            writer = writers.get(format)
            if writer is None:
                raise ValueError(f"Unknown output format: {format}")

            if format == "txt":
                with open(f"{fname_dupe_check(outname, format)}.txt", "w", encoding="utf-8") as f:
                    writer(result["segments"], file=f)
            elif format == "vtt" or "srt":
                with open(f"{fname_dupe_check(outname, format)}.{format}", "w", encoding="utf-8") as f:
                    writer(remove_keys(result["segments"], "words"), file=f)
                if per_word:
                    with open(f"{fname_dupe_check(outname, format)}.words.{format}", "w", encoding="utf-8") as f:
                        writer(flatten(result["segments"], "words"), file=f)
            else:
                with open(f"{fname_dupe_check(outname, format)}.{format}", "w", encoding="utf-8") as f:
                    writer(result["segments"], file=f)
                if per_word:
                    with open(f"{fname_dupe_check(outname, format)}.words.{format}", "w", encoding="utf-8") as f:
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
        if "could not convert" in str(e):
            return False, "Input must be a number or collection of numbers separated with commas. Ex: 0.2, 0.3, 0.4 ..."
        return False, str(e)
