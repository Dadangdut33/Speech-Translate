# pylint: disable=deprecated-module
from audioop import rms as calculate_rms
from io import BytesIO
from wave import Wave_read, Wave_write
from wave import open as w_open

import torch
from numpy import abs as np_abs
from numpy import float32, frombuffer, iinfo, int16, log10, reshape
from scipy.signal import butter, filtfilt, resample_poly
from webrtcvad import Vad

from speech_translate._constants import WHISPER_SR


class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, _bytes, timestamp, duration):
        self.bytes = _bytes
        self.timestamp = timestamp
        self.duration = duration


def get_frame_duration(sample_rate: int, chunk_size: int) -> int:
    """
    Get the frame duration to be used in the frame generator.
    Value return is either 10, 20, or 30 ms.

    Parameters
    ----------
    sample_rate : int
        sample rate of the audio data
    chunk_size : int
        chunk size of the audio data

    Returns
    -------
    int
        frame duration in ms
    """
    ms_per_read = int((chunk_size / sample_rate) * 1000)

    if ms_per_read >= 30:
        return 30
    elif ms_per_read >= 20:
        return 20
    else:
        return 10


def frame_generator(frame_duration_ms, audio, sample_rate, get_only_first_frame=False):
    """Generates audio frames from PCM audio data.

    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.

    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n
        if get_only_first_frame:
            break


def resample_sr(data: bytes, sample_rate: int, target_sample_rate: int) -> bytes:
    """
    This function resamples the audio data from a given sample rate to a target sample rate.
    The function is used when the sample rate of the audio is not 16kHz.

    If by chance the sample rate is already 16kHz, the function will return the original audio data.

    Parameters
    ----------
    data : bytes
        chunk of audio data from pyaudio input stream in bytes
    sample_rate : int
        sample rate of the audio data
    target_sample_rate : int
        target sample rate

    Returns
    -------
    bytes
    """
    if sample_rate == target_sample_rate:
        return data

    audio_as_np_int16 = frombuffer(data, dtype=int16)  # read as numpy array of int16
    audio_as_np_float32 = audio_as_np_int16.astype(float32)  # convert to float32

    # Filter the audio with a anti aliasing filter
    nyquist = 0.5 * sample_rate  # nyquist frequency / folding frequency
    cutoff = 0.9 * nyquist  # Adjust the cutoff frequency as needed

    # Use a butterworth filter with order of 4
    filter_order = 4
    b, a = butter(filter_order, cutoff / nyquist, btype='lowpass')

    # Filter the audio using filtfilt (zero-phase filtering)
    filtered_audio = filtfilt(b, a, audio_as_np_float32)

    # Resample the filtered audio with zero-padding
    resampled = resample_poly(filtered_audio, target_sample_rate, sample_rate, window=('kaiser', 5.0))

    return resampled.astype(int16).tobytes()  # convert back to int16 and bytes


def get_db(audio_data: bytes) -> float:
    """Get the db value of the audio data.

    Parameters
    ----------
    audio_data : bytes
        chunk of audio data from pyaudio input stream in bytes

    Returns
    -------
    float
        db value of the audio data
    """
    rms: float = calculate_rms(audio_data, 2) / 32767
    if rms == 0.0:
        return 0.0
    else:
        return 20 * log10(rms)  # convert to db


def get_speech_webrtc(
    data: bytes, sample_rate: int, frame_duration_ms: int, vad: Vad, get_only_first_frame: bool = True
) -> bool:
    frames = list(frame_generator(frame_duration_ms, data, sample_rate, get_only_first_frame=get_only_first_frame))
    data_to_check = data if len(frames) == 0 else frames[0].bytes
    is_speech: bool = vad.is_speech(data_to_check, sample_rate)
    return is_speech


def to_silero(sound_bytes: bytes, num_of_channels: int, samp_width: int = 2):
    """Converts a byte array to a 32-bit float tensor.

    Parameters
    ----------
    sound_bytes : byte array
        A byte array representing a sound file.
    num_of_channels : int
        The number of channels in the sound file.
    samp_width : int, optional
        The sample width of the sound file, by default 2 (16-bit)

    Returns
    -------
    torch tensor
        A tensor representing the sound file data.
    """
    if num_of_channels == 1:
        audio_as_np_int16 = frombuffer(sound_bytes, dtype=int16).flatten()
        abs_max = np_abs(audio_as_np_int16).max()
        np_buf = audio_as_np_int16.astype('float32')
        if abs_max > 0:
            np_buf *= 1 / abs_max
    else:
        # need to make temp in memory to make sure the audio will be read properly
        wf = BytesIO()
        wav_writer: Wave_write = w_open(wf, "wb")
        wav_writer.setframerate(WHISPER_SR)
        wav_writer.setsampwidth(samp_width)
        wav_writer.setnchannels(num_of_channels)
        wav_writer.writeframes(sound_bytes)
        wav_writer.close()
        wf.seek(0)

        wav_reader: Wave_read = w_open(wf)
        samples = wav_reader.getnframes()
        audio_bytes = wav_reader.readframes(samples)

        audio_as_np_int16 = frombuffer(audio_bytes, dtype=int16).flatten()
        audio_as_np_float32 = audio_as_np_int16.astype(float32)
        chunk_length = len(audio_as_np_float32) / num_of_channels
        audio_reshaped = reshape(audio_as_np_float32, (int(chunk_length), num_of_channels))
        np_buf = audio_reshaped[:, 0] / iinfo(int16).max  # take left channel only

    torch_float32 = torch.from_numpy(np_buf.squeeze())
    return torch_float32
