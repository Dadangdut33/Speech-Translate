from os import path

from sounddevice import play
from soundfile import read
from loguru import logger

from speech_translate._path import dir_assets


def beep():
    beepPath = path.join(dir_assets, "beep.mp3")
    try:
        data, fs = read(beepPath)
        play(data, fs, blocking=False)
    except Exception as e:
        logger.exception(e)
        pass
