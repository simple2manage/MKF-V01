# # your_app/services.py
#
# import os
# import requests
# from dotenv import load_dotenv
#
# load_dotenv()  # Loads variables from .env file
#
#
# def transcribe_audio_with_sarvam(audio_file_data):
#     """
#     Sends audio data to the Sarvam AI API for transcription.
#     """
#     api_key = os.getenv("SARVAM_API_KEY")
#     # Note: Please verify the exact API endpoint from Sarvam AI's documentation.
#     # This is a general example for a speech-to-text API.
#     url = "https://api.sarvam.ai/v1/speech/transcriptions"
#
#     if not api_key:
#         return {"error": "Sarvam API key not found."}
#
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#     }
#
#     files = {
#         'file': ('audio.wav', audio_file_data, 'audio/wav')
#     }
#
#     # You might need to specify a model, check Sarvam's documentation
#     # data = {
#     #     "model": "whisper-1" # Example model name
#     # }
#
#     try:
#         response = requests.post(url, headers=headers, files=files)  # , data=data)
#         response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
#
#         # The response structure might vary, adjust based on Sarvam's API docs.
#         # Assuming it returns a JSON with a 'text' or 'transcription' key.
#         return response.json()
#
#     except requests.exceptions.RequestException as e:
#         return {"error": f"API request failed: {e}"}

import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def transcribe_audio_with_sarvam(audio_file_data):
    """
    Sends audio data to the Sarvam AI API for transcription.
    """
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        return {"error": "Sarvam API key not found."}

    url = "https://api.sarvam.ai/speech-to-text"
    headers = {
        "api-subscription-key": api_key,
    }

    files = {
        'file': ('audio.wav', audio_file_data, 'audio/wav')
    }

    data = {
        "model": "saarika:v2.5",  # Default model
        "language_code": "unknown",  # Auto-detect language
    }

    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()

        # Assuming the response contains a 'transcript' field
        transcription = response.json().get("transcript")
        if transcription:
            return {"transcription": transcription}
        else:
            return {"error": "No transcription found in the response."}

    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
