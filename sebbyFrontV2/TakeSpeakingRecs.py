import are_they_speaking as vad
import threading
import time
import numpy as np


extraAudio = np.array([], dtype=np.int16)

def start_recording_speach():
    threading.Thread(target=vad.start_listening_loop, daemon=True).start()
    threading.Thread(target=vad.cleanup_buffer, daemon=True).start()

    
def get_clip():
    global extraAudio  # moved to top of function
    while True:
        if vad.are_they_speaking() == False or extraAudio.size > 3:
            clip = vad.clip()
            if clip is not None:
                clip = np.concatenate([extraAudio, clip])
                extraAudio = np.array([], dtype=np.int16)
                return clip
        time.sleep(.15)
        
def sped_clip():
    global extraAudio  # already correct
    clip = vad.clip()
    if clip is not None:
        extraAudio = np.concatenate([extraAudio, clip])