import os
import sys
from typing import Dict
from loguru import logger

toAdd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(toAdd)

from speech_translate.utils.translate.language import ( # noqa: E402
    GOOGLE_SOURCE, LIBRE_SOURCE, MYMEMORY_SOURCE, GOOGLE_TARGET, LIBRE_TARGET,
    MY_MEMORY_TARGET, get_whisper_key_from_similar, GOOGLE_KEY_VAL, LIBRE_KEY_VAL, MYMEMORY_KEY_VAL
)

# print(MYMEMORY_KEY_VAL)
# exit()

# making sure that every key in google source pass the get_whisper_key_from_similar
# skipping auto detect because this is not a language and when on auto mode we already have a method set for it
# when in auto mode, we set the language parameter for the transcribing function to None so it will auto detect by whisper

# GOOGLE
logger.debug("---------------------------------------------------------")
logger.debug("testing google source")
for key in GOOGLE_SOURCE:
    key = key.lower()
    if key == "auto detect":
        continue

    get = get_whisper_key_from_similar(key)

    logger.debug("matching key with google key val")
    assert isinstance(GOOGLE_KEY_VAL, Dict)
    GOOGLE_KEY_VAL[key]
    logger.debug("matched")

logger.debug("---------------------------------------------------------")
logger.debug("testing google target")
for key in GOOGLE_TARGET:
    key = key.lower()
    # no need to match with whisper because this one is fed directly to google translate

    logger.debug("matching key with google key val")
    assert isinstance(GOOGLE_KEY_VAL, Dict)
    GOOGLE_KEY_VAL[key]
    logger.debug("matched")

# LIBRE
logger.debug("---------------------------------------------------------")
logger.debug("testing libre source")
for key in LIBRE_SOURCE:
    key = key.lower()
    if key == "auto detect":
        continue

    get = get_whisper_key_from_similar(key)

    logger.debug("matching key with libre key val")
    assert isinstance(LIBRE_KEY_VAL, Dict)
    LIBRE_KEY_VAL[key]
    logger.debug("matched")

logger.debug("---------------------------------------------------------")
logger.debug("testing libre target")
for key in LIBRE_TARGET:
    key = key.lower()
    # no need to match with whisper because this one is fed directly to libre translate

    logger.debug("matching key with libre key val")
    assert isinstance(LIBRE_KEY_VAL, Dict)
    LIBRE_KEY_VAL[key]
    logger.debug("matched")

# MYMEMORY
logger.debug("---------------------------------------------------------")
logger.debug("testing mymemory source")
for key in MYMEMORY_SOURCE:
    key = key.lower()
    # no auto detect in mymemory
    get = get_whisper_key_from_similar(key)

    logger.debug("matching key with mymemory key val")
    assert isinstance(MYMEMORY_KEY_VAL, Dict)
    MYMEMORY_KEY_VAL[key]
    logger.debug("matched")

logger.debug("---------------------------------------------------------")
logger.debug("testing mymemory target")
for key in MY_MEMORY_TARGET:
    key = key.lower()
    # no need to match with whisper because this one is fed directly to mymemory translate

    logger.debug("matching key with mymemory key val")
    assert isinstance(MYMEMORY_KEY_VAL, Dict)
    MYMEMORY_KEY_VAL[key]
    logger.debug("matched")


# see difference between each of them
def get_diff(list1, list2):
    return list(set(list1) - set(list2))


logger.debug("---------------------------------------------------------")
logger.debug("checking difference between each source")
logger.debug(f"google source - libre source: {get_diff(GOOGLE_SOURCE, LIBRE_SOURCE)}")
logger.debug(f"google source - mymemory source: {get_diff(GOOGLE_SOURCE, MYMEMORY_SOURCE)}")
logger.debug(f"libre source - google source: {get_diff(LIBRE_SOURCE, GOOGLE_SOURCE)}")
logger.debug(f"libre source - mymemory source: {get_diff(LIBRE_SOURCE, MYMEMORY_SOURCE)}")
logger.debug(f"mymemory source - google source: {get_diff(MYMEMORY_SOURCE, GOOGLE_SOURCE)}")
logger.debug(f"mymemory source - libre source: {get_diff(MYMEMORY_SOURCE, LIBRE_SOURCE)}")

logger.debug("---------------------------------------------------------")
logger.debug("checking difference between each target")
logger.debug(f"google target - libre target: {get_diff(GOOGLE_TARGET, LIBRE_TARGET)}")
logger.debug(f"google target - mymemory target: {get_diff(GOOGLE_TARGET, MY_MEMORY_TARGET)}")
logger.debug(f"libre target - google target: {get_diff(LIBRE_TARGET, GOOGLE_TARGET)}")
logger.debug(f"libre target - mymemory target: {get_diff(LIBRE_TARGET, MY_MEMORY_TARGET)}")
logger.debug(f"mymemory target - google target: {get_diff(MY_MEMORY_TARGET, GOOGLE_TARGET)}")
logger.debug(f"mymemory target - libre target: {get_diff(MY_MEMORY_TARGET, LIBRE_TARGET)}")

# if no error, mean all check passed
# print length of each
logger.debug("---------------------------------------------------------")
logger.debug("all check passed")
# remove auto first from all source
GOOGLE_SOURCE.remove("Auto detect")
LIBRE_SOURCE.remove("Auto detect")

logger.debug(f"length of google source (google translate language that is compatible with whisper): {len(GOOGLE_SOURCE)} ")
logger.debug(f"length of google target (all google translate compatible): {len(GOOGLE_TARGET)} ")
logger.debug(f"length of libre source (libre translate language that is compatible with whisper): {len(LIBRE_SOURCE)} ")
logger.debug(f"length of libre target (all libre translate compatible): {len(LIBRE_TARGET)} ")
logger.debug(
    f"length of mymemory source (mymemory translate language that is compatible with whisper): {len(MYMEMORY_SOURCE)} "
)
logger.debug(f"length of mymemory target (all mymemory translate compatible): {len(MY_MEMORY_TARGET)} ")
logger.debug("---------------------------------------------------------")
logger.info("To verify each language compatibility with the translator, you can run the test in test/test/translate.py")

sys.path.remove(toAdd)
