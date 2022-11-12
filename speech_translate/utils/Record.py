import os
import sys
import threading
from datetime import datetime
from multiprocessing import Process, Queue
from time import sleep, time
from typing import Literal

import sounddevice as sd
import whisper
from notifypy import Notify, exceptions
from scipy.io.wavfile import write

sys.path.append("..")

from Globals import app_icon, app_name, dir_temp, fJson, gClass

from .Helper import modelSelectDict
from .Translate import google_tl, libre_tl, memory_tl


def getInputDevice():
    return sd.query_devices(kind="input")


def getOutputDevice():
    return sd.query_devices(kind="output")


def notifyError(title: str, message: str) -> None:
    """Notify Error

    Args:
        title (str): Title of the notification
        message (str): Message of the notification
    """
    notification = Notify()
    notification.title = title
    notification.message = message
    notification.application_name = app_name
    try:
        notification.icon = app_icon
    except exceptions.InvalidIconPath:
        pass
    notification.send()


def multiProc_Whisper(queue: Queue, audio: str, modelName: str, auto: bool, transcribing: bool, lang_source: str | None = None):
    """Multi Processing for Whisper

    Args:
        queue (Queue): Queue
        audio (str): Audio File
        model (whisper.Whisper): Model
        auto (bool): Auto Detect Language
        transcribing (bool): Transcribing or not
        lang_source (str | None, optional): Source Language. Defaults to None.
    """
    print("Source Language: Auto" if auto else f"Source Language: {lang_source}")
    model = whisper.load_model(modelName)
    result = model.transcribe(audio, task="transcribe" if transcribing else "translate", language=lang_source if not auto else None)
    queue.put(result)


def whisper_transcribe(
    audio_name: str,
    modelName: str,
    lang_source: str,
    auto: bool,
    verbose: bool,
    translate: bool = False,
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"] | None = None,
    lang_target: str | None = None,
    multiProc: bool = False,
) -> None:
    """Transcribe Audio using whisper

    Args:
        audio_name (str): Name of the audio file
        model (whisper.Whisper): Model
        lang_source (str): Source Language
        auto (bool): Auto Detect Language
        verbose (bool): Verbose or not
        translate (bool, optional): Translate or not. Defaults to False.
        engine (Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"], optional): Engine to use for translation. Defaults to None.
        lang_target (str | None, optional): Target Language. Defaults to None.
        multiProc (bool, optional): Multi Processing or not. Defaults to False. (Use this to make the process killable)
    """
    gClass.enableTranscribing()
    result_Tc = ""

    # Transcribe
    print("-" * 50)
    print("> Transcribing Audio:", audio_name)
    try:
        if multiProc:
            queue = Queue()
            gClass.tc_proc = Process(target=multiProc_Whisper, args=(queue, audio_name, modelName, auto, True, lang_source), daemon=True)
            gClass.tc_proc.start()
            gClass.tc_proc.join()
            result_Tc = queue.get()
        else:
            print("Source Language: Auto" if auto else f"Source Language: {lang_source}")
            model = whisper.load_model(modelName)
            result_Tc = model.transcribe(audio_name, language=lang_source if not auto else None)

        gClass.disableTranscribing()
    except Exception as e:
        gClass.disableTranscribing()  # flag processing as done if error
        print(e)
        notifyError("Error: Transcribing Audio", str(e))
        return

    print("-" * 50)
    print("Transcribed:")  # type: ignore
    if not verbose:
        print(result_Tc["text"].strip())  # type: ignore
    else:
        print(result_Tc)

    # insert to textbox
    gClass.insertTbTranscribed(result_Tc["text"].strip() + fJson.settingCache["separate_with"])  # type: ignore

    if translate:
        translateThread = threading.Thread(target=whisper_translate, args=(audio_name, modelName, lang_source, lang_target, auto, verbose, engine, result_Tc["text"], multiProc), daemon=True)  # type: ignore
        translateThread.start()  # Start translation in a new thread to prevent blocking


