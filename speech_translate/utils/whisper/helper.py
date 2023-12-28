# pylint: disable=import-outside-toplevel, protected-access
import argparse
import csv
import json
import os
import re
from typing import Dict, List, Literal, Optional, Union

import requests
import stable_whisper
import torch
from loguru import logger
from stable_whisper.utils import isolate_useful_options, str_to_valid_type
from whisper import DecodingOptions
from whisper.tokenizer import LANGUAGES
from whisper.utils import optional_float, optional_int

from speech_translate._path import p_base_filter, p_filter_file_import, p_filter_rec
from speech_translate.utils.types import SettingDict, StableTsResultDict, StableTsSegmentResult
from speech_translate.utils.whisper.download import get_default_download_root

from ..helper import rate_similarity

model_select_dict = {
    "⚡ Tiny [1GB VRAM] (Fastest)": "tiny",
    "🚀 Base [1GB VRAM] (Faster)": "base",
    "⛵ Small [2GB VRAM] (Moderate)": "small",
    "🌀 Medium [5GB VRAM] (Accurate)": "medium",
    "🐌 Large V1 [10GB VRAM] (Most Accurate)": "large-v1",
    "🐌 Large V2 [10GB VRAM] (Most Accurate)": "large-v2",
    "🐌 Large V3 [10GB VRAM] (Most Accurate)": "large-v3",
}
model_keys = list(model_select_dict.keys())
model_values = list(model_select_dict.values())
USE_EFFICIENT_BY_DEFAULT = True
TRUST_WHISPER_TIMESTAMP_BY_DEFAULT = True

str2val = {"true": True, "false": False, "1": True, "0": False}


def str2bool(string: str) -> bool:
    string = string.lower()
    if string in str2val:
        return str2val[string]
    raise ValueError(f"Expected one of {set(str2val.keys())}, got {string}")


class ArgumentParserWithErrors(argparse.ArgumentParser):
    """
    An ArgumentParser that raises ValueError on error 
    so we can see the error message by catching it 
    """
    def error(self, message):
        raise ValueError(message)


