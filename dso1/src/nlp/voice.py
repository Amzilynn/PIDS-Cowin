import edge_tts
import asyncio
import os
import uuid
import pygame

# 🔴 Flag global
is_speaking = False

async def _amain(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    output_file = f"speech_{uuid.uuid4()}.mp3"
    await communicate.save(output_file)
    
    pygame.mixer.init()
    pygame.mixer.music.load(output_file)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    pygame.mixer.music.unload()
    os.remove(output_file)

def speak(text, lang="fr"):
    voice = "fr-FR-DeniseNeural" if lang == "fr" else "en-US-EmmaNeural"
    asyncio.run(_amain(text, voice))

def get_voice(lang):
    if lang == "fr":
        return "fr-FR-DeniseNeural"
    return "en-US-EmmaNeural"
