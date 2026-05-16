from transformers import pipeline

# load model
_emotion_model = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=None
)

# map it to desired labs
def _map_emotion(label):
    label = label.lower()

    if label in ["anger"]:
        return "angry"
    elif label in ["joy", "happiness"]:
        return "happy"
    elif label in ["sadness"]:
        return "sad"
    elif label in ["fear"]:
        return "suspicious"
    elif label in ["surprise"]:
        return "surprised"
    else:
        return "default"

# dec emotion func
def detect_emotion(text: str) -> str:
    results = _emotion_model(text)[0]

    # get best
    best = max(results, key=lambda x: x["score"])
    return _map_emotion(best["label"])