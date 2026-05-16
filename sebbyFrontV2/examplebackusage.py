import requests
import base64
import numpy as np
import soundfile as sf
import sounddevice as sd

API_URL = "http://localhost:5000/SebbyBrain"

# --- Send request ---
with open("sebbyFrontV2/clip5.wav", "rb") as audio_file, open("snapshot.jpg", "rb") as image_file:
    response = requests.post(API_URL, files={
        "audio": ("sebbyFrontV2/clip5.wav", audio_file, "audio/wav"),
        "image": ("sebbyFrontV2/snapshot.jpg", image_file, "image/jpeg"),
    })

data = response.json()

# --- Print detected emotion ---
print("Emotion:", data["text"])

# --- Decode and play back the response audio ---
audio_bytes = base64.b64decode(data["audio_b64"])
audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

print("Playing response audio...")
sd.play(audio_array, samplerate=16000)
sd.wait()

# --- Optionally save the response audio ---
sf.write("sebbyFrontV2/response_audio.wav", audio_array, 16000)
print("Saved to response_audio.wav")