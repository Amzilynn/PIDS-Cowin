import edge_tts
import asyncio
import os
import sys
import uuid


def get_voice(lang):
    if lang.startswith("fr"):
        return "fr-FR-DeniseNeural"
    elif lang.startswith("en"):
        return "en-US-AriaNeural"
    elif lang.startswith("ar"):
        return "ar-SA-ZariyahNeural"
    else:
        return "en-US-AriaNeural"  # fallback


def play_audio(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    elif sys.platform == "darwin":
        os.system(f"afplay '{filename}'")
    else:
        for player in ["mpg123", "mpg321", "ffplay -nodisp -autoexit"]:
            if os.system(f"which {player.split()[0]} > /dev/null 2>&1") == 0:
                os.system(f"{player} '{filename}'")
                break


async def _speak_async(text, voice):
    filename = f"response_{uuid.uuid4().hex}.mp3"
    try:
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(filename)
        play_audio(filename)
    except Exception as e:
        print(f"[Voice error] {e}")
    finally:
        await asyncio.sleep(2)
        if os.path.exists(filename):
            os.remove(filename)


def speak_text(text, lang="en"):
    voice = get_voice(lang)
    asyncio.run(_speak_async(text, voice))