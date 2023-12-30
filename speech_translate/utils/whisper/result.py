import re
from typing import List, Union

import stable_whisper

from speech_translate.utils.types import SettingDict

from ..helper import rate_similarity


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
