import re, json

from rest_framework.response import Response
from rest_framework import status


from .models import Nudges
from .serializer import *
from crops.models import CropPlanRow

from .utils import transcribe_audio_with_sarvam  # your audio transcription util
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Nudges
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Phase, SubPhase, NudgesPhase
from .serializer import PhaseSerializer, NudgesPhaseSerializer

from rest_framework.views import APIView

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from .models import NudgesMachine
from .serializer import NudgesMachineSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from .models import NudgesInput
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import NudgesPhase, Phase, SubPhase
from .serializer import NudgesPhaseSerializer
from crops.models import CropPlanRow  # adjust import if your app layout differs



#################Labour voice#######################
def default_labour_details():
    return {
        "male_labour_cost": 0.0,
        "male_labour_count": 0,
        "female_labour_cost": 0.0,
        "female_labour_count": 0,
        "is_read": False
    }

# Transliteration map
TRANSLITERATION_MAP = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "വൺ": "1", "ടു": "2", "ത്രീ": "3", "ഫോർ": "4", "ഫൈവ്": "5",
    "സിക്സ്": "6", "സെവൻ": "7", "എയിറ്റ്": "8", "നയൺ": "9", "ടെൻ": "10",
    "ஒன்று": "1", "ரண்டு": "2", "மூன்று": "3", "நான்கு": "4", "ஐந்து": "5",
    "ஆறு": "6", "ஏழு": "7", "எட்டு": "8", "ஒன்பது": "9", "பத்து": "10"
}

# Convert string/word to number
def _to_number(val: str) -> float:
    val = val.strip().replace(',', '')
    if not val:
        return 0.0
    if val in TRANSLITERATION_MAP:
        val = TRANSLITERATION_MAP[val]
    try:
        return float(val)
    except ValueError:
        try:
            from word2number import w2n
            return float(w2n.word_to_num(val))
        except Exception:
            return 0.0

# Parse labour details
def parse_labour_details_from_text(text: str) -> dict:
    parsed_data = default_labour_details()
    text = text.replace('.', '').replace('-', ' ').strip()
    print("DEBUG: Transcribed text =>", text)

    # Regex matches all occurrences
    male_cost_matches = re.findall(r"(?:male|മെയിൽ|மேல்)\s*(?:labour|ലേബർ|തൊഴിലாளர்)\s*(?:cost|കോസ്റ്റ്|சിലவு|ചെലവ്)\s*(?:is|:)?\s*([^\s,]+)", text)
    male_count_matches = re.findall(r"(?:male|മെയിൽ|மேல்)\s*(?:labour|ലേബർ|തൊഴിലാളി|workers?)\s*(?:count|നമ്പർ|எண்ணிக்கை|കൗണ്ട്)\s*(?:is|:)?\s*([^\s,]+)", text)
    female_cost_matches = re.findall(r"(?:female|ഫീമെയിൽ|ஃபீமேல்)\s*(?:labour|ലേബർ|തൊഴിലாளர்)\s*(?:cost|കോസ്റ്റ്|சിലவு|ചെലവ്)\s*(?:is|:)?\s*([^\s,]+)", text)
    female_count_matches = re.findall(r"(?:female|ഫീമെയിൽ|ஃபீமேல்)\s*(?:labour|ലേബർ|തൊഴിലാളി|workers?)\s*(?:count|നമ്പർ|எண்ணிக்கை|കൗണ്ട്)\s*(?:is|:)?\s*([^\s,]+)", text)

    # Take the first occurrence (avoids overwriting male/female)
    if male_cost_matches:
        parsed_data["male_labour_cost"] = _to_number(male_cost_matches[0])
    if male_count_matches:
        parsed_data["male_labour_count"] = _to_number(male_count_matches[0])
    if female_cost_matches:
        parsed_data["female_labour_cost"] = _to_number(female_cost_matches[0])
    if female_count_matches:
        parsed_data["female_labour_count"] = _to_number(female_count_matches[0])

    parsed_data["is_read"] = any(
        v > 0 for k, v in parsed_data.items() if "cost" in k or "count" in k
    )

    print("DEBUG: Final parsed data =>", parsed_data)
    return parsed_data

