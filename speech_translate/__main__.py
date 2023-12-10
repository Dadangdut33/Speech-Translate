import subprocess
from os import environ
from warnings import simplefilter

from numba.core.errors import NumbaDeprecationWarning, NumbaPendingDeprecationWarning

from ._constants import LOG_FORMAT

# override loguru default format so we dont need to do logger.remove on the logger init
environ["LOGURU_FORMAT"] = LOG_FORMAT


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
