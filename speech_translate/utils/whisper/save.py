import csv
import json
import os
from typing import List, Union

import stable_whisper
from loguru import logger

from speech_translate.utils.types import StableTsResultDict

from .load import parse_args_stable_ts


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