# ======================
# Voice-based API View
# ======================
class NudgesLaborVoiceView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _process_voice_input(self, request):
        audio_file = request.FILES.get("audio_file")
        if not audio_file:
            sample_text = "male labour cost 4000, male labour count 5, female labour cost 3000, female labour count 4"
            return parse_labour_details_from_text(sample_text)

        audio_data = audio_file.read()
        transcription_result = transcribe_audio_with_sarvam(audio_data)
        if "error" in transcription_result:
            return transcription_result

        transcribed_text = transcription_result.get("transcription") or transcription_result.get("text", "")
        return parse_labour_details_from_text(transcribed_text)

    def _get_crop_plan_row(self, user, row_number, zone_id, crop_id):
        try:
            row_index = int(row_number) - 1
            crop_plan_rows = CropPlanRow.objects.filter(
                user_crop_plan__zone_id=zone_id,
                user_crop_plan__crop_id=crop_id,
                user_crop_plan__user=user
            ).order_by("id")
            return crop_plan_rows[row_index]
        except Exception:
            return None

    def post(self, request):
        voice_data = self._process_voice_input(request)
        if "error" in voice_data:
            return Response({"error": voice_data["error"]}, status=500)

        row_number = request.data.get("row_number")
        zone_id = request.data.get("zone")
        crop_id = request.data.get("crop")

        if not (row_number and zone_id and crop_id):
            return Response({"error": "row_number, zone, and crop are required"}, status=400)

        crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
        if not crop_plan_row:
            return Response({"error": "Invalid crop plan row"}, status=400)

        data = {
            "user": request.user.id,
            "crop_plan_row": crop_plan_row.id,
            "zone": zone_id,
            "crop": crop_id,
            "male_labour_cost": voice_data["male_labour_cost"],
            "male_labour_count": voice_data["male_labour_count"],
            "female_labour_cost": voice_data["female_labour_cost"],
            "female_labour_count": voice_data["female_labour_count"],
        }

        serializer = NudgesSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user, crop_plan_row=crop_plan_row)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("DEBUG: Serializer errors =>", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#################Machine voice#############################


def default_machine_details():
    return {
        "machine_count": 0,
        "working_hours": 0.0,
        "rate_per_hour": 0.0,
        "is_read": False
    }

# Transliteration map for numbers (same as your labour map)
TRANSLITERATION_MAP = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "വൺ": "1", "ടു": "2", "ത്രി": "3", "ത്രീ":"3","ഫോർ": "4", "ഫൈവ്": "5",
    "സിക്സ്": "6", "സെവൻ": "7", "എയിറ്റ്": "8", "നൈന": "9", "ടെൻ": "10",
    "ஒன்று": "1", "ரண்டு": "2", "மூன்று": "3", "நான்கு": "4", "ஐந்து": "5",
    "ஆறு": "6", "ஏழு": "7", "எட்டு": "8", "ஒன்பது": "9", "பத்து": "10"
}


def _to_number(val: str) -> float:
    val = val.strip().replace(',', '')
    if not val:
        return 0.0
    if val in TRANSLITERATION_MAP:
        val = TRANSLITERATION_MAP[val]
    try:
        return float(val)
    except ValueError:
        try:
            from word2number import w2n
            return float(w2n.word_to_num(val))
        except Exception:
            return 0.0

def parse_machine_details_from_text(text: str) -> dict:
    parsed_data = default_machine_details()
    text = text.replace('.', '').replace('-', ' ').strip()
    print("DEBUG: Transcribed text =>", text)

    machine_count_matches = re.findall(
        r"(?:machine|മഷീൻ|മഷീന്|മെഷീൻ)\s*(?:count|നമ്പർ|എണ്ണிக்கை|കൗണ്ട്)\s*(?:is|:)?\s*([\w\-\u0D00-\u0D7F]+)",
        text
    )

    working_hours_matches = re.findall(
        r"(?:working|വർക്കിംഗ്|വർക്കിംഗ്)\s*(?:hours|അവേഴ്സ്|മണി|ഘണ്ട്)\s*(?:is|:)?\s*([^\s,]+)", text)

    rate_matches = re.findall(
        r"(?:rate|റേറ്റ്|റൈറ്റ്|ரேட்)\s*(?:per hour|പ്രതി മണിക്കൂർ|പെർ അവർ|ஒரு மணி நேரத்திற்கு)\s*(?:is|:)?\s*([^\s,]+)",
        text
    )

    if machine_count_matches:
        parsed_data["machine_count"] = int(_to_number(machine_count_matches[0]))
    if working_hours_matches:
        parsed_data["working_hours"] = _to_number(working_hours_matches[0])
    if rate_matches:
        parsed_data["rate_per_hour"] = _to_number(rate_matches[0])

    parsed_data["is_read"] = any(v > 0 for k, v in parsed_data.items() if k in ["machine_count", "working_hours", "rate_per_hour"])
    print("DEBUG: Final parsed data =>", parsed_data)
    return parsed_data

# ======================
# Voice-based API View for NudgesMachine
# ======================
class NudgesMachineVoiceView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _process_voice_input(self, request):
        audio_file = request.FILES.get("audio_file")
        if not audio_file:
            sample_text = "machine count 3, working hours 10, rate per hour 500"
            return parse_machine_details_from_text(sample_text)

        audio_data = audio_file.read()
        transcription_result = transcribe_audio_with_sarvam(audio_data)
        if "error" in transcription_result:
            return transcription_result

        transcribed_text = transcription_result.get("transcription") or transcription_result.get("text", "")
        return parse_machine_details_from_text(transcribed_text)

    def _get_crop_plan_row(self, user, row_number, zone_id, crop_id):
        try:
            row_index = int(row_number) - 1
            crop_plan_rows = CropPlanRow.objects.filter(
                user_crop_plan__zone_id=zone_id,
                user_crop_plan__crop_id=crop_id,
                user_crop_plan__user=user
            ).order_by("id")
            return crop_plan_rows[row_index]
        except Exception:
            return None

    def post(self, request):
        machine_data = self._process_voice_input(request)
        if "error" in machine_data:
            return Response({"error": machine_data["error"]}, status=500)

        row_number = request.data.get("row_number")
        zone_id = request.data.get("zone")
        crop_id = request.data.get("crop")

        if not (row_number and zone_id and crop_id):
            return Response({"error": "row_number, zone, and crop are required"}, status=400)

        crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
        if not crop_plan_row:
            return Response({"error": "Invalid crop plan row"}, status=400)

        data = {
            "user": request.user.id,
            "crop_plan_row": crop_plan_row.id,
            "zone": zone_id,
            "crop": crop_id,
            "machine_count": machine_data["machine_count"],
            "working_hours": machine_data["working_hours"],
            "rate_per_hour": machine_data["rate_per_hour"],
        }

        serializer = NudgesMachineSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user, crop_plan_row=crop_plan_row)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("DEBUG: Serializer errors =>", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
########Input Voice#######




# Default values
def default_input_details():
    return {
        "input_quantity": 0.0,
        "input_cost": 0.0,
        "is_read": False
    }

# Transliteration map (same as machine/labour)
TRANSLITERATION_MAP = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "വൺ": "1", "ടു": "2", "ത്രി": "3", "ത്രീ": "3", "ഫോർ": "4", "ഫൈവ്": "5",
    "സിക്സ്": "6", "സെവൻ": "7", "എയിറ്റ്": "8", "നൈന": "9", "ടെൻ": "10",
    "ஒன்று": "1", "ரண்டு": "2", "மூன்று": "3", "நான்கு": "4", "ஐந்து": "5",
    "ஆறு": "6", "ஏழு": "7", "எட்டு": "8", "ஒன்பது": "9", "பத்து": "10", "த்ரீ": "3",
}

