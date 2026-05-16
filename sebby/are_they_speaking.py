import sounddevice as sd
import numpy as np
import queue
import time
import threading
import torch

print("VAD Initializing...")

# Load Silero VAD
model, utils = torch.hub.load(
    repo_or_dir='snakers4/silero-vad',
    model='silero_vad',
    force_reload=False
)

(_, _, _, VADIterator, _) = utils

SAMPLE_RATE = 16000
BLOCK_SIZE = 512  # Number of samples per block (64ms at 16kHz)

audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)
    audio_queue.put(indata.copy())

stream = sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    blocksize=BLOCK_SIZE,
    callback=audio_callback
)
stream.start()

vad_iterator = VADIterator(model)

# ---- STATE ----
speach_on = False

# (timestamp, audio_chunk, valid)
audio_buffer = []

last_clip_time = time.time()
lock = threading.Lock()

print("VAD Initialized!")

# ---- LOOP ----
# ---- LOOP ----
def start_listening_loop():
    global speach_on

    print("Listening...")
    
    # stors buffer to make it clean
    pre_roll_buffer = [] 

    while True:
        audio_chunk = audio_queue.get()
        audio_chunk = np.squeeze(audio_chunk).astype(np.float32)
        audio_tensor = torch.from_numpy(audio_chunk)

        result = vad_iterator(audio_tensor, return_seconds=True)

        # Detect the MOMENT speech starts (transition from False to True)
        new_speech_state = speach_on
        if result:
            new_speech_state = not speach_on

        now = time.time()

        with lock:
            # 1. If speech JUST started, inject the 2 pre-roll chunks first
            if new_speech_state and not speach_on:
                for p_now, p_chunk in pre_roll_buffer:
                    # We mark them as 'valid' so your clip() function grabs them
                    audio_buffer.append((p_now, p_chunk, True))
            
            # 2. Update the state
            speach_on = new_speech_state

            # 3. Store the current chunk
            audio_buffer.append((now, audio_chunk.copy(), speach_on))

        # 4. If we aren't speaking, keep this chunk in the pre-roll for next time
        if not speach_on:
            pre_roll_buffer.append((now, audio_chunk.copy()))
            # Keep only the last 5
            if len(pre_roll_buffer) > 5:
                pre_roll_buffer.pop(0)
        else:
            # Clear pre-roll while speaking so it's fresh for the next sentence
            pre_roll_buffer.clear()

# clip audio
def clip():
    global last_clip_time

    with lock:
        #reset time from last clip
        now = time.time()
        
        # look for first valid chunk in seq
        first_speech_idx = None
        for i, (t, chunk, valid) in enumerate(audio_buffer):
            if t >= last_clip_time and valid:
                first_speech_idx = i
                break
        
        if first_speech_idx is None:
            return None

        # add two chunks before so when clipped no cutoff
        start_idx = max(0, first_speech_idx - 60)

        # save all "speach" chunks to "valid"
        relevant_chunks = [
            chunk for (t, chunk, valid) in audio_buffer[start_idx:]
            if t >= last_clip_time and valid
        ]

        last_clip_time = now

    if not relevant_chunks:
        return None

    return np.concatenate(relevant_chunks)


def are_they_speaking():
    return speach_on


# clean up old audio chunks
def cleanup_buffer(max_seconds=60):
    while True:
        time.sleep(5)
        now = time.time()
        with lock:
            audio_buffer[:] = [
                x for x in audio_buffer
                if now - x[0] <= max_seconds
            ]


# example usage
#threading.Thread(target=start_listening_loop, daemon=True).start()
#threading.Thread(target=cleanup_buffer, daemon=True).start()
#time.sleep(50)