def whisper_translate(
    audio_name: str,
    modelName: str,
    lang_source: str,
    lang_target: str,
    auto: bool,
    verbose: bool,
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"],
    transcribed_text: str | None = None,
    multiProc: bool = False,
) -> None:
    """Translate Audio

    Args:
        audio_name (str): Name of the audio file
        model (whisper.Whisper): Model
        lang_source (str): Source Language
        lang_target (str): Target Language
        auto (bool): Auto Detect Language
        verbose (bool): Verbose
        engine (Literal["Whisper", "Google", "LibreTranslate", "MyMemory", "MyMemoryTranslator"]): Engine to use for translation
        transcribed_text (str | None, optional): Transcribed Text. Defaults to None. If provided will use this model for online translation instead of offline using whisper.
        multiProc (bool, optional): Multi Processing or not. Defaults to False. (Use this to make the process killable)
    """
    gClass.enableTranslating()
    result_Tl = ""

    # Translate
    print("-" * 50)
    if transcribed_text is None:
        print("> Task: Translating Audio", audio_name)
    else:
        print("> Task: Translating Text")
    try:
        if engine == "Whisper":
            try:
                if multiProc:
                    queue = Queue()
                    gClass.tl_proc = Process(target=multiProc_Whisper, args=(queue, audio_name, modelName, auto, False, lang_source), daemon=True)
                    gClass.tl_proc.start()
                    gClass.tl_proc.join()
                    result_Tl = queue.get()
                else:
                    print("Source Language: Auto" if auto else f"Source Language: {lang_source}")
                    model = whisper.load_model(modelName)
                    result_Tl = model.transcribe(audio_name, task="translate", language=lang_source if not auto else None)

            except Exception as e:
                gClass.disableTranslating()  # flag processing as done if error
                print(e)
                notifyError("Error: translating with whisper failed", str(e))
                return

        elif engine == "Google":
            assert transcribed_text is not None
            oldMethod = "alt" in lang_target
            success, result_Tl = google_tl(transcribed_text, lang_source, lang_target, oldMethod)
            if not success:
                notifyError("Error: translation with google failed", result_Tl)

        elif engine == "LibreTranslate":
            assert transcribed_text is not None
            success, result_Tl = libre_tl(
                transcribed_text, lang_source, lang_target, fJson.settingCache["libre_https"], fJson.settingCache["libre_host"], fJson.settingCache["libre_port"], fJson.settingCache["libre_api_key"]
            )
            if not success:
                notifyError("Error: translation with libre failed", result_Tl)

        elif engine == "MyMemoryTranslator":
            assert transcribed_text is not None
            success, result_Tl = memory_tl(transcribed_text, lang_source, lang_target)
            if not success:
                notifyError("Error: translation with mymemory failed", str(result_Tl))

        gClass.disableTranslating()  # flag processing as done. No need to check for transcription because it is done before this
    except Exception as e:
        gClass.disableTranslating()  # flag processing as done if error
        print(e)
        notifyError("Error: translating failed", str(e))
        return

    if engine == "Whisper":
        gClass.insertTbTranslated(result_Tl["text"].strip() + fJson.settingCache["separate_with"])  # type: ignore
        print("-" * 50)
        print("Translated:")
        if verbose:
            print(result_Tl)  # type: ignore
        else:
            print(result_Tl["text"].strip())  # type: ignore
    else:
        gClass.insertTbTranslated(result_Tl.strip() + fJson.settingCache["separate_with"])  # type: ignore


def record_from_mic(audio_name: str, seconds=5) -> None:
    """Record Audio From Microphone

    Args:
        audio_name (str): Name of the audio file
        seconds (int, optional): Seconds to record. Defaults to 5.

    Returns:
        None
    """
    if not gClass.recording:
        return  # stop if canceled

    # Record
    fs = 44100
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    print("-" * 50)
    print(f"> Task: Recording Audio. (For {seconds} seconds)")
    sd.wait()  # Wait (blocking operation) until recording is finished
    print("Audio recording complete")
    write(audio_name, fs, myrecording)  # Save as WAV file


