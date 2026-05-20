import are_they_speaking as vad
import threading
import time
import numpy as np

extraAudio = np.array([], dtype=np.int16)
audio_lock = threading.Lock()  # Added to prevent thread collisions

def start_recording_speach():
    threading.Thread(target=vad.start_listening_loop, daemon=True).start()
    threading.Thread(target=vad.cleanup_buffer, daemon=True).start()

def get_clip():
    global extraAudio
    
    while True:
        # 1. Wait until the person has STOPPED speaking
        if not vad.are_they_speaking():
            clip = vad.clip()
            
            with audio_lock:
                has_clip = clip is not None and clip.size > 0
                has_extra = extraAudio.size > 0
                
                # 2. If we have ANY audio (from the current clip or saved earlier), return it
                if has_clip or has_extra:
                    parts_to_combine = []
                    
                    if has_extra:
                        parts_to_combine.append(extraAudio)
                    if has_clip:
                        parts_to_combine.append(clip)
                        
                    # Safely combine everything
                    final_clip = np.concatenate(parts_to_combine)
                    
                    # 3. Clear the extra audio buffer for the next time
                    extraAudio = np.array([], dtype=np.int16)
                    
                    return final_clip
                    
        # If they are still speaking (or no audio exists yet), wait a bit
        time.sleep(0.15)

def sped_clip():
    global extraAudio
    clip = vad.clip()
    
    if clip is not None and clip.size > 0:
        with audio_lock:
            # Append the current clip safely
            extraAudio = np.concatenate([extraAudio, clip])