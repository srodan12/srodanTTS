import os
from pydub import AudioSegment
from pydub.utils import make_chunks
import tkinter as tk
from tkinter import filedialog, Label, Button, Entry, StringVar, IntVar, Radiobutton
import random

def select_folder(prompt):
    folder = filedialog.askdirectory(title=prompt)
    return folder

def cut_audio_files(noise_folder, output_folder, chunk_length_ms=None, random_chunks=False):
    for filename in os.listdir(noise_folder):
        if filename.endswith(".wav") or filename.endswith(".mp3"):
            audio_path = os.path.join(noise_folder, filename)
            audio = AudioSegment.from_file(audio_path)
            
            if random_chunks:
                # Create random chunks between 500ms and 3500ms
                start = 0
                while start < len(audio):
                    chunk_length_ms = random.randint(500, 3500)
                    end = start + chunk_length_ms
                    chunk = audio[start:end]
                    chunk_name = f"{os.path.splitext(filename)[0]}_chunk{start}.wav"
                    chunk_path = os.path.join(output_folder, chunk_name)
                    chunk.export(chunk_path, format="wav")
                    print(f"Exported {chunk_path}")
                    start = end
            else:
                # Create equal-sized chunks
                chunks = make_chunks(audio, chunk_length_ms)
                for i, chunk in enumerate(chunks):
                    chunk_name = f"{os.path.splitext(filename)[0]}_chunk{i}.wav"
                    chunk_path = os.path.join(output_folder, chunk_name)
                    chunk.export(chunk_path, format="wav")
                    print(f"Exported {chunk_path}")

def start_chunking():
    noise_folder = select_folder("Select the noise folder")
    output_folder = select_folder("Select the output folder")
    
    if random_chunks.get():
        cut_audio_files(noise_folder, output_folder, random_chunks=True)
    else:
        chunk_length = int(chunk_length_var.get())
        cut_audio_files(noise_folder, output_folder, chunk_length_ms=chunk_length)

# GUI Setup
root = tk.Tk()
root.title("Audio Chunker")

frame = tk.Frame(root, bg="white")
frame.pack(padx=10, pady=10)

# Chunking method selection
random_chunks = IntVar()
random_chunks.set(0)

label = Label(frame, text="Choose chunking method:")
label.pack()

equal_chunks_radio = Radiobutton(frame, text="Equal-sized chunks", variable=random_chunks, value=0)
equal_chunks_radio.pack(anchor=tk.W)

random_chunks_radio = Radiobutton(frame, text="Random chunks (500ms-3500ms)", variable=random_chunks, value=1)
random_chunks_radio.pack(anchor=tk.W)

# Chunk length input for equal-sized chunks
chunk_length_label = Label(frame, text="Chunk length (ms) for equal-sized chunks:")
chunk_length_label.pack()

chunk_length_var = StringVar()
chunk_length_entry = Entry(frame, textvariable=chunk_length_var)
chunk_length_entry.pack()
chunk_length_var.set("1000")  # Default to 1000ms

# Start button
start_button = Button(frame, text="Start Chunking", command=start_chunking)
start_button.pack(pady=10)

root.mainloop()
