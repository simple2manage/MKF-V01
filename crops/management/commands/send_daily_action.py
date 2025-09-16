
import requests
from datetime import date
from django.core.management.base import BaseCommand
from crops.models import CropPlanRow
import os

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
