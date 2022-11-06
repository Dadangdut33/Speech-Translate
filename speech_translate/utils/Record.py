import threading
from typing import Literal
import whisper
import sounddevice as sd
from scipy.io.wavfile import write

from notifypy import Notify, exceptions
from datetime import datetime
from time import sleep, time
import os
import sys

sys.path.append("..")

from Globals import dir_temp, gClass, fJson, app_icon, app_name
from .Helper import modelSelectDict
from .Translate import google_tl, libre_tl, memory_tl

fs = 44100  # Sample rate


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


def whisper_transcribe(
    audio_name: str,
    model: whisper.Whisper,
    lang_source: str,
    auto: bool,
    verbose: bool,
    translate: bool = False,
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"] | None = None,
    lang_target: str | None = None,
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
    """
    gClass.enableTranscribing()
    result_Tc = ""

    # Transcribe
    print("-" * 50)
    print("> Transcribing Audio:", audio_name)
    try:
        if auto:
            result_Tc = model.transcribe(audio_name)
        else:
            result_Tc = model.transcribe(audio_name, language=lang_source)

        gClass.disableTranscribing()  # flag processing as done
    except Exception as e:
        gClass.disableTranscribing()  # flag processing as done if error
        print(e)
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
        translateThread = threading.Thread(target=whisper_translate, args=(audio_name, model, lang_source, lang_target, auto, verbose, engine, result_Tc["text"]))
        translateThread.start()


def whisper_translate(
    audio_name: str,
    model: whisper.Whisper,
    lang_source: str,
    lang_target: str,
    auto: bool,
    verbose: bool,
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"],
    transcribed_text: str | None = None,
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
    """
    gClass.translating = True
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
                if auto:
                    result_Tl = model.transcribe(audio_name, task="translate")
                else:
                    result_Tl = model.transcribe(audio_name, task="translate", language=lang_source)
            except Exception as e:
                print(e)
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

        gClass.translating = False  # flag processing as done. No need to check for transcription because it is done before this
    except Exception as e:
        gClass.translating = False  # flag processing as done if error
        print(e)
        return

    if engine == "Whisper":
        gClass.insertTbTranslated(result_Tl["text"].strip() + fJson.settingCache["separate_with"])  # type: ignore
        if verbose:
            print(result_Tl)  # type: ignore
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
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    print("-" * 50)
    print("> Task: Recording Audio")
    sd.wait()  # Wait until recording is finished
    print("Audio recording complete")
    write(audio_name, fs, myrecording)  # Save as WAV file


def rec_mic(modelInput: str, langSource: str, langTarget: str, transcibe: bool, translate: bool, engine: str, verbose: bool = False, cutOff: int = 5) -> None:
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
    print(f"> Start [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]")

    tempList = []  # List of all the temp files
    src_english = langSource == "english"
    auto = langSource == "auto detect"

    # there are no english models for large
    model = modelSelectDict[modelInput]
    if model != "large" and src_english:
        model = model + ".en"

    # Create a new whisper model
    audio_model = whisper.load_model(model)

    # turn off loadbar
    assert gClass.mw is not None
    gClass.mw.stop_loadBar("mic")

    # Record
    while gClass.recording:
        audio_name = os.path.join(dir_temp, datetime.now().strftime("%Y-%m-%d %H_%M_%S_%f")) + ".wav"  # temp audio file
        tempList.append(audio_name)

        # Start recording
        record_from_mic(audio_name, cutOff)

        # Do Task in thread so it doesn't block the recording
        if transcibe:  # if transcribe will automatically check translate on or not
            tcThread = threading.Thread(target=whisper_transcribe, args=(audio_name, audio_model, langSource, auto, verbose, translate, engine, langTarget))
            tcThread.start()
        elif translate:  # Translate only
            tlThread = threading.Thread(target=whisper_translate, args=(audio_name, audio_model, langSource, langTarget, auto, verbose, engine))
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
            print(f"> Waiting for transcription to finish ({timeNow:.2f}s)", end="\r", flush=True)
            sleep(0.1)  # waiting for process to finish
        print(end="\r\r", flush=True)

        startTime = time()
        while gClass.translating:
            timeNow = time() - startTime
            print(f"> Waiting for translation to finish ({timeNow:.2f}s)", end="\r", flush=True)
            sleep(0.1)  # waiting for process to finish
        print(end="\r\r", flush=True)

        print("-" * 50)
        print("Task: Cleaning up")
        for audio in tempList:
            try:
                os.remove(audio)
            except FileNotFoundError:
                pass
        print("> Done!")

    print(f"> End [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]")


def rec_pc(modelInput: str, langSource: str, langTarget: str, transcibe: bool, translate: bool, engine: str, verbose: bool = False) -> None:
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
    print(f"> Start [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]")
    pass
