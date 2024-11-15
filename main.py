import asyncio
from system import initialize
asyncio.run(initialize())  # noqa
import pyaudio
import struct
import pvporcupine
import speech_recognition as sr
from dotenv import load_dotenv
import os
import wave
import threading
import queue
import time
from collections import deque
from conversation_flow import ConversationFlow
from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np

# Load the saved voice embedding for you (Owen)
KNOWN_EMBEDDING_PATH = "known_speakers/Owen_embedding.npy"
known_embedding = np.load(KNOWN_EMBEDDING_PATH)

# Initialize the voice encoder
encoder = VoiceEncoder()

# Load environment variables from the .env file
load_dotenv()

# Retrieve access keys from the environment variables
access_key = os.getenv('PORCUPINE_API_KEY')


def recognize_command(audio_data):
    # Initialize recognizer for transcription
    recognizer = sr.Recognizer()
    command = ""
    is_owen = False

    # Load the audio file into the recognizer
    with sr.AudioFile(audio_data) as source:
        print("Loading and recognizing audio...")
        audio = recognizer.record(source)

        # Recognize the voice as belonging to a known speaker (speaker identification)
        wav = preprocess_wav(audio_data)  # Preprocess the audio file
        user_embedding = encoder.embed_utterance(wav)  # Generate voice embedding

        # Calculate similarity to verify if it's Owen
        similarity = np.dot(user_embedding, known_embedding) / (
            np.linalg.norm(user_embedding) * np.linalg.norm(known_embedding)
        )
        threshold = 0.6  # Adjusted threshold
        if similarity > threshold:
            print("Voice recognized as Owen.")
            is_owen = True
        else:
            print(f"Voice not recognized as Owen. Similarity: {similarity}")

        # Proceed to transcribe the audio
        try:
            print("Recognizing command... ", end="")
            command = recognizer.recognize_google(audio, language='en-US')
            print(f"User said: {command}")
        except sr.UnknownValueError:
            print("Could not understand your audio. Please try again.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")

    return command.lower(), is_owen


def main(test=False, num_mics=1):
    if test:
        while True:
            command = input("Enter your command, sir\n")
            ConversationFlow(command, True, test)
        return  # Exit the main function after testing

    porcupine = None
    pa = None
    audio_stream = None
    audio_queue = queue.Queue()
    sliding_buffer = deque(maxlen=16000)  # Keep ~1 second of audio (for 16kHz sample rate)

    print("Ready for your commands, sir.")

    try:
        porcupine = pvporcupine.create(
            keywords=["jarvis"], access_key=access_key, sensitivities=[0.7]
        )
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=num_mics,  # Set the number of channels to num_mics
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
            # Uncomment and set the correct device index if needed
            # input_device_index=your_device_index,
        )

        # Start the audio reading thread
        threading.Thread(
            target=audio_reader,
            args=(audio_stream, audio_queue, sliding_buffer, num_mics),
            daemon=True,
        ).start()

        # Continuously process audio frames from the queue
        while True:
            pcm = audio_queue.get()
            if pcm is None:
                continue

            total_samples = len(pcm) // 2  # Total int16 samples
            samples_per_channel = total_samples // num_mics  # Samples per channel

            # Unpack audio data
            pcm_unpacked = struct.unpack_from("<{}h".format(total_samples), pcm)

            # Convert multi-channel to mono
            pcm_mono = multi_channel_to_mono(pcm_unpacked, num_mics)

            # Ensure we have the correct number of samples
            if len(pcm_mono) != porcupine.frame_length:
                print(f"Expected {porcupine.frame_length} mono samples, but got {len(pcm_mono)}")
                continue

            keyword_index = porcupine.process(pcm_mono)

            if keyword_index >= 0:
                # Wake word detected
                print("Wake word detected, listening for command...")

                # Capture remaining part of the command immediately
                frames = list(sliding_buffer)  # Include buffered audio to not miss any words

                # Adjusted silence detection parameters
                silence_threshold = 1000  # Adjusted based on testing
                initial_silence_duration = 0.5
                max_silence_duration = 3
                grace_period = 1.5  # Slightly reduced for responsiveness

                current_silence_duration = initial_silence_duration
                silence_start_time = None
                while True:
                    pcm = audio_queue.get()
                    if pcm is None:
                        break

                    total_samples = len(pcm) // 2
                    samples_per_channel = total_samples // num_mics

                    # Unpack and convert data
                    pcm_unpacked = struct.unpack_from("<{}h".format(total_samples), pcm)
                    pcm_mono = multi_channel_to_mono(pcm_unpacked, num_mics)

                    frames.extend(pcm_mono)

                    # Calculate RMS (Root Mean Square) to determine volume level
                    rms = calculate_rms(pcm_mono)
                    # Debugging: print RMS values to adjust silence_threshold
                    # print(f"RMS: {rms}")

                    if rms < silence_threshold:
                        if silence_start_time is None:
                            silence_start_time = time.time()

                        # Check if total silence has exceeded the combined threshold and grace period
                        if time.time() - silence_start_time > current_silence_duration + grace_period:
                            break
                    else:
                        # Reset silence timer if audio is detected
                        silence_start_time = None

                        # Increase silence duration slowly, up to the maximum duration
                        current_silence_duration = min(
                            current_silence_duration + 0.1, max_silence_duration
                        )

                # Save to WAV and recognize
                wav_filename = "command.wav"
                save_to_wav(wav_filename, frames, porcupine.sample_rate)

                command, authenticated = recognize_command(wav_filename)
                if command:
                    ConversationFlow(command, authenticated, test)

    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()


def audio_reader(audio_stream, audio_queue, sliding_buffer, num_mics):
    """Read audio frames from the stream and put them in a queue for processing."""
    while True:
        try:
            pcm = audio_stream.read(
                audio_stream._frames_per_buffer, exception_on_overflow=False
            )
            audio_queue.put(pcm)

            total_samples = len(pcm) // 2
            samples_per_channel = total_samples // num_mics

            # Unpack and convert data
            pcm_unpacked = struct.unpack_from("<{}h".format(total_samples), pcm)
            pcm_mono = multi_channel_to_mono(pcm_unpacked, num_mics)

            sliding_buffer.extend(pcm_mono)
        except IOError as e:
            print(f"Audio stream read error: {e}")
            audio_queue.put(None)


def multi_channel_to_mono(pcm_unpacked, num_mics):
    """Convert interleaved multi-channel PCM data to mono."""
    if num_mics == 1:
        # Mono input; no need to convert
        return pcm_unpacked
    else:
        # Average samples across channels
        return [
            int(sum(pcm_unpacked[i:i+num_mics]) / num_mics)
            for i in range(0, len(pcm_unpacked), num_mics)
        ]


def save_to_wav(filename, frames, sample_rate):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)  # Mono audio
        wf.setsampwidth(2)  # 2 bytes per sample
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<{}h".format(len(frames)), *frames))


def calculate_rms(frame):
    """Calculate the RMS (Root Mean Square) of the audio frame."""
    return (sum(sample ** 2 for sample in frame) / len(frame)) ** 0.5


if __name__ == "__main__":
    testMode = False
    num_microphones = 1  # Replace with the actual number of microphones
    main(test=testMode, num_mics=num_microphones)
    from system import set_test_mode
    set_test_mode
