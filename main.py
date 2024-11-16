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
from scipy.signal import resample_poly

# Add debug flag
DEBUG = True

# Load environment variables from the .env file
load_dotenv()

# Retrieve access keys from the environment variables
access_key = os.getenv('PORCUPINE_API_KEY')

# Load the saved voice embedding for you (Owen)
KNOWN_EMBEDDING_PATH = "known_speakers/Owen_embedding.npy"
known_embedding = np.load(KNOWN_EMBEDDING_PATH)

# Initialize the voice encoder
encoder = VoiceEncoder()

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

def multi_channel_to_mono(pcm_unpacked, num_mics):
    """Convert interleaved multi-channel PCM data to mono."""
    return [
        int(sum(pcm_unpacked[i:i+num_mics]) / num_mics)
        for i in range(0, len(pcm_unpacked), num_mics)
    ]

def save_to_wav(filename, frames, original_sample_rate, target_sample_rate=16000):
    # Convert frames to numpy array
    frames = np.array(frames)

    # Resample frames to target_sample_rate if necessary
    if original_sample_rate != target_sample_rate:
        frames = resample_poly(frames, up=target_sample_rate, down=original_sample_rate)
        frames = frames.astype(np.int16)
        sample_rate = target_sample_rate
    else:
        sample_rate = original_sample_rate

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)  # Mono audio
        wf.setsampwidth(2)  # 2 bytes per sample
        wf.setframerate(sample_rate)
        wf.writeframes(frames.tobytes())

def calculate_rms(frame):
    """Calculate the RMS (Root Mean Square) of the audio frame."""
    return (sum(sample ** 2 for sample in frame) / len(frame)) ** 0.5

