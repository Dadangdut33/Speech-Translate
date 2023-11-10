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
# i dont add test for libre because i added and tested the code from the docs directly and nowadays there is rarely any free libre server that is up

test_string = "Hello world"

# GOOGLE
logger.debug("---------------------------------------------------------")
logger.debug("testing google target")

for key in GOOGLE_TARGET:
    key = key.lower()
    assert isinstance(GOOGLE_KEY_VAL, Dict)
    lang_code = GOOGLE_KEY_VAL[key]

    logger.debug(f"Translating {test_string} to {key}")
    res = GoogleTranslator(source="english", target=lang_code).translate(test_string)
    logger.debug(f"Translated {test_string} to {key} with result {res}")

# MYMEMORY
logger.debug("---------------------------------------------------------")
logger.debug("testing mymemory target")

fail_mymemory = 0
for key in MY_MEMORY_TARGET:
    key = key.lower()
    assert isinstance(MYMEMORY_KEY_VAL, Dict)
    lang_code = MYMEMORY_KEY_VAL[key]

    try:
        logger.debug(f"Translating {test_string} to {key}")
        res = MyMemoryTranslator(source="english", target=lang_code).translate(test_string)
        logger.debug(f"Translated {test_string} to {key} with result {res}")
    except Exception as e:
        logger.exception(f"Error {str(e)}")
        fail_mymemory += 1

logger.debug(f"Failed {fail_mymemory} times")
