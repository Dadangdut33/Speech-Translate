import logging
import time
import os

# ------------------ #
dir_project: str = os.path.dirname(os.path.realpath(__file__))
dir_log: str = os.path.join(dir_project, "../log")
current_log: str = f"{time.strftime('%Y-%m-%d %H-%M-%S')}.log"
# make sure log folder exist
if not os.path.exists(dir_log):
    os.makedirs(dir_log)
# ------------------ #
class c_formatter(logging.Formatter):
    bold = "\033[1m"
    green = "\u001b[32;1m"
    white = "\u001b[37m"
    cyan = "\u001b[46m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[34;20m"
    reset = "\x1b[0m"
    textFormat = "%(levelname)-7s - %(message)s"
    timeFormat = blue + "%(asctime)s " + reset
    fileLineFormat = green + " (%(filename)s:%(lineno)d) [%(threadName)s]" + reset

    FORMATS = {
        logging.DEBUG: timeFormat + cyan + textFormat + reset + fileLineFormat,
        logging.INFO: timeFormat + white + textFormat + reset + fileLineFormat,
        logging.WARNING: timeFormat + yellow + textFormat + reset + fileLineFormat,
        logging.ERROR: timeFormat + red + textFormat + reset + fileLineFormat,
        logging.CRITICAL: timeFormat + bold_red + textFormat + reset + fileLineFormat,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class f_formatter(logging.Formatter):
    textFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: textFormat,
        logging.INFO: textFormat,
        logging.WARNING: textFormat,
        logging.ERROR: textFormat,
        logging.CRITICAL: textFormat,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# ------------------ #
# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(dir_log + "/" + current_log, encoding="utf-8")
c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.WARNING)

# Create formatters and add it to handlers
c_handler.setFormatter(c_formatter())
f_handler.setFormatter(f_formatter())

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

# ------------------ #
# to debug/test the logger
if __name__ == "__main__":
    print("This is a normal print text")
    print("This is a looooooooooooooong print text")

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
