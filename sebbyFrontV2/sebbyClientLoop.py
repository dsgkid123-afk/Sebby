from logging import DEBUG

from scipy.io.wavfile import write
import threading
import time
import sounddevice as sd
import TakeThosePics as camera
import robo_eyes
import TakeSpeakingRecs as vad
import are_they_speaking as vad2
import requests
import base64
import numpy as np
import soundfile as sf

API_URL = "http://localhost:5000/SebbyBrain"


with open("sebby/system.txt", "r", encoding="utf-8") as f:
    systemPrompt = f.read()
    
print("System Prompt Loaded: " + systemPrompt[:60] + "...")
heartbeat=0

response=""

# reset chat
# load system


robot = robo_eyes.RoboEyes()

def setactions(actions):
    if 4 in actions:
        robot.mood("angry")
    elif 5 in actions:
        robot.mood("happy")
    elif 6 in actions:
        robot.mood("sad")
    elif 7 in actions:
        robot.mood("suspicious")
    elif 8 in actions:
        robot.mood("surprised")
    elif 3 in actions:
        robot.mood("default")
        
    if 1 in actions:
        robot.yes(intensity=5)
        #robot.no(intensity=0)
    elif 2 in actions:
        #robot.yes(intensity=0)
        robot.no(intensity=5)
    else:
        robot.no(intensity=0)
        robot.yes(intensity=0)

    if 0 in actions:
        robot.standby(looking_intensity=20, blinking_avg_freq=4500)
    robot.standby(looking_intensity=8, blinking_avg_freq=8000)




def process_server_response(AudioOut, emotion):
        
        print("Detected Emotion:" + emotion)
        
        #GIVE emotion
        if emotion == "angry":
            setactions([4])
        elif emotion == "happy":
            setactions([5])
        elif emotion == "sad":
            setactions([6])
        elif emotion == "suspicious":
            setactions([7])
        elif emotion == "surprised":
            setactions([8])
        else:
            setactions([3])  # default
            
            
        #speak response with speach
        sd.play(AudioOut, 16000)
        sd.wait()



vad.start_recording_speach()
vad2.clip()
print("RECORDING")
while True:
    for i in range(20):
        heartbeat += 1
        print ("heartbeat: " + str(heartbeat))
        clip = vad.get_clip()
        if clip is not None:
            camera.snapshot()
            write("sebbyFrontV2/clip5.wav", 16000, clip)
            # call api
            with open("sebbyFrontV2/clip5.wav", "rb") as audio_file, open("sebbyFrontV2/snapshot.jpg", "rb") as image_file:
                response = requests.post(API_URL, files={
                    "audio": ("sebbyFrontV2/clip5.wav", audio_file, "audio/wav"),
                    "image": ("sebbyFrontV2/snapshot.jpg", image_file, "image/jpeg"),
            })
            data = response.json()
            audio_bytes = base64.b64decode(data["audio_b64"])
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            process_server_response(audio_array, data["text"])
            time.sleep(1)
            vad2.clip()
        time.sleep(1)
            
    camera.snapshot()
    # call api
    with open("sebbyFrontV2/clip5.wav", "rb") as audio_file, open("snapshot.jpg", "rb") as image_file:
        response = requests.post(API_URL, files={
            "audio": None,
            "image": ("sebbyFrontV2/snapshot.jpg", image_file, "image/jpeg"),
        })
    data = response.json()
    audio_bytes = base64.b64decode(data["audio_b64"])
    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
    process_server_response(audio_array, data["text"])
    time.sleep(1)
    vad2.clip()
    
                
                