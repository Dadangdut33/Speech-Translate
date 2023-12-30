import sys
from os import environ
from warnings import simplefilter

from ._constants import LOG_FORMAT

# override loguru default format so we dont need to do logger.remove on the logger init
environ["LOGURU_FORMAT"] = LOG_FORMAT

# If frozen, stdout will not work because there is no console. So we need to replace stdout
# with stderr so that any module that uses stdout will not break the app
if getattr(sys, "frozen", False):
    sys.stdout = sys.stderr

# supress general user warning like in pytorch
simplefilter("ignore", category=UserWarning)

from .ui.window.main import main  # pylint: disable=wrong-import-position

if __name__ == "__main__":
    main()
