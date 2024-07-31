import os
import sys
import subprocess
import pyttsx3
import random
import pyaudio
import wave
import speech_recognition as sr
from pydub import AudioSegment
from pydub.playback import play
from threading import Thread, Event
from warnings import warn
import tkinter as tk
from tkinter import filedialog, Text, Label
import uuid
import time

# Ensure all necessary dependencies are installed
def install_dependencies():
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyttsx3', 'pyaudio', 'speechrecognition', 'pydub', 'numpy', 'pillow', 'pywin32'])
    except subprocess.CalledProcessError as e:
        print(f"Error during installation of dependencies: {e}")
        print("Please ensure all required dependencies are installed manually.")
        sys.exit(1)

install_dependencies()

# Initialize the TTS engine
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)  # Set the speech rate to a slower value
    voices = engine.getProperty('voices')
except Exception as e:
    print(f"Error initializing pyttsx3: {e}")
    sys.exit(1)

# Configure audio input and output
CHUNK = 256
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open the stream for input
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK)

def get_random_voice():
    return random.choice(voices)

def text_to_speech(word, voice):
    engine.setProperty('voice', voice.id)
    filename = f'temp_{uuid.uuid4()}.wav'  # Generate a unique filename
    engine.save_to_file(word, filename)
    engine.runAndWait()
    
    # Wait until the file exists
    while not os.path.exists(filename):
        time.sleep(0.01)
    
    # Ensure the file is not empty
    while os.path.getsize(filename) == 0:
        time.sleep(0.01)
    
    audio_segment = AudioSegment.from_wav(filename)
    os.remove(filename)  # Clean up the temporary file
    return audio_segment

def play_audio_segment(audio_segment):
    stream = p.open(format=p.get_format_from_width(audio_segment.sample_width),
                    channels=audio_segment.channels,
                    rate=audio_segment.frame_rate,
                    output=True)
    stream.write(audio_segment.raw_data)
    stream.stop_stream()
    stream.close()

def play_background_noise(noise_folder, stop_event):
    while not stop_event.is_set():
        if not os.path.exists(noise_folder) or not os.listdir(noise_folder):
            continue
        
        noise_files = [os.path.join(noise_folder, f) for f in os.listdir(noise_folder) if f.endswith('.wav') or f.endswith('.mp3')]
        if not noise_files:
            continue
        
        noise_file = random.choice(noise_files)
        noise = AudioSegment.from_file(noise_file)
        noise = noise - 8  # Lower the volume by 6dB

        play(noise.fade_in(10).fade_out(10))
         # Sleep for the duration of the noise clip

def generate_response_with_nato():
    nato_phonetic_alphabet = [
        "Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", 
        "Juliett", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo", 
        "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "X-ray", "Yankee", "Zulu"
    ]
    random_words = random.sample(nato_phonetic_alphabet, 3)
    return "Generating response: " + " ".join(random_words)

def recognize_and_process(noise_folder, stop_event):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    while not stop_event.is_set():
        print("Listening...")
        with mic as source:
            audio = recognizer.listen(source)
        
        try:
            text = recognizer.recognize_google(audio)
            print(f"Recognized Text: {text}")
            response_prefix = generate_response_with_nato()
            display_text(response_prefix + "\n" + text)
            print(response_prefix)
            engine.say(response_prefix)
            engine.runAndWait()

            if noise_folder and os.path.exists(noise_folder):
                noise_stop_event = Event()
                noise_thread = Thread(target=play_background_noise, args=(noise_folder, noise_stop_event))
                noise_thread.start()

            words = text.split()
            previous_voice = None
            for word in words:
                if stop_event.is_set():
                    break
                voice = get_random_voice()
                while voice == previous_voice:
                    voice = get_random_voice()
                previous_voice = voice
                
                word_audio = text_to_speech(word, voice)
                play_audio_segment(word_audio)

            if noise_folder and os.path.exists(noise_folder):
                noise_stop_event.set()
                noise_thread.join()

        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")

def display_text(text):
    text_display.delete(1.0, tk.END)
    text_display.insert(tk.END, text)

