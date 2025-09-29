from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from rest_framework.views import APIView

from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.http import JsonResponse



from rest_framework import status


from .serializers import NudgesSerializer

from django.utils import timezone





class NudgesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        row_number = data.get('row_number')
        zone_id = data.get('zone')
        crop_id = data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=400)

        try:
            row_index = int(row_number) - 1
            crop_plan_rows = CropPlanRow.objects.filter(
                user_crop_plan__zone_id=zone_id,
                user_crop_plan__crop_id=crop_id,
                user_crop_plan__user=request.user   # ✅ restrict to logged-in user
            ).order_by('id')
            crop_plan_row = crop_plan_rows[row_index]
            data['crop_plan_row'] = crop_plan_row.id
        except (IndexError, ValueError):
            return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)

        # Handle is_read flags
        for field in ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']:
            if field in data:
                value = data[field]
                if isinstance(value, dict) and "data" in value:
                    value["is_read"] = True
                else:
                    value = {"data": value, "is_read": True}
                data[field] = value

        serializer = NudgesSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        data = request.data.copy()
        row_number = data.get('row_number')
        zone_id = data.get('zone')
        crop_id = data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=400)

        # ✅ find crop_plan_row scoped to the logged-in user
        try:
            row_index = int(row_number) - 1
            crop_plan_rows = CropPlanRow.objects.filter(
                user_crop_plan__zone_id=zone_id,
                user_crop_plan__crop_id=crop_id,
                user_crop_plan__user=request.user   # ✅ user-specific filter
            ).order_by('id')
            crop_plan_row = crop_plan_rows[row_index]
        except (IndexError, ValueError):
            return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)

        # fetch existing nudges record
        try:
            budgeting = Nudges.objects.get(crop_plan_row=crop_plan_row, user=request.user)
        except Nudges.DoesNotExist:
            return Response({'error': 'Nudges object not found for this crop_plan_row'}, status=404)

        # Handle is_read flags
        for field in ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']:
            if field in data:
                value = data[field]
                if isinstance(value, dict) and "data" in value:
                    value["is_read"] = True
                else:
                    value = {"data": value, "is_read": True}
                data[field] = value

        serializer = NudgesSerializer(budgeting, data=data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        crop_plan_row_id = request.query_params.get('crop_plan_row')

        if crop_plan_row_id:
            try:
                budget = Nudges.objects.get(
                    crop_plan_row=crop_plan_row_id,
                    user=request.user   # ✅ ensure only own data
                )
            except Nudges.DoesNotExist:
                return Response({'error': 'Nudges object not found for this crop_plan_row'}, status=404)
            serializer = NudgesSerializer(budget, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        # If no crop_plan_row provided, return all budgets for the user
        budgets = Nudges.objects.filter(user=request.user)
        serializer = NudgesSerializer(budgets, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)



class NudgesViewSupervisor(APIView):
    permission_classes = [IsAuthenticated]

    # def calculate_summary(self, budgets):
    #     total_labour_cost = Decimal(0)
    #     total_machine_cost = Decimal(0)
    #     total_input_cost = Decimal(0)
    #     total_miscellaneous = Decimal(0)
    #
    #     for budget in budgets:
    #
    #         # ✅ Labour cost
    #         try:
    #             labour = budget.labour_estimation or {}
    #             male = Decimal(labour.get('male_labour_cost', 0)) * int(labour.get('male_labour_count', 0))
    #             female = Decimal(labour.get('female_labour_cost', 0)) * int(labour.get('female_labour_count', 0))
    #             total_labour_cost += male + female
    #         except Exception:
    #             pass
    #
    #         # ✅ Machine cost (loop through list)
    #         try:
    #             machine_data = budget.machine_estimation or {}
    #             for m in machine_data.get("machines", []):
    #                 mc = Decimal(m.get("machine_count", 0))
    #                 hrs = Decimal(m.get("working_hours", 0))
    #                 rate = Decimal(m.get("rate_per_hour", 0))
    #                 total_machine_cost += mc * hrs * rate
    #         except Exception:
    #             pass
    #
    #         # ✅ Input cost (loop through list)
    #         try:
    #             input_data = budget.input_estimation or {}
    #             for inp in input_data.get("inputs", []):
    #                 qty = Decimal(inp.get("quantity", 0))
    #                 cost = Decimal(inp.get("cost_per_unit", 0))
    #                 total_input_cost += qty * cost
    #         except Exception:
    #             pass
    #
    #
    #         # ✅ Miscellaneous
    #         try:
    #             total_miscellaneous += Decimal(budget.miscellaneous or 0)
    #         except Exception:
    #             pass
    #
    #     total = total_labour_cost + total_machine_cost + total_input_cost + total_miscellaneous
    #
    #     return {
    #         "total_labour_cost": str(total_labour_cost),
    #         "total_machine_cost": str(total_machine_cost),
    #         "total_input_cost": str(total_input_cost),
    #         "total_miscellaneous": str(total_miscellaneous),
    #         "total_budget_cost": str(total)
    #     }
    def calculate_summary(self, budgets):
        total_labour_cost = Decimal(0)
        total_machine_cost = Decimal(0)
        total_input_cost = Decimal(0)
        total_miscellaneous = Decimal(0)

        for budget in budgets:
            # ✅ Labour cost
            try:
                labour = (budget.labour_estimation or {}).get("data", {})
                male = Decimal(labour.get('male_labour_cost', 0)) * int(labour.get('male_labour_count', 0))
                female = Decimal(labour.get('female_labour_cost', 0)) * int(labour.get('female_labour_count', 0))
                total_labour_cost += male + female
            except Exception:
                pass

            # ✅ Machine cost
            try:
                machine_data = (budget.machine_estimation or {}).get("data", {})
                for m in machine_data.get("machines", []):
                    mc = Decimal(m.get("machine_count", 0))
                    hrs = Decimal(m.get("working_hours", 0))
                    rate = Decimal(m.get("rate_per_hour", 0))
                    total_machine_cost += mc * hrs * rate
            except Exception:
                pass

            # ✅ Input cost
            try:
                input_data = (budget.input_estimation or {}).get("data", {})
                for inp in input_data.get("inputs", []):
                    qty = Decimal(inp.get("quantity", 0))
                    cost = Decimal(inp.get("cost_per_unit", 0))
                    total_input_cost += qty * cost
            except Exception:
                pass

            # # ✅ Miscellaneous
            # try:
            #     total_miscellaneous += Decimal(budget.miscellaneous or 0)
            # except Exception:
            #     pass
            # ✅ Miscellaneous
            try:
                misc = (budget.miscellaneous or {}).get("data", 0)
                total_miscellaneous += Decimal(misc or 0)
            except Exception:
                pass

        total = total_labour_cost + total_machine_cost + total_input_cost + total_miscellaneous

        return {
            "total_labour_cost": str(total_labour_cost),
            "total_machine_cost": str(total_machine_cost),
            "total_input_cost": str(total_input_cost),
            "total_miscellaneous": str(total_miscellaneous),
            "total_budget_cost": str(total),
        }

    # def calculate_summary(self, budgets):
    #     total_labour_cost = Decimal(0)
    #     total_machine_cost = Decimal(0)
    #     total_input_cost = Decimal(0)
    #     total_miscellaneous = Decimal(0)

    #     for budget in budgets:

    #         try:
    #             labour = budget.labour_estimation or {}
    #             male = Decimal(labour.get('male_labour_cost', 0)) * int(labour.get('male_labour_count', 0))
    #             female = Decimal(labour.get('female_labour_cost', 0)) * int(labour.get('female_labour_count', 0))
    #             total_labour_cost += male + female
    #         except Exception:
    #             pass

    #         # ✅ Machine cost
    #         try:
    #             machine = budget.machine_estimation or {}
    #             mc = Decimal(machine.get('machine_count', 0))
    #             hrs = Decimal(machine.get('working_hours', 0))
    #             rate = Decimal(machine.get('rate_per_hour', 0))
    #             total_machine_cost += mc * rate * hrs
    #         except Exception:
    #             pass

    #         # ✅ Input cost
    #         try:
    #             input_data = budget.input_estimation or {}
    #             qty = Decimal(input_data.get('input_quantity', 0))
    #             cost = Decimal(input_data.get('input_cost', 0))
    #             total_input_cost += qty * cost
    #         except Exception:
    #             pass

    #         # ✅ Miscellaneous
    #         try:
    #             total_miscellaneous += Decimal(budget.miscellaneous or 0)
    #         except Exception:
    #             pass

    #     total = total_labour_cost + total_machine_cost + total_input_cost + total_miscellaneous

    #     return {
    #         "total_labour_cost": str(total_labour_cost),
    #         "total_machine_cost": str(total_machine_cost),
    #         "total_input_cost": str(total_input_cost),
    #         "total_miscellaneous": str(total_miscellaneous),
    #         "total_budget_cost": str(total)
    #     }

    def get(self, request, *args, **kwargs):
        try:
            row_number = request.query_params.get('row_number')
            zone_id = request.query_params.get('zone_id')
            crop_id = request.query_params.get('crop_id')

            if not (zone_id and crop_id):
                return JsonResponse({'error': 'zone_id and crop_id are required'}, status=400)

            # ✅ Fetch all rows for given zone + crop
            all_crop_plan_rows = CropPlanRow.objects.filter(
                user_crop_plan__zone_id=zone_id,
                user_crop_plan__crop_id=crop_id
            ).order_by('id')

            # ✅ Only include rows where this user has budgeting data
            user_crop_plan_rows = [
                row for row in all_crop_plan_rows
                if Nudges.objects.filter(crop_plan_row=row, user=request.user).exists()
            ]

            if not user_crop_plan_rows:
                return JsonResponse({'error': 'No budgeting data found for this user in the given zone and crop'}, status=404)

            # ✅ If row_number provided, pick only that row
            if row_number:
                try:
                    index = int(row_number) - 1
                    if index < 0 or index >= len(user_crop_plan_rows):
                        return JsonResponse({'error': 'Invalid row_number for this user'}, status=400)
                    user_crop_plan_rows = [user_crop_plan_rows[index]]
                except ValueError:
                    return JsonResponse({'error': 'row_number must be an integer'}, status=400)

            row_summaries = []
            total_labour = Decimal(0)
            total_machine = Decimal(0)
            total_input = Decimal(0)
            total_misc = Decimal(0)

            for idx, row in enumerate(user_crop_plan_rows, start=1):
                budgets =Nudges.objects.filter(crop_plan_row=row, user=request.user)
                summary = self.calculate_summary(budgets)

                total_labour += Decimal(summary['total_labour_cost'])
                total_machine += Decimal(summary['total_machine_cost'])
                total_input += Decimal(summary['total_input_cost'])
                total_misc += Decimal(summary['total_miscellaneous'])

                row_summaries.append({
                    "row_number": idx,
                    "stage": row.stage,
                    "date": str(row.date),
                    "zone_id": str(zone_id),
                    "crop_id": int(crop_id),
                    "total_labour_cost": summary['total_labour_cost'],
                    "total_machine_cost": summary['total_machine_cost'],
                    "total_input_cost": summary['total_input_cost'],
                    "total_miscellaneous": summary['total_miscellaneous'],
                    "total_budget_cost": summary['total_budget_cost'],
                })

            total_budget_cost = total_labour + total_machine + total_input + total_misc

            return JsonResponse({
                "rows": row_summaries,
                "total_summary": {
                    "total_labour_cost": str(total_labour),
                    "total_machine_cost": str(total_machine),
                    "total_input_cost": str(total_input),
                    "total_miscellaneous": str(total_misc),
                    "total_budget_cost": str(total_budget_cost)
                }
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


#
# class TodayCropPlanActivityAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request, *args, **kwargs):
#         user = request.user
#         zone_id = request.query_params.get('zone')
#         crop_id = request.query_params.get('crop')
#
#         if not (zone_id and crop_id):
#             return Response({'error': 'zone and crop query parameters are required'}, status=400)
#
#         today = timezone.now().date()
#
#         # Include today's rows + previous unread rows
#         crop_plan_rows = CropPlanRow.objects.filter(
#             user_crop_plan__user=user,
#             user_crop_plan__zone_id=zone_id,
#             user_crop_plan__crop_id=crop_id
#         ).filter(
#             models.Q(date=today) | models.Q(date__lt=today, read=False)
#         ).order_by('date', 'id')
#
#         result = []
#
#         for row in crop_plan_rows:
#             row_data = CropPlanRowSerializer(row, context={'request': request}).data
#
#             # Get latest nudge for this row
#             nudges_qs = Nudges.objects.filter(
#                 user=user,
#                 crop_plan_row=row.id
#             ).order_by('-id')
#
#             if nudges_qs.exists():
#                 nudge = nudges_qs.first()
#                 nudge_data = NudgesSerializer(nudge, context={'request': request}).data
#
#                 # Merge cost-related fields
#                 for field in ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']:
#                     if field in nudge_data:
#                         row_data[field] = nudge_data[field]
#             else:
#                 # Default if no nudge exists
#                 for field in ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']:
#                     row_data[field] = {"data": None, "is_read": False}
#
#             result.append(row_data)
#
#         return Response(result, status=200)
class TodayCropPlanActivityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        zone_id = request.query_params.get('zone')
        crop_id = request.query_params.get('crop')

        if not (zone_id and crop_id):
            return Response({'error': 'zone and crop query parameters are required'}, status=400)

        today = timezone.now().date()

        # Include only unread rows (today + previous unread)
        crop_plan_rows = CropPlanRow.objects.filter(
            user_crop_plan__user=user,
            user_crop_plan__zone_id=zone_id,
            user_crop_plan__crop_id=crop_id
        ).filter(
            models.Q(date=today, read=False) | models.Q(date__lt=today, read=False)
        ).order_by('date', 'id')

        result = []

        for row in crop_plan_rows:
            row_data = CropPlanRowSerializer(row, context={'request': request}).data

            # Get latest nudge for this row
            nudges_qs = Nudges.objects.filter(
                user=user,
                crop_plan_row=row.id
            ).order_by('-id')

            if nudges_qs.exists():
                nudge = nudges_qs.first()
                nudge_data = NudgesSerializer(nudge, context={'request': request}).data

                # Merge cost-related fields
                for field in ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']:
                    if field in nudge_data:
                        row_data[field] = nudge_data[field]
            else:
                # Default if no nudge exists
                for field in ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']:
                    row_data[field] = {"data": None, "is_read": False}

            result.append(row_data)

        return Response(result, status=200)


# your_app/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser  # Import parsers

# Import your models and serializer
from .models import Nudges, CropPlanRow
from .serializers import NudgesSerializer

# Import your new services
from .services import transcribe_audio_with_sarvam
from .utils import parse_cost_details_from_text


# class NudgesViewVoice(APIView):
#     permission_classes = [IsAuthenticated]
#     # Add parser classes to handle both JSON and file uploads
#     parser_classes = [JSONParser, MultiPartParser, FormParser]
#
#     # def _process_voice_input(self, request):
#     #     """Helper to process audio file if it exists."""
#     #     audio_file = request.FILES.get('audio_file')
#     #     if not audio_file:
#     #         return None, None  # No audio file to process
#     #
#     #     audio_data = audio_file.read()
#     #     transcription_result = transcribe_audio_with_sarvam(audio_data)
#     #
#     #     if "error" in transcription_result:
#     #         return None, Response({'error': f"Transcription failed: {transcription_result['error']}"},
#     #                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     #
#     #     # Adjust the key based on the actual API response from Sarvam
#     #     transcribed_text = transcription_result.get('text') or transcription_result.get('transcription')
#     #
#     #     if not transcribed_text:
#     #         return None, Response({'error': 'Transcription result was empty.'}, status=status.HTTP_400_BAD_REQUEST)
#     #
#     #     # Parse the text to get cost data
#     #     parsed_costs = parse_cost_details_from_text(transcribed_text)
#     #     return parsed_costs, None
#     def _process_voice_input(self, request):
#         audio_file = request.FILES.get('audio_file')
#         if not audio_file:
#             return None, None
#
#         audio_data = audio_file.read()
#         transcription_result = transcribe_audio_with_sarvam(audio_data)
#
#         if "error" in transcription_result:
#             return None, Response({'error': f"Transcription failed: {transcription_result['error']}"},
#                                   status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#         transcribed_text = transcription_result.get('transcription') or transcription_result.get('text')
#         if not transcribed_text:
#             return None, Response({'error': 'Transcription result was empty.'}, status=status.HTTP_400_BAD_REQUEST)
#
#         parsed_costs = parse_cost_details_from_text(transcribed_text)
#
#         # Wrap numbers into proper JSON format
#         for field, value in parsed_costs.items():
#             parsed_costs[field] = {"data": value, "is_read": True}
#
#         # Validate using the voice serializer
#         serializer = NudgesVoiceSerializer(data=parsed_costs)
#         serializer.is_valid(raise_exception=True)
#
#         return serializer.validated_data, None
#
#     def post(self, request):
#         data = request.data.copy()
#
#         # --- Voice Processing Logic ---
#         parsed_costs, error_response = self._process_voice_input(request)
#         if error_response:
#             return error_response
#         if parsed_costs:
#             data.update(parsed_costs)  # Add parsed costs to the data dict
#         # --- End of Voice Processing ---
#
#         row_number = data.get('row_number')
#         zone_id = data.get('zone')
#         crop_id = data.get('crop')
#
#         if not (row_number and zone_id and crop_id):
#             return Response({'error': 'row_number, zone, and crop are required'}, status=400)
#
#         try:
#             row_index = int(row_number) - 1
#             crop_plan_rows = CropPlanRow.objects.filter(
#                 user_crop_plan__zone_id=zone_id,
#                 user_crop_plan__crop_id=crop_id,
#                 user_crop_plan__user=request.user
#             ).order_by('id')
#             crop_plan_row = crop_plan_rows[row_index]
#             data['crop_plan_row'] = crop_plan_row.id
#         except (IndexError, ValueError):
#             return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)
#
#         # Handle is_read flags
#         for field in ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']:
#             if field in data:
#                 value = data[field]
#                 if isinstance(value, dict) and "data" in value:
#                     value["is_read"] = True
#                 else:
#                     value = {"data": value, "is_read": True}
#                 data[field] = value
#
#         serializer = NudgesVoiceSerializer(data=data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def patch(self, request):
#         data = request.data.copy()
#
#         # --- Voice Processing Logic ---
#         parsed_costs, error_response = self._process_voice_input(request)
#         if error_response:
#             return error_response
#         if parsed_costs:
#             data.update(parsed_costs)  # Add parsed costs to the data dict
#         # --- End of Voice Processing ---
#
#         row_number = data.get('row_number')
#         zone_id = data.get('zone')
#         crop_id = data.get('crop')
#
#         if not (row_number and zone_id and crop_id):
#             return Response({'error': 'row_number, zone, and crop are required'}, status=400)
#
#         try:
#             row_index = int(row_number) - 1
#             crop_plan_rows = CropPlanRow.objects.filter(
#                 user_crop_plan__zone_id=zone_id,
#                 user_crop_plan__crop_id=crop_id,
#                 user_crop_plan__user=request.user
#             ).order_by('id')
#             crop_plan_row = crop_plan_rows[row_index]
#         except (IndexError, ValueError):
#             return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)
#
#         try:
#             budgeting = Nudges.objects.get(crop_plan_row=crop_plan_row, user=request.user)
#         except Nudges.DoesNotExist:
#             return Response({'error': 'Nudges object not found for this crop_plan_row'}, status=404)
#
#         # Handle is_read flags
#         for field in ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']:
#             if field in data:
#                 value = data[field]
#                 if isinstance(value, dict) and "data" in value:
#                     value["is_read"] = True
#                 else:
#                     value = {"data": value, "is_read": True}
#                 data[field] = value
#
#         serializer = NudgesVoiceSerializer(budgeting, data=data, partial=True, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     # GET method remains unchanged
#     def get(self, request):
#         crop_plan_row_id = request.query_params.get('crop_plan_row')
#
#         if crop_plan_row_id:
#             try:
#                 budget = Nudges.objects.get(
#                     crop_plan_row=crop_plan_row_id,
#                     user=request.user
#                 )
#             except Nudges.DoesNotExist:
#                 return Response({'error': 'Nudges object not found for this crop_plan_row'}, status=404)
#             serializer = NudgesVoiceSerializer(budget, context={'request': request})
#             return Response(serializer.data, status=status.HTTP_200_OK)
#
#         budgets = Nudges.objects.filter(user=request.user)
#         serializer = NudgesVoiceSerializer(budgets, many=True, context={'request': request})
#         return Response(serializer.data, status=status.HTTP_200_OK)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from .serializers import NudgesVoiceSerializer
from .models import Nudges, CropPlanRow
from .services import transcribe_audio_with_sarvam

from .utils import parse_cost_details_from_text
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Nudges, CustomUser
from crops.models import CropPlanRow
from .serializers import NudgesVoiceSerializer
from .services import transcribe_audio_with_sarvam

# Default wrappers
def default_labour(): return {"data": {}, "is_read": False}
def default_machine(): return {"data": {}, "is_read": False}
def default_input(): return {"data": {}, "is_read": False}
def default_miscellaneous(): return {"data": 0.0, "is_read": False}

from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Nudges, CustomUser
from crops.models import CropPlanRow
from .serializers import NudgesVoiceSerializer
from .services import transcribe_audio_with_sarvam

import re

# Default wrappers for JSONFields
def default_labour(): return {"data": 0, "is_read": False}
def default_machine(): return {"data": 0, "is_read": False}
def default_input(): return {"data": 0, "is_read": False}
def default_miscellaneous(): return {"data": 0.0, "is_read": False}

# Safe parser for transcription text
def parse_cost_details_from_text(text: str) -> dict:
    """
    Extract numbers from text for each field.
    Returns dicts suitable for JSONField.
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
        # Look for a number (integer or decimal) after the keyword
        match = re.search(rf"{keyword}[\s\w]*?([\d,.]+)", text)
        if match:
            # Convert to float (remove commas if present)
            value = float(match.group(1).replace(',', ''))
        else:
            value = 0 if field != 'miscellaneous' else 0.0
        parsed_data[field] = {"data": value, "is_read": True}

    return parsed_data


import json  # Import json module


class NudgesViewVoice(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _process_voice_input(self, request):
        """Transcribe audio and parse cost details."""
        audio_file = request.FILES.get('audio_file')
        if not audio_file:
            return {}  # Return empty dict if no audio

        audio_data = audio_file.read()
        transcription_result = transcribe_audio_with_sarvam(audio_data)

        if "error" in transcription_result:
            # We will handle the error response in the main view method
            return transcription_result

        transcribed_text = transcription_result.get('transcription') or transcription_result.get('text', '')

        # This function should just return the parsed data directly
        return parse_cost_details_from_text(transcribed_text)

    def _get_crop_plan_row(self, user, row_number, zone_id, crop_id):
        try:
            row_index = int(row_number) - 1
            crop_plan_rows = CropPlanRow.objects.filter(
                user_crop_plan__zone_id=zone_id,
                user_crop_plan__crop_id=crop_id,
                user_crop_plan__user=user
            ).order_by('id')
            return crop_plan_rows[row_index]
        except (IndexError, ValueError, CropPlanRow.DoesNotExist):
            return None

    def post(self, request):
        # 1. Process voice input first
        voice_data = self._process_voice_input(request)
        if "error" in voice_data:
            return Response(
                {'error': f"Transcription failed: {voice_data['error']}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        row_number = request.data.get('row_number')
        zone_id = request.data.get('zone')
        crop_id = request.data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=400)

        crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
        if not crop_plan_row:
            return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)

        # 2. Prepare the data for the serializer
        data = request.data.dict()  # Create a mutable copy of the form data
        data.update(voice_data)  # Merge voice data, overwriting form data if conflicts exist

        # 3. **CRITICAL STEP**: Ensure all JSON fields are valid dictionaries
        json_fields = {
            'labour_estimation': default_labour,
            'machine_estimation': default_machine,
            'input_estimation': default_input,
            'miscellaneous': default_miscellaneous,
        }

        for field, default_func in json_fields.items():
            value = data.get(field)

            # If the value from the form is not already a dict, wrap it.
            if value is not None and not isinstance(value, dict):
                try:
                    # Attempt to parse as JSON string first (e.g., '{"data":{}}')
                    data[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # If it fails, treat it as a raw value (e.g., '5000')
                    try:
                        # Convert to float for numeric fields
                        numeric_value = float(value)
                        data[field] = {"data": numeric_value, "is_read": True}
                    except (ValueError, TypeError):
                        # If not a number, use the default structure
                        data[field] = default_func()
                        data[field]['is_read'] = True

        data['crop_plan_row'] = crop_plan_row.id

        serializer = NudgesVoiceSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            # Pass crop_plan_row directly to save method
            serializer.save(user=request.user, crop_plan_row=crop_plan_row)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        # The logic for PATCH is nearly identical to POST
        voice_data = self._process_voice_input(request)
        if "error" in voice_data:
            return Response(
                {'error': f"Transcription failed: {voice_data['error']}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        row_number = request.data.get('row_number')
        zone_id = request.data.get('zone')
        crop_id = request.data.get('crop')

        if not (row_number and zone_id and crop_id):
            return Response({'error': 'row_number, zone, and crop are required'}, status=400)

        crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
        if not crop_plan_row:
            return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)

        try:
            nudges_obj = Nudges.objects.get(crop_plan_row=crop_plan_row, user=request.user)
        except Nudges.DoesNotExist:
            return Response({'error': 'Nudges object not found for this crop_plan_row'}, status=404)

        data = request.data.dict()
        data.update(voice_data)

        json_fields = {
            'labour_estimation': default_labour,
            'machine_estimation': default_machine,
            'input_estimation': default_input,
            'miscellaneous': default_miscellaneous,
        }

        for field, default_func in json_fields.items():
            if field in data:
                value = data.get(field)
                if value is not None and not isinstance(value, dict):
                    try:
                        data[field] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            numeric_value = float(value)
                            data[field] = {"data": numeric_value, "is_read": True}
                        except (ValueError, TypeError):
                            data[field] = default_func()
                            data[field]['is_read'] = True

        serializer = NudgesVoiceSerializer(nudges_obj, data=data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        # Your GET method is likely fine as is.
        crop_plan_row_id = request.query_params.get('crop_plan_row')

        if crop_plan_row_id:
            try:
                nudges_obj = Nudges.objects.get(crop_plan_row=crop_plan_row_id, user=request.user)
                serializer = NudgesVoiceSerializer(nudges_obj)
                return Response(serializer.data)
            except Nudges.DoesNotExist:
                return Response({'error': 'Nudges object not found'}, status=404)

        nudges_objs = Nudges.objects.filter(user=request.user)
        serializer = NudgesVoiceSerializer(nudges_objs, many=True)
        return Response(serializer.data)

# class NudgesViewVoice(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [JSONParser, MultiPartParser, FormParser]
#
#     def _wrap_jsonfield(self, value):
#         if isinstance(value, dict):
#             value.setdefault("is_read", True)
#             if "data" not in value:
#                 value["data"] = {}
#             return value
#         # If it's a number, string, or list
#         return {"data": value, "is_read": True}
#
#     def _process_voice_input(self, request):
#         """Process audio file if uploaded and parse cost details."""
#         audio_file = request.FILES.get('audio_file')
#         if not audio_file:
#             return {}
#
#         audio_data = audio_file.read()
#         transcription_result = transcribe_audio_with_sarvam(audio_data)
#
#         if "error" in transcription_result:
#             return Response(
#                 {'error': f"Transcription failed: {transcription_result['error']}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#
#         transcribed_text = transcription_result.get('transcription') or transcription_result.get('text')
#         if not transcribed_text:
#             return Response({'error': 'Transcription result was empty.'}, status=status.HTTP_400_BAD_REQUEST)
#
#         parsed_costs = parse_cost_details_from_text(transcribed_text)
#
#         # Wrap numbers into proper JSONField format
#         wrapped_costs = {field: self._wrap_jsonfield(value) for field, value in parsed_costs.items()}
#
#         # Validate using serializer
#         serializer = NudgesVoiceSerializer(data=wrapped_costs)
#         serializer.is_valid(raise_exception=True)
#         return serializer.validated_data
#
#     def _get_crop_plan_row(self, user, row_number, zone_id, crop_id):
#         try:
#             row_index = int(row_number) - 1
#             crop_plan_rows = CropPlanRow.objects.filter(
#                 user_crop_plan__zone_id=zone_id,
#                 user_crop_plan__crop_id=crop_id,
#                 user_crop_plan__user=user
#             ).order_by('id')
#             return crop_plan_rows[row_index]
#         except (IndexError, ValueError):
#             return None
#
#     # def _prepare_data(self, request_data, voice_data):
#     #     """Merge request data and voice data and wrap JSONFields."""
#     #     data = request_data.copy()
#     #     data.update(voice_data)
#     #
#     #     for field in ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']:
#     #         if field in data:
#     #             data[field] = self._wrap_jsonfield(data[field])
#     #     return data
#     def _prepare_data(self, request_data, voice_data):
#         data = request_data.copy()
#         data.update(voice_data)
#
#         # Ensure JSONFields are always dicts
#         for field in ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']:
#             if field not in data or data[field] is None:
#                 # fallback to defaults
#                 if field == 'labour_estimation':
#                     data[field] = default_labour()
#                 elif field == 'machine_estimation':
#                     data[field] = default_machine()
#                 elif field == 'input_estimation':
#                     data[field] = default_input()
#                 elif field == 'miscellaneous':
#                     data[field] = default_miscellaneous()
#             else:
#                 data[field] = self._wrap_jsonfield(data[field])
#
#         return data
#
#     def post(self, request):
#         # Process voice input
#         voice_data = self._process_voice_input(request)
#         if isinstance(voice_data, Response):
#             return voice_data  # Error from transcription
#
#         row_number = request.data.get('row_number')
#         zone_id = request.data.get('zone')
#         crop_id = request.data.get('crop')
#
#         if not (row_number and zone_id and crop_id):
#             return Response({'error': 'row_number, zone, and crop are required'}, status=400)
#
#         crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
#         if not crop_plan_row:
#             return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)
#
#         data = self._prepare_data(request.data, voice_data)
#         data['crop_plan_row'] = crop_plan_row.id
#
#         serializer = NudgesVoiceSerializer(data=data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def patch(self, request):
#         # Process voice input
#         voice_data = self._process_voice_input(request)
#         if isinstance(voice_data, Response):
#             return voice_data  # Error from transcription
#
#         row_number = request.data.get('row_number')
#         zone_id = request.data.get('zone')
#         crop_id = request.data.get('crop')
#
#         if not (row_number and zone_id and crop_id):
#             return Response({'error': 'row_number, zone, and crop are required'}, status=400)
#
#         crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
#         if not crop_plan_row:
#             return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)
#
#         try:
#             nudges_obj = Nudges.objects.get(crop_plan_row=crop_plan_row, user=request.user)
#         except Nudges.DoesNotExist:
#             return Response({'error': 'Nudges object not found for this crop_plan_row'}, status=404)
#
#         data = self._prepare_data(request.data, voice_data)
#         serializer = NudgesVoiceSerializer(nudges_obj, data=data, partial=True, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def get(self, request):
#         crop_plan_row_id = request.query_params.get('crop_plan_row')
#
#         if crop_plan_row_id:
#             try:
#                 nudges_obj = Nudges.objects.get(crop_plan_row=crop_plan_row_id, user=request.user)
#             except Nudges.DoesNotExist:
#                 return Response({'error': 'Nudges object not found for this crop_plan_row'}, status=404)
#             serializer = NudgesVoiceSerializer(nudges_obj, context={'request': request})
#             return Response(serializer.data, status=status.HTTP_200_OK)
#
#         nudges_objs = Nudges.objects.filter(user=request.user)
#         serializer = NudgesVoiceSerializer(nudges_objs, many=True, context={'request': request})
#         return Response(serializer.data, status=status.HTTP_200_OK)
