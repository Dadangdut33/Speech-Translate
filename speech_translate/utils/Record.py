import os
import threading
import ast
import shlex
from datetime import datetime
from multiprocessing import Process, Queue
from time import sleep, time
from typing import Literal

import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import pyaudiowpatch as pyaudio
import wave

from speech_translate.Globals import app_icon, app_name, dir_temp, fJson, gClass
from speech_translate.Logging import logger
from speech_translate.components.MBox import Mbox

from .Helper import modelSelectDict, nativeNotify
from .Translate import google_tl, libre_tl, memory_tl
from .DownloadModel import check_model, download_model, verify_model


def getInputDevices():
    devices = sd.query_devices()
    devices = [device for device in devices if device["max_input_channels"] > 0]  # type: ignore # Filter out devices that are not input devices
    devices = [f"{device['name']}, {sd.query_hostapis(device['hostapi'])['name']}" for device in devices]  # type: ignore # Map the name
    return devices


def getOutputDevices():
    p = pyaudio.PyAudio()

    devices = p.get_device_count()
    devices = [p.get_device_info_by_index(i) for i in range(devices)]
    devices = [device for device in devices if device["maxOutputChannels"] > 0]  # Filter out devices that are not output devices
    devices = [f"{device['name']}, {sd.query_hostapis(device['hostApi'])['name']} [ID: {device['index']}]" for device in devices]  # type: ignore  # Map the name

    p.terminate()
    return devices


def getDefaultOutputDevice():
    p = pyaudio.PyAudio()
    sucess = False
    default_device = None
    try:
        # Get default WASAPI info
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_device = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        sucess = True
    except OSError:
        print("Looks like WASAPI is not available on the system.")
        sucess = False
    finally:
        p.terminate()
        return sucess, default_device


def verboseWhisperLogging(result):
    """
    This will log the result of the whisper engine in a verbose way.

    Args:
        result: whisper result

    """
    logger.debug(f"Language: {result['language']}")
    logger.debug(f"Text: {result['text']}")
    logger.debug(f"Segments:")
    for segment in result["segments"]:
        logger.debug(f"ID: {segment['id']}")
        logger.debug(f"Seek: {segment['seek']}")
        logger.debug(f"Start: {segment['start']}")
        logger.debug(f"End: {segment['end']}")
        logger.debug(f"Text: {segment['text']}")
        logger.debug(f"Tokens: {segment['tokens']}")
        logger.debug(f"Temperature: {segment['temperature']}")
        logger.debug(f"Avg Logprob: {segment['avg_logprob']}")
        logger.debug(f"Compression Ratio: {segment['compression_ratio']}")
        logger.debug(f"No Speech Prob: {segment['no_speech_prob']}")


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
    logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")
    model = whisper.load_model(modelName)
    result = model.transcribe(audio, task="transcribe" if transcribing else "translate", language=lang_source if not auto else None)
    queue.put(result)


def whisper_transcribe(
    audio_name: str,
    modelName: str,
    lang_source: str,
    auto: bool,
    verbose: bool,
    transcribe: bool,
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
    assert gClass.mw is not None
    gClass.enableTranscribing()
    gClass.mw.start_loadBar()
    result_Tc = ""

    # Transcribe
    logger.info("-" * 50)
    logger.info(f"Transcribing Audio: {audio_name.split(os.sep)[-1]}")

    # verify audio file exists
    if not os.path.isfile(audio_name):
        logger.warning("Audio file does not exist (It might have not been created/already cancelled)")
        gClass.disableTranslating()
        return

    try:
        if multiProc:
            queue = Queue()
            gClass.tc_proc = Process(target=multiProc_Whisper, args=(queue, audio_name, modelName, auto, True, lang_source), daemon=True)
            gClass.tc_proc.start()
            gClass.tc_proc.join()
            result_Tc = queue.get()
        else:
            logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")
            model = whisper.load_model(modelName)
            result_Tc = model.transcribe(audio_name, language=lang_source if not auto else None)

        gClass.disableTranscribing()
        gClass.mw.stop_loadBar()
    except Exception as e:
        gClass.disableTranscribing()  # flag processing as done if error
        gClass.mw.stop_loadBar()
        logger.exception(e)
        nativeNotify("Error: Transcribing Audio", str(e), app_icon, app_name)
        return

    logger.info("-" * 50)
    logger.info(f"Transcribed: : {audio_name.split(os.sep)[-1]}")  # type: ignore
    if not verbose:
        logger.debug(result_Tc["text"].strip())  # type: ignore
    else:
        verboseWhisperLogging(result_Tc)

    # insert to textbox
    if transcribe:
        if len(result_Tc["text"].strip()) > 0:  # type: ignore
            gClass.insertTbTranscribed(result_Tc["text"].strip() + ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"])))  # type: ignore
            gClass.insertDetachedTbTranscribed(result_Tc["text"].strip())  # type: ignore
        else:
            logger.warning("Transcribed Text is empty")
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
    assert gClass.mw is not None
    gClass.enableTranslating()
    gClass.mw.start_loadBar()
    result_Tl = ""

    # Translate
    logger.info("-" * 50)
    if transcribed_text is None:
        logger.info(f"Task: Translating Audio {audio_name.split(os.sep)[-1]}")
    else:
        logger.info("Task: Translating Text")

    try:
        if engine == "Whisper":
            try:
                # verify audio file exists
                if not os.path.isfile(audio_name):
                    logger.warning("Audio file does not exist (It might have not been created/already cancelled)")
                    gClass.disableTranslating()
                    return

                if multiProc:
                    queue = Queue()
                    gClass.tl_proc = Process(target=multiProc_Whisper, args=(queue, audio_name, modelName, auto, False, lang_source), daemon=True)
                    gClass.tl_proc.start()
                    gClass.tl_proc.join()
                    result_Tl = queue.get()
                else:
                    logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")
                    model = whisper.load_model(modelName)
                    result_Tl = model.transcribe(audio_name, task="translate", language=lang_source if not auto else None)

            except Exception as e:
                gClass.disableTranslating()  # flag processing as done if error
                gClass.mw.stop_loadBar()
                logger.exception(e)
                nativeNotify("Error: translating with whisper failed", str(e), app_icon, app_name)
                return

        elif engine == "Google":
            assert transcribed_text is not None
            oldMethod = "alt" in lang_target
            success, result_Tl = google_tl(transcribed_text, lang_source, lang_target, oldMethod)
            if not success:
                nativeNotify("Error: translation with google failed", result_Tl, app_icon, app_name)

        elif engine == "LibreTranslate":
            assert transcribed_text is not None
            success, result_Tl = libre_tl(
                transcribed_text, lang_source, lang_target, fJson.settingCache["libre_https"], fJson.settingCache["libre_host"], fJson.settingCache["libre_port"], fJson.settingCache["libre_api_key"]
            )
            if not success:
                nativeNotify("Error: translation with libre failed", result_Tl, app_icon, app_name)

        elif engine == "MyMemoryTranslator":
            assert transcribed_text is not None
            success, result_Tl = memory_tl(transcribed_text, lang_source, lang_target)
            if not success:
                nativeNotify("Error: translation with mymemory failed", str(result_Tl), app_icon, app_name)

        gClass.disableTranslating()  # flag processing as done. No need to check for transcription because it is done before this
        gClass.mw.stop_loadBar()
    except Exception as e:
        gClass.disableTranslating()  # flag processing as done if error
        gClass.mw.stop_loadBar()
        logger.exception(e)
        nativeNotify("Error: translating failed", str(e), app_icon, app_name)
        return

    if engine == "Whisper":
        if len(result_Tl["text"].strip()) > 0:  # type: ignore
            gClass.insertTbTranslated(result_Tl["text"].strip() + ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"])))  # type: ignore
            gClass.insertDetachedTbTranslated(result_Tl["text"].strip())  # type: ignore
        else:
            logger.warning("Translated Text is empty")
        logger.info("-" * 50)
        logger.info(f"Translated: {audio_name.split(os.sep)[-1]}")
        if verbose:
            verboseWhisperLogging(result_Tl)
        else:
            logger.debug(result_Tl["text"].strip())  # type: ignore
    else:
        if len(result_Tl.strip()) > 0:  # type: ignore
            gClass.insertTbTranslated(result_Tl.strip() + ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"])))  # type: ignore
            gClass.insertDetachedTbTranslated(result_Tl.strip() + ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"])))  # type: ignore
        else:
            logger.warning("Translated Text is empty")


def record_from_mic(audio_name: str, device: str, seconds=5) -> None:
    """Record Audio From Microphone

    Args:
        audio_name (str): Name of the audio file
        device (str): Device to use
        seconds (int, optional): Seconds to record. Defaults to 5.

    Returns:
        None
    """
    if not gClass.recording:
        return  # stop if canceled

    # Record
    fs = 44100
    channel = sd.query_devices(device, "input")["max_input_channels"]  # type: ignore

    logger.info("-" * 50)
    logger.info(f"Task: Recording Audio. (For {seconds} seconds)")

    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=channel, device=device)

    logger.info("Start record")
    logger.debug(f"Device: {device}")
    logger.debug(f"Channels: {channel}")

    sd.wait()  # Wait (blocking operation) until recording is finished
    logger.info("Audio recording complete")
    write(audio_name, fs, myrecording)  # Save as WAV file


def record_from_pc(audio_name: str, device: str, seconds=5) -> None:
    """Record Audio From PC

    Args:
        audio_name (str): Name of the audio file
        device (str): Device to use
        seconds (int, optional): Seconds to record. Defaults to 5.

    Returns:
        None
    """
    if not gClass.recording:
        return  # stop if canceled

    # Record
    logger.info("-" * 50)
    logger.info(f"Task: Recording Audio. (For {seconds} seconds)")

    # get the device id in [ID: x]
    device_id = device.split("[ID: ")[1]  # first get the id bracket
    device_id = device_id.split("]")[0]  # then get the id

    p = pyaudio.PyAudio()

    # Get default WASAPI speakers
    device_detail = p.get_device_info_by_index(int(device_id))  # type: ignore

    if not device_detail["isLoopbackDevice"]:
        for loopback in p.get_loopback_device_info_generator():
            """
            Try to find loopback device with same name(and [Loopback suffix]).
            Unfortunately, this is the most adequate way at the moment.
            """
            if device_detail["name"] in loopback["name"]:
                device_detail = loopback
                break
        else:
            # raise exception
            raise Exception("Loopback device not found")

    logger.debug(f"Recording from: ({device_detail['index']}){device_detail['name']}")

    wave_file = wave.open(audio_name, "wb")
    wave_file.setnchannels(device_detail["maxInputChannels"])
    wave_file.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
    wave_file.setframerate(int(device_detail["defaultSampleRate"]))

    def callback(in_data, frame_count, time_info, status):
        """Write frames and return PA flag"""
        wave_file.writeframes(in_data)
        return (in_data, pyaudio.paContinue)

    logger.info("Start record")

    with p.open(
        format=pyaudio.paInt16,
        channels=device_detail["maxInputChannels"],
        rate=int(device_detail["defaultSampleRate"]),
        frames_per_buffer=pyaudio.get_sample_size(pyaudio.paInt16),
        input=True,
        input_device_index=device_detail["index"],
        stream_callback=callback,
    ) as stream:
        """
        Opena PA stream via context manager.
        After leaving the context, everything will
        be correctly closed(Stream, PyAudio manager)
        """
        logger.info(f"The next {seconds} seconds will be written to {audio_name.split(os.sep)[-1]}")
        sleep(seconds)  # Blocking execution while playing

    wave_file.close()
    p.terminate()

    logger.info("Audio recording complete")


def rec_mic(device: str, modelInput: str, langSource: str, langTarget: str, transcribe: bool, translate: bool, engine: str) -> None:
    """Function to record audio from default microphone. It will then transcribe/translate the audio depending on the input.

    Args:
        device (str): Device to use for recording
        modelInput (str): The model to use for the input.
        langSource (str): The language of the input.
        langTarget (str): The language to translate to.
        transcibe (bool): Whether to transcribe the audio.
        translate (bool): Whether to translate the audio.
        engine (str): The engine to use for the translation.

    Returns:
        None
    """
    startProc = time()
    logger.info(f"Start Record (Mic)")

    tempList = []  # List of all the temp files
    src_english = langSource == "english"
    auto = langSource == "auto detect"
    whisperEngine = engine == "Whisper"

    # there are no english models for large
    modelName = modelSelectDict[modelInput]
    if modelName != "large" and src_english:
        modelName = modelName + ".en"

    # first check if model is downloaded
    if check_model(modelName) is False:
        gClass.mw.btn_record_mic.config(text="Downloading model... (Click to cancel)")  # type: ignore
        logger.info("Model is not yet downloaded")
        gClass.dl_proc = Process(target=download_model, args=(modelName,), daemon=True)
        gClass.dl_proc.start()
        nativeNotify("Downloading Model", "Downloading model for the first time. This may take a while. (Check the console/log for progress)", app_icon, app_name)
        gClass.dl_proc.join()

    # verify downloaded model
    if verify_model(modelName) is False:
        gClass.mw.btn_record_mic.config(text="Downloading model... (Click to cancel)")  # type: ignore
        logger.info("Model is downloaded but checksum does not match")
        logger.info("Redownloading the model")
        gClass.dl_proc = Process(target=download_model, args=(modelName,), daemon=True)
        gClass.dl_proc.start()
        nativeNotify("Downloading Model", "Model is downloaded but checksum does not match. Redownloading the model. This may take a while. (Check the console/log for progress)", app_icon, app_name)
        gClass.dl_proc.join()

    # turn off loadbar
    assert gClass.mw is not None
    gClass.mw.stop_loadBar("mic")

    # Record
    while gClass.recording:
        try:
            audio_name = os.path.join(dir_temp, datetime.now().strftime("%Y-%m-%d %H_%M_%S_%f")) + ".wav"  # temp audio file
            tempList.append(audio_name)

            # Start recording
            record_from_mic(audio_name, device, fJson.settingCache["cutOff"]["mic"])

            # Do Task in thread so it doesn't block the recording
            if translate and not transcribe and whisperEngine:  # if only translating and using the whisper engine
                tcThread = threading.Thread(target=whisper_translate, args=(audio_name, modelName, langSource, langTarget, auto, fJson.settingCache["verbose"], engine), daemon=True)
                tcThread.start()
            else:
                # will automatically check translate on or not depend on input
                # translate is called from here because other engine need to get transcribed text first if translating
                tcThread = threading.Thread(target=whisper_transcribe, args=(audio_name, modelName, langSource, auto, fJson.settingCache["verbose"], transcribe, translate, engine, langTarget), daemon=True)
                tcThread.start()

            # Max tempfile
            if len(tempList) > fJson.settingCache["max_temp"]:
                try:
                    os.remove(tempList.pop(0))  # pop from the first element
                except FileNotFoundError:
                    pass
        except Exception as e:
            logger.exception(e)
            nativeNotify("Error", str(e), app_icon, app_name)
            gClass.disableRecording()

    # clean up
    if not fJson.settingCache["keep_audio"]:
        gClass.mw.start_loadBar()
        startTime = time()
        while gClass.transcribing:
            timeNow = time() - startTime
            print(f"TC Wait ({timeNow:.2f}s)", end="\r", flush=True)
            sleep(0.1)  # waiting for process to finish

        startTime = time()
        while gClass.translating:
            timeNow = time() - startTime
            print(f"TL Wait ({timeNow:.2f}s)", end="\r", flush=True)
            sleep(0.1)  # waiting for process to finish

        logger.info("-" * 50)
        logger.info("Task: Cleaning up")
        for audio in tempList:
            try:
                os.remove(audio)
            except FileNotFoundError:
                pass
        logger.info("Done!")
        gClass.mw.stop_loadBar("mic")

    logger.info(f"End Record (MIC) [Total time: {time() - startProc:.2f}s]")


def rec_pc(device: str, modelInput: str, langSource: str, langTarget: str, transcribe: bool, translate: bool, engine: str) -> None:
    """Function to record audio from default microphone. It will then transcribe/translate the audio depending on the input.

    Args:
        device (str): Device to use for recording
        modelInput (str): The model to use for the input.
        langSource (str): The language of the input.
        langTarget (str): The language to translate to.
        transcibe (bool): Whether to transcribe the audio.
        translate (bool): Whether to translate the audio.
        engine (str): The engine to use for the translation.

    Returns:
        None
    """
    startProc = time()
    logger.info(f"Start Record (System sound)")

    tempList = []  # List of all the temp files
    src_english = langSource == "english"
    auto = langSource == "auto detect"
    whisperEngine = engine == "Whisper"

    # there are no english models for large
    modelName = modelSelectDict[modelInput]
    if modelName != "large" and src_english:
        modelName = modelName + ".en"

    # first check if model is downloaded
    if check_model(modelName) is False:
        gClass.mw.btn_record_pc.config(text="Downloading model... (Click to cancel)")  # type: ignore
        logger.info("Model is not yet downloaded")
        gClass.dl_proc = Process(target=download_model, args=(modelName,), daemon=True)
        gClass.dl_proc.start()
        nativeNotify("Downloading Model", "Downloading model for the first time. This may take a while. (Check the console/log for progress)", app_icon, app_name)
        gClass.dl_proc.join()

    # verify downloaded model
    if verify_model(modelName) is False:
        gClass.mw.btn_record_pc.config(text="Downloading model... (Click to cancel)")  # type: ignore
        logger.info("Model is downloaded but checksum does not match")
        logger.info("Redownloading the model")
        gClass.dl_proc = Process(target=download_model, args=(modelName,), daemon=True)
        gClass.dl_proc.start()
        nativeNotify("Downloading Model", "Model is downloaded but checksum does not match. Redownloading the model. This may take a while. (Check the console/log for progress)", app_icon, app_name)
        gClass.dl_proc.join()

    # turn off loadbar
    assert gClass.mw is not None
    gClass.mw.stop_loadBar("pc")

    # Record
    while gClass.recording:
        try:
            audio_name = os.path.join(dir_temp, datetime.now().strftime("%Y-%m-%d %H_%M_%S_%f")) + ".wav"  # temp audio file
            tempList.append(audio_name)

            # Start recording
            record_from_pc(audio_name, device, fJson.settingCache["cutOff"]["speaker"])

            # Do Task in thread so it doesn't block the recording
            if translate and not transcribe and whisperEngine:  # if only translating and using the whisper engine
                tcThread = threading.Thread(target=whisper_translate, args=(audio_name, modelName, langSource, langTarget, auto, fJson.settingCache["verbose"], engine), daemon=True)
                tcThread.start()
            else:
                # will automatically check translate on or not depend on input
                # translate is called from here because other engine need to get transcribed text first if translating
                tcThread = threading.Thread(target=whisper_transcribe, args=(audio_name, modelName, langSource, auto, fJson.settingCache["verbose"], transcribe, translate, engine, langTarget), daemon=True)
                tcThread.start()

            # Max tempfile
            if len(tempList) > fJson.settingCache["max_temp"]:
                try:
                    os.remove(tempList.pop(0))  # pop from the first element
                except FileNotFoundError:
                    pass
        except Exception as e:
            logger.exception(e)
            nativeNotify("Error", str(e), app_icon, app_name)
            gClass.disableRecording()

    # clean up
    if not fJson.settingCache["keep_audio"]:
        gClass.mw.start_loadBar()
        startTime = time()
        while gClass.transcribing:
            timeNow = time() - startTime
            print(f"TC Wait ({timeNow:.2f}s)", end="\r", flush=True)
            sleep(0.1)  # waiting for process to finish

        startTime = time()
        while gClass.translating:
            timeNow = time() - startTime
            print(f"TL Wait ({timeNow:.2f}s)", end="\r", flush=True)
            sleep(0.1)  # waiting for process to finish

        logger.info("-" * 50)
        logger.info("Task: Cleaning up")
        for audio in tempList:
            try:
                os.remove(audio)
            except FileNotFoundError:
                pass
        logger.info("Done!")
        gClass.mw.stop_loadBar("pc")

    logger.info(f"End Record (System Sound) [Total time: {time() - startProc:.2f}s]")


def from_file(filePath: str, modelInput: str, langSource: str, langTarget: str, transcribe: bool, translate: bool, engine: str) -> None:
    """Function to record audio from default microphone. It will then transcribe/translate the audio depending on the input.

    Args:
        filePath (str): The path to the audio/video file.
        modelInput (str): The model to use for the input.
        langSource (str): The language of the input.
        langTarget (str): The language to translate to.
        transcibe (bool): Whether to transcribe the audio.
        translate (bool): Whether to translate the audio.
        engine (str): The engine to use for the translation.

    Returns:
        None
    """
    startProc = time()
    logger.info(f"Start Process (FILE)")

    src_english = langSource == "english"
    auto = langSource == "auto detect"
    whisperEngine = engine == "Whisper"

    # there are no english models for large
    modelName = modelSelectDict[modelInput]
    if modelName != "large" and src_english:
        modelName = modelName + ".en"

    # update button text
    gClass.mw.btn_record_file.config(text="Cancel")  # type: ignore

    # first check if model is downloaded
    if check_model(modelName) is False:
        gClass.mw.btn_record_file.config(text="Downloading model... (Click to cancel)")  # type: ignore
        logger.info("Model is not yet downloaded")
        gClass.dl_proc = Process(target=download_model, args=(modelName,), daemon=True)
        gClass.dl_proc.start()
        nativeNotify("Downloading Model", "Downloading model for the first time. This may take a while. (Check the console/log for progress)", app_icon, app_name)
        gClass.dl_proc.join()

    # verify downloaded model
    if verify_model(modelName) is False:
        gClass.mw.btn_record_file.config(text="Downloading model... (Click to cancel)")  # type: ignore
        logger.info("Model is downloaded but checksum does not match")
        logger.info("Redownloading the model")
        gClass.dl_proc = Process(target=download_model, args=(modelName,), daemon=True)
        gClass.dl_proc.start()
        nativeNotify("Downloading Model", "Model is downloaded but checksum does not match. Redownloading the model. This may take a while. (Check the console/log for progress)", app_icon, app_name)
        gClass.dl_proc.join()

    # Proccess it
    if translate and not transcribe and whisperEngine:  # if only translating and using the whisper engine
        tcThread = threading.Thread(target=whisper_translate, args=(filePath, modelName, langSource, langTarget, auto, fJson.settingCache["verbose"], engine), daemon=True)
        tcThread.start()
    else:
        # will automatically check translate on or not depend on input
        # translate is called from here because other engine need to get transcribed text first if translating
        tcThread = threading.Thread(target=whisper_transcribe, args=(filePath, modelName, langSource, auto, fJson.settingCache["verbose"], transcribe, translate, engine, langTarget, True), daemon=True)
        tcThread.start()

    # wait for process to finish
    startTime = time()
    while gClass.transcribing:
        timeNow = time() - startTime
        print(f"TC Wait ({timeNow:.2f}s)", end="\r", flush=True)
        sleep(0.1)  # waiting for process to finish

    startTime = time()
    while gClass.translating:
        timeNow = time() - startTime
        print(f"TL Wait ({timeNow:.2f}s)", end="\r", flush=True)
        sleep(0.1)  # waiting for process to finish

    # turn off loadbar
    assert gClass.mw is not None
    gClass.mw.stop_loadBar("file")

    logger.info(f"End process (FILE) [Total time: {time() - startProc:.2f}s]")