def parse_args_stable_ts(
    arguments: str, mode: Union[Literal["load", "transcribe", "align", "refine", "save"], str], method=None, **kwargs
):
    """Parse arguments to be passed onto stable ts with each mode in mind

    Pass in kwargs if needed

    Parameters
    ----------
    arguments : str
        arguments to be parsed
    mode : Literal[&quot;load&quot;, &quot;transcribe&quot;, &quot;align&quot;, &quot;refine&quot;, &quot;save&quot;]
        mode to parse arguments for
    pass_method : _type_, optional
        method to pass arguments to, by default None

    Returns
    -------
    dict
        parsed arguments

    Raises
    ------
    ValueError
        if there are missing values or invalid values
    """

    parser = ArgumentParserWithErrors(
        description="Example Argument Parser", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    args = {}

    def update_options_with_args(arg_key: str, options: Optional[dict] = None, pop: bool = False):
        extra_options = args.pop(arg_key) if pop else args.get(arg_key)
        if not extra_options:
            return
        extra_options = [kv.split('=', maxsplit=1) for kv in extra_options]
        missing_val = [kv[0] for kv in extra_options if len(kv) == 1]
        if missing_val:
            raise ValueError(f'Following expected values for the following custom options: {missing_val}')
        extra_options = dict(
            (k.replace('"', "").replace("'", ""), str_to_valid_type(v.replace('"', '').replace("'", "")))
            for k, v in extra_options
        )
        if options is None:
            return extra_options
        options.update(extra_options)

    try:
        # ruff: noqa: E501
        # yapf: disable
        parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu",
                            help="device to use for PyTorch inference")
        parser.add_argument("--cpu_preload", type=str2bool, default=True,
                            help="load model into CPU memory first then move model to specified device; "
                                "this reduces GPU memory usage when loading model.")

        parser.add_argument("--dynamic_quantization", "-dq", action='store_true',
                        help="whether to apply Dynamic Quantization to model "
                             "to reduced memory usage (~half less) and increase inference speed "
                             "at cost of slight decrease in accuracy; Only for CPU; "
                             "NOTE: overhead might make inference slower for models smaller than 'large'")

        parser.add_argument("--prepend_punctuations", '-pp', type=str, default="\"'“¿([{-",
                            help="Punctuations to prepend to next word")
        parser.add_argument("--append_punctuations", '-ap', type=str, default="\"'.。,，!！?？:：”)]}、",
                            help="Punctuations to append to previous word")

        parser.add_argument("--gap_padding", type=str, default=" ...",
                            help="padding prepend to each segments for word timing alignment;"
                                "used to reduce the probability of model predicting timestamps "
                                "earlier than the first utterance")

        parser.add_argument("--word_timestamps", type=str2bool, default=True,
                            help="extract word-level timestamps using the cross-attention pattern and dynamic time warping,"
                             "and include the timestamps for each word in each segment;"
                             "disabling this will prevent segments from splitting/merging properly.")

        parser.add_argument("--regroup", type=str, default="True",
                            help="whether to regroup all words into segments with more natural boundaries;"
                                "specify string for customizing the regrouping algorithm"
                                "ignored if [word_timestamps]=False.")

        parser.add_argument('--ts_num', type=int, default=0,
                            help="number of extra inferences to perform to find the mean timestamps")
        parser.add_argument('--ts_noise', type=float, default=0.1,
                            help="percentage of noise to add to audio_features to perform inferences for [ts_num]")

        parser.add_argument('--suppress_silence', type=str2bool, default=True,
                            help="whether to suppress timestamp where audio is silent at segment-level"
                                "and word-level if [suppress_word_ts]=True")
        parser.add_argument('--suppress_word_ts', type=str2bool, default=True,
                            help="whether to suppress timestamps where audio is silent at word-level; "
                                "ignored if [suppress_silence]=False")

        parser.add_argument('--suppress_ts_tokens', type=str2bool, default=False,
                            help="whether to use silence mask to suppress silent timestamp tokens during inference; "
                                "increases word accuracy in some cases, but tends reduce 'verbatimness' of the transcript"
                                "ignored if [suppress_silence]=False")

        parser.add_argument("--q_levels", type=int, default=20,
                            help="quantization levels for generating timestamp suppression mask; "
                                "acts as a threshold to marking sound as silent;"
                                "fewer levels will increase the threshold of volume at which to mark a sound as silent")

        parser.add_argument("--k_size", type=int, default=5,
                            help="Kernel size for average pooling waveform to generate suppression mask; "
                                "recommend 5 or 3; higher sizes will reduce detection of silence")

        parser.add_argument('--time_scale', type=float,
                            help="factor for scaling audio duration for inference;"
                                "greater than 1.0 'slows down' the audio; "
                                "less than 1.0 'speeds up' the audio; "
                                "1.0 is no scaling")

        parser.add_argument('--vad', type=str2bool, default=False,
                            help='whether to use Silero VAD to generate timestamp suppression mask; '
                                'Silero VAD requires PyTorch 1.12.0+;'
                                'Official repo: https://github.com/snakers4/silero-vad')
        parser.add_argument('--vad_threshold', type=float, default=0.35,
                            help='threshold for detecting speech with Silero VAD. (Default: 0.35); '
                                'low threshold reduces false positives for silence detection')
        parser.add_argument('--vad_onnx', type=str2bool, default=False,
                            help='whether to use ONNX for Silero VAD')

        parser.add_argument('--min_word_dur', type=float, default=0.1,
                            help="only allow suppressing timestamps that result in word durations greater than this value")

        # parser.add_argument('--max_chars', type=int,
        #                     help="maximum number of character allowed in each segment")
        # parser.add_argument('--max_words', type=int,
        #                     help="maximum number of words allowed in each segment")

        parser.add_argument('--demucs', type=str2bool, default=False,
                            help='whether to reprocess the audio track with Demucs to isolate vocals/remove noise; '
                                'Demucs official repo: https://github.com/facebookresearch/demucs')
        parser.add_argument('--demucs_output', action="extend", nargs="+", type=str,
                        help='path(s) to save the vocals isolated by Demucs as WAV file(s); '
                             'ignored if [demucs]=False')
        parser.add_argument('--only_voice_freq', '-ovf', action='store_true',
                            help='whether to only use sound between 200 - 5000 Hz, where majority of human speech are.')

        parser.add_argument('--strip', type=str2bool, default=True,
                            help="whether to remove spaces before and after text on each segment for output")

        parser.add_argument('--tag', type=str, action="extend", nargs="+",
                            help="a pair tags used to change the properties a word at its predicted time"
                                "SRT Default: '<font color=\"#00ff00\">', '</font>'"
                                "VTT Default: '<u>', '</u>'"
                                "ASS Default: '{\\1c&HFF00&}', '{\\r}'")
        # parser.add_argument('--segment_level', type=str2bool, default=True,
        #                     help="whether to use segment-level timestamps in output")
        # parser.add_argument('--word_level', type=str2bool, default=True,
        #                     help="whether to use word-level timestamps in output")

        parser.add_argument('--reverse_text', type=str2bool, default=False,
                            help="whether to reverse the order of words for each segment of text output")

        # ass output
        parser.add_argument('--font', type=str, default='Arial',
                            help="word font for ASS output(s)")
        parser.add_argument('--font_size', type=int, default=48,
                            help="word font size for ASS output(s)")
        parser.add_argument('--karaoke', type=str2bool, default=False,
                            help="whether to use progressive filling highlights for karaoke effect (only for ASS outputs)")

        # parser.add_argument("--temperature", type=float, default=0,
        #                     help="temperature to use for sampling")
        # parser.add_argument("--best_of", type=optional_int,
        #                     help="number of candidates when sampling with non-zero temperature")
        # parser.add_argument("--beam_size", type=optional_int,
        #                     help="number of beams in beam search, only applicable when temperature is zero")
        # parser.add_argument("--patience", type=float, default=None,
        #                     help="optional patience value to use in beam decoding, "
        #                         "as in https://arxiv.org/abs/2204.05424, "
        #                         "the default (1.0) is equivalent to conventional beam search")

        parser.add_argument("--length_penalty", type=float, default=None,
                            help="optional token length penalty coefficient (alpha) "
                                "as in https://arxiv.org/abs/1609.08144, uses simple length normalization by default")

        # parser.add_argument("--fp16", type=str2bool, default=True,
        #                     help="whether to perform inference in fp16; True by default")

        parser.add_argument("--compression_ratio_threshold", type=optional_float, default=2.4,
                            help="if the gzip compression ratio is higher than this value, treat the decoding as failed")
        parser.add_argument("--logprob_threshold", type=optional_float, default=-1.0,
                            help="if the average log probability is lower than this value, treat the decoding as failed")
        parser.add_argument("--no_speech_threshold", type=optional_float, default=0.6,
                            help="if the probability of the <|nospeech|> token is higher than this value AND the decoding "
                                "has failed due to `logprob_threshold`, consider the segment as silence")
        parser.add_argument("--threads", type=optional_int, default=0,
                            help="number of threads used by torch for CPU inference; "
                                "supercedes MKL_NUM_THREADS/OMP_NUM_THREADS")

        parser.add_argument('--mel_first', action='store_true',
                            help='process entire audio track into log-Mel spectrogram first instead in chunks')

        # parser.add_argument('--align', '-a', action="extend", nargs='+', type=str,
        #                     help='path(s) to TXT file(s) or JSON previous result(s)')

        # parser.add_argument('--refine', '-r', action='store_true',
        #                     help='Refine timestamps to increase precision of timestamps')

        parser.add_argument('--demucs_option', '-do', action="extend", nargs='+', type=str,
                        help='Extra option(s) to use for demucs; Replace True/False with 1/0; '
                             'E.g. --demucs_option "shifts=3" --demucs_options "overlap=0.5"')

        parser.add_argument('--refine_option', '-ro', action="extend", nargs='+', type=str,
                            help='Extra option(s) to use for refining timestamps; Replace True/False with 1/0; '
                                'E.g. --refine_option "steps=sese" --refine_options "rel_prob_decrease=0.05"')
        parser.add_argument('--model_option', '-mo', action="extend", nargs='+', type=str,
                            help='Extra option(s) to use for loading model; Replace True/False with 1/0; '
                                'E.g. --model_option "download_root=./downloads"')
        parser.add_argument('--transcribe_option', '-to', action="extend", nargs='+', type=str,
                            help='Extra option(s) to use for transcribing/alignment; Replace True/False with 1/0; '
                                'E.g. --transcribe_option "ignore_compatibility=1"')
        parser.add_argument('--save_option', '-so', action="extend", nargs='+', type=str,
                            help='Extra option(s) to use for text outputs; Replace True/False with 1/0; '
                                'E.g. --save_option "highlight_color=ffffff"')
        # yapf: enable
        args = parser.parse_args(arguments.split()).__dict__
        threads = args.pop('threads')  # pop to be added in certain mode -> transcribe, align, refine

        args['demucs_options'] = update_options_with_args('demucs_option', pop=True)
        if dq := args.pop('dynamic_quantization', False):
            args['device'] = 'cpu'
            args['dq'] = dq
        if args['reverse_text']:
            args['reverse_text'] = (args.get('prepend_punctuations'), args.get('append_punctuations'))

        regroup = args.pop('regroup')
        if regroup:
            try:
                args["regroup"] = str2bool(regroup)
            except ValueError:
                pass

        if tag := args.get('tag'):
            assert tag == ['-1'] or len(tag) == 2, f'[tag] must be a pair of str but got {tag}'

        # need to hard code it a bit, to get the same result as stable ts from cli
        if mode == "load":
            temp = args["model_option"]

            args = isolate_useful_options(args, method)
            args["model_option"] = temp

            update_options_with_args('model_option', args)
            args.pop('model_option')
        elif mode == "transcribe":
            # should be ok when using faster whisper too
            temp = args["transcribe_option"]  # store temp transcribe_option

            # isolate with the transcribe function
            args = isolate_useful_options(args, method)
            # logger.debug(f"Isolated args with method: {args}")

            # update args with transcribe_option after isolate
            args["transcribe_option"] = temp
            update_options_with_args('transcribe_option', args)
            args.pop('transcribe_option')  # pop transcribe_option
            # logger.debug(f"Updated args with transcribe_option: {args}")

            # add in the extra kwargs
            # args.update(isolate_useful_options(kwargs, method))  # add with method
            # add with the other
            if "faster_whisper" in str(method):
                from faster_whisper.transcribe import TranscriptionOptions

                # force some option because it is needed in order to work for faster whisper
                if kwargs["best_of"] is None:
                    kwargs["best_of"] = 1
                if kwargs["beam_size"] is None:
                    kwargs["beam_size"] = 1
                if kwargs["patience"] is None:
                    kwargs["patience"] = 1
                args.update(isolate_useful_options(kwargs, TranscriptionOptions))
            else:
                args.update(isolate_useful_options(kwargs, DecodingOptions))
            # logger.debug(f"Updated args with kwargs: {args}")

            args["threads"] = threads

        elif mode == "align":
            temp = args["transcribe_option"]

            args = isolate_useful_options(args, method)
            args["transcribe_option"] = temp

            update_options_with_args('transcribe_option', args)
            args.pop('transcribe_option')
            args.update(isolate_useful_options(args, DecodingOptions))
            args["threads"] = threads

        elif mode == "refine":
            temp = args["refine_option"]

            args = isolate_useful_options(args, method)
            args["refine_option"] = temp

            update_options_with_args('refine_option', args)
            args.pop('refine_option')
            args["threads"] = threads

        elif mode == "save":
            temp = args["save_option"]
            args['filepath'] = kwargs.get('save_path')
            args['path'] = kwargs.get('save_path')
            args["word_level"] = kwargs.get('word_level')
            args["segment_level"] = kwargs.get('segment_level')

            args = isolate_useful_options(args, method)
            args["save_option"] = temp

            update_options_with_args('save_option', args)
            args.pop('save_option')

        # download_root for loading model is set in get_model_args
        args.pop('download_root', None)

        args["success"] = True

        if kwargs.pop('show_parsed', True):
            logger.debug(f"Mode {mode} args get: {args}")
    except ValueError as e:
        logger.exception(e)
        args["success"] = False
        args["msg"] = str(e)
    except Exception as e:
        logger.exception(e)
        args["success"] = False
        args["msg"] = str(e)

    return args


