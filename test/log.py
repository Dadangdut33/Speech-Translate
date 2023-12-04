import os
import sys
import threading
from loguru import logger

toAdd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(toAdd)

from speech_translate._constants import LOG_FORMAT  # noqa: E402
from speech_translate._logging import init_logging  # noqa: E402

os.environ["LOGURU_FORMAT"] = LOG_FORMAT

init_logging("DEBUG")

# test file
# logger.add("file_{time}.log", format=my_format, level="DEBUG", encoding="utf-8", backtrace=True, diagnose=True)
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

x = {
    "index": 2,
    "text": "Hello",
    "color": "red",
}
test_dict = {'detail': "Not found"}
logger.info(f"example of logging dict = {str(test_dict)}")


def threaded_log():
    logger.info("info message")


threading.Thread(target=threaded_log).start()

logger.info("done")

sys.path.remove(toAdd)
