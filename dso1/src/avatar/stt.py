import threading

text_received_event = threading.Event()
received_text = ""
received_lang = "fr"

def get_user_text():
    global received_text, received_lang
    print("⏳ En attente du texte STT (depuis le Web Speech API)...")
    text_received_event.clear()
    text_received_event.wait()
    text_received_event.clear()

    text = received_text.strip()
    lang = received_lang
    received_text = ""
    return text, lang

def set_user_text(text, lang="fr"):
    global received_text, received_lang
    received_text = text
    received_lang = lang
    text_received_event.set()

# On simule la suppression de whisper pour éviter une erreur aux anciens imports
model = None
def record_audio():
    pass