def flatten(list_of_lists, key=None):
    for sublist in list_of_lists:
        for item in sublist.get(key, []) if key else sublist:
            yield item


def remove_keys(list_of_dicts, key):
    for d in list_of_dicts:
        yield {k: d[k] for k in d.keys() - {key}}


def write_csv(
    transcript: Union[stable_whisper.WhisperResult, StableTsResultDict],
    file,
    sep=",",
    text_first=True,
    format_timestamps=None,
    header=False
):
    writer = csv.writer(file, delimiter=sep)
    if format_timestamps is None:
        format_timestamps = lambda x: x  # pylint: disable=unnecessary-lambda-assignment
    if header is True:
        header = ["text", "start", "end"] if text_first else ["start", "end", "text"]
    if header:
        writer.writerow(header)
    if text_first:
        if isinstance(transcript, stable_whisper.WhisperResult):
            writer.writerows(
                [
                    [segment.text.strip(),
                     format_timestamps(segment.start),
                     format_timestamps(segment.end)] for segment in transcript.segments
                ]
            )
        else:
            writer.writerows(
                [
                    [segment["text"].strip(),
                     format_timestamps(segment['start']),
                     format_timestamps(segment['end'])] for segment in transcript['segments']
                ]
            )
    else:
        if isinstance(transcript, stable_whisper.WhisperResult):
            writer.writerows(
                [
                    [format_timestamps(segment.start),
                     format_timestamps(segment.end),
                     segment.text.strip()] for segment in transcript.segments
                ]
            )
        else:
            writer.writerows(
                [
                    [format_timestamps(segment['start']),
                     format_timestamps(segment['end']), segment["text"].strip()] for segment in transcript['segments']
                ]
            )


