import audioop
import wave
import numpy as np
from scipy.signal import resample_poly, butter, filtfilt

import pyaudiowpatch as pyaudio
import webrtcvad

# Set the chunk size and sample rate
chunk_size = 1024  # 160 = 10 ms
sample_rate = 16000
channel = 2
max_int16 = 2**15

ms_per_read = (chunk_size / sample_rate) * 1000

# Set the frame duration in ms based on ms_per_read
# frame_duration_ms is based on WebRTC VAD compatibility (either 10, 20, or 30 ms)
# if possible, set bigger frame duration for better detection
if ms_per_read >= 30:
    frame_duration_ms = 30
elif ms_per_read >= 20:
    frame_duration_ms = 20
else:
    frame_duration_ms = 10

print(
    f"Chunk size: {chunk_size}, Sample rate: {sample_rate}, Channel: {channel}, "
    f"Ms Per Read: {ms_per_read} ms, Frame duration: {frame_duration_ms} ms"
)

# 16kHz is needed for both whisper and WebRTC VAD
# WebRTCVad supports 8kHz, 16kHz, 32kHz, and 48kHz but to avoid double resampling
# We just resample it straight to 16kHz
TARGET_RESAMPLE = 16000

# Create a PyAudio object
p = pyaudio.PyAudio()

# Open the audio stream
stream = p.open(format=pyaudio.paInt16, channels=channel, rate=sample_rate, input=True, frames_per_buffer=chunk_size)

# Initialize WebRTC VAD
vad = webrtcvad.Vad()
vad.set_mode(3)  # Set the aggressiveness level (0-3)

# Start recording
recording = False
framestotal = []


class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
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
        data = stream.read(chunk_size)

        if sample_rate != TARGET_RESAMPLE:
            # resample the audio data to 16kHz
            audio_as_np_int16 = np.frombuffer(data, dtype=np.int16)  # read as numpy array of int16
            audio_as_np_float32 = audio_as_np_int16.astype(np.float32)  # convert to float32

            # old using librosa
            # resampled = librosa.resample(audio_as_np_float32, orig_sr=sample_rate, target_sr=TARGET_RESAMPLE)

            # Filter the audio with a anti aliasing filter
            nyquist = 0.5 * sample_rate
            cutoff = 0.9 * nyquist  # Adjust the cutoff frequency as needed
            b, a = butter(4, cutoff / nyquist, btype='low')
            y_filtered = filtfilt(b, a, audio_as_np_float32)

            # Resample the filtered audio with zero-padding
            resampled = resample_poly(audio_as_np_float32, TARGET_RESAMPLE, sample_rate, window=('kaiser', 5.0))

            data = resampled.astype(np.int16).tobytes()  # convert back to int16 and bytes

        frames = list(frame_generator(frame_duration_ms, data, TARGET_RESAMPLE, get_only_first_frame=True))

        # Use WebRTC VAD to detect speech
        data_to_check = data if len(frames) == 0 else frames[0].bytes
        is_speech = vad.is_speech(data_to_check, TARGET_RESAMPLE)

        # Calculate the dB value
        rms = audioop.rms(data, 2) / 32767
        if rms == 0.0:
            db = 0.0
        else:
            db = 20 * np.log10(rms)

        # If recording, store the audio data
        if is_speech:
            framestotal.append(data)

        # Print debugging information
        print(f"Speech: {is_speech}, dB: {db:.2f}\tFrames: {len(frames)}", end="\r\r")

except KeyboardInterrupt:
    pass

# Save the recorded audio to a WAV file
wf = wave.open("output.wav", "wb")
wf.setnchannels(channel)
wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
wf.setframerate(TARGET_RESAMPLE)
wf.writeframes(b"".join(framestotal))
wf.close()

# Close the audio stream and PyAudio object
stream.stop_stream()
stream.close()
p.terminate()
