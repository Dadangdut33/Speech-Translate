import audioop
import math
import time
import wave

import numpy as np
import pyaudiowpatch as pyaudio

# Set the chunk size and sample rate
chunk_size = 1024
sample_rate = 41000
channel = 1

# Create a PyAudio object
p = pyaudio.PyAudio()

# Open the audio stream
stream = p.open(format=pyaudio.paInt16, channels=channel, rate=sample_rate, input=True, frames_per_buffer=chunk_size)

# Set the threshold value for the db
threshold = 0
min_threshold = -60
max_threshold = 0
steps = 1
optimal = False

# Start recording
recording = False
framestotal = []
recording_start = time.time()
adjustment_start = time.time()

try:
    while True:
        # Read the audio data
        data = stream.read(chunk_size)

        # Calculate the db value
        rms = audioop.rms(data, 2) / 32767
        if rms == 0.0:
            db = 0.0
        else:
            db = 20 * np.log10(rms)

        # Check if the db value is above the threshold every 1 second
        if recording:
            framestotal.append(data)

            if db > threshold:  # still speaking
                recording_start = time.time()
            else:
                # check again every 1 second wetber still recording or not
                if time.time() - recording_start > 1:
                    # db < threshold = stop recording
                    if db < threshold:
                        recording = False
                    else:
                        recording_start = time.time()
                        # still recording? verify again
                        # increase the threshold to make sure that it is not a false positive
                        if optimal and threshold <= max_threshold:
                            if abs(abs(threshold) - math.ceil(abs(db))) > steps:
                                adjustment_start = time.time()
                                prev = threshold
                                threshold += steps
                                # make sure that it is not a false positive
                                if threshold > db:
                                    threshold = prev - steps

        else:
            # recording is false, check if db > threshold
            if db > threshold:
                # Start recording
                recording_start = time.time()
                recording = True
            else:
                # db < threshold = not picking up voice
                # adjust threshold
                if optimal and threshold >= min_threshold:
                    if abs(abs(threshold) - abs(db)) > steps + 2:
                        adjustment_start = time.time()
                        prev = threshold
                        threshold -= steps
                        # make sure that it is not a false negative
                        if threshold < db:
                            threshold = prev + steps

        # Adjust the max min if needed
        if db < min_threshold:
            min_threshold = db
        elif db > max_threshold:
            max_threshold = db

        # first time
        # will go until optimal
        if not optimal:
            # not speaking
            if db < threshold:
                # adjust threshold until near db
                if threshold >= min_threshold:
                    if abs(abs(threshold) - math.ceil(abs(db))) > steps:
                        threshold -= steps
                    else:
                        optimal = True

            # speaking
            elif db > threshold:
                # adjust threshold until near db
                if threshold <= max_threshold:
                    if abs(abs(threshold) - abs(db)) > steps + 2:
                        threshold += steps  # increse
                    else:
                        optimal = True

        # threshold_now = time.time()
        print(
            f"Recording: {recording}, dB: {db:.2f}, threshold: {threshold:.2f}, "
            f"UP: {math.ceil(abs(abs(threshold) - abs(db))) > steps + 2}, "
            f"DOWN: {abs(abs(threshold) - abs(db)) > steps + 1}, Optimal: {optimal}",
            end="\r\r",
        )

except KeyboardInterrupt:
    pass

wf = wave.open("output.wav", "wb")
wf.setnchannels(channel)
wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
wf.setframerate(sample_rate)
wf.writeframes(b"".join(framestotal))
wf.close()

# Close the audio stream and PyAudio object
stream.stop_stream()
stream.close()
p.terminate()
