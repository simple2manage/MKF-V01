#
# import requests
# from datetime import date
# from django.core.management.base import BaseCommand
# from crops.models import CropPlanRow
# import os
# from deep_translator import GoogleTranslator
#
# # Configuration
# PHONE_NUMBER_ID = "758493914016711"
# WHATSAPP_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
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
# def translate_to_malayalam(text):
#     """Translate text from English (or auto-detected) to Malayalam"""
#     try:
#         return GoogleTranslator(source="auto", target="ml").translate(text)
#     except Exception as e:
#         # Fallback to original text if translation fails
#         return text
#
#
# class Command(BaseCommand):
#     help = "Send today's CropPlanRow action as text via WhatsApp (in Malayalam)"
#
#     def handle(self, *args, **kwargs):
#         today = date.today()
#
#         plan_rows = CropPlanRow.objects.filter(date=today).order_by(
#             'user_crop_plan__user', 'created'
#         )
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
#             # Translate action text to Malayalam
#             action_text_ml = translate_to_malayalam(action_text)
#
#             # Final WhatsApp message
#             # Final WhatsApp message with user name
#             input_text = f"ഹായ് {user.name}, ഞാന്‍ മൈ ക്രിഷി ഫ്രണ്ട്. {action_text_ml}"
#
#             try:
#                 text_msg_id = whatsapp_send_text(recipient, input_text)
#
#                 self.stdout.write(self.style.SUCCESS(
#                     f"✅ Sent Malayalam text (ID: {text_msg_id}) to {user} ({recipient})"
#                 ))
#
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(
#                     f"❌ Failed for user {user} ({recipient}): {str(e)}"
#                 ))
# import requests
# from datetime import date
# from django.core.management.base import BaseCommand
# from crops.models import CropPlanRow
# import os
# from deep_translator import GoogleTranslator
#
# # Configuration
# PHONE_NUMBER_ID = "758493914016711"
# WHATSAPP_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
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
# def translate_to_malayalam(text):
#     """Translate text from English (or auto-detected) to Malayalam"""
#     try:
#         return GoogleTranslator(source="auto", target="ml").translate(text)
#     except Exception:
#         return text
#
#
# class Command(BaseCommand):
#     help = "Send today's CropPlanRow action + pending (unread) tasks via WhatsApp"
#
#     def handle(self, *args, **kwargs):
#         today = date.today()
#
#         # Get today's crop plan rows
#         plan_rows = CropPlanRow.objects.filter(date=today).order_by(
#             'user_crop_plan__user', 'created'
#         )
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
#             # --- Collect today's action ---
#             tasks = []
#             if row.action:
#                 tasks.append(("ഇന്നത്തെ ടാസ്ക്", row.action))  # Today's task
#
#             # --- Collect previous unread actions ---
#             previous_unread = CropPlanRow.objects.filter(
#                 user_crop_plan=row.user_crop_plan,
#                 date__lt=today,
#                 read=False
#             ).order_by("date")
#
#             for prev in previous_unread:
#                 if prev.action:
#                     tasks.append((f"{prev.date} ലെ ടാസ്ക്", prev.action))
#
#             if not tasks:
#                 self.stdout.write(self.style.WARNING(f"Skipping user {user} - No action specified."))
#                 continue
#
#             # Translate and format as task list
#             translated_tasks = []
#             for label, action_text in tasks:
#                 action_ml = translate_to_malayalam(action_text)
#                 translated_tasks.append(f"✅ {label}: {action_ml}")
#
#             tasklist_text = "\n".join(translated_tasks)
#
#             # Final message
#             input_text = f"ഹായ് {user.name}, ഞാന്‍ മൈ ക്രിഷി ഫ്രണ്ട് 👩‍🌾\n\nനിങ്ങളുടെ ടാസ്ക് ലിസ്റ്റ്:\n{tasklist_text}"
#
#             try:
#                 text_msg_id = whatsapp_send_text(recipient, input_text)
#
#                 self.stdout.write(self.style.SUCCESS(
#                     f"✅ Sent tasklist (ID: {text_msg_id}) to {user} ({recipient})"
#                 ))
#
#                 # ✅ Optional: Mark previous tasks as read
#                 previous_unread.update(read=True)
#
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(
#                     f"❌ Failed for user {user} ({recipient}): {str(e)}"
#                 ))
import requests
from datetime import date
from django.core.management.base import BaseCommand
from crops.models import CropPlanRow
import os
from deep_translator import GoogleTranslator
from collections import defaultdict

# Configuration
PHONE_NUMBER_ID = "758493914016711"
WHATSAPP_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')


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


def translate_to_malayalam(text):
    """Translate text from English (or auto-detected) to Malayalam"""
    try:
        return GoogleTranslator(source="auto", target="ml").translate(text)
    except Exception:
        return text


class Command(BaseCommand):
    help = "Send today's CropPlanRow action + previous unread tasks via WhatsApp"

    def handle(self, *args, **kwargs):
        today = date.today()
        user_tasks = defaultdict(list)

        # --- Collect today's tasks ---
        today_rows = CropPlanRow.objects.filter(date=today).order_by(
            'user_crop_plan__user', 'created'
        )
        for row in today_rows:
            if row.action:
                user_tasks[row.user_crop_plan.user].append(("ഇന്നത്തെ ടാസ്ക്", row.action))

        # --- Collect previous unread tasks for all users ---
        previous_unread_rows = CropPlanRow.objects.filter(
            date__lt=today,
            read=False
        ).order_by("user_crop_plan__user", "date")

        for row in previous_unread_rows:
            if row.action:
                user_tasks[row.user_crop_plan.user].append((f"{row.date} ലെ ടാസ്ക്", row.action))

        if not user_tasks:
            self.stdout.write(self.style.WARNING("No CropPlanRow actions (today or pending) found."))
            return

        # --- Send one message per user ---
        for user, tasks in user_tasks.items():
            recipient = user.phone_number
            if not recipient:
                self.stdout.write(self.style.WARNING(f"Skipping user {user} - No phone number found."))
                continue

            translated_tasks = []
            # Merge same-day actions into a single line if multiple actions exist on the same day
            tasks_by_day = defaultdict(list)
            for label, action_text in tasks:
                tasks_by_day[label].append(action_text)

            for label, actions in tasks_by_day.items():
                action_ml = translate_to_malayalam(", ".join(actions))
                translated_tasks.append(f"✅ {label}: {action_ml}")

            tasklist_text = "\n".join(translated_tasks)

            input_text = (
                f"ഹായ് {user.name}, ഞാന്‍ മൈ ക്രിഷി ഫ്രണ്ട് 👩‍🌾\n\n"
                f"നിങ്ങളുടെ ടാസ്ക് ലിസ്റ്റ്:\n{tasklist_text}"
            )

            try:
                text_msg_id = whatsapp_send_text(recipient, input_text)
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Sent grouped tasklist (ID: {text_msg_id}) to {user} ({recipient})"
                ))

                # mark previous tasks as read
                previous_unread_rows.filter(user_crop_plan__user=user).update(read=True)

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"❌ Failed for user {user} ({recipient}): {str(e)}"
                ))