def rec_mic(modelInput: str, langSource: str, langTarget: str, transcibe: bool, translate: bool, engine: str) -> None:
    """Function to record audio from default microphone. It will then transcribe/translate the audio depending on the input.

    Args:
        modelInput (str): The model to use for the input.
        langSource (str): The language of the input.
        langTarget (str): The language to translate to.
        transcibe (bool): Whether to transcribe the audio.
        translate (bool): Whether to translate the audio.
        engine (str): The engine to use for the translation.
        verbose (bool, optional): Whether to print the verbose output. Defaults to False.
        cutOff (int, optional): The cutoff time for the recording. Defaults to 5.

    Returns:
        None
    """
    print(f"> Start Record (Mic) [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]")

    tempList = []  # List of all the temp files
    src_english = langSource == "english"
    auto = langSource == "auto detect"

    # there are no english models for large
    model = modelSelectDict[modelInput]
    if model != "large" and src_english:
        model = model + ".en"

    # turn off loadbar
    assert gClass.mw is not None
    gClass.mw.stop_loadBar("mic")

    # Record
    while gClass.recording:
        audio_name = os.path.join(dir_temp, datetime.now().strftime("%Y-%m-%d %H_%M_%S_%f")) + ".wav"  # temp audio file
        tempList.append(audio_name)

        # Start recording
        record_from_mic(audio_name, fJson.settingCache["cutOff"])

        # Do Task in thread so it doesn't block the recording
        if transcibe:  # if transcribe will automatically check translate on or not
            tcThread = threading.Thread(target=whisper_transcribe, args=(audio_name, model, langSource, auto, fJson.settingCache["verbose"], translate, engine, langTarget), daemon=True)
            tcThread.start()
        elif translate:  # Translate only
            tlThread = threading.Thread(target=whisper_translate, args=(audio_name, model, langSource, langTarget, auto, fJson.settingCache["verbose"], engine), daemon=True)
            tlThread.start()

        # Max tempfile
        if len(tempList) > fJson.settingCache["max_temp"]:
            try:
                os.remove(tempList.pop(0))  # pop from the first element
            except FileNotFoundError:
                pass

    # clean up
    if not fJson.settingCache["keep_audio"]:
        startTime = time()
        while gClass.transcribing:
            timeNow = time() - startTime
            print(f"> TC Wait ({timeNow:.2f}s)", end="\r", flush=True)
            sleep(0.1)  # waiting for process to finish

        startTime = time()
        while gClass.translating:
            timeNow = time() - startTime
            print(f"> TL Wait ({timeNow:.2f}s)", end="\r", flush=True)
            sleep(0.1)  # waiting for process to finish

        print("-" * 50)
        print("Task: Cleaning up")
        for audio in tempList:
            try:
                os.remove(audio)
            except FileNotFoundError:
                pass
        print("> Done!")

    print(f"> End [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]")


def rec_pc(modelInput: str, langSource: str, langTarget: str, transcibe: bool, translate: bool, engine: str) -> None:
    """Function to record audio from default microphone. It will then transcribe/translate the audio depending on the input.

    Args:
        modelInput (str): The model to use for the input.
        langSource (str): The language of the input.
        langTarget (str): The language to translate to.
        transcibe (bool): Whether to transcribe the audio.
        translate (bool): Whether to translate the audio.
        engine (str): The engine to use for the translation.
        verbose (bool, optional): Whether to print the verbose output. Defaults to False.

    Returns:
        None
    """
    print(f"> Start Record (System sound) [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]")

    src_english = langSource == "english"
    auto = langSource == "auto detect"

    # there are no english models for large
    model = modelSelectDict[modelInput]
    if model != "large" and src_english:
        model = model + ".en"

    # turn off loadbar
    assert gClass.mw is not None
    gClass.mw.stop_loadBar("pc")


def from_file(filePath: str, modelInput: str, langSource: str, langTarget: str, transcibe: bool, translate: bool, engine: str) -> None:
    """Function to record audio from default microphone. It will then transcribe/translate the audio depending on the input.

    Args:
        filePath (str): The path to the audio/video file.
        modelInput (str): The model to use for the input.
        langSource (str): The language of the input.
        langTarget (str): The language to translate to.
        transcibe (bool): Whether to transcribe the audio.
        translate (bool): Whether to translate the audio.
        engine (str): The engine to use for the translation.
        verbose (bool, optional): Whether to print the verbose output. Defaults to False.

    Returns:
        None
    """
    print(f"> Start [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]")

    src_english = langSource == "english"
    auto = langSource == "auto detect"

    # there are no english models for large
    modelName = modelSelectDict[modelInput]
    if modelName != "large" and src_english:
        modelName = modelName + ".en"

    # update button text
    gClass.mw.btn_record_file.config(text="Cancel")  # type: ignore

    # Proccess it
    startTime = time()
    if transcibe:  # if transcribe will automatically check translate on or not
        tcThread = threading.Thread(target=whisper_transcribe, args=(filePath, modelName, langSource, auto, fJson.settingCache["verbose"], translate, engine, langTarget, True), daemon=True)
        tcThread.start()

    elif translate:  # Translate only
        tlThread = threading.Thread(target=whisper_translate, args=(filePath, modelName, langSource, langTarget, auto, fJson.settingCache["verbose"], engine, True), daemon=True)
        tlThread.start()

    # wait for process to finish
    while gClass.transcribing:
        timeNow = time() - startTime
        print(f"> TC Wait ({timeNow:.2f}s)", end="\r", flush=True)
        sleep(0.1)  # waiting for process to finish

    while gClass.translating:
        timeNow = time() - startTime
        print(f"> TL Wait ({timeNow:.2f}s)", end="\r", flush=True)
        sleep(0.1)  # waiting for process to finish

    # turn off loadbar
    assert gClass.mw is not None
    gClass.mw.stop_loadBar("file")

    print(f"> End [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]")