def fname_dupe_check(filename: str, extension: str):
    # check if file already exists
    if os.path.exists(filename + extension):
        # add (2) to the filename, but if that already exists, add (3) and so on
        i = 2
        while os.path.exists(filename + f" ({i})"):
            i += 1

        filename += f" ({i})"

    return filename


def save_output_stable_ts(
    result: Union[stable_whisper.WhisperResult, StableTsResultDict], outname, output_formats: List, sj
):
    output_formats_methods = {
        "srt": "to_srt_vtt",
        "ass": "to_ass",
        "json": "save_as_json",
        "vtt": "to_srt_vtt",
        "tsv": "to_tsv",
        "txt": "to_txt",
    }

    # make sure the output dir is exist
    os.makedirs(os.path.dirname(outname), exist_ok=True)

    for f_format in output_formats:
        outname = fname_dupe_check(outname, f_format)
        logger.debug(f"Saving to {f_format}")

        # Save CSV
        if f_format == "csv":
            with open(outname + ".csv", "w", encoding="utf-8") as f_csv:
                write_csv(result, file=f_csv)

        # Save JSON
        elif f_format == "json":
            with open(fname_dupe_check(outname, f_format) + ".json", "w", encoding="utf-8") as f_json:
                res = result.to_dict() if isinstance(result, stable_whisper.WhisperResult) else result
                json.dump(res, f_json, indent=2, allow_nan=True, ensure_ascii=False)

        # Save other formats (SRT, ASS, VTT, TSV)
        else:
            save_method = getattr(result, output_formats_methods[f_format])
            kwargs_to_pass = {
                "save_path": outname,
                "segment_level": sj.cache["segment_level"],
                "word_level": sj.cache["word_level"]
            }
            if f_format == "vtt":
                kwargs_to_pass["vtt"] = True

            if f_format == "tsv":
                # must keep only segment or word level
                # prioritize word level
                logger.debug("Format is TSV so we only keep 1 type of export level")
                if kwargs_to_pass["word_level"]:
                    logger.debug("Prioritizing word level format")
                    kwargs_to_pass["segment_level"] = False
                if kwargs_to_pass["segment_level"]:
                    logger.debug("Using segment level format")
                    kwargs_to_pass["word_level"] = False

                if not kwargs_to_pass["word_level"] and not kwargs_to_pass["segment_level"]:
                    logger.warning("Somehow both word level and segment level is False ??, setting segment level to True")
                    kwargs_to_pass["word_level"] = True

            args = parse_args_stable_ts(sj.cache["whisper_args"], "save", save_method, **kwargs_to_pass)
            args.pop('success')  # no need to check, because it probably have been checked before since this is the last step
            save_method(**args)  # run the method


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


