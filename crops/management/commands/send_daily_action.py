# import os
# import requests
# import base64
# from datetime import date
# from django.core.management.base import BaseCommand
# from crops.models import CropPlanRow
# from sarvamai import SarvamAI
#
# # ---------------- Configuration ----------------
# SARVAM_API_KEY       = "sk_y1xdysnp_6uaVU3nUlJmR9Vy6l3YjwOtB"
# PHONE_NUMBER_ID      = "758493914016711"  # Your WABA Phone Number ID
# WHATSAPP_TOKEN       = "EAATEOp0sFpABPWiQSWO0NMdzg0b7Ax5jt2Fm3ZA8LaM051RW4LiHcaDZAQ5n30q29KDD3JAes85rv1lKr89Or4Qyrmp38fboH0mcumjbizquu2NZASxZCmxWV47sGZADZCvqOlvGcXZCwlHcFkmDH72PCIJn4wbF2K0BhYgCRGP2jJ7oy9pwwImUuYmD77AVdGiUeZA99iujreDZAYir8TZCQA1ZAXCaPHHDAM7GYZAanhGpTzRA4gZDZD"
# RECIPIENT            = "919947942405"  # Target recipient (without '+')
# TARGET_LANG          = "ml-IN"          # Malayalam
# TTS_SPEAKER          = "manisha"
# OUTPUT_FILE          = "voice.mp3"
#
# # Initialize SarvamAI Client
# sarvamclient = SarvamAI(api_subscription_key=SARVAM_API_KEY)
#
#
# # --------------- Helper Functions ----------------
# def translate_text(input_text):
#     resp = sarvamclient.text.translate(
#         input=input_text,
#         source_language_code="auto",
#         target_language_code=TARGET_LANG
#     )
#     return resp.translated_text
#
#
# def text_to_speech(text, output_file):
#     tts_resp = sarvamclient.text_to_speech.convert(
#         text=text,
#         target_language_code=TARGET_LANG,
#         speaker=TTS_SPEAKER,
#         output_audio_codec="mp3"
#     )
#     audio_b64 = tts_resp.audios[0]
#     audio_bytes = base64.b64decode(audio_b64)
#     with open(output_file, "wb") as f:
#         f.write(audio_bytes)
#     print(f"TTS audio saved → {output_file}")
#
#
# def whatsapp_upload_media(file_path):
#     url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/media"
#     headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
#     files = {'file': (file_path, open(file_path, 'rb'), 'audio/mpeg')}
#     data = {"messaging_product": "whatsapp"}
#     response = requests.post(url, headers=headers, files=files, data=data)
#     response.raise_for_status()
#     media_id = response.json().get("id")
#     print(f"Media uploaded successfully: media_id={media_id}")
#     return media_id
#
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
#     print("WhatsApp Send Response:", response.json())
#     response.raise_for_status()
#     return response.json()["messages"][0]["id"]
#
#
# # ---------------- Management Command ----------------
# class Command(BaseCommand):
#     help = "Send today's CropPlanRow action via WhatsApp"
#
#     def handle(self, *args, **kwargs):
#         try:
#             # Fetch today's CropPlanRow action
#             today = date.today()
#             row = CropPlanRow.objects.filter(date=today).first()
#             if not row or not row.action:
#                 self.stdout.write(self.style.ERROR("No action found for today!"))
#                 return
#             input_text = f"Hi, I am from Simplify Agri: {row.action}"
#             self.stdout.write(f"Composed message: {input_text}")
#
#             # input_text = row.action
#             # self.stdout.write(f"Today's action: {input_text}")
#
#             # Translate and generate TTS
#             self.stdout.write("\n[1] Translating text...")
#             translated_text = translate_text(input_text)
#             self.stdout.write(f"Translated Text: {translated_text}")
#
#             self.stdout.write("\n[2] Generating TTS audio...")
#             text_to_speech(translated_text, OUTPUT_FILE)
#
#             self.stdout.write("\n[3] Uploading media to WhatsApp...")
#             media_id = whatsapp_upload_media(OUTPUT_FILE)
#
#             self.stdout.write("\n[4] Sending audio message via WhatsApp...")
#             msg_id = whatsapp_send_audio(RECIPIENT, media_id)
#             self.stdout.write(self.style.SUCCESS(f"✅ WhatsApp Audio Message Sent! Message ID: {msg_id}"))
#
#         except Exception as e:
#             self.stdout.write(self.style.ERROR(f"\n❌ Error Occurred: {str(e)}"))





