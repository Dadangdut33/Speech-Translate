import os
import sys

toAdd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(toAdd)

from speech_translate.custom_logging import logger  # noqa: E402

print("This is a normal print text")
print("This is a looooooooooooooong print text")
x = {"a": 1, "b": 2, "c": 3}

logger.info(f"X is: {x}")

logger.info("This is an info")
logger.info("This is a looooooooooooooooooong info")
logger.debug("This is a debug")
logger.debug("This is a looooooooooooooooooooong debug")
logger.warning("This is a warning")
logger.warning("This is a looooooooooooooooooong  warning")
logger.error("This is an error")
logger.error("This is a looooooooooooooooooooong error")
try:
    x = 1 / 0
except Exception as e:
    logger.exception("This is an exception")
    logger.exception("This is a looooooooooooooooooooong exception")
    logger.exception(e)

sys.path.remove(toAdd)
