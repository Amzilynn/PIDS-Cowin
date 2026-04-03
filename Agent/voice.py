import edge_tts
import asyncio
import os
import uuid
import pygame

# 🔴 Flag global
is_speaking = False

# Initialisation audio
pygame.mixer.init()


def get_voice(lang):
    if lang.startswith("fr"):
        return "fr-FR-DeniseNeural"
    elif lang.startswith("en"):
        return "en-US-AriaNeural"
    elif lang.startswith("ar"):
        return "ar-SA-ZariyahNeural"
    else:
        return "en-US-AriaNeural"


def play_audio(filename):
    try:
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        # 🔥 attendre la fin du son
        while pygame.mixer.music.get_busy():
            continue

    except Exception as e:
        print(f"[Audio error] {e}")


async def _speak_async(text, voice):
    global is_speaking

    filename = f"response_{uuid.uuid4().hex}.mp3"
    is_speaking = True

    try:
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(filename)

        play_audio(filename)

    except Exception as e:
        print(f"[Voice error] {e}")

    finally:
        is_speaking = False

        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass


def speak_text(text, lang="en"):
    voice = get_voice(lang)
    asyncio.run(_speak_async(text, voice))