from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
import hmac
import hashlib
import json
from rest_framework.permissions import IsAuthenticated, AllowAny

from .services import rag_service

def verify_signature(request):
    secret = settings.META_APP_SECRET
    if not secret:
        return True
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature[7:], expected)

def send_whatsapp_text(to_number, text):
    url = f"https://graph.facebook.com/v20.0/{settings.PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text[:4096]}
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def sarvam_tts(text):
    if not settings.SARVAM_API_KEY:
        return None
    try:
        from sarvamai import SarvamAI
        client = SarvamAI(api_key=settings.SARVAM_API_KEY)
        audio = client.tts.synthesize(text=text, voice=settings.SARVAM_VOICE, format=settings.SARVAM_FORMAT)
        return audio if isinstance(audio, (bytes, bytearray)) else None
    except Exception:
        return None

@csrf_exempt
def webhook(request):
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        if mode == "subscribe" and token == settings.VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponseForbidden("Verification failed")

    if request.method == "POST":
        if not verify_signature(request):
            return HttpResponseForbidden("Invalid signature")

        data = json.loads(request.body.decode())
        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            messages = value.get("messages", [])
            if not messages:
                return JsonResponse({"status": "ignored"})

            msg = messages[0]
            from_number = msg["from"]
            msg_type = msg.get("type")

            if msg_type == "text":
                user_text = msg["text"]["body"].strip()
            elif msg_type == "interactive":
                user_text = msg["interactive"]["button_reply"]["title"] if "button_reply" in msg["interactive"] \
                    else msg["interactive"]["list_reply"]["title"]
            else:
                send_whatsapp_text(from_number, "Please send a text question.")
                return JsonResponse({"status": "non-text"})

            answer_text = rag_service.answer(user_text)
            send_whatsapp_text(from_number, answer_text)

            if settings.REPLY_WITH_VOICE:
                audio = sarvam_tts(answer_text)
                if audio:
                    upload_url = f"https://graph.facebook.com/v20.0/{settings.PHONE_NUMBER_ID}/media"
                    headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
                    files = {
                        "file": ("tts.mp3", audio, "audio/mpeg")
                    }
                    data = {"messaging_product": "whatsapp"}
                    upload_resp = requests.post(upload_url, headers=headers, files=files, data=data)
                    upload_resp.raise_for_status()
                    media_id = upload_resp.json()["id"]
                    msg_url = f"https://graph.facebook.com/v20.0/{settings.PHONE_NUMBER_ID}/messages"
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": from_number,
                        "type": "audio",
                        "audio": {"id": media_id}
                    }
                    requests.post(msg_url, headers=headers, json=payload)

            return JsonResponse({"status": "ok"})
        except Exception as e:
            print("Error:", e)
            return JsonResponse({"status": "error"})


class TriggerMessageView(APIView):
    permission_classes = [AllowAny] 


    def post(self, request):
        phone_number = request.data.get("phone_number")
        if not phone_number:
            return Response({"error": "Phone number is required."}, status=400)
        try:
            url = f"https://graph.facebook.com/v20.0/{settings.PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {"body": "How can I help you?"}
            }
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return Response({"status": "message sent"})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
