import argparse
from typing import Literal, Optional, Union

import stable_whisper
import torch
from loguru import logger
from stable_whisper.utils import isolate_useful_options, str_to_valid_type
from whisper import DecodingOptions

from speech_translate.utils.types import SettingDict
from speech_translate.utils.whisper.download import get_default_download_root

from .helper import get_temperature

str2val = {"true": True, "false": False, "1": True, "0": False}


def optional_int(string):
    return None if string == "None" else int(string)


def optional_float(string):
    return None if string == "None" else float(string)


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
                from faster_whisper.transcribe import TranscriptionOptions  # pylint: disable=import-outside-toplevel

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
        # suppres token in the setting is saved as string
        # if fail to parse, it means that the suppress_tokens is set to empty
        # if empty, faster whisper needs to be set to None
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
    # pylint: disable=import-outside-toplevel, protected-access
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
