import are_they_speaking as vad
import threading
import time

def start_recording_speach():
    #start necessary threads for VAD
    threading.Thread(target=vad.start_listening_loop, daemon=True).start()
    threading.Thread(target=vad.cleanup_buffer, daemon=True).start()

    
def get_clip():
    while True:
        if vad.are_they_speaking()==False:
            return vad.clip()
        time.sleep(.25)