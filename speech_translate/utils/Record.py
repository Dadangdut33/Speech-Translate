import threading
import whisper
import sounddevice as sd
from scipy.io.wavfile import write

import tkinter as tk
from datetime import datetime
import os
import sys

sys.path.append("..")

from Globals import dir_temp, autoStr, gClass
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
    print("Transcribing Audio")
    if auto:
        result = model.transcribe(f"{audio_name}.wav")
    else:
        result = model.transcribe(f"{audio_name}.wav", language=lang)

    if not verbose:
        predicted_text = result["text"]
        print("You said: " + predicted_text)  # type: ignore
    else:
        print(result)

    gClass.mw.tb_transcribed.insert(tk.END, result["text"] + " ")  # type: ignore


def record(audio_name, seconds=5):
    if not gClass.recording:
        return  # stop if canceled

    # Record
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    print("Recording Audio")
    sd.wait()  # Wait until recording is finished
    print("Audio recording complete")
    write(f"{audio_name}.wav", fs, myrecording)  # Save as WAV file


def transcribe(modelInput: str, lang: str, verbose: bool = False, cutOff: int = 5):
    english = lang == "english"
    auto = lang == autoStr.lower()
    model = modelSelectDict[modelInput]

    # there are no english models for large
    if model != "large" and english:
        model = model + ".en"

    audio_model = whisper.load_model(model)
    audio_name = os.path.join(dir_temp, datetime.now().strftime("%Y-%m-%d %H_%M_%S"))

    count = 0
    while gClass.recording:
        record(audio_name, cutOff)
        # whisper_transcribe(audio_name, audio_model, lang, verbose, auto)
        transcribeThread = threading.Thread(target=whisper_transcribe, args=(audio_name, audio_model, lang, verbose, auto))
        transcribeThread.start()

        count += 1
        if count == 2:
            gClass.recording = False
            break
