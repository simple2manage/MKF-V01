import os
import requests
from dotenv import load_dotenv

load_dotenv()
def transcribe_audio_with_sarvam(audio_file_data):
    """
    Sends audio data to the Sarvam AI API for transcription.
    """
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        return {"error": "Sarvam API key not found in environment variables."}

    url = "https://api.sarvam.ai/speech-to-text"
    headers = {
        "api-subscription-key": api_key,
    }
    files = {
        'file': ('audio.wav', audio_file_data, 'audio/wav')
    }
    data = {
        "model": "saarika:v2.5",
        "language_code": "unknown",  # Auto-detect language
    }

    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()

        transcription = response.json().get("transcript")
        if transcription:
            return {"transcription": transcription}
        else:
            return {"error": f"No transcription found in the API response. Response: {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}

