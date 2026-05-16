from logging import DEBUG

from scipy.io.wavfile import write
import threading
import time
from whisperTranscribe import WhisperTranscriber
import speach as speach
import sebbyllm as sebbyllm
import sounddevice as sd
import TakeThosePics as camera
import robo_eyes
import EmotionFind as emotionFind
import TakeSpeakingRecs as vad
import are_they_speaking as vad2

with open("sebby/system.txt", "r", encoding="utf-8") as f:
    systemPrompt = f.read()
    
print("System Prompt Loaded: " + systemPrompt[:60] + "...")
heartbeat=0
transcriber = WhisperTranscriber(
    model_size="large-v3", 
    device="cuda",        
    compute_type="float16"  
)
response=""

sebbyllm.reset_chat()
sebbyllm.set_system(str(systemPrompt))







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




def process_response(result):
        #print(result)
        print("Response from LLM:" + result)
        emotion = emotionFind.detect_emotion(result)
        
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
        if result.strip() != "":
            sample, audioOut=speach.speech_speak(result)
            sd.play(audioOut, sample)
            sd.wait()



vad.start_recording_speach()
vad2.clip()
print("RECORDING")
while True:
    for i in range(10):
        heartbeat += 1
        print ("heartbeat: " + str(heartbeat))
        clip = vad.get_clip()
        if clip is not None:
            camera.snapshot()
            write("sebby/clip5.wav", 16000, clip)
            transcription = transcriber.transcribe_wav("sebby/clip5.wav")
            print("DEBUG:" + transcription)
            #get response from sebbyllm
            MAX_LOOPS = 4
            result, is_final, tool, tresult = sebbyllm.analyze(
                image_path="snapshot.jpg",
                prompt=transcription
            )
            process_response(result)
            if not is_final:
                for _ in range(MAX_LOOPS):
                    result, is_final, tool, tresult = sebbyllm.analyze(
                        image_path=None,
                        prompt="",
                    )
                    process_response(result)
                    if is_final:
                        break
            time.sleep(1)
            vad2.clip()
            i += 10
        time.sleep(1)
            
    camera.snapshot()
    result, is_final, tool, tresult = sebbyllm.analyze(
        image_path="snapshot.jpg",
        prompt=""
    )
    process_response(result)
    time.sleep(1)
    vad2.clip()
    
                
                