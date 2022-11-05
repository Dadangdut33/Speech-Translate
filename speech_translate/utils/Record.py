import threading
import whisper
import sounddevice as sd
from scipy.io.wavfile import write

import tkinter as tk
from datetime import datetime
import os
import sys

sys.path.append("..")

from Globals import dir_temp, autoStr, gClass, fJson
from .Helper import modelSelectDict

fs = 44100  # Sample rate


def getInputDevice():
    return sd.query_devices(kind="input")


def getOutputDevice():
    return sd.query_devices(kind="output")


def whisper_transcribe(audio_name, model: whisper.Whisper, lang: str, verbose: bool, auto: bool):
    if not gClass.recording:
        return  # stop if canceled

    # Transcribed
    print("> Transcribing Audio")
    try:
        if auto:
            result = model.transcribe(f"{audio_name}.wav")
        else:
            result = model.transcribe(f"{audio_name}.wav", language=lang)
    except Exception as e:
        print(e)
        return

    if not verbose:
        predicted_text = result["text"]
        print("You said: " + predicted_text)  # type: ignore
    else:
        print(result)

    assert gClass.mw is not None
    gClass.mw.tb_transcribed.insert(tk.END, result["text"] + fJson.settingCache["separate_with"])  # type: ignore


def record(audio_name, seconds=5):
    if not gClass.recording:
        return  # stop if canceled

    # Record
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    print(">>>")
    print("> Recording Audio")
    sd.wait()  # Wait until recording is finished
    print("Audio recording complete")
    write(f"{audio_name}.wav", fs, myrecording)  # Save as WAV file


def transcribe_mic(modelInput: str, lang: str, verbose: bool = False, cutOff: int = 5):
    english = lang == "english"
    auto = lang == autoStr.lower()
    model = modelSelectDict[modelInput]
    tempList = []

    # there are no english models for large
    if model != "large" and english:
        model = model + ".en"

    audio_model = whisper.load_model(model)

    # turn off loadbar
    assert gClass.mw is not None
    gClass.mw.stop_loadBar("mic")

    while gClass.recording:
        audio_name = os.path.join(dir_temp, datetime.now().strftime("%Y-%m-%d %H_%M_%S_%f"))
        tempList.append(audio_name)
        record(audio_name, cutOff)  # record
        transcribeThread = threading.Thread(target=whisper_transcribe, args=(audio_name, audio_model, lang, verbose, auto))  # transcribe thread
        transcribeThread.start()  # transcribe in a thread so its not blocking

        # temp max
        if len(tempList) > fJson.settingCache["max_temp"]:
            # pop from the first element
            try:
                os.remove(tempList.pop(0) + ".wav")
            except FileNotFoundError:
                pass

    # clean up
    if not fJson.settingCache["keep_audio"]:
        for audio in tempList:
            try:
                os.remove(f"{audio}.wav")
            except FileNotFoundError:
                pass
