

import re

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
    # The API expects the file to be sent in the 'files' parameter
    files = {
        'file': ('audio.wav', audio_file_data, 'audio/wav')
    }
    # Additional parameters are sent in the 'data' parameter
    data = {
        "model": "saarika:v2.5",
        "language_code": "unknown",  # Auto-detect language
    }

    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        transcription = response.json().get("transcript")
        if transcription:
            return {"transcription": transcription}
        else:
            # Handle cases where the API call succeeded but returned no transcript
            return {"error": f"No transcription found in the API response. Response: {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}


def parse_cost_details_from_text(text: str) -> dict:
    """
    Parses transcribed text to extract cost details for specific keywords.
    It returns a dictionary with keys matching the model fields and values
    formatted correctly for the JSONField structure.
    """
    parsed_data = {}
    text = text.lower()

    keywords_map = {
        'labour': 'labour_estimation',
        'machine': 'machine_estimation',
        'input': 'input_estimation',
        'miscellaneous': 'miscellaneous',
    }

    for keyword, field in keywords_map.items():
        # Regex to find a keyword followed by any characters (non-greedy) and then a number.
        # Handles numbers with commas and decimal points.
        match = re.search(rf"{keyword}[\s\w]*?([\d,.]+)", text)

        if match:
            # Clean the matched number string (remove commas) and convert to float
            value_str = match.group(1).replace(',', '')
            value = float(value_str)
        else:
            value = 0.0

        # Wrap the extracted value in the required dictionary format
        parsed_data[field] = {"data": value, "is_read": True}

    return parsed_data