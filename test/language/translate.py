import os
import sys
from typing import Dict

import requests
from deep_translator import GoogleTranslator, MyMemoryTranslator
from loguru import logger

toAdd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(toAdd)

from speech_translate.utils.translate.language import (  # pylint: disable=wrong-import-position
    GOOGLE_KEY_VAL,
    GOOGLE_TARGET,
    LIBRE_KEY_VAL,
    LIBRE_TARGET,
    MY_MEMORY_TARGET,
    MYMEMORY_KEY_VAL,
)

# * using deep_translator v1.11.1
# * v1.11.4 seems to add weird language code for mymemory
# * you can try pip installing that version and you will see what i mean when you run the test code for mymemory below

# this time we are checking the key for translation. We want to see wether the translation works or not
# this check may took a while because we are testing all the language
# feel free to comment any engine that you dont want to test

TEST_STR = "Hello world"

# GOOGLE
logger.debug("---------------------------------------------------------")
logger.debug("testing google target")

fail_info = []
for key in GOOGLE_TARGET:
    key = key.lower()
    assert isinstance(GOOGLE_KEY_VAL, Dict)
    lang_code = GOOGLE_KEY_VAL[key]

    try:
        logger.debug(f"Translating {TEST_STR} to {key}")
        res = GoogleTranslator(source="english", target=lang_code).translate(TEST_STR)
        logger.debug(f"Translated {TEST_STR} to {key} with result {res}")

    except Exception as e:
        logger.exception(e)
        fail_info.append([key, lang_code, f"got err {e}"])
        logger.debug(f"Failed google {len(fail_info)} times")

logger.debug(f"Failed google translate {len(fail_info)} times")
logger.debug(f"Failed on: {fail_info}")

# MYMEMORY
logger.debug("---------------------------------------------------------")
logger.debug("testing mymemory target")

fail_info = []
for key in MY_MEMORY_TARGET:
    key = key.lower()
    assert isinstance(MYMEMORY_KEY_VAL, Dict)
    lang_code = MYMEMORY_KEY_VAL[key]

    try:
        logger.debug(f"Translating {TEST_STR} to {key}")
        res = MyMemoryTranslator(source="english", target=lang_code).translate(TEST_STR)
        logger.debug(f"Translated {TEST_STR} to {key} with result {res}")
        if "invalid" in str(res).lower():
            fail_info.append([key, lang_code, "got invalid"])
            logger.debug(f"Failed mymemory {len(fail_info)} times")
    except Exception as e:
        logger.exception(e)
        fail_info.append([key, lang_code, f"got err {e}"])
        logger.debug(f"Failed mymemory {len(fail_info)} times")

logger.debug(f"Failed mymemory {len(fail_info)} times")
logger.debug(f"Failed on: {fail_info}")

logger.debug("---------------------------------------------------------")
logger.debug("testing libre target")

fail_info = []
for key in LIBRE_TARGET:
    key = key.lower()
    assert isinstance(LIBRE_KEY_VAL, Dict)
    lang_code = LIBRE_KEY_VAL[key]
    req = {"q": TEST_STR, "source": "en", "target": lang_code, "format": "text"}

    try:
        logger.debug(f"Translating {TEST_STR} to {key}")
        res = requests.post("http://127.0.0.1:5000/translate", json=req, timeout=5).json()
        logger.debug(f"Translated {TEST_STR} to {key} with result {res}")
        if "invalid" in str(res).lower() or "not supported" in str(res).lower():
            fail_info.append([key, lang_code, "got err"])
            logger.debug(f"Failed libre {len(fail_info)} times")

    except Exception as e:
        logger.exception(e)
        fail_info.append([key, lang_code, f"got err {e}"])
        logger.debug(f"Failed libre {len(fail_info)} times")

logger.debug(f"Failed libre {len(fail_info)} times")
logger.debug(f"Failed on: {fail_info}")