def stablets_verbose_log(result: stable_whisper.WhisperResult):
    """
    This will log the result of the whisper engine in a verbose way.

    Parameters
    ----
    result:
        whisper result
    """
    res = result.to_dict()
    assert isinstance(res, StableTsResultDict)
    logger.debug(f"Language: {res['language']}")
    logger.debug(f"Text: {res['text']}")
    logger.debug("Segments:")
    for segment in res["segments"]:
        assert isinstance(segment, StableTsSegmentResult)
        logger.debug(f"Segment {segment['id']}")
        logger.debug(f"Seek: {segment['seek']}")
        logger.debug(f"Start: {segment['start']}")
        logger.debug(f"End: {segment['end']}")
        logger.debug(f"Text: {segment['text']}")
        logger.debug(f"Tokens: {segment['tokens']}")
        logger.debug(f"Temperature: {segment['temperature']}")
        logger.debug(f"Avg Logprob: {segment['avg_logprob']}")
        logger.debug(f"Compression Ratio: {segment['compression_ratio']}")
        logger.debug(f"No Speech Prob: {segment['no_speech_prob']}")

        logger.debug("Words:")
        for words in segment["words"]:
            logger.debug(f"Word {words['id']} | Segment {words['segment_id']}")
            logger.debug(f"Start: {words['start']}")
            logger.debug(f"End: {words['end']}")
            logger.debug(f"Word: {words['word']}")
            logger.debug(f"Tokens: {words['tokens']}")
            logger.debug(f"Probability: {words['probability']}")


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


