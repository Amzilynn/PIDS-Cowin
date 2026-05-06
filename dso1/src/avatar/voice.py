import requests
import os

# ─── Configuration ────────────────────────────────────────────────────────────
# We now point to the LivePortrait Engine on port 8027
AVATAR_API_URL = "http://localhost:8027/chat"

# 🔴 Flag global (Maintained for logic compatibility)
is_speaking = False

def get_voice(lang):
    """Map language codes to Edge-TTS voices."""
    if lang.startswith("fr"):
        return "fr-FR-DeniseNeural"
    elif lang.startswith("en"):
        return "en-US-AvaNeural"
    elif lang.startswith("ar"):
        return "ar-SA-ZariyahNeural"
    else:
        return "en-US-AvaNeural"

def speak_text(text, lang="fr"):
    """
    Sends the text to the Avatar Engine.
    The Avatar Engine handles TTS generation, Lip-Sync, and Frontend streaming.
    """
    global is_speaking
    
    voice = get_voice(lang)
    
    print(f"[DSO1 -> Avatar] Sending speech: '{text[:60]}...'")
    
    try:
        # Trigger the Avatar's speak pipeline
        response = requests.post(
            AVATAR_API_URL,
            json={
                "text": text,
                "voice": voice
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print("[DSO1] ✅ Speech signal delivered to Sarah.")
            
            # 🕒 SMART TIMER: Wait for the duration of the speech
            # Average speaking speed is ~150 words per minute (2.5 words per second)
            word_count = len(text.split())
            duration = max(1.5, (word_count / 2.5) + 1.0) # Min 1.5s, plus a bit of buffer
            
            print(f"[DSO1] 🕒 Waiting {duration:.1f}s for Sarah to finish speaking...")
            import time
            time.sleep(duration)
        else:
            print(f"[DSO1] ❌ Avatar engine returned error: {response.status_code}")
            
    except Exception as e:
        print(f"[DSO1] ❌ Could not contact Avatar engine: {e}")
    finally:
        # We don't block here because the Avatar engine handles its own queue
        is_speaking = False