def _to_number(val: str) -> float:
    val = val.strip().replace(',', '')
    if not val:
        return 0.0
    if val in TRANSLITERATION_MAP:
        val = TRANSLITERATION_MAP[val]
    try:
        return float(val)
    except ValueError:
        try:
            from word2number import w2n
            return float(w2n.word_to_num(val))
        except Exception:
            return 0.0

# Parse input details from text
def parse_input_details_from_text(text: str) -> dict:
    parsed_data = default_input_details()
    text = re.sub(r'\s+', ' ', text.replace('.', '').replace('-', ' ')).strip()
    print("DEBUG: Transcribed text =>", text)

    quantity_matches = re.findall(
        r"(?:input|ഇൻപുട്ട്|இன்புட്)?\s*(?:quantity|മാത്രാ|அളവ്|குவாண்டிட்டி)\s*(?:is|:)?\s*([\w\-\u0D00-\u0D7F\u0B80-\u0BFF]+)",
        text
    )

    cost_matches = re.findall(
        r"(?:input|ഇൻപുട്ട്|இன்புட்)?\s*(?:cost|ചെലവ്|കോസ്റ്റ്|காஸ்ட்)\s*(?:is|:)?\s*([\w\-\u0D00-\u0D7F]+)",
        text
    )

    if quantity_matches:
        parsed_data["input_quantity"] = _to_number(quantity_matches[0])
    if cost_matches:
        parsed_data["input_cost"] = _to_number(cost_matches[0])

    parsed_data["is_read"] = any(
        v > 0 for k, v in parsed_data.items() if k in ["input_quantity", "input_cost"]
    )
    print("DEBUG: Final parsed data =>", parsed_data)
    return parsed_data