# import os
# import requests
# import base64
# from datetime import date
# from django.core.management.base import BaseCommand
# from crops.models import CropPlanRow
# from sarvamai import SarvamAI
#
# # ---------------- Configuration ----------------
# SARVAM_API_KEY       = "sk_y1xdysnp_6uaVU3nUlJmR9Vy6l3YjwOtB"
# PHONE_NUMBER_ID      = "758493914016711"
# WHATSAPP_TOKEN       = "EAATEOp0sFpABPe8yzhZA9zuo6SNX1sWdHDHJnJuGII5h3VaVqiU2bwJcO0K84V0W2j3w7fexMABKSv81ZAq28x7OZABansc2xRse1HVLRBvaHT6NegPxrH2pP7ZBQv01MI5T3SNxElFzQBT6pOZB8HvOLYfMZAnSCkmOLMQXNHNzfIS1T1iuDxFUEBdrsojOFPuYEcAJmSBa83G6dt3mnCoRJkL5mYuZBY1jrObfaGaVOqKdAZDZD"
# TARGET_LANG          = "ml-IN"
# TTS_SPEAKER          = "manisha"
# OUTPUT_FILE_TEMPLATE = "voice_{user_id}.mp3"
#
#
# # Initialize SarvamAI Client
# sarvamclient = SarvamAI(api_subscription_key=SARVAM_API_KEY)
#
#
# # --------------- Helper Functions ----------------
# def translate_text(input_text):
#     resp = sarvamclient.text.translate(
#         input=input_text,
#         source_language_code="auto",
#         target_language_code=TARGET_LANG
#     )
#     return resp.translated_text
#
#
# def text_to_speech(text, output_file):
#     tts_resp = sarvamclient.text_to_speech.convert(
#         text=text,
#         target_language_code=TARGET_LANG,
#         speaker=TTS_SPEAKER,
#         output_audio_codec="mp3"
#     )
#     audio_b64 = tts_resp.audios[0]
#     audio_bytes = base64.b64decode(audio_b64)
#     with open(output_file, "wb") as f:
#         f.write(audio_bytes)
#
#
# def whatsapp_upload_media(file_path):
#     url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/media"
#     headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
#     files = {'file': (file_path, open(file_path, 'rb'), 'audio/mpeg')}
#     data = {"messaging_product": "whatsapp"}
#     response = requests.post(url, headers=headers, files=files, data=data)
#     response.raise_for_status()
#     return response.json().get("id")
#
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
#
# def whatsapp_send_text(recipient, message_text):
#     url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
#     headers = {
#         "Authorization": f"Bearer {WHATSAPP_TOKEN}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "messaging_product": "whatsapp",
#         "to": recipient,
#         "type": "text",
#         "text": {"body": message_text}
#     }
#     response = requests.post(url, headers=headers, json=payload)
#     response.raise_for_status()
#     return response.json()["messages"][0]["id"]
#
#
# # ---------------- Management Command ----------------
# class Command(BaseCommand):
#     help = "Send today's CropPlanRow action as both text and voice via WhatsApp"
#
#     def handle(self, *args, **kwargs):
#         today = date.today()
#
#         # Fetch all CropPlanRows for today
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
#             input_text = f"Hi, I am from Simplify Agri: {action_text}"
#
#             try:
#                 # Send text message
#                 text_msg_id = whatsapp_send_text(recipient, input_text)
#
#                 # Translate text for TTS
#                 translated_text = translate_text(input_text)
#
#                 # Generate unique voice file per user
#                 output_file = OUTPUT_FILE_TEMPLATE.format(user_id=user.id)
#                 text_to_speech(translated_text, output_file)
#
#                 # Upload media
#                 media_id = whatsapp_upload_media(output_file)
#
#                 # Send audio message
#                 audio_msg_id = whatsapp_send_audio(recipient, media_id)
#
#                 # Clean up audio file
#                 os.remove(output_file)
#
#                 self.stdout.write(self.style.SUCCESS(
#                     f"✅ Sent text (ID: {text_msg_id}) and audio (ID: {audio_msg_id}) to {user} ({recipient})"
#                 ))
#
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"❌ Failed for user {user} ({recipient}): {str(e)}"))
# import os
# import requests
# import base64
# from datetime import date
# from django.core.management.base import BaseCommand
# from crops.models import CropPlanRow
# from sarvamai import SarvamAI
#
# # ---------------- Configuration ----------------
# SARVAM_API_KEY       = "sk_y1xdysnp_6uaVU3nUlJmR9Vy6l3YjwOtB"
# PHONE_NUMBER_ID      = "758493914016711"
# WHATSAPP_TOKEN       = "EAATEOp0sFpABPe8yzhZA9zuo6SNX1sWdHDHJnJuGII5h3VaVqiU2bwJcO0K84V0W2j3w7fexMABKSv81ZAq28x7OZABansc2xRse1HVLRBvaHT6NegPxrH2pP7ZBQv01MI5T3SNxElFzQBT6pOZB8HvOLYfMZAnSCkmOLMQXNHNzfIS1T1iuDxFUEBdrsojOFPuYEcAJmSBa83G6dt3mnCoRJkL5mYuZBY1jrObfaGaVOqKdAZDZD"
# TARGET_LANG          = "ml-IN"
# TTS_SPEAKER          = "anushka"  # Valid and clear voice agent
# OUTPUT_FILE_TEMPLATE = "voice_{user_id}.mp3"
#
#
# # Initialize SarvamAI Client
# sarvamclient = SarvamAI(api_subscription_key=SARVAM_API_KEY)
#
#
# # --------------- Helper Functions ----------------
# def translate_text(input_text):
#     resp = sarvamclient.text.translate(
#         input=input_text,
#         source_language_code="auto",
#         target_language_code=TARGET_LANG
#     )
#     return resp.translated_text
#
#
# def text_to_speech(text, output_file):
#     tts_resp = sarvamclient.text_to_speech.convert(
#         text=text,
#         target_language_code=TARGET_LANG,
#         speaker=TTS_SPEAKER,
#         output_audio_codec="mp3"
#     )
#     audio_b64 = tts_resp.audios[0]
#     audio_bytes = base64.b64decode(audio_b64)
#     with open(output_file, "wb") as f:
#         f.write(audio_bytes)
#
#
# def whatsapp_upload_media(file_path):
#     url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/media"
#     headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
#     files = {'file': (file_path, open(file_path, 'rb'), 'audio/mpeg')}
#     data = {"messaging_product": "whatsapp"}
#     response = requests.post(url, headers=headers, files=files, data=data)
#     response.raise_for_status()
#     return response.json().get("id")
#
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
#
# def whatsapp_send_text(recipient, message_text):
#     url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
#     headers = {
#         "Authorization": f"Bearer {WHATSAPP_TOKEN}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "messaging_product": "whatsapp",
#         "to": recipient,
#         "type": "text",
#         "text": {"body": message_text}
#     }
#     response = requests.post(url, headers=headers, json=payload)
#     response.raise_for_status()
#     return response.json()["messages"][0]["id"]
#
#
# # ---------------- Management Command ----------------
# class Command(BaseCommand):
#     help = "Send today's CropPlanRow action as both text and voice via WhatsApp"
#
#     def handle(self, *args, **kwargs):
#         today = date.today()
#
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
#             input_text = f"Hi, I am your friend . {action_text}"
#
#             try:
#                 # Send text message
#                 text_msg_id = whatsapp_send_text(recipient, input_text)
#
#                 # Translate text for TTS
#                 translated_text = translate_text(input_text)
#
#                 # Generate unique voice file per user
#                 output_file = OUTPUT_FILE_TEMPLATE.format(user_id=user.id)
#                 text_to_speech(translated_text, output_file)
#
#                 # Upload media
#                 media_id = whatsapp_upload_media(output_file)
#
#                 # Send audio message
#                 audio_msg_id = whatsapp_send_audio(recipient, media_id)
#
#                 # Clean up audio file
#                 os.remove(output_file)
#
#                 self.stdout.write(self.style.SUCCESS(
#                     f"✅ Sent text (ID: {text_msg_id}) and audio (ID: {audio_msg_id}) to {user} ({recipient})"
#                 ))
#
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"❌ Failed for user {user} ({recipient}): {str(e)}"))
import requests
from datetime import date
from django.core.management.base import BaseCommand
from crops.models import CropPlanRow


