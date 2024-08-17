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
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")


def get_youtube_transcript(video_id):
    import requests
    from selectolax.parser import HTMLParser

    url = "https://youtubetranscript.com/"
    params = {"server_vid2": video_id}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
        "Referer": f"https://youtubetranscript.com/?v={video_id}",
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        parser = HTMLParser(response.text)
        transcript_elements = parser.css('text')

        def format_timestamp(seconds):
            minutes, seconds = divmod(int(float(seconds)), 60)
            return f"{minutes:02d}:{seconds:02d}"

        timestamp_text_pairs = []
        for element in transcript_elements:
            start_time = element.attributes.get('start', '0')
            formatted_time = format_timestamp(start_time)
            text = element.text().strip()
            text = ' '.join(text.split())  # This replaces all whitespace (including newlines) with a single space
            pair = f"{formatted_time}:{text}"
            timestamp_text_pairs.append(pair)

        return "\n".join(timestamp_text_pairs)
    except Exception as e:
        raise Exception(f"Failed to fetch transcript: {e}")


if __name__ == "__main__":
    video_id = "wiLJ1-cQgFM"
    result = get_youtube_transcript(video_id)
    print(result[:5000])  # Print first 500 characters of the transcript
