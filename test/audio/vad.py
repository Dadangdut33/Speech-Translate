import audioop  # pylint: disable=deprecated-module
import wave

import numpy as np
import pyaudiowpatch as pyaudio
import webrtcvad
from scipy.signal import butter, filtfilt, resample_poly

# Set the chunk size and sample rate
CHUNK_SIZE = 1024  # 160 = 10 ms
SR = 16000
CHANNELS = 2
MAX_INT16 = 2**15

MS_PER_READ = (CHUNK_SIZE / SR) * 1000

# Set the frame duration in ms based on ms_per_read
# frame_duration_ms is based on WebRTC VAD compatibility (either 10, 20, or 30 ms)
# if possible, set bigger frame duration for better detection
if MS_PER_READ >= 30:
    FRAME_DURATION_MS = 30
elif MS_PER_READ >= 20:
    FRAME_DURATION_MS = 20
else:
    FRAME_DURATION_MS = 10

print(
    f"Chunk size: {CHUNK_SIZE}, Sample rate: {SR}, Channel: {CHANNELS}, "
    f"Ms Per Read: {MS_PER_READ} ms, Frame duration: {FRAME_DURATION_MS} ms"
)

# 16kHz is needed for both whisper and WebRTC VAD
# WebRTCVad supports 8kHz, 16kHz, 32kHz, and 48kHz but to avoid double resampling
# We just resample it straight to 16kHz
TARGET_RESAMPLE = 16000

# Create a PyAudio object
p = pyaudio.PyAudio()

# Open the audio stream
stream = p.open(format=pyaudio.paInt16, channels=CHANNELS, rate=SR, input=True, frames_per_buffer=CHUNK_SIZE)

# Initialize WebRTC VAD
vad = webrtcvad.Vad()
vad.set_mode(3)  # Set the aggressiveness level (0-3)

# Start recording
RECORDING = False
framestotal = []


class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, _bytes, timestamp, duration):
        self.bytes = _bytes
        self.timestamp = timestamp
        self.duration = duration


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


try:
    print("Recording speech only...")
    print("Press Ctrl+C to stop recording")
    while True:
        # Read the audio data
        data = stream.read(CHUNK_SIZE)

        if SR != TARGET_RESAMPLE:
            # resample the audio data to 16kHz
            audio_as_np_int16 = np.frombuffer(data, dtype=np.int16)  # read as numpy array of int16
            audio_as_np_float32 = audio_as_np_int16.astype(np.float32)  # convert to float32

            # old using librosa
            # resampled = librosa.resample(audio_as_np_float32, orig_sr=sample_rate, target_sr=TARGET_RESAMPLE)

            # Filter the audio with a anti aliasing filter
            NYQUIST = 0.5 * SR
            CUTOFF = 0.9 * NYQUIST  # Adjust the cutoff frequency as needed
            b, a = butter(4, CUTOFF / NYQUIST, btype='low')
            y_filtered = filtfilt(b, a, audio_as_np_float32)

            # Resample the filtered audio with zero-padding
            resampled = resample_poly(audio_as_np_float32, TARGET_RESAMPLE, SR, window=('kaiser', 5.0))

            data = resampled.astype(np.int16).tobytes()  # convert back to int16 and bytes

        frames = list(frame_generator(FRAME_DURATION_MS, data, TARGET_RESAMPLE, get_only_first_frame=True))

        # Use WebRTC VAD to detect speech
        data_to_check = data if len(frames) == 0 else frames[0].bytes
        is_speech = vad.is_speech(data_to_check, TARGET_RESAMPLE)

        # Calculate the dB value
        rms = audioop.rms(data, 2) / 32767
        if rms == 0.0:
            DB = 0.0
        else:
            DB = 20 * np.log10(rms)

        # If recording, store the audio data
        if is_speech:
            framestotal.append(data)

        # Print debugging information
        print(f"Speech: {is_speech}, dB: {DB:.2f}\tFrames: {len(frames)}", end="\r\r")

except KeyboardInterrupt:
    pass

# Save the recorded audio to a WAV file
wf = wave.open("output.wav", "wb")
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
wf.setframerate(TARGET_RESAMPLE)
wf.writeframes(b"".join(framestotal))
wf.close()

# Close the audio stream and PyAudio object
stream.stop_stream()
stream.close()
p.terminate()