def result_to_dict(res: stable_whisper.WhisperResult):
    """Just a little funtion to help keeping the type hinting when converting result to dict

    Parameters
    ----------
    res : WhisperResult
        Result from stable whisper

    Returns
    -------
    StableTsResultDict
        Result in dict format
    """
    x: StableTsResultDict = res.to_dict()  # type: ignore
    return x


def get_model_args(setting_cache: SettingDict):
    """Get arguments / parameter to load to stable ts

    Parameters
    ----------
    setting_cache: dict
        Setting value

    Returns
    -------
    dict
       The parameter / argument to load to stable ts

    Raises
    ------
    Exception
        If the model args is not valid will throw exception containing the failure message
    """
    from faster_whisper import WhisperModel

    # load model
    model_args = parse_args_stable_ts(
        setting_cache["whisper_args"], "load",
        WhisperModel if setting_cache["use_faster_whisper"] else stable_whisper.load_model
    )
    if not model_args.pop("success"):
        raise Exception(model_args["msg"])

    if setting_cache["dir_model"] != "auto":
        model_args["download_root"] = setting_cache["dir_model"]
    else:
        model_args["download_root"] = get_default_download_root()

    return model_args


def get_tc_args(process_func, setting_cache: SettingDict, mode="transcribe"):
    """
    Get arguments / parameter to load to stable ts 
    for transcribe / translate using whisper and get their respective function

    Parameters
    ----------
    model_name_tc : str
        The model name for transcribe / translate
    lang_source : str
        The source language
    auto : bool
        Wether the source language is auto or not
    setting_cache : SettingDict
        The setting value

    Returns
    -------
    tuple of dict, function, function
        The parameter / argument to load to stable ts, the transcribe function, and the translate function

    Raises
    ------
    Exception
        If temperature is not valid will throw exception containing the failure message
    Exception
        If the model args is not valid will throw exception containing the failure message
    """
    temperature = setting_cache["temperature"]
    success, data = get_temperature(temperature)
    if not success:
        raise Exception(data)
    else:
        temperature = data

    try:
        suppress_tokens = [int(x) for x in setting_cache["suppress_tokens"].split(",")]
    except Exception:
        if "faster_whisper" in str(process_func):
            suppress_tokens = None
        else:
            suppress_tokens = setting_cache["suppress_tokens"]

    # parse whisper_args
    pass_kwarg = {
        "temperature": temperature,
        "best_of": setting_cache["best_of"],
        "beam_size": setting_cache["beam_size"],
        "patience": setting_cache["patience"],
        "compression_ratio_threshold": setting_cache["compression_ratio_threshold"],
        "logprob_threshold": setting_cache["logprob_threshold"],
        "no_speech_threshold": setting_cache["no_speech_threshold"],
        "suppress_tokens": suppress_tokens,
        "suppress_blank": setting_cache["suppress_blank"],
        "initial_prompt": setting_cache["initial_prompt"],
        "prefix": setting_cache["prefix"],
        "condition_on_previous_text": setting_cache["condition_on_previous_text"],
        "max_initial_timestamp": setting_cache["max_initial_timestamp"],
        "fp16": setting_cache["fp16"],
    }
    logger.debug("Pass kwarg:")
    logger.debug(pass_kwarg)
    data = parse_args_stable_ts(setting_cache["whisper_args"], mode, process_func, **pass_kwarg)
    if not data.pop("success"):
        raise Exception(data["msg"])
    else:
        whisper_args = data
        threads = whisper_args.pop("threads")
        if threads:
            torch.set_num_threads(threads)

    return whisper_args


