import json
import os
import sys

import stable_whisper
from loguru import logger
from whisper.tokenizer import TO_LANGUAGE_CODE

toAdd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(toAdd)

from speech_translate.utils.translate.language import get_whisper_lang_similar  # pylint: disable=wrong-import-position

WHISPER_LANG_LIST = list(TO_LANGUAGE_CODE.keys())
WHISPER_LANG_LIST.sort()

HALLUCINATION_LIST_FW = {}
audio = os.path.join(os.path.dirname(os.path.abspath(__file__)), "empty.mp3")  # feel free to change the audio if you want
model = stable_whisper.load_faster_whisper("small")
# play with the parameter of suppress_tokens here to get different results
kwargs_fw = {
    # "suppress_tokens": [-1],
    "suppress_tokens": None,
}
kwargs_sw = {
    # "suppress_tokens": "-1",
    "suppress_tokens": "",
}

logger.debug("Audio Path: " + audio)
for lang in WHISPER_LANG_LIST:
    try:
        res: stable_whisper.WhisperResult = model.transcribe_stable( # type: ignore # pylint: disable=not-callable
            audio, task="transcribe",
            language=TO_LANGUAGE_CODE[get_whisper_lang_similar(lang, False)],
            verbose=False, **kwargs_fw,
        )
        HALLUCINATION_LIST_FW[lang] = [res.text.strip()]
        logger.debug(f"Got {res.text} for {lang}")
    except Exception as e:
        logger.error(f"Error for {lang}: {e}")

logger.debug("---------------------------------------------------------")
logger.debug("Results FW")
logger.debug(HALLUCINATION_LIST_FW)

with open("hallucination_list_fw.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(HALLUCINATION_LIST_FW, ensure_ascii=False, indent=4))

logger.debug("---------------------------------------------------------")
logger.debug("Getting for standard whisper")
model_sw = stable_whisper.load_model("small")

HALLUCINATION_LIST_SW = {}
for lang in WHISPER_LANG_LIST:
    try:
        res: stable_whisper.WhisperResult = model_sw.transcribe( # type: ignore
            audio, task="transcribe",
            language=TO_LANGUAGE_CODE[get_whisper_lang_similar(lang, False)],
            verbose=False, **kwargs_sw # type: ignore
        )
        HALLUCINATION_LIST_SW[lang] = [res.text.strip()]
        logger.debug(f"Got {res.text} for {lang}")
    except Exception as e:
        logger.error(f"Error for {lang}: {e}")

logger.debug("---------------------------------------------------------")
logger.debug("Results standard whisper")
logger.debug(HALLUCINATION_LIST_SW)

with open("hallucination_list_sw.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(HALLUCINATION_LIST_SW, ensure_ascii=False, indent=4))

sys.path.remove(toAdd)


# Use this function below if you want to combine the results
def combine_json_files(file1, file2, output_file):
    # Load data from the three input JSON files
    with open(file1, 'r', encoding="utf-8") as f1:
        data1 = json.load(f1)

    with open(file2, 'r', encoding="utf-8") as f2:
        data2 = json.load(f2)

    # Combine the data from the three files
    # Combine the lists of data within each key
    combined_data = {}
    for key in data1.keys():
        combined_data[key] = data1.get(key, []) + data2.get(key, [])

    # Write the combined data to the output JSON file
    with open(output_file, 'w', encoding="utf-8") as out_file:
        json.dump(combined_data, out_file, indent=2, ensure_ascii=False)
