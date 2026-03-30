import speech_recognition as sr

def listen_to_user(lang="fr"):
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print(" Speak now...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        if lang == "fr":
            text = recognizer.recognize_google(audio, language="fr-FR")
        elif lang == "ar":
            text = recognizer.recognize_google(audio, language="ar-SA")
        else:
            text = recognizer.recognize_google(audio, language="en-US")

        print(" You said:", text)
        return text

    except sr.UnknownValueError:
        print(" Could not understand audio")
        return ""

    except sr.RequestError as e:
        print(f" API error: {e}")
        return ""