def get_model(
    transcribe: bool, translate: bool, tl_engine_whisper: bool, model_name_tc: str, engine: str, setting_cache: SettingDict,
    **model_args
):
    """Get model and the function for stable whisper while also checking using faster whisper or not

    Parameters
    ----------
    transcribe : bool
        Transcribe or not
    translate : bool
        Translate or not
    tl_engine_whisper : bool
        Translate using whisper or not
    model_name_tc : str
        Name of the transcription model
    engine : str
        engine name
    setting_cache : SettingDict
        Setting value

    Returns
    -------
    tuple
        model_tc, model_tl, stable_tc, stable_tl, load_to_tc_args
    """
    model_tc, model_tl, stable_tc, stable_tl = None, None, None, None
    if setting_cache["use_faster_whisper"] and model_name_tc:
        if transcribe and translate and model_name_tc == engine:
            # same model for both transcribe and translate. Load only once
            logger.debug("Loading model for both transcribe and translate using faster-whisper | Load only once")
            model_tc = stable_whisper.load_faster_whisper(model_name_tc, **model_args)
            stable_tc = model_tc.transcribe_stable  # type: ignore
            stable_tl = stable_tc
        else:
            if transcribe:  # if transcribe, load model for transcribe
                logger.debug("Loading model for transcribe using faster-whisper")
                model_tc = stable_whisper.load_faster_whisper(model_name_tc, **model_args)
                stable_tc = model_tc.transcribe_stable  # type: ignore

            if translate and tl_engine_whisper:  # if translate using whisper, load model for translate
                logger.debug("Loading model for translate using faster-whisper")
                model_tl = stable_whisper.load_faster_whisper(engine, **model_args)
                stable_tl = model_tl.transcribe_stable  # type: ignore

            # if translate and the engine is not using whisper,
            # load model for transcribe, but check first wether the model is already loaded or not
            # if model is already loaded it means that the user is also transcribing
            elif translate and not tl_engine_whisper and model_tc is None:
                logger.debug(
                    "Mode is translate and engine is not using whisper, " \
                    "model for transcribe is not loaded yet, loading model for transcribe"
                )
                model_tc = stable_whisper.load_faster_whisper(model_name_tc, **model_args)
                stable_tc = model_tc.transcribe_stable  # type: ignore
    else:
        if transcribe and translate and model_name_tc == engine:
            # same model for both transcribe and translate. Load only once
            logger.debug("Loading model for both transcribe and translate using whisper | Load only once")
            model_tc = stable_whisper.load_model(model_name_tc, **model_args)
            stable_tc = model_tc.transcribe
            stable_tl = stable_tc
        else:
            if transcribe:  # if transcribe, load model for transcribe
                logger.debug("Loading model for transcribe using whisper")
                model_tc = stable_whisper.load_model(model_name_tc, **model_args)
                stable_tc = model_tc.transcribe

            if translate and tl_engine_whisper:  # if translate using whisper, load model for translate
                logger.debug("Loading model for translate using whisper")
                model_tl = stable_whisper.load_model(engine, **model_args)
                stable_tl = model_tl.transcribe

            # if translate and the engine is not using whisper,
            # load model for transcribe, but check first wether the model is already loaded or not
            # if model is already loaded it means that the user is also transcribing
            elif translate and not tl_engine_whisper and model_tc is None:
                logger.debug(
                    "Mode is translate and engine is not using whisper, " \
                    "model for transcribe is not loaded yet, loading model for transcribe"
                )
                model_tc = stable_whisper.load_model(model_name_tc, **model_args)
                stable_tc = model_tc.transcribe_stable

    load_to_tc_args = stable_tc if stable_tc is not None else stable_tl  # making sure that the load_to_tc_args is not None

    logger.debug(f"Model loaded | Is Faster Whisper: {setting_cache['use_faster_whisper']} | Load Status:")
    logger.debug(f"TC: {'Set' if model_tc else 'Not Set'}")
    logger.debug(f"TL: {'Set' if model_tl else 'Not Set'}")
    logger.debug(f"func_tc: {'Set' if stable_tc else 'Not Set'}")
    logger.debug(f"func_tl: {'Set' if stable_tl else 'Not Set'}")

    return model_tc, model_tl, stable_tc, stable_tl, load_to_tc_args


def to_language_name(lang):
    """
    Getting language name from language code, 
    if the language is already language name, it will return the language name

    Parameters
    ----------
    lang 
        Language name

    Returns
    -------
    str
        Language name
    """
    try:
        return LANGUAGES[lang]
    except KeyError:
        # already language name
        return lang


def get_task_format(
    task,
    task_lang,
    task_with,
    task_lang_with,
    normal_only=True,
    short_only=False,
    both=False,
):
    """Get task format

    Parameters
    ----------
    task : str
        Str for task
    task_lang : str
        Str for task lang
    task_with : str
        Str for task with
    task_lang_with : str
        Str for task lang with

    Returns
    -------
    dict
        Dict for task format

    Raises
    ------
    ValueError
        If normal_only, short_only, and both is all False
    """
    normal = {
        "{task}": task,
        "{task-lang}": task_lang,
        "{task-with}": task_with,
        "{task-lang-with}": task_lang_with,
    }
    short = {
        "{task-short}": task,
        "{task-short-lang}": task_lang,
        "{task-short-with}": task_with,
        "{task-short-lang-with}": task_lang_with,
    }
    combined = {**normal, **short}

    if short_only or both:
        normal_only = False  # toggle off the default value

    if normal_only:
        return normal
    elif short_only:
        return short
    elif both:
        return combined
    else:
        raise ValueError("normal_only, short_only, and both can't be all False")


