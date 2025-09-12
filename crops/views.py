# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Crop, UserCropPlan
from .serializer import CropSerializer, UserCropPlanSerializer
from rest_framework import generics
from .models import CropPlanRow
from .serializer import CropPlanRowSerializer
import pandas as pd
from .models import UserCropPlan, CropPlanRow
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from .models import UserCropPlan, CropPlanRow
from .serializer import UserCropPlanSerializer
import re
from rest_framework import generics, permissions
from .models import CropPlanRow
from .serializer import CropPlanRowSerializer
from .utils import reset_cropplanrow_id

class CropAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        crop_id = request.query_params.get('crop_id', None)

        # Filter crops by the logged-in user
        crops = Crop.objects.filter(created_by=request.user)

        if crop_id:
            crop_ids = [int(cid) for cid in crop_id.split(',') if cid.isdigit()]
            crops = crops.filter(id__in=crop_ids)

        serializer = CropSerializer(crops, many=True)
        return Response(serializer.data)


    # def get(self, request):
    #     crop_id = request.query_params.get('crop_id', None)
    #     if crop_id:
    #         crop_ids = [int(cid) for cid in crop_id.split(',') if cid.isdigit()]
    #         crops = Crop.objects.filter(id__in=crop_ids)
    #     else:
    #         crops = Crop.objects.all()
    #     serializer = CropSerializer(crops, many=True)
    #     return Response(serializer.data)
    def post(self, request):
        serializer = CropSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)  # Save with logged-in user as creator
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ZoneCropAPIView(APIView):
    permission_classes = [IsAuthenticated]  # authentication

    def get(self, request):
        zone_id = request.query_params.get('zone_id')

        if not zone_id:
            return Response({"error": "zone_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        crops = Crop.objects.filter(
            id__in=UserCropPlan.objects.filter(zone_id=zone_id).values_list('crop_id', flat=True),
            created_by=request.user  # Only crops created by the logged-in user
        ).distinct()

        serializer = CropSerializer(crops, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    # def get(self, request):
    #     zone_id = request.query_params.get('zone_id')
    #
    #     if not zone_id:
    #         return Response({"error": "zone_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     crops = Crop.objects.filter(
    #         id__in=UserCropPlan.objects.filter(zone_id=zone_id).values_list('crop_id', flat=True)
    #     ).distinct()
    #
    #     serializer = CropSerializer(crops, many=True)
    #     return Response(serializer.data, status=status.HTTP_200_OK)




class UserCropPlanAPIView(APIView):
    permission_classes = []  # Add IsAuthenticated if needed

    def get(self, request):
        plans = UserCropPlan.objects.filter(user=request.user)
        serializer = UserCropPlanSerializer(plans, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserCropPlanSerializer(data=request.data)
        if serializer.is_valid():
            # reset_cropplanrow_id()
            user_crop_plan = serializer.save()
            user_crop_plan.plan_rows.all().delete()


            # Read Excel and create CropPlanRow
            if user_crop_plan.crop_plan:
                df = pd.read_excel(user_crop_plan.crop_plan)

                # Normalize column names (strip spaces + lowercase)
                df.columns = [col.strip().lower() for col in df.columns]

                for _, row in df.iterrows():
                    # ✅ Extract day number from 'Day 1', 'day-12', etc.
                    day_value = row.get('day')
                    if isinstance(day_value, str):
                        match = re.search(r'\d+', day_value)
                        day_number = int(match.group()) if match else 0
                    else:
                        day_number = int(day_value) if pd.notna(day_value) else 0

                    # ✅ Create CropPlanRow
                    CropPlanRow.objects.create(
                        user_crop_plan=user_crop_plan,
                        date=row.get('date') or user_crop_plan.start_date,
                        day=day_number,
                        stage=row.get('stage') or "",
                        action=row.get('action') or "",

                    )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserCropPlanDeleteAPIView(APIView):
    permission_classes = []  # Add IsAuthenticated if needed

    def delete(self, request, pk):
        try:
            plan = UserCropPlan.objects.get(pk=pk, user=request.user)
        except UserCropPlan.DoesNotExist:
            return Response({"error": "Crop plan not found"}, status=status.HTTP_404_NOT_FOUND)

        plan.delete()
        return Response({"message": "Crop plan deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class CropPlanRowListCreateView(generics.ListCreateAPIView):
    serializer_class = CropPlanRowSerializer
    permission_classes = [permissions.IsAuthenticated]  # Require any token

    def get_queryset(self):
        user_crop_plan_id = self.request.query_params.get('user_crop_plan_id')

        if user_crop_plan_id:
            # ✅ Return all rows for this crop plan ID (no user check)
            return CropPlanRow.objects.filter(user_crop_plan_id=user_crop_plan_id)
        return CropPlanRow.objects.none()

    def perform_create(self, serializer):
        # ✅ Save without checking who owns the plan
        serializer.save()

class CropPlanRowFlexibleUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user_crop_plan_id = request.query_params.get('user_crop_plan_id')
        row_id = request.query_params.get('row_id')
        row_number = request.query_params.get('row_number')
        date = request.query_params.get('date')
        day = request.query_params.get('day')

        if not user_crop_plan_id:
            return Response({"error": "user_crop_plan_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        row = None

        try:
            if row_id:
                # Lookup by primary key
                row = CropPlanRow.objects.get(
                    id=row_id,
                    user_crop_plan__id=user_crop_plan_id
                )
            elif row_number:
                # Lookup by row_number (1-based index within that plan)
                rows = CropPlanRow.objects.filter(
                    user_crop_plan_id=user_crop_plan_id
                ).order_by('id')  # Make sure ordering is consistent
                row_index = int(row_number) - 1  # Convert to 0-based index
                if row_index < 0 or row_index >= rows.count():
                    return Response({"error": "Invalid row_number."}, status=status.HTTP_404_NOT_FOUND)
                row = rows[row_index]
            elif date:
                # Lookup by date
                row = CropPlanRow.objects.get(
                    date=date,
                    user_crop_plan__id=user_crop_plan_id
                )
            elif day:
                # Lookup by day
                row = CropPlanRow.objects.get(
                    day=day,
                    user_crop_plan__id=user_crop_plan_id
                )
            else:
                return Response({"error": "Provide either row_id, row_number, date, or day."},
                                status=status.HTTP_400_BAD_REQUEST)

        except CropPlanRow.DoesNotExist:
            return Response({"error": "CropPlanRow not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid row_number format."}, status=status.HTTP_400_BAD_REQUEST)

        # Partial update of the row
        serializer = CropPlanRowSerializer(row, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class CropPlanRowFlexibleUpdateView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def patch(self, request, *args, **kwargs):
#         user_crop_plan_id = request.query_params.get('user_crop_plan_id')
#         row_id = request.query_params.get('row_id')
#         date = request.query_params.get('date')
#         day = request.query_params.get('day')
#
#         if not user_crop_plan_id:
#             return Response({"error": "user_crop_plan_id is required."}, status=status.HTTP_400_BAD_REQUEST)
#
#         row = None
#
#         try:
#             if row_id:
#                 row = CropPlanRow.objects.get(
#                     id=row_id,
#                     user_crop_plan__id=user_crop_plan_id
#                 )
#             elif date:
#                 row = CropPlanRow.objects.get(
#                     date=date,
#                     user_crop_plan__id=user_crop_plan_id
#                 )
#             elif day:
#                 row = CropPlanRow.objects.get(
#                     day=day,
#                     user_crop_plan__id=user_crop_plan_id
#                 )
#             else:
#                 return Response({"error": "Provide either row_id, date, or day."}, status=status.HTTP_400_BAD_REQUEST)
#
#         except CropPlanRow.DoesNotExist:
#             return Response({"error": "CropPlanRow not found."}, status=status.HTTP_404_NOT_FOUND)
#
#         # Update the row
#         serializer = CropPlanRowSerializer(row, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# crops/views.py
import os
import requests
import base64
from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from crops.models import CropPlanRow
from sarvamai import SarvamAI

# ---------------- Configuration ----------------
SARVAM_API_KEY = "sk_y1xdysnp_6uaVU3nUlJmR9Vy6l3YjwOtB"
PHONE_NUMBER_ID = "758493914016711"
WHATSAPP_TOKEN = "EAATEOp0sFpABPQ8ZBPKJsgNvnqqJZBEiQvNTflS2eUy4RWOR1zz71ftNAVY4dltGy8HXkhZB8Pc9MFBGksNlXjNeNsuv1WXrZBKd8yzzx9T0AiVBuj3QZAXKo39n3y0CP4ZAlNwn6kfeBkndukKAvoW2ePzKbnqXhBOHtqYpcUo2iw4xIZARtGZB6pQ61EfgDq8yV6rnrtZAbaqOIiKmW533PKHz6KWqwyfV6eXHeugMqxWjZBywZDZD"
TTS_SPEAKER = "manisha"
OUTPUT_FILE = "voice.mp3"
TARGET_LANG = "ml-IN"

# Initialize SarvamAI Client
sarvamclient = SarvamAI(api_subscription_key=SARVAM_API_KEY)


# -------- Helper Functions --------
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


def whatsapp_upload_media(file_path):
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


# ---------------- Class-Based View ----------------
class SendCropPlanActionView(APIView):
    """
    API view to send today's CropPlanRow action as WhatsApp audio.
    """

    def post(self, request):
        recipient = request.data.get("recipient")
        if not recipient:
            return Response({"error": "Recipient is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            today = date.today()
            row = CropPlanRow.objects.filter(date=today).first()
            if not row or not row.action:
                return Response({"error": "No action found for today"}, status=status.HTTP_404_NOT_FOUND)

            input_text = row.action

            # 1️⃣ Translate
            translated_text = translate_text(input_text)

            # 2️⃣ Generate TTS
            text_to_speech(translated_text, OUTPUT_FILE)

            # 3️⃣ Upload Media
            media_id = whatsapp_upload_media(OUTPUT_FILE)

            # 4️⃣ Send Audio via WhatsApp
            message_id = whatsapp_send_audio(recipient, media_id)

            return Response({
                "message": "WhatsApp Audio Message Sent!",
                "message_id": message_id,
                "translated_text": translated_text
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
