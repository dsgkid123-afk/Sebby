from scipy.io.wavfile import write
#import qwen_test
import time
import sounddevice as sd
import robo_eyes
import DesisionMindV1 as DesisionMindV1
from whisperTranscribe import WhisperTranscriber
import TakeSpeakingRecs as rec


transcriber = WhisperTranscriber(
    model_size="base",      # change to "small" or "medium" for better accuracy
    device="cuda",          # or "cpu"
    compute_type="float16"  # use "int8" if low VRAM
)

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

rec.start_recording_speach()

while True:
    #setactions([6])
    #time.sleep(10)
    
    print("Getting clip...")
    time.sleep(3)
    clip = rec.get_clip()
    print("fineshed clip")
    if clip is not None:
        sd.play(clip, 16000)
        sd.wait()
        write("clip.wav", 16000, clip)
        
        transcription = transcriber.transcribe_wav("clip.wav")
        print("user said:", transcription)
        #actions = DesisionMindV1.evaluate_path(transcription)
        #print(f"Actions: {actions}")
        #setactions(actions)
        
        
        