def split_res(result: stable_whisper.WhisperResult, sj_cache: SettingDict):
    """Split the segment results if max char or max word is set
    
    Parameters
    ----------
    result : WhisperResult
        The result from whisper
    sj : SettingDict
        The setting value

    Returns
    -------
    WhisperResult
        The result after splitting

    """

    if sj_cache["segment_max_chars"] == "" and sj_cache["segment_max_words"] == "":
        return result  # no splitting done

    return result.split_by_length(
        max_chars=int(sj_cache["segment_max_chars"]) if sj_cache["segment_max_chars"] != "" else None,  # type: ignore
        max_words=int(sj_cache["segment_max_words"]) if sj_cache["segment_max_words"] != "" else None,  # type: ignore
        newline=str(sj_cache["segment_split_or_newline"]).lower() == "newline",
        even_split=sj_cache["segment_even_split"]
    )


def remove_segments_by_str(
    result: stable_whisper.WhisperResult,
    str_to_find: Union[str, List[str]],
    case_sensitive: bool = False,
    strip: bool = True,
    ignore_punctuations: str = "\"',.?!",
    exact_match: bool = False,
    sim_rate: float = 0.8,
    debug: bool = False,
):
    """
    Remove segments that contains the string specified in ``str_to_find``.
    Some of the code on this function is taken from ``stable_whisper.WhisperResult.remove_words_by_str``

    Parameters
    ----------
    result : WhisperResult
        The result from whisper
    str_to_find : Union[str, List[str], None]
        The string to find
    case_sensitive : bool, optional
        Whether the case of the string need to match to be removed, by default False
    strip : bool, optional
        Whether to ignore spaces before and after each word.
    ignore_punctuations : str, optional
        Punctuations to ignore
    """
    if isinstance(str_to_find, str):
        str_to_find = [str_to_find]

    all_segments = result.segments
    all_segments_text = [segment.text for segment in all_segments]
    if strip:
        all_segments_text = [segment.strip() for segment in all_segments_text]
        str_to_find = [segment.strip() for segment in str_to_find]
    if ignore_punctuations:
        ptn = f'[{ignore_punctuations}]+$'
        all_segments_text = [re.sub(ptn, '', text) for text in all_segments_text]
        str_to_find = [re.sub(ptn, '', text) for text in str_to_find]
    if not case_sensitive:
        all_segments_text = [text.lower() for text in all_segments_text]
        str_to_find = [text.lower() for text in str_to_find]

    for i, full_segment in reversed(list(enumerate(all_segments_text))):
        if exact_match:
            if any(to_find == full_segment for to_find in str_to_find):
                result.remove_segment(i, verbose=debug)
        else:
            if any(rate_similarity(to_find, full_segment) >= sim_rate for to_find in str_to_find):
                result.remove_segment(i, verbose=debug)
    return result


def get_base_filter() -> Dict:
    try:
        with open(p_base_filter, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Base filter file not found, attempting to download it")
        filter_https = "https://raw.githubusercontent.com/Dadangdut33/Speech-Translate/" \
            "master/speech_translate/assets/base_hallucination_filter.json"
        r = requests.get(filter_https, timeout=5)
        if r.status_code != 200:
            logger.error("Failed to download base filter file!, returning empty!")
            return {}

        with open(p_base_filter, "w", encoding="utf-8") as f:
            f.write(r.text)

        return json.loads(r.text)


def create_hallucination_filter(_type: Union[Literal["rec"], Literal["file"]], return_if_exist=False):
    f_name = p_filter_rec if _type == "rec" else p_filter_file_import
    # if already exist, change the name of the old file
    if os.path.exists(f_name):
        if return_if_exist:
            return
        os.rename(f_name, f_name + ".old")

    hallucination_filter = get_base_filter()

    logger.debug(f"Creating new hallucination filter file at {f_name}")
    with open(f_name, "w", encoding="utf-8") as f:
        json.dump(hallucination_filter, f, indent=4, ensure_ascii=False)


def get_hallucination_filter(_type: Union[Literal["rec"], Literal["file"]], location: str = "auto") -> Dict:
    if location == "auto":
        location = p_filter_rec if _type == "rec" else p_filter_file_import
        if not os.path.exists(location):
            logger.warning(f"Hallucination filter file not found, creating new one at {location}")
            create_hallucination_filter(_type)

    with open(location, "r", encoding="utf-8") as f:
        return json.load(f)
