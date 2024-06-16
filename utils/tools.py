def play_beep():
    import winsound

    winsound.Beep(1000, 1000)


def search_google(query):
    import os

    os.system(f"start https://www.google.com/search?q={query.replace(' ', '+')}")


def convert_speech_to_text():
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("Listening...")
            audio = recognizer.listen(source)
            print("Audio recorded.")
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
