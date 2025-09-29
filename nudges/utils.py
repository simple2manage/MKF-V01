# your_app/utils.py (or can be in services.py)

# import re
#
# def parse_cost_details_from_text(text: str) -> dict:
#     """
#     Parses transcribed text to extract cost details using keywords.
#     Ensures that each field is returned as a dict suitable for JSONField:
#         {"data": <number>, "is_read": True}
#     If a field is not mentioned in the text, defaults to 0.
#     """
#     parsed_data = {}
#     text = text.lower()
#
#     # Map keywords to your model/serializer fields
#     keywords_map = {
#         'labour': 'labour_estimation',
#         'machine': 'machine_estimation',
#         'input': 'input_estimation',
#         'miscellaneous': 'miscellaneous',
#     }
#
#     for keyword, field in keywords_map.items():
#         # Search for a number following the keyword (e.g., "labour 5000")
#         match = re.search(f"{keyword}[\\s\\w]*?(\\d+)", text)
#         value = int(match.group(1)) if match else 0
#         parsed_data[field] = {"data": value, "is_read": True}
#
#     return parsed_data


# your_app/utils.py

import re
from word2number import w2n  # pip install word2number
#
# def parse_cost_details_from_text(text: str) -> dict:
#     """
#     Parses transcribed text to extract cost details using keywords.
#     Supports both numeric and word-based numbers (e.g., "five thousand").
#     """
#     parsed_data = {}
#     text = text.lower()
#
#     # Define keywords and their corresponding model fields
#     keywords_map = {
#         'labour': 'labour_estimation',
#         'machine': 'machine_estimation',
#         'input': 'input_estimation',
#         'miscellaneous': 'miscellaneous',
#     }
#
#     for keyword, field in keywords_map.items():
#         # Regex to match either digits or words after the keyword
#         pattern = rf"{keyword}[\s\w]*?([\d]+|(?:\w+\s?)+)"
#         match = re.search(pattern, text)
#         if match:
#             value_str = match.group(1).strip()
#             try:
#                 # Try converting digits first
#                 value = int(value_str)
#             except ValueError:
#                 try:
#                     # Convert word numbers to int
#                     value = w2n.word_to_num(value_str)
#                 except ValueError:
#                     continue  # skip if not convertible
#             parsed_data[field] = value
#
#     return parsed_data

# save as generate_sample_audio.py
from gtts import gTTS
import soundfile as sf
import numpy as np
import io
import os
import os
import requests
from dotenv import load_dotenv

load_dotenv()
#
# # Text to convert
# text = "Labour 5000, machine 2000, input 1500, miscellaneous 500"
#
# # Generate speech with gTTS
# tts = gTTS(text=text, lang='en')
# tts.save("sample_audio.mp3")
#
# print("Audio saved as sample_audio.mp3")
# #pip install gtts
#
# #pip install pydub soundfile
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