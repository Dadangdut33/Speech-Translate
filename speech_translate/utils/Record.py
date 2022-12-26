import io
import os
import platform
import threading
import ast
import shlex
import numpy
from datetime import datetime, timedelta
from multiprocessing import Process, Queue
from time import sleep, time
from typing import Literal, Optional

import whisper
import sounddevice as sd

if platform.system() == "Windows":
    import pyaudiowpatch as pyaudio
else:
    import pyaudio  # type: ignore


import wave

from speech_translate.Globals import app_icon, app_name, dir_temp, fJson, gClass
from speech_translate.Logging import logger

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
    devices = [device for device in devices if device["maxOutputChannels"] > 0]  # type: ignore # Filter out devices that are not output devices
    devices = [f"{device['name']}, {sd.query_hostapis(device['hostApi'])['name']} [ID: {device['index']}]" for device in devices]  # type: ignore  # Map the name

    p.terminate()
    return devices


def getDefaultInputDevice():
    return sd.query_devices(kind="input")


def getDefaultOutputDevice():
    p = pyaudio.PyAudio()
    sucess = False
    default_device = None
    try:
        # Get default WASAPI info
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_device = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])  # type: ignore
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

    Parameters
    ----
    result:
        whisper result
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


def checkModelFirst(modelName: str):
    # check if model is downloaded
    if check_model(modelName) is False:
        gClass.mw.btn_record_pc.config(text="Downloading model... (Click to cancel)")  # type: ignore
        logger.info("Model is not yet downloaded")
        gClass.dl_proc = Process(target=download_model, args=[modelName], daemon=True)
        gClass.dl_proc.start()
        nativeNotify("Downloading Model", "Downloading model for the first time. This may take a while. (Check the console/log for progress)", app_icon, app_name)
        gClass.dl_proc.join()

    # verify downloaded model
    if verify_model(modelName) is False:
        gClass.mw.btn_record_pc.config(text="Downloading model... (Click to cancel)")  # type: ignore
        logger.info("Model is downloaded but checksum does not match")
        logger.info("Redownloading the model")
        gClass.dl_proc = Process(target=download_model, args=[modelName], daemon=True)
        gClass.dl_proc.start()
        nativeNotify("Downloading Model", "Model is downloaded but checksum does not match. Redownloading the model. This may take a while. (Check the console/log for progress)", app_icon, app_name)
        gClass.dl_proc.join()


