import os
import requests
import base64
from datetime import date
from django.core.management.base import BaseCommand
from crops.models import CropPlanRow
from sarvamai import SarvamAI

# ---------------- Configuration ----------------
SARVAM_API_KEY       = "sk_y1xdysnp_6uaVU3nUlJmR9Vy6l3YjwOtB"
PHONE_NUMBER_ID      = "758493914016711"  # Your WABA Phone Number ID
WHATSAPP_TOKEN       = "EAATEOp0sFpABPT0Hpn2o5EBFBHPFjByERZBorkE7ZCtRpZBbcu9UnEMMZC17G4SWsn9GofyohJWK1XcIOzrSZB3A0LinO7z1q4yorudSSQ5ZAZCeuqSNz9UZBb1NrVq6QH0dddGcHZCTSSSsGEagCMmIaOKZAfxesf5VYSgIahTf54PFV2tcsDOtlWZBEA3uesdpTih68bvREU4RWR66yXI4qhbrmqHZCxUzCMFHm87Pn11IyZBL7fgZDZD"
RECIPIENT            = "919947942405"  # Target recipient (without '+')
TARGET_LANG          = "ml-IN"          # Malayalam
TTS_SPEAKER          = "manisha"
OUTPUT_FILE          = "voice.mp3"

# Initialize SarvamAI Client
sarvamclient = SarvamAI(api_subscription_key=SARVAM_API_KEY)


# --------------- Helper Functions ----------------
def translate_text(input_text):
    resp = sarvamclient.text.translate(
        input=input_text,
        source_language_code="auto",
        target_language_code=TARGET_LANG
    )
    return resp.translated_text


def text_to_speech(text, output_file):
    tts_resp = sarvamclient.text_to_speech.convert(
        text=text,
        target_language_code=TARGET_LANG,
        speaker=TTS_SPEAKER,
        output_audio_codec="mp3"
    )
    audio_b64 = tts_resp.audios[0]
    audio_bytes = base64.b64decode(audio_b64)
    with open(output_file, "wb") as f:
        f.write(audio_bytes)
    print(f"TTS audio saved → {output_file}")


def whatsapp_upload_media(file_path):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/media"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {'file': (file_path, open(file_path, 'rb'), 'audio/mpeg')}
    data = {"messaging_product": "whatsapp"}
    response = requests.post(url, headers=headers, files=files, data=data)
    response.raise_for_status()
    media_id = response.json().get("id")
    print(f"Media uploaded successfully: media_id={media_id}")
    return media_id


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
    print("WhatsApp Send Response:", response.json())
    response.raise_for_status()
    return response.json()["messages"][0]["id"]


# ---------------- Management Command ----------------
class Command(BaseCommand):
    help = "Send today's CropPlanRow action via WhatsApp"

    def handle(self, *args, **kwargs):
        try:
            # Fetch today's CropPlanRow action
            today = date.today()
            row = CropPlanRow.objects.filter(date=today).first()
            if not row or not row.action:
                self.stdout.write(self.style.ERROR("No action found for today!"))
                return
            input_text = f"Hi, I am from Simplify Agri: {row.action}"
            self.stdout.write(f"Composed message: {input_text}")

            # input_text = row.action
            # self.stdout.write(f"Today's action: {input_text}")

            # Translate and generate TTS
            self.stdout.write("\n[1] Translating text...")
            translated_text = translate_text(input_text)
            self.stdout.write(f"Translated Text: {translated_text}")

            self.stdout.write("\n[2] Generating TTS audio...")
            text_to_speech(translated_text, OUTPUT_FILE)

            self.stdout.write("\n[3] Uploading media to WhatsApp...")
            media_id = whatsapp_upload_media(OUTPUT_FILE)

            self.stdout.write("\n[4] Sending audio message via WhatsApp...")
            msg_id = whatsapp_send_audio(RECIPIENT, media_id)
            self.stdout.write(self.style.SUCCESS(f"✅ WhatsApp Audio Message Sent! Message ID: {msg_id}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error Occurred: {str(e)}"))
