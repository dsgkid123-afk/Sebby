from faster_whisper import WhisperModel


class WhisperTranscriber:
    def __init__(self, model_size="large-v3", device="auto", compute_type="auto"):
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )

    def transcribe_wav(self, file_path):
        segments, info = self.model.transcribe(
            file_path,
            initial_prompt="""
            Sebby is the AI assistant.
            The user may say:
            Hey Sebby
            Sebby can you help
            Sebby what do you think
            """
        )

        full_text = ""
        for segment in segments:
            full_text += segment.text + " "

        return full_text.strip()


# --- Example usage ---
#if __name__ == "__main__":
#    transcriber = WhisperTranscriber(
#        model_size="large-v3",  # change to "small" or "medium" for better accuracy
#        device="cuda",          # or "cpu"
#        compute_type="float16"  # use "int8" if low VRAM
#    )
#
#    result = transcriber.transcribe_wav("audio.wav")
#    print("Transcription:")
#    print(result)