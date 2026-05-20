from flask import Flask, request
from PIL import Image
import base64, io
import numpy as np
import scipy.signal
import wave

from scipy.io.wavfile import read as wav_read, write as wav_write
from whisperTranscribe import WhisperTranscriber
import speach as speach
import sebbyllm as sebbyllm
import EmotionFind as emotionFind

app = Flask(__name__)

with open("sebbyBackV2/system.txt", "r", encoding="utf-8") as f:
    systemPrompt = f.read()

print("System Prompt Loaded: " + systemPrompt[:60] + "...")

transcriber = WhisperTranscriber(
    model_size="large-v3-turbo",
    device="cuda",
    compute_type="float16"
)

sebbyllm.reset_chat()
sebbyllm.set_system(str(systemPrompt))


def process_response(result):
    emotion = emotionFind.detect_emotion(result)

    audioOut = np.array([], dtype=np.int16)

    if result.strip() != "":
        sample_rate, audio = speach.speech_speak(result)
        if sample_rate != 16000:
            num_samples = int(len(audio) * 16000 / sample_rate)
            audio = scipy.signal.resample(audio, num_samples)
        if audio.dtype != np.int16:
            audio = (audio * 32767).clip(-32768, 32767).astype(np.int16)
        audioOut = audio

    return audioOut, emotion


def SebbyBrain(audio_bytes, image):
    print("Received audio and image data.")
    sample_rate, audio = wav_read(io.BytesIO(audio_bytes))
    if audio.dtype != np.int16:
        audio = (audio * 32767).clip(-32768, 32767).astype(np.int16)
    if sample_rate != 16000:
        num_samples = int(len(audio) * 16000 / sample_rate)
        audio = scipy.signal.resample(audio, num_samples).astype(np.int16)

    total_audio = np.array([], dtype=np.int16)

    with open("sebbyBackV2/snapshot.jpg", "wb") as f:
        f.write(image)
    wav_write("sebbyBackV2/clip5.wav", 16000, audio)
    transcription = transcriber.transcribe_wav("sebbyBackV2/clip5.wav")
    if transcription is not None:
        print("DEBUG:" + transcription)

        MAX_LOOPS = 4
        result, is_final, tool, tresult = sebbyllm.analyze(
            image_path="snapshot.jpg",
            prompt=transcription
        )
        audioOut, emotion = process_response(result)
        total_audio = np.concatenate([total_audio, audioOut])

        if not is_final:
            for _ in range(MAX_LOOPS):
                result, is_final, tool, tresult = sebbyllm.analyze(
                    image_path=None,
                    prompt="",
                )
                audioOut, emotion = process_response(result)

                silence = np.zeros(16000, dtype=np.int16)  # 1 second at 16kHz
                total_audio = np.concatenate([total_audio, silence, audioOut])

                if is_final:
                    break
        print("Final response ready with emotion:", emotion)
        return emotion, total_audio
    print("faulty vad detected")
    return "default", total_audio

@app.route("/SebbyBrain", methods=["POST"])
def process():
    audio_file = request.files.get("audio")
    if audio_file is None:
        # Build a 1-second silence WAV with proper RIFF headers
        sample_rate = 16000
        silence = np.zeros(sample_rate, dtype=np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)          # 16-bit = 2 bytes
            wf.setframerate(sample_rate)
            wf.writeframes(silence.tobytes())
        audio = buf.getvalue()
    else:
        audio = audio_file.read()

    image = request.files["image"]
    img = Image.open(io.BytesIO(image.read()))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG")

    emotion, total_audio = SebbyBrain(audio, buf.getvalue())

    return {
        "text": emotion,
        "audio_b64": base64.b64encode(total_audio.tobytes()).decode()
    }

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)