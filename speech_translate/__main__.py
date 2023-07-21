import platform

from ._version import __version__
from .custom_logging import logger

from .components.window.main import MainWindow, AppTray, get_gpu_info, check_cuda_and_gpu
from .components.window.about import AboutWindow
from .components.window.log import LogWindow
from .components.window.setting import SettingWindow
from .components.window.transcribed import TcsWindow
from .components.window.translated import TlsWindow

def main():
    logger.info(f"App Version: {__version__}")
    logger.info(f"OS: {platform.system()} {platform.release()} {platform.version()} | CPU: {platform.processor()}")
    logger.info(f"GPU: {get_gpu_info()} | CUDA: {check_cuda_and_gpu()}")
    # --- GUI ---
    AppTray()  # Start tray app in the background
    main = MainWindow()
    TcsWindow(main.root)
    TlsWindow(main.root)
    SettingWindow(main.root)
    LogWindow(main.root)
    AboutWindow(main.root)
    main.root.mainloop()  # Start main app

if __name__ == "__main__":
    main()