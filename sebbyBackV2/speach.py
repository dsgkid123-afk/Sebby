from pocket_tts import TTSModel
import scipy.io.wavfile
import torch

tts_model = TTSModel.load_model()#.to("cuda")
voice_state = tts_model.get_state_for_audio_prompt("marius")

def speech_speak(text_to_speak):
    audio = tts_model.generate_audio(voice_state, text_to_speak)
    return tts_model.sample_rate, audio.numpy()