def main(test=False, num_mics=1):
    if test:
        while True:
            command = input("Enter your command, sir\n")
            ConversationFlow(command, True, test)
        return

    porcupine = None
    pa = None
    audio_stream = None
    audio_queue = queue.Queue()
    sliding_buffer = deque(maxlen=16000)

    print("Ready for your commands, sir.")

    try:
        # Add debug print for Porcupine initialization
        if DEBUG:
            print("Initializing Porcupine...")
        
        # Try different wake words and increased sensitivity
        porcupine = pvporcupine.create(
            keywords=["porcupine"],  # This is often the most reliable wake word
            access_key=access_key, 
            sensitivities=[1.0]
        )
        if DEBUG:
            print(f"Porcupine initialized successfully")
            print(f"Expected sample rate: {porcupine.sample_rate}")
            print(f"Expected frame length: {porcupine.frame_length}")

        pa = pyaudio.PyAudio()

        # Debug print available audio devices
        if DEBUG:
            print("\nAvailable audio devices:")
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                print(f"Device {i}: {info['name']}")
                print(f"    Max Input Channels: {info['maxInputChannels']}")
                print(f"    Default Sample Rate: {info['defaultSampleRate']}")
                print(f"    Input Device: {info['maxInputChannels'] > 0}")

        deviceIndex = None
        num_mics = None

        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if "Wireless GO II RX" in info['name']:
                if DEBUG:
                    print(f"\nFound target device:")
                    print(f"    Index: {i}")
                    print(f"    Name: {info['name']}")
                    print(f"    Sample Rate: {info['defaultSampleRate']} Hz")
                    print(f"    Max Input Channels: {info['maxInputChannels']}")
                
                deviceIndex = i
                sample_rate = int(info['defaultSampleRate'])
                num_mics = int(info['maxInputChannels'])
                break

        if deviceIndex is None:
            print("Error: Audio input device not found.")
            return

        if num_mics is None:
            num_mics = 1

        # Debug print audio stream parameters
        if DEBUG:
            print("\nInitializing audio stream with parameters:")
            print(f"    Sample Rate: {sample_rate}")
            print(f"    Channels: {num_mics}")
            print(f"    Device Index: {deviceIndex}")
            print(f"    Frame Buffer Size: {int(porcupine.frame_length * (sample_rate / porcupine.sample_rate))}")

        audio_stream = pa.open(
            rate=sample_rate,
            channels=num_mics,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=int(porcupine.frame_length * (sample_rate / porcupine.sample_rate)),
            input_device_index=deviceIndex,
        )

        if DEBUG:
            print("Audio stream opened successfully")

        frame_counter = 0
        last_time = time.time()

        def debug_audio_reader(audio_stream, audio_queue, sliding_buffer, num_mics, sample_rate, porcupine_sample_rate):
            nonlocal frame_counter, last_time
            frames_per_buffer = audio_stream._frames_per_buffer
            while True:
                try:
                    pcm = audio_stream.read(frames_per_buffer, exception_on_overflow=False)
                    
                    frame_counter += 1
                    if frame_counter % 100 == 0:
                        current_time = time.time()
                        fps = 100 / (current_time - last_time)
                        
                        pcm_unpacked = struct.unpack_from("<{}h".format(len(pcm) // 2), pcm)
                        rms = np.sqrt(np.mean(np.array(pcm_unpacked)**2))
                        
                        print(f"\rProcessing audio - FPS: {fps:.2f}, RMS Level: {rms:.2f}", end="")
                        
                        last_time = current_time

                    audio_queue.put(pcm)

                    total_samples = len(pcm) // 2
                    pcm_unpacked = struct.unpack_from("<{}h".format(total_samples), pcm)
                    pcm_mono = multi_channel_to_mono(pcm_unpacked, num_mics)

                    pcm_resampled = resample_poly(pcm_mono, up=porcupine_sample_rate, down=sample_rate)
                    pcm_resampled = pcm_resampled.astype(np.int16)

                    sliding_buffer.extend(pcm_resampled)
                except IOError as e:
                    print(f"\nAudio stream read error: {e}")
                    audio_queue.put(None)

        # Start the debug audio reader thread
        threading.Thread(
            target=debug_audio_reader,
            args=(audio_stream, audio_queue, sliding_buffer, num_mics, sample_rate, porcupine.sample_rate),
            daemon=True,
        ).start()

        print("\nListening for wake word ('Alexa')...")  # Updated wake word notification

        while True:
            pcm = audio_queue.get()
            if pcm is None:
                continue

            total_samples = len(pcm) // 2
            pcm_unpacked = struct.unpack_from("<{}h".format(total_samples), pcm)
            pcm_mono = multi_channel_to_mono(pcm_unpacked, num_mics)

            # Debug print for audio conversion
            if frame_counter % 500 == 0:
                print(f"\nAudio stats:")
                print(f"Sample count: {len(pcm_mono)}")
                print(f"Min value: {min(pcm_mono)}")
                print(f"Max value: {max(pcm_mono)}")
                print(f"Mean value: {np.mean(pcm_mono)}")
            
            # Resample and normalize the audio
            pcm_resampled = resample_poly(pcm_mono, up=porcupine.sample_rate, down=sample_rate)
            pcm_normalized = np.int16(pcm_resampled / np.max(np.abs(pcm_resampled)) * 32767 if np.max(np.abs(pcm_resampled)) > 0 else pcm_resampled)

            if len(pcm_normalized) != porcupine.frame_length:
                if len(pcm_normalized) > porcupine.frame_length:
                    pcm_normalized = pcm_normalized[:porcupine.frame_length]
                else:
                    pcm_normalized = np.pad(pcm_normalized, (0, porcupine.frame_length - len(pcm_normalized)), 'constant')

            keyword_index = porcupine.process(pcm_normalized)

            if keyword_index >= 0:
                print("\nWake word detected!")
                frames = list(sliding_buffer)

                silence_threshold = 1000
                initial_silence_duration = 0.5
                max_silence_duration = 3
                grace_period = 1.5

                current_silence_duration = initial_silence_duration
                silence_start_time = None
                while True:
                    pcm = audio_queue.get()
                    if pcm is None:
                        break

                    total_samples = len(pcm) // 2
                    samples_per_channel = total_samples // num_mics

                    pcm_unpacked = struct.unpack_from("<{}h".format(total_samples), pcm)
                    pcm_mono = multi_channel_to_mono(pcm_unpacked, num_mics)

                    frames.extend(pcm_mono)

                    rms = calculate_rms(pcm_mono)

                    if rms < silence_threshold:
                        if silence_start_time is None:
                            silence_start_time = time.time()

                        if time.time() - silence_start_time > current_silence_duration + grace_period:
                            break
                    else:
                        silence_start_time = None
                        current_silence_duration = min(
                            current_silence_duration + 0.1, max_silence_duration
                        )

                wav_filename = "command.wav"
                save_to_wav(wav_filename, frames, sample_rate)

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

if __name__ == "__main__":
    testMode = False
    num_microphones = 2  # Replace with the actual number of microphones
    from system import set_test_mode
    set_test_mode(testMode)
    main(test=testMode, num_mics=num_microphones)