def rec_realTime(
    lang_source: str,
    lang_target: str,
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"],
    modelInput: str,
    device: str,
    transcribe: bool,
    translate: bool,
    speaker: bool = False,
) -> None:
    """
    Function to record audio and translate it in real time. Speaker as input can only be used on Windows.
    Other OS need to use mic, speaker can be used only by using Loopback software such as PulseAudio, blackhole, etc.

    Parameters
    ----
    lang_source: str
        Source language
    lang_target: str
        Target language
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"]
        Translation engine
    modelInput: str
        Model to use
    device: str
        Device to use
    transcribe: bool
        Whether to transcribe the audio
    translate: bool
        Whether to translate the audio
    speaker: bool, optional
        Whether to use speaker diarization

    Returns
    ----
    None
    """
    src_english = lang_source == "english"
    auto = lang_source == "auto detect"
    whisperEngine = engine == "Whisper"

    # there are no english models for large
    modelName = modelSelectDict[modelInput]
    if modelName != "large" and src_english:
        modelName = modelName + ".en"

    # load model
    model = whisper.load_model(modelName)

    # read from settings
    sample_rate = int(fJson.settingCache["sample_rate"])
    chunk_size = int(fJson.settingCache["chunk_size"])
    max_sentences = int(fJson.settingCache["max_sentences"])
    max_int16 = 2**15
    separator = ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"]))

    # recording session init
    global prev_tl_text, sentences_tl
    tempList = []
    sentences_tc = []
    sentences_tl = []
    prev_tc_text = ""
    prev_tl_text = ""
    next_transcribe_time = None
    last_sample = bytes()
    transcribe_rate = timedelta(seconds=fJson.settingCache["transcribe_rate"] / 1000)
    max_record_time = int(fJson.settingCache["speaker_maxBuffer"]) if speaker else int(fJson.settingCache["mic_maxBuffer"])
    task = "translate" if whisperEngine and translate and not transcribe else "transcribe"  # if only translate to english using whisper engine

    checkModelFirst(modelName)
    if not gClass.recording:  # if cancel button is pressed while downloading
        return

    # stop loadbar
    assert gClass.mw is not None
    gClass.mw.stop_loadBar("mic" if not speaker else "pc")

    # ----------------- Start recording -----------------
    logger.info("-" * 50)
    logger.info(f"Task: {task}")
    logger.info(f"Modelname: {modelName}")
    logger.info(f"Engine: {engine}")
    logger.info(f"Auto mode: {auto}")
    logger.info(f"Source Lang: {lang_source}")
    if translate:
        logger.info(f"Target Lang: {lang_target}")

    # pyaudio
    p = pyaudio.PyAudio()

    if speaker:
        # get the device id in [ID: x]
        device_id = device.split("[ID: ")[1]  # first get the id bracket
        device_id = device_id.split("]")[0]  # then get the id

        # Get device detail
        device_detail = p.get_device_info_by_index(int(device_id))

        if not device_detail["isLoopbackDevice"]:
            for loopback in p.get_loopback_device_info_generator():  # type: ignore
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

        # speaker will automatically use the max sample rate and channels, because it won't work if not set like this
        num_of_channels = int(device_detail["maxInputChannels"])
        sample_rate = int(device_detail["defaultSampleRate"])
        logger.debug(f"Sample Rate {sample_rate} | channels {num_of_channels}")
    else:
        # get the device id from sounddevice module
        device_id = sd.query_devices(device, "input")["index"]  # type: ignore
        device_detail = p.get_device_info_by_index(int(device_id))  # Get device detail
        num_of_channels = 1

        # check if user set auto stream param
        if fJson.settingCache["auto_stream_params"]:
            sample_rate = int(device_detail["defaultSampleRate"])
            num_of_channels = int(device_detail["maxInputChannels"])

    logger.debug(f"Device: ({device_detail['index']}) {device_detail['name']}")
    logger.debug(device_detail)

    gClass.stream = p.open(format=pyaudio.paInt16, channels=num_of_channels, rate=sample_rate, input=True, frames_per_buffer=chunk_size, input_device_index=int(device_detail["index"]))
    record_thread = threading.Thread(target=realtime_recording_thread, args=[chunk_size], daemon=True)
    record_thread.start()

    logger.debug(f"Record Session Started")

    # transcribing thread
    while gClass.recording:
        if not gClass.data_queue.empty():
            now = datetime.utcnow()
            # Set next_transcribe_time for the first time.
            if not next_transcribe_time:
                next_transcribe_time = now + transcribe_rate

            # Only run transcription occasionally. This reduces stress on the GPU and makes transcriptions
            # more accurate because they have more audio context, but makes the transcription less real time.
            if now > next_transcribe_time:
                next_transcribe_time = now + transcribe_rate

                # Getting the stream data from the queue.
                while not gClass.data_queue.empty():
                    data = gClass.data_queue.get()
                    last_sample += data

                # Write out raw frames as a wave file.
                wav_file = io.BytesIO()
                wav_writer: wave.Wave_write = wave.open(wav_file, "wb")
                wav_writer.setframerate(sample_rate)
                wav_writer.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                wav_writer.setnchannels(num_of_channels)
                wav_writer.writeframes(last_sample)  # get the audio data from the buffer.
                wav_writer.close()

                # Read the audio data
                wav_file.seek(0)
                wav_reader: wave.Wave_read = wave.open(wav_file)
                samples = wav_reader.getnframes()
                audio = wav_reader.readframes(samples)
                wav_reader.close()

                logger.info(f"Processing Audio")
                if speaker or num_of_channels > 1:
                    # If stereo or speaker, the old fast method does not work so we have to resort to using the old, a little slower, but working method
                    # which is to save the audio file and read it directly to the whisper model
                    audio_target = os.path.join(dir_temp, datetime.now().strftime("%Y-%m-%d %H_%M_%S_%f")) + ".wav"
                    tempList.append(audio_target)  # add to the temp list to delete later

                    # block until the file is written
                    with open(audio_target, "wb") as f:
                        f.write(wav_file.getvalue())  # write it

                    if len(tempList) > fJson.settingCache["max_temp"] and not fJson.settingCache["keep_temp"]:
                        # delete the oldest file
                        os.remove(tempList[0])
                        tempList.pop(0)
                else:
                    # Convert the wave data straight to a numpy array for the model.
                    # https://stackoverflow.com/a/62298670
                    audio_as_np_int16 = numpy.frombuffer(audio, dtype=numpy.int16)
                    audio_as_np_float32 = audio_as_np_int16.astype(numpy.float32)
                    audio_target = audio_as_np_float32 / max_int16  # normalized as Numpy array

                logger.info(f"Transcribing")
                result = model.transcribe(audio_target, language=lang_source if not auto else None, task=task)
                text = result["text"].strip()  # type: ignore

                if len(text) > 0 and text != prev_tc_text:
                    prev_tc_text = text
                    if transcribe:
                        # this works like this:
                        # clear the textbox first, then insert the text. The text inserted is a continuation of the previous text.
                        # the longer it is the clearer the transcribed text will be, because of more context.
                        logger.info(f"New transcribed text")
                        if fJson.settingCache["verbose"]:
                            logger.info(verboseWhisperLogging(result))
                        else:
                            logger.debug(f"{text}")
                        gClass.clearMwTc()
                        gClass.clearExTc()
                        toExTc = ""

                        # insert previous sentences if there are any
                        for sentence in sentences_tc:
                            gClass.insertMwTbTc(sentence + separator)
                            toExTc += sentence + separator

                        # insert the current sentence after previous sentences
                        gClass.insertMwTbTc(text + separator)
                        toExTc += text + separator
                        gClass.insertExTbTc(toExTc)

                    if translate:
                        if whisperEngine:
                            tlThread = threading.Thread(target=whisper_realtime_tl, args=[audio_target, lang_source, auto, model], daemon=True)
                            tlThread.start()
                        else:
                            tlThread = threading.Thread(target=realtime_tl, args=[text, lang_source, lang_target, engine], daemon=True)
                            tlThread.start()

                # break up the buffer If we've reached max recording time
                audio_length_in_seconds = samples / float(sample_rate)
                logger.debug(f"Audio length: {audio_length_in_seconds}")
                if audio_length_in_seconds > max_record_time:
                    last_sample = bytes()

                    if transcribe:
                        sentences_tc.append(prev_tc_text)
                        if len(sentences_tc) >= max_sentences:
                            sentences_tc.pop(0)

                    if translate:
                        sentences_tl.append(prev_tl_text)
                        if len(sentences_tl) >= max_sentences:
                            sentences_tl.pop(0)

        sleep(0.1)
    else:
        logger.info("-" * 50)
        logger.info("Stopping stream")
        gClass.stream.stop_stream()
        gClass.stream.close()
        logger.info("Stream stopped and closed")

        logger.info("-" * 50)
        logger.info("Terminating pyaudio")
        p.terminate()
        logger.info("Pyaudio terminated")

        if (speaker or num_of_channels > 1) and not fJson.settingCache["keep_temp"]:
            logger.info("-" * 50)
            logger.info("Cleaning up audioFiles")
            for audio in tempList:
                try:
                    os.remove(audio)
                except FileNotFoundError:
                    pass
            logger.info("Done!")


def realtime_recording_thread(chunk_size: int):
    """Record Audio From stream buffer and save it to a queue"""
    assert gClass.stream is not None
    while gClass.recording:  # Record in a thread at a fast rate.
        data = gClass.stream.read(chunk_size)
        gClass.data_queue.put(data)


def whisper_realtime_tl(audio_normalised: numpy.ndarray, lang_source: str, auto: bool, model: whisper.Whisper):
    """Translate the result"""
    assert gClass.mw is not None
    gClass.enableTranslating()
    global prev_tl_text, sentences_tl
    separator = ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"]))

    result = model.transcribe(audio_normalised, language=lang_source if not auto else None, task="translate")
    text = result["text"].strip()  # type: ignore

    if len(text) > 0 and text != prev_tl_text:
        prev_tl_text = text
        # this works like this:
        # clear the textbox first, then insert the text. The text inserted is a continuation of the previous text.
        # the longer it is the clearer the transcribed text will be, because of more context.
        gClass.clearMwTl()
        gClass.clearExTl()
        toExTb = ""

        # insert previous sentences if there are any
        for sentence in sentences_tl:
            gClass.insertMwTbTl(sentence + separator)
            toExTb += sentence + separator

        # insert the current sentence after previous sentences
        gClass.insertMwTbTl(text + separator)
        toExTb += text + separator
        gClass.insertExTbTl(toExTb)


def realtime_tl(text: str, lang_source: str, lang_target: str, engine: Literal["Google", "LibreTranslate", "MyMemoryTranslator"]):
    """Translate the result"""
    assert gClass.mw is not None
    gClass.enableTranslating()
    global prev_tl_text, sentences_tl
    result_Tl = ""
    separator = ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"]))

    try:
        if engine == "Google":
            oldMethod = "alt" in lang_target
            success, result_Tl = google_tl(text, lang_source, lang_target, oldMethod)
            if not success:
                nativeNotify("Error: translation with google failed", result_Tl, app_icon, app_name)

        elif engine == "LibreTranslate":
            success, result_Tl = libre_tl(text, lang_source, lang_target, fJson.settingCache["libre_https"], fJson.settingCache["libre_host"], fJson.settingCache["libre_port"], fJson.settingCache["libre_api_key"])
            if not success:
                nativeNotify("Error: translation with libre failed", result_Tl, app_icon, app_name)

        elif engine == "MyMemoryTranslator":
            success, result_Tl = memory_tl(text, lang_source, lang_target)
            if not success:
                nativeNotify("Error: translation with mymemory failed", str(result_Tl), app_icon, app_name)

        gClass.disableTranslating()  # flag processing as done. No need to check for transcription because it is done before this
    except Exception as e:
        gClass.disableTranslating()  # flag processing as done if error
        logger.exception(e)
        nativeNotify("Error: translating failed", str(e), app_icon, app_name)
        return

    result_Tl = result_Tl.strip()  # type: ignore
    if len(result_Tl) > 0 and result_Tl != prev_tl_text:
        prev_tl_text = result_Tl
        # this works like this:
        # clear the textbox first, then insert the text. The text inserted is a continuation of the previous text.
        # the longer it is the clearer the transcribed text will be, because of more context.
        gClass.clearMwTl()
        gClass.clearExTl()
        toExTb = ""

        # insert previous sentences if there are any
        for sentence in sentences_tl:
            gClass.insertMwTbTl(sentence + separator)
            toExTb += sentence + separator

        # insert the current sentence after previous sentences
        gClass.insertMwTbTl(result_Tl + separator)
        toExTb += result_Tl + separator
        gClass.insertExTbTl(toExTb)


# --------------------------------------------------------------------------------------------------------------------------------------
# multiproc file
def whisper_multiproc(queue: Queue, audio: str, modelName: str, auto: bool, transcribing: bool, lang_source: Optional[str] = None):
    """Multi Processing for Whisper

    Args:
        queue (Queue): Queue
        audio (str): Audio File
        model (whisper.Whisper): Model
        auto (bool): Auto Detect Language
        transcribing (bool): Transcribing or not
        lang_source (str, optional): Source Language. Defaults to None.
    """
    logger.debug("Source Language: Auto" if auto else f"Source Language: {lang_source}")
    model = whisper.load_model(modelName)
    result = model.transcribe(audio, task="transcribe" if transcribing else "translate", language=lang_source if not auto else None)
    queue.put(result)


def multiproc_tl(toTranslate: str, lang_source: str, lang_target: str, modelName: str, engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"], auto: bool):
    """Translate the result

    Args:
        toTranslate (str or int): Audio File or Text
        lang_source (str): Source Language
        lang_target (str): Target Language
        modelName (str): Model Name
        engine (Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"]): Engine
        auto (bool): Auto Detect Language

    """
    assert gClass.mw is not None
    gClass.enableTranslating()
    gClass.mw.start_loadBar()
    result_Tl = ""
    separator = ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"]))

    logger.debug(f"Translating...")

    try:
        if engine == "Whisper":
            try:
                # verify audio file exists
                if not os.path.isfile(toTranslate):
                    logger.warning("Audio file does not exist")
                    gClass.disableTranslating()
                    return

                queue = Queue()
                gClass.tl_proc = Process(target=whisper_multiproc, args=[queue, toTranslate, modelName, auto, False, lang_source], daemon=True)
                gClass.tl_proc.start()
                gClass.tl_proc.join()
                result_Tl = queue.get()

            except Exception as e:
                gClass.disableTranslating()  # flag processing as done if error
                gClass.mw.stop_loadBar()
                logger.exception(e)
                nativeNotify("Error: translating with whisper failed", str(e), app_icon, app_name)
                return

        elif engine == "Google":
            oldMethod = "alt" in lang_target
            success, result_Tl = google_tl(toTranslate, lang_source, lang_target, oldMethod)
            if not success:
                nativeNotify("Error: translation with google failed", result_Tl, app_icon, app_name)

        elif engine == "LibreTranslate":
            success, result_Tl = libre_tl(toTranslate, lang_source, lang_target, fJson.settingCache["libre_https"], fJson.settingCache["libre_host"], fJson.settingCache["libre_port"], fJson.settingCache["libre_api_key"])
            if not success:
                nativeNotify("Error: translation with libre failed", result_Tl, app_icon, app_name)

        elif engine == "MyMemoryTranslator":
            success, result_Tl = memory_tl(toTranslate, lang_source, lang_target)
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
            gClass.insertMwTbTl(result_Tl["text"].strip() + separator)  # type: ignore
        else:
            logger.warning("Translated Text is empty")

        logger.info("-" * 50)
        logger.info(f"Translated:")
        if fJson.settingCache["verbose"]:
            verboseWhisperLogging(result_Tl)
        else:
            logger.debug(result_Tl["text"].strip())  # type: ignore
    else:
        resGet = result_Tl.strip()  # type: ignore
        if len(resGet) > 0:
            gClass.insertMwTbTl(resGet + separator)
        else:
            logger.warning("Translated Text is empty")


def multiproc_tc(
    audio_name: str,
    lang_source: str,
    lang_target: str,
    modelName: str,
    auto: bool,
    transcribe: bool,
    translate: bool,
    engine: Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"],
) -> None:
    """Transcribe Audio using whisper

    Args:
        audio_name (str): Audio file name
        lang_source (str): Source Language
        lang_target (str): Target Language
        modelName (str): Model Name
        auto (bool): Auto Detect Language
        transcribe (bool): Transcribe
        translate (bool): Translate
        engine (Literal["Whisper", "Google", "LibreTranslate", "MyMemoryTranslator"]): Engine to use
    """
    assert gClass.mw is not None
    gClass.enableTranscribing()
    gClass.mw.start_loadBar()
    result_Tc = ""
    separator = ast.literal_eval(shlex.quote(fJson.settingCache["separate_with"]))

    # Transcribe
    logger.info("-" * 50)
    logger.info(f"Transcribing Audio: {audio_name.split(os.sep)[-1]}")

    # verify audio file exists
    if not os.path.isfile(audio_name):
        logger.warning("Audio file does not exist")
        gClass.disableTranslating()
        return

    try:
        queue = Queue()
        gClass.tc_proc = Process(target=whisper_multiproc, args=[queue, audio_name, modelName, auto, True, lang_source], daemon=True)
        gClass.tc_proc.start()
        gClass.tc_proc.join()
        result_Tc = queue.get()

        gClass.disableTranscribing()
        gClass.mw.stop_loadBar()
    except Exception as e:
        gClass.disableTranscribing()  # flag processing as done if error
        gClass.mw.stop_loadBar()
        logger.exception(e)
        nativeNotify("Error: Transcribing Audio", str(e), app_icon, app_name)
        return

    # insert to textbox
    if transcribe:
        if len(result_Tc["text"].strip()) > 0:  # type: ignore
            gClass.insertMwTbTc(result_Tc["text"].strip() + separator)  # type: ignore
        else:
            logger.warning("Transcribed Text is empty")
    if translate:
        toTranslate = result_Tc["text"].strip() if engine != "Whisper" else audio_name
        translateThread = threading.Thread(target=multiproc_tl, args=[toTranslate, lang_source, lang_target, modelName, engine, auto], daemon=True)  # type: ignore
        translateThread.start()  # Start translation in a new thread to prevent blocking


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
    # cancel function is already handled in main, and recording process will be stopped beccause of the flag set to disabled
    checkModelFirst(modelName)

    # Proccess it
    if translate and not transcribe and whisperEngine:  # if only translating and using the whisper engine
        tcThread = threading.Thread(target=multiproc_tl, args=[filePath, langSource, langTarget, modelName, engine, auto], daemon=True)
        tcThread.start()
    else:
        # will automatically check translate on or not depend on input
        # translate is called from here because other engine need to get transcribed text first if translating
        tcThread = threading.Thread(target=multiproc_tc, args=[filePath, langSource, langTarget, modelName, auto, transcribe, translate, engine], daemon=True)
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