# ======================
# Voice-based API View for NudgesInput
# ======================
class NudgesInputVoiceView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _process_voice_input(self, request):
        audio_file = request.FILES.get("audio_file")
        if not audio_file:
            sample_text = "input quantity 10, input cost 500"
            return parse_input_details_from_text(sample_text)

        audio_data = audio_file.read()
        transcription_result = transcribe_audio_with_sarvam(audio_data)
        if "error" in transcription_result:
            return transcription_result

        transcribed_text = transcription_result.get("transcription") or transcription_result.get("text", "")
        return parse_input_details_from_text(transcribed_text)

    def _get_crop_plan_row(self, user, row_number, zone_id, crop_id):
        try:
            row_index = int(row_number) - 1
            crop_plan_rows = CropPlanRow.objects.filter(
                user_crop_plan__zone_id=zone_id,
                user_crop_plan__crop_id=crop_id,
                user_crop_plan__user=user
            ).order_by("id")
            return crop_plan_rows[row_index]
        except Exception:
            return None

    def post(self, request):
        input_data = self._process_voice_input(request)
        if "error" in input_data:
            return Response({"error": input_data["error"]}, status=500)

        row_number = request.data.get("row_number")
        zone_id = request.data.get("zone")
        crop_id = request.data.get("crop")

        if not (row_number and zone_id and crop_id):
            return Response({"error": "row_number, zone, and crop are required"}, status=400)

        crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
        if not crop_plan_row:
            return Response({"error": "Invalid crop plan row"}, status=400)

        data = {
            "user": request.user.id,
            "crop_plan_row": crop_plan_row.id,
            "zone": zone_id,
            "crop": crop_id,
            "input_quantity": input_data["input_quantity"],
            "input_cost": input_data["input_cost"],
        }

        serializer = NudgesInputSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user, crop_plan_row=crop_plan_row)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("DEBUG: Serializer errors =>", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




#############labour text###################

class NudgesView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_crop_plan_row(self, user, zone_id, crop_id, row_number):
        """Helper to safely get crop_plan_row by row_number"""
        try:
            row_index = int(row_number) - 1
        except ValueError:
            return None, 'row_number must be an integer'

        crop_plan_rows = CropPlanRow.objects.filter(
            user_crop_plan__zone_id=zone_id,
            user_crop_plan__crop_id=crop_id,
            user_crop_plan__user=user
        ).order_by('id')

        if not crop_plan_rows.exists():
            return None, 'No matching crop plan rows found'

        if row_index < 0 or row_index >= crop_plan_rows.count():
            return None, 'row_number out of range'

        return crop_plan_rows[row_index], None

    def post(self, request):
        data = request.data.copy()
        row_number = data.get('row_number')
        zone_id = data.get('zone')
        crop_id = data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=400)

        # Get the crop_plan_row safely
        try:
            row_index = int(row_number) - 1
            crop_plan_rows = CropPlanRow.objects.filter(
                user_crop_plan__zone_id=zone_id,
                user_crop_plan__crop_id=crop_id,
                user_crop_plan__user=request.user
            ).order_by('id')

            if not crop_plan_rows.exists():
                return Response({'error': 'No matching crop plan rows found'}, status=400)

            if row_index < 0 or row_index >= crop_plan_rows.count():
                return Response({'error': 'row_number out of range'}, status=400)

            crop_plan_row = crop_plan_rows[row_index]
        except ValueError:
            return Response({'error': 'row_number must be an integer'}, status=400)

        # Ensure crop_plan_row is passed to serializer
        serializer = NudgesSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user, crop_plan_row=crop_plan_row)  # ✅ pass object directly
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        data = request.data.copy()
        row_number = data.get('row_number')
        zone_id = data.get('zone')
        crop_id = data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=400)

        crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
        if error:
            return Response({'error': error}, status=400)

        try:
            nudges = Nudges.objects.get(crop_plan_row=crop_plan_row, user=request.user)
        except Nudges.DoesNotExist:
            return Response({'error': 'Nudges object not found for this crop_plan_row'}, status=404)

        serializer = NudgesSerializer(nudges, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        row_number = request.query_params.get('row_number')
        zone_id = request.query_params.get('zone')
        crop_id = request.query_params.get('crop')

        if row_number and zone_id and crop_id:
            crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
            if error:
                return Response({'error': error}, status=404)

            try:
                nudges = Nudges.objects.get(crop_plan_row=crop_plan_row, user=request.user)
                serializer = NudgesSerializer(nudges)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Nudges.DoesNotExist:
                return Response({'error': 'Nudges object not found for this row_number'}, status=404)

        # Return all nudges for the logged-in user
        nudges = Nudges.objects.filter(user=request.user)
        serializer = NudgesSerializer(nudges, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NudgesMachineView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_crop_plan_row(self, user, zone_id, crop_id, row_number):
        """Helper to safely get crop_plan_row by row_number"""
        try:
            row_index = int(row_number) - 1
        except ValueError:
            return None, 'row_number must be an integer'

        crop_plan_rows = CropPlanRow.objects.filter(
            user_crop_plan__zone_id=zone_id,
            user_crop_plan__crop_id=crop_id,
            user_crop_plan__user=user
        ).order_by('id')

        if not crop_plan_rows.exists():
            return None, 'No matching crop plan rows found'

        if row_index < 0 or row_index >= crop_plan_rows.count():
            return None, 'row_number out of range'

        return crop_plan_rows[row_index], None

    def _add_row_number_to_response(self, user, zone_id, crop_id, instance_data):
        """Replace crop_plan_row with row_number in response"""
        crop_plan_row_id = instance_data.get('crop_plan_row')
        if not crop_plan_row_id:
            return instance_data

        crop_plan_rows = CropPlanRow.objects.filter(
            user_crop_plan__zone_id=zone_id,
            user_crop_plan__crop_id=crop_id,
            user_crop_plan__user=user
        ).order_by('id')

        for idx, row in enumerate(crop_plan_rows, start=1):
            if row.id == crop_plan_row_id:
                instance_data['row_number'] = idx
                break

        # Remove crop_plan_row to match your request
        instance_data.pop('crop_plan_row', None)
        return instance_data

    def post(self, request):
        """Create a new NudgesMachine entry"""
        data = request.data.copy()
        row_number = data.get('row_number')
        zone_id = data.get('zone')
        crop_id = data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=400)

        crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
        if error:
            return Response({'error': error}, status=400)

        serializer = NudgesMachineSerializer(data=data)
        if serializer.is_valid():
            instance = serializer.save(user=request.user, crop_plan_row=crop_plan_row)
            response_data = self._add_row_number_to_response(request.user, zone_id, crop_id, serializer.data)
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """Partially update an existing NudgesMachine record"""
        data = request.data.copy()
        row_number = data.get('row_number')
        zone_id = data.get('zone')
        crop_id = data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=400)

        crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
        if error:
            return Response({'error': error}, status=400)

        try:
            nudges_machine = NudgesMachine.objects.get(crop_plan_row=crop_plan_row, user=request.user)
        except NudgesMachine.DoesNotExist:
            return Response({'error': 'NudgesMachine object not found for this crop_plan_row'}, status=404)

        serializer = NudgesMachineSerializer(nudges_machine, data=data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            response_data = self._add_row_number_to_response(request.user, zone_id, crop_id, serializer.data)
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """Retrieve either one or all NudgesMachine records"""
        row_number = request.query_params.get('row_number')
        zone_id = request.query_params.get('zone')
        crop_id = request.query_params.get('crop')

        if row_number and zone_id and crop_id:
            crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
            if error:
                return Response({'error': error}, status=404)

            try:
                nudges_machine = NudgesMachine.objects.get(crop_plan_row=crop_plan_row, user=request.user)
                serializer = NudgesMachineSerializer(nudges_machine)
                response_data = self._add_row_number_to_response(request.user, zone_id, crop_id, serializer.data)
                return Response(response_data, status=status.HTTP_200_OK)
            except NudgesMachine.DoesNotExist:
                return Response({'error': 'NudgesMachine object not found for this row_number'}, status=404)

        # Return all entries for the logged-in user
        nudges_machine = NudgesMachine.objects.filter(user=request.user)
        serializer = NudgesMachineSerializer(nudges_machine, many=True)

        response_list = [
            self._add_row_number_to_response(request.user, obj.zone_id, obj.crop_id, data)
            for obj, data in zip(nudges_machine, serializer.data)
        ]
        return Response(response_list, status=status.HTTP_200_OK)
class NudgesInputView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_crop_plan_row(self, user, zone_id, crop_id, row_number):
        """Helper to safely get crop_plan_row by row_number"""
        try:
            row_index = int(row_number) - 1
        except ValueError:
            return None, 'row_number must be an integer'

        crop_plan_rows = CropPlanRow.objects.filter(
            user_crop_plan__zone_id=zone_id,
            user_crop_plan__crop_id=crop_id,
            user_crop_plan__user=user
        ).order_by('id')

        if not crop_plan_rows.exists():
            return None, 'No matching crop plan rows found'

        if row_index < 0 or row_index >= crop_plan_rows.count():
            return None, 'row_number out of range'

        return crop_plan_rows[row_index], None

    def post(self, request):
        """Create a new NudgesInput entry"""
        data = request.data.copy()
        row_number = data.get('row_number')
        zone_id = data.get('zone')
        crop_id = data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=400)

        crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
        if error:
            return Response({'error': error}, status=400)

        serializer = NudgesInputSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user, crop_plan_row=crop_plan_row)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """Partially update an existing NudgesInput record"""
        data = request.data.copy()
        row_number = data.get('row_number')
        zone_id = data.get('zone')
        crop_id = data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=400)

        crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
        if error:
            return Response({'error': error}, status=400)

        try:
            nudges_input = NudgesInput.objects.get(crop_plan_row=crop_plan_row, user=request.user)
        except NudgesInput.DoesNotExist:
            return Response({'error': 'NudgesInput object not found for this crop_plan_row'}, status=404)

        serializer = NudgesInputSerializer(nudges_input, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """Retrieve either one or all NudgesInput records"""
        row_number = request.query_params.get('row_number')
        zone_id = request.query_params.get('zone')
        crop_id = request.query_params.get('crop')

        if row_number and zone_id and crop_id:
            crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
            if error:
                return Response({'error': error}, status=404)

            try:
                nudges_input = NudgesInput.objects.get(crop_plan_row=crop_plan_row, user=request.user)
                serializer = NudgesInputSerializer(nudges_input)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except NudgesInput.DoesNotExist:
                return Response({'error': 'NudgesInput object not found for this row_number'}, status=404)

        # Return all entries for the logged-in user
        nudges_input = NudgesInput.objects.filter(user=request.user)
        serializer = NudgesInputSerializer(nudges_input, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
####################


#
# class PhaseListAPIView(APIView):
#     """
#     Returns list of all phases and their subphases
#     """
#     permission_classes = [permissions.AllowAny]
#
#     def get(self, request):
#         phases = Phase.objects.prefetch_related('subphases').all()
#         serializer = PhaseSerializer(phases, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

class PhaseListAPIView(APIView):
    """
    Returns list of all phases and their subphases.
    If ?phase=<id> is provided, returns only that phase and its subphases.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        phase_id = request.query_params.get('phase')

        if phase_id:
            try:
                phase = Phase.objects.prefetch_related('subphases').get(id=phase_id)
            except Phase.DoesNotExist:
                return Response({'error': 'Phase not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = PhaseSerializer(phase)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # If no param, return all
        phases = Phase.objects.prefetch_related('subphases').all()
        serializer = PhaseSerializer(phases, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#################phase########################
class NudgesPhaseAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_crop_plan_row(self, user, zone_id, crop_id, row_number):
        """Helper to safely get crop_plan_row by row_number (reuse from NudgesInputView)"""
        try:
            row_index = int(row_number) - 1
        except (TypeError, ValueError):
            return None, 'row_number must be an integer'

        crop_plan_rows = CropPlanRow.objects.filter(
            user_crop_plan__zone_id=zone_id,
            user_crop_plan__crop_id=crop_id,
            user_crop_plan__user=user
        ).order_by('id')

        if not crop_plan_rows.exists():
            return None, 'No matching crop plan rows found'

        if row_index < 0 or row_index >= crop_plan_rows.count():
            return None, 'row_number out of range'

        return crop_plan_rows[row_index], None

    def get(self, request):
        """
        Retrieve one or all NudgesPhase records.
        To get a specific record by row use ?row_number=X&zone=Y&crop=Z
        """
        row_number = request.query_params.get('row_number')
        zone_id = request.query_params.get('zone')
        crop_id = request.query_params.get('crop')

        if row_number and zone_id and crop_id:
            crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
            if error:
                return Response({'error': error}, status=status.HTTP_404_NOT_FOUND)

            nudges_phases = NudgesPhase.objects.filter(user=request.user, crop_plan_row=crop_plan_row)
            serializer = NudgesPhaseSerializer(nudges_phases, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # No filter -> return all for user
        nudges_phases = NudgesPhase.objects.filter(user=request.user)
        serializer = NudgesPhaseSerializer(nudges_phases, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new NudgesPhase record by resolving crop_plan_row from row_number, zone, crop.
        Allows multiple phases for the same row.
        """
        data = request.data.copy()
        row_number = data.get('row_number')
        zone_id = data.get('zone')
        crop_id = data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=status.HTTP_400_BAD_REQUEST)

        crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = NudgesPhaseSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user, crop_plan_row=crop_plan_row)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """
        Partially update an existing NudgesPhase record by resolving crop_plan_row.
        """
        data = request.data.copy()
        row_number = data.get('row_number')
        zone_id = data.get('zone')
        crop_id = data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=status.HTTP_400_BAD_REQUEST)

        crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        try:
            nudges_phase = NudgesPhase.objects.get(user=request.user, crop_plan_row=crop_plan_row)
        except NudgesPhase.DoesNotExist:
            return Response({'error': 'NudgesPhase not found for this row_number'}, status=status.HTTP_404_NOT_FOUND)

        serializer = NudgesPhaseSerializer(nudges_phase, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class NudgesPhaseSummaryAPIView(APIView):
    """
    Get all Nudges, Machines, and Inputs for a given zone, phase,
    and optionally a specific row_number.
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_crop_plan_row(self, user, zone_id, crop_id, row_number):
        """Helper method to get CropPlanRow by row_number"""
        try:
            row_index = int(row_number) - 1
        except ValueError:
            return None, 'row_number must be an integer'

        crop_plan_rows = CropPlanRow.objects.filter(
            user_crop_plan__zone_id=zone_id,
            user_crop_plan__crop_id=crop_id,
            user_crop_plan__user=user
        ).order_by('id')

        if not crop_plan_rows.exists():
            return None, 'No matching crop plan rows found'

        if row_index < 0 or row_index >= crop_plan_rows.count():
            return None, 'row_number out of range'

        return crop_plan_rows[row_index], None

    def get(self, request):
        zone_id = request.query_params.get("zone")
        phase_id = request.query_params.get("phase")
        row_number = request.query_params.get("row_number")
        crop_id = request.query_params.get("crop")

        if not zone_id or not phase_id:
            return Response(
                {"error": "Both 'zone' and 'phase' parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Base queryset of NudgesPhase
        nudges_phase_qs = NudgesPhase.objects.filter(
            user=request.user,
            zone_id=zone_id,
            phase_id=phase_id,
        )

        if not nudges_phase_qs.exists():
            return Response(
                {"message": "No records found for the given zone and phase."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # If row_number provided → narrow down to that row
        if row_number and crop_id:
            crop_plan_row, error = self._get_crop_plan_row(request.user, zone_id, crop_id, row_number)
            if error:
                return Response({'error': error}, status=400)

            nudges_phase_qs = nudges_phase_qs.filter(crop_plan_row=crop_plan_row)
            crop_plan_rows = [crop_plan_row.id]
        else:
            crop_plan_rows = list(nudges_phase_qs.values_list('crop_plan_row_id', flat=True))

        # Fetch related entries
        nudges = Nudges.objects.filter(
            user=request.user, zone_id=zone_id, crop_plan_row_id__in=crop_plan_rows
        )
        machines = NudgesMachine.objects.filter(
            user=request.user, zone_id=zone_id, crop_plan_row_id__in=crop_plan_rows
        )
        inputs = NudgesInput.objects.filter(
            user=request.user, zone_id=zone_id, crop_plan_row_id__in=crop_plan_rows
        )

        # Serialize
        nudges_data = NudgesSerializer(nudges, many=True).data
        machines_data = NudgesMachineSerializer(machines, many=True).data
        inputs_data = NudgesInputSerializer(inputs, many=True).data

        return Response(
            {
                "zone": zone_id,
                "phase": phase_id,
                "row_number": row_number if row_number else "all",
                "nudges": nudges_data,
                "machines": machines_data,
                "inputs": inputs_data,
            },
            status=status.HTTP_200_OK,
        )