from os import environ
from ._constants import LOG_FORMAT

# override loguru default format so we dont need to do logger.remove on the logger init
environ["LOGURU_FORMAT"] = LOG_FORMAT

from .ui.window.main import main  # noqa: E402

if __name__ == "__main__":
    main()
