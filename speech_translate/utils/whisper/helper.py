import json
import os
from typing import Dict, Literal, Union

import requests
from loguru import logger

from speech_translate._path import p_base_filter, p_filter_file_import, p_filter_rec
from speech_translate.utils.types import StableTsResultDict

from ..translate.language import LANGUAGES

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


def append_dot_en(model_key: str, src_english: bool, use_en_model):
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
    if "large" not in name and src_english and use_en_model:
        name = name + ".en"

    logger.debug(f"modelName: {name}")
    return name


def stablets_verbose_log(result):
    """
    This will log the result of the whisper engine in a verbose way.

    Parameters
    ----
    result:
        whisper result
    """
    res = result.to_dict()  # type: StableTsResultDict
    logger.debug(f"Language: {res['language']}")
    logger.debug(f"Text: {res['text']}")
    for segment in res["segments"]:
        logger.debug(f"Segment {segment['id']}\n" \
                    f"Seek: {segment['seek']}\n" \
                    f"Start: {segment['start']}\n" \
                    f"End: {segment['end']}\n" \
                    f"Text: {segment['text']}\n" \
                    f"Tokens: {segment['tokens']}\n" \
                    f"Temperature: {segment['temperature']}\n" \
                    f"Avg Logprob: {segment['avg_logprob']}\n" \
                    f"Compression Ratio: {segment['compression_ratio']}\n" \
                    f"No Speech Prob: {segment['no_speech_prob']}")

        for words in segment["words"]:
            logger.debug(f"Segment {words['segment_id']} - Word {words['id']}\n" \
                        f"Start: {words['start']}\n" \
                        f"End: {words['end']}\n" \
                        f"Word: {words['word']}\n" \
                        f"Tokens: {words['tokens']}\n" \
                        f"Probability: {words['probability']}")


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