# Configuration
PHONE_NUMBER_ID = "758493914016711"
WHATSAPP_TOKEN = "EAATEOp0sFpABPcxnW8GCxcUtxtYj3UV9coXhqPzYv7bmosyPDonWY1bltgM9NS3kCYDzppYZC7NPpw1SLiJZBM7reUjuLIsiI61fzZBeTMTKq00sDElqpfyUzvrxoaJc5eJOSQndATlO2QlkzB2eqB2axtpf1fRpebctiIK0If7KYnnaWw2VmDKtmhcZCSKZBQUnQyMMfKdbEOYZCB1hlNUY6dKvWQRseonnvZAbQoOQJsO7gZDZD"


def whatsapp_send_text(recipient, message_text):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message_text}
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["messages"][0]["id"]


class Command(BaseCommand):
    help = "Send today's CropPlanRow action as text via WhatsApp"

    def handle(self, *args, **kwargs):
        today = date.today()

        plan_rows = CropPlanRow.objects.filter(date=today).order_by('user_crop_plan__user', 'created')

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

            input_text = f"Hi, I am your friend. {action_text}"

            try:
                text_msg_id = whatsapp_send_text(recipient, input_text)

                self.stdout.write(self.style.SUCCESS(
                    f"✅ Sent text (ID: {text_msg_id}) to {user} ({recipient})"
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed for user {user} ({recipient}): {str(e)}"))
