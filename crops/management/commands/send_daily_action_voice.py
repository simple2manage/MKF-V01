#
# import os
# import requests
# import base64
# from datetime import date
# from django.core.management.base import BaseCommand
# from crops.models import CropPlanRow
# from sarvamai import SarvamAI
#
# # ----------------- Configuration -----------------
# SARVAM_API_KEY = "sk_y1xdysnp_6uaVU3nUlJmR9Vy6l3YjwOtB"# Replace with valid key
# PHONE_NUMBER_ID ="758493914016711"
# WHATSAPP_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
#
# TARGET_LANG = "ml-IN"  # Malayalam
# TTS_SPEAKER = "anushka"
# OUTPUT_FILE_TEMPLATE = "voice_{user_id}.mp3"
# SPEECH_PACE = 0.8 # Normal speed (adjust 0.5-2.0)
# # -------------------------------------------------
#
# sarvamclient = SarvamAI(api_subscription_key=SARVAM_API_KEY)
#
# # ----------------- Helper Functions -----------------
# def translate_text(input_text):
#     resp = sarvamclient.text.translate(
#         input=input_text,
#         source_language_code="auto",
#         target_language_code=TARGET_LANG
#     )
#     return resp.translated_text
#
# def text_to_speech(text, output_file):
#     tts_resp = sarvamclient.text_to_speech.convert(
#         text=text,
#         target_language_code=TARGET_LANG,
#         speaker=TTS_SPEAKER,
#         output_audio_codec="mp3",
#         pace=SPEECH_PACE
#     )
#
#     audio_b64 = tts_resp.audios[0]
#     if not audio_b64:
#         raise ValueError("No audio returned from TTS API.")
#
#     audio_bytes = base64.b64decode(audio_b64)
#     with open(output_file, "wb") as f:
#         f.write(audio_bytes)
#
#     # Optional: Play audio locally to verify
#     if os.name == "nt":  # Windows
#         os.system(f'start {output_file}')
#     else:  # Linux/macOS
#         os.system(f'afplay {output_file}')  # or 'mpg123 {output_file}'
#
# def whatsapp_upload_media(file_path):
#     if not os.path.exists(file_path):
#         raise FileNotFoundError(f"File not found: {file_path}")
#
#     url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/media"
#     headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
#     files = {'file': (file_path, open(file_path, 'rb'), 'audio/mpeg')}
#     data = {"messaging_product": "whatsapp"}
#     response = requests.post(url, headers=headers, files=files, data=data)
#     response.raise_for_status()
#     return response.json().get("id")
#
# def whatsapp_send_audio(recipient, media_id):
#     url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
#     headers = {
#         "Authorization": f"Bearer {WHATSAPP_TOKEN}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "messaging_product": "whatsapp",
#         "to": recipient,
#         "type": "audio",
#         "audio": {"id": media_id}
#     }
#     response = requests.post(url, headers=headers, json=payload)
#     response.raise_for_status()
#     return response.json()["messages"][0]["id"]
#
# # ----------------- Django Command -----------------
# class Command(BaseCommand):
#     help = "Send today's CropPlanRow action as voice via WhatsApp"
#
#     def handle(self, *args, **kwargs):
#         today = date.today()
#         plan_rows = CropPlanRow.objects.filter(date=today).order_by('user_crop_plan__user', 'created')
#
#         if not plan_rows.exists():
#             self.stdout.write(self.style.WARNING("No CropPlanRow actions found for today."))
#             return
#
#         for row in plan_rows:
#             user = row.user_crop_plan.user
#             recipient = user.phone_number
#
#             if not recipient:
#                 self.stdout.write(self.style.WARNING(f"Skipping user {user} - No phone number found."))
#                 continue
#
#             action_text = row.action
#             if not action_text:
#                 self.stdout.write(self.style.WARNING(f"Skipping user {user} - No action specified."))
#                 continue
#
#             # Final WhatsApp message with user name
#             input_text = f"ഹായ് {user.name}, ഞാന്‍ മൈ ക്രിഷി ഫ്രണ്ട്. {action_text}"
#
#
#             try:
#                 translated_text = translate_text(input_text)
#
#                 output_file = OUTPUT_FILE_TEMPLATE.format(user_id=user.id)
#                 text_to_speech(translated_text, output_file)
#
#                 media_id = whatsapp_upload_media(output_file)
#                 audio_msg_id = whatsapp_send_audio(recipient, media_id)
#
#                 os.remove(output_file)
#
#                 self.stdout.write(self.style.SUCCESS(
#                     f"✅ Sent audio (ID: {audio_msg_id}) to {user} ({recipient})"
#                 ))
#
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(
#                     f"❌ Failed for user {user} ({recipient}): {str(e)}"
#                 ))
import os
import requests
import base64
from datetime import date
from django.core.management.base import BaseCommand
from crops.models import CropPlanRow
from sarvamai import SarvamAI
from deep_translator import GoogleTranslator

# ----------------- Configuration -----------------
SARVAM_API_KEY = "sk_y1xdysnp_6uaVU3nUlJmR9Vy6l3YjwOtB"  # Replace with valid key
PHONE_NUMBER_ID = "758493914016711"
WHATSAPP_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')

TARGET_LANG = "ml-IN"  # Malayalam
TTS_SPEAKER = "anushka"
OUTPUT_FILE_TEMPLATE = "voice_{user_id}.mp3"
SPEECH_PACE = 0.8  # Adjust 0.5–2.0 (0.8 = slower pace)

# -------------------------------------------------
sarvamclient = SarvamAI(api_subscription_key=SARVAM_API_KEY)

# ----------------- Helpers -----------------
def translate_to_malayalam(text):
    """Translate text from English (or auto-detected) to Malayalam"""
    try:
        return GoogleTranslator(source="auto", target="ml").translate(text)
    except Exception:
        return text


def text_to_speech(text, output_file):
    """Convert Malayalam text to speech using SarvamAI"""
    tts_resp = sarvamclient.text_to_speech.convert(
        text=text,
        target_language_code=TARGET_LANG,
        speaker=TTS_SPEAKER,
        output_audio_codec="mp3",
        pace=SPEECH_PACE
    )

    audio_b64 = tts_resp.audios[0]
    if not audio_b64:
        raise ValueError("No audio returned from TTS API.")

    audio_bytes = base64.b64decode(audio_b64)
    with open(output_file, "wb") as f:
        f.write(audio_bytes)


def whatsapp_upload_media(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/media"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {'file': (file_path, open(file_path, 'rb'), 'audio/mpeg')}
    data = {"messaging_product": "whatsapp"}
    response = requests.post(url, headers=headers, files=files, data=data)
    response.raise_for_status()
    return response.json().get("id")


def whatsapp_send_audio(recipient, media_id):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "audio",
        "audio": {"id": media_id}
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["messages"][0]["id"]


# ----------------- Django Command -----------------
class Command(BaseCommand):
    help = "Send today's CropPlanRow action as voice via WhatsApp"

    def handle(self, *args, **kwargs):
        today = date.today()
        plan_rows = CropPlanRow.objects.filter(date=today).order_by(
            'user_crop_plan__user', 'created'
        )

        if not plan_rows.exists():
            self.stdout.write(self.style.WARNING("No CropPlanRow actions found for today."))
            return

        for row in plan_rows:
            user = row.user_crop_plan.user
            recipient = user.phone_number

            if not recipient:
                self.stdout.write(self.style.WARNING(f"Skipping user {user} - No phone number found."))
                continue

            action_text = row.action
            if not action_text:
                self.stdout.write(self.style.WARNING(f"Skipping user {user} - No action specified."))
                continue

            try:
                # ✅ Translate only the action_text
                action_text_ml = translate_to_malayalam(action_text)

                # Final Malayalam input text
                input_text = f"ഹായ് {user.name}, ഞാന്‍ മൈ ക്രിഷി ഫ്രണ്ട്. {action_text_ml}"

                # Convert to speech
                output_file = OUTPUT_FILE_TEMPLATE.format(user_id=user.id)
                text_to_speech(input_text, output_file)

                # Upload & send
                media_id = whatsapp_upload_media(output_file)
                audio_msg_id = whatsapp_send_audio(recipient, media_id)

                # Remove temp file
                os.remove(output_file)

                self.stdout.write(self.style.SUCCESS(
                    f"✅ Sent audio (ID: {audio_msg_id}) to {user} ({recipient})"
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"❌ Failed for user {user} ({recipient}): {str(e)}"
                ))
