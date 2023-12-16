import os
import subprocess
import sys
from warnings import simplefilter

from numba.core.errors import NumbaDeprecationWarning, NumbaPendingDeprecationWarning

from ._constants import LOG_FORMAT

# override loguru default format so we dont need to do logger.remove on the logger init
os.environ["LOGURU_FORMAT"] = LOG_FORMAT

# If frozen, stdout will not work because there is no console. So we need to replace stdout
# with stderr so that any module that uses stdout will not break the app
if getattr(sys, "frozen", False):
    sys.stdout = sys.stderr


# monkey patch subprocess.run
class NoConsolePopen(subprocess.Popen):
    """
    A custom Popen class that disables creation of a console window
    """
    def __init__(self, args, **kwargs):
        if 'startupinfo' not in kwargs:
            kwargs['startupinfo'] = subprocess.STARTUPINFO()
            kwargs['startupinfo'].dwFlags |= subprocess.STARTF_USESHOWWINDOW
        super().__init__(args, **kwargs)


subprocess.Popen = NoConsolePopen

# remove numba warnings
simplefilter("ignore", category=NumbaDeprecationWarning)
simplefilter("ignore", category=NumbaPendingDeprecationWarning)
simplefilter("ignore", category=UserWarning)  # supress general user warning like in pytorch

from .ui.window.main import main  # pylint: disable=wrong-import-position

if __name__ == "__main__":
    main()