def start_live_recognition():
    global stop_event
    if stop_event.is_set():
        stop_event.clear()  # Reset the stop event
        start_button.config(text="Stop Live Recognition")
        Thread(target=recognize_and_process, args=(noise_folder, stop_event)).start()
    else:
        stop_event.set()  # Signal the previous thread to stop if running
        start_button.config(text="Start Live Recognition")

def upload_audio():
    file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")])
    if file_path:
        Thread(target=process_uploaded_audio, args=(file_path, noise_folder)).start()

def process_uploaded_audio(file_path, noise_folder):
    recognizer = sr.Recognizer()
    
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    
    try:
        text = recognizer.recognize_google(audio)
        print(f"Recognized Text: {text}")
        response_prefix = generate_response_with_nato()
        display_text(response_prefix + "\n" + text)
        print(response_prefix)
        engine.say(response_prefix)
        engine.runAndWait()

        if noise_folder and os.path.exists(noise_folder):
            noise_stop_event = Event()
            noise_thread = Thread(target=play_background_noise, args=(noise_folder, noise_stop_event))
            noise_thread.start()

        words = text.split()
        previous_voice = None
        for word in words:
            voice = get_random_voice()
            while voice == previous_voice:
                voice = get_random_voice()
            previous_voice = voice
            
            word_audio = text_to_speech(word, voice)
            play_audio_segment(word_audio)

        if noise_folder and os.path.exists(noise_folder):
            noise_stop_event.set()
            noise_thread.join()

    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")

def process_text_input():
    text = text_entry.get("1.0", tk.END).strip()
    if text:
        display_text(text)
        Thread(target=process_text, args=(text,)).start()

def process_text(text):
    stop_event = Event()

    response_prefix = generate_response_with_nato()
    display_text(response_prefix + "\n" + text)
    print(response_prefix)
    engine.say(response_prefix)
    engine.runAndWait()

    if noise_folder and os.path.exists(noise_folder):
        noise_stop_event = Event()
        noise_thread = Thread(target=play_background_noise, args=(noise_folder, noise_stop_event))
        noise_thread.start()

    words = text.split()
    previous_voice = None
    for word in words:
        voice = get_random_voice()
        while voice == previous_voice:
            voice = get_random_voice()
        previous_voice = voice
        
        word_audio = text_to_speech(word, voice)
        play_audio_segment(word_audio)

    if noise_folder and os.path.exists(noise_folder):
        noise_stop_event.set()
        noise_thread.join()

def select_noise_folder():
    global noise_folder
    noise_folder = filedialog.askdirectory()
    noise_folder_label.config(text=f"Noise Folder: {noise_folder}" if noise_folder else "Noise Folder: None")

# GUI Setup
root = tk.Tk()
root.title("Real-Time Speech Processing")
root.geometry("800x600")  # Set the window size

frame = tk.Frame(root, bg="white")
frame.place(relwidth=1, relheight=1)

# Text display
text_display = tk.Text(frame, height=10)
text_display.pack()

# Text input
text_entry = tk.Text(frame, height=3)
text_entry.pack()

# Buttons
start_button = tk.Button(frame, text="Start Live Recognition", padx=10, pady=5, fg="white", bg="blue", command=start_live_recognition)
start_button.pack()

upload_button = tk.Button(frame, text="Upload Audio File", padx=10, pady=5, fg="white", bg="green", command=upload_audio)
upload_button.pack()

text_button = tk.Button(frame, text="Process Text Input", padx=10, pady=5, fg="white", bg="red", command=process_text_input)
text_button.pack()

noise_folder_button = tk.Button(frame, text="Select Noise Folder", padx=10, pady=5, fg="white", bg="purple", command=select_noise_folder)
noise_folder_button.pack()

noise_folder_label = tk.Label(frame, text="Noise Folder: None", bg="white")
noise_folder_label.pack()

# Usage example
noise_folder = ''  # Set to None or empty string to disable noise

# Stop event for managing threads
stop_event = Event()

root.mainloop()
