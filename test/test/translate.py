import os
import sys
from typing import Dict
from loguru import logger
from deep_translator import MyMemoryTranslator, GoogleTranslator

toAdd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(toAdd)

from speech_translate.utils.translate.language import ( # noqa: E402
    GOOGLE_TARGET, MY_MEMORY_TARGET, GOOGLE_KEY_VAL, MYMEMORY_KEY_VAL
)

# * using deep_translator v1.11.1
# * v1.11.4 seems to add weird language code for mymemory
# * you can try pip installing that version and you will see what i mean when you run the test code for mymemory below

# this time we are checking the key for translation. We want to see wether the translation works or not
# this check may took a while because we are testing all the language
# feel free to comment any engine that you dont want to test
# i dont add test for libre because i added and tested the code from the docs directly and there is rarely any free libre server that is up

test_string = "Hello world"

# GOOGLE
logger.debug("---------------------------------------------------------")
logger.debug("testing google target")

fail_info = []
for key in GOOGLE_TARGET:
    key = key.lower()
    assert isinstance(GOOGLE_KEY_VAL, Dict)
    lang_code = GOOGLE_KEY_VAL[key]

    try:
        logger.debug(f"Translating {test_string} to {key}")
        res = GoogleTranslator(source="english", target=lang_code).translate(test_string)
        logger.debug(f"Translated {test_string} to {key} with result {res}")

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
        logger.debug(f"Translating {test_string} to {key}")
        res = MyMemoryTranslator(source="english", target=lang_code).translate(test_string)
        logger.debug(f"Translated {test_string} to {key} with result {res}")
        if "invalid" in str(res).lower():
            fail_info.append([key, lang_code, "got invalid"])
            logger.debug(f"Failed mymemory {len(fail_info)} times")
    except Exception as e:
        logger.exception(e)
        fail_info.append([key, lang_code, f"got err {e}"])
        logger.debug(f"Failed mymemory {len(fail_info)} times")

logger.debug(f"Failed mymemory {len(fail_info)} times")
logger.debug(f"Failed on: {fail_info}")
