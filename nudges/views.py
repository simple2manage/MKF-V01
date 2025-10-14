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




from .models import Nudges, CustomUser # Assuming these models are defined elsewhere
from crops.models import CropPlanRow # Assuming this model is defined elsewhere
from .serializers import NudgesVoiceSerializer # Assuming this serializer is defined elsewhere
from .utils import transcribe_audio_with_sarvam  # Assuming this is the correct import


import re
import json
from word2number import w2n
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

# ======================
# Default JSON field structures
# ======================
#
# def default_labour():
#     return {
#         "male_labour_cost": 0,
#         "male_labour_count": 0,
#         "female_labour_cost": 0,
#         "female_labour_count": 0,
#         "is_read": False
#     }
#
# def default_machine():
#     return {"data": 0, "is_read": False}
#
# def default_input():
#     return {"data": 0, "is_read": False}
#
# def default_miscellaneous():
#     return {"data": 0.0, "is_read": False}
#
#
# # ======================
# # Helpers
# # ======================
#
# def _to_number(val: str) -> float:
#     """Convert digit or word into a number."""
#     try:
#         return float(val)
#     except ValueError:
#         try:
#             return float(w2n.word_to_num(val))
#         except Exception:
#             return 0
#
#
# # ======================
# # Parser function
# # ======================
# def parse_cost_details_from_text(text: str) -> dict:
#     """
#     Extract numbers from speech text, handling both English and Transliterated (Malayalam) keywords.
#     """
#     parsed_data = {}
#     text = text.lower().replace('.', '')
#     print("DEBUG: Transcribed text =>", text)
#
#     labour_data = default_labour()
#
#     # FIX: Updated patterns to include Malayalam transcribed keywords (മെയിൽ, ലേബർ, ഫീമെയിൽ, മെഷീൻ, ഇൻപുട്ട്, മിസലേനിയസ്)
#     # The regex now matches (English OR Malayalam) word, followed by optional 'cost', or 'count'.
#
#     # Matching (male OR മെയിൽ), (labour OR ലേബർ)
#     MALE_LABOUR = r"(?:male|മെയിൽ)\s+(?:labou?r|ലേബർ|ലബര)"
#     FEMALE_LABOUR = r"(?:female|ഫീമെയിൽ)\s+(?:labou?r|ലേബർ|ലബര)"
#
#     # Allow numbers to be words or digits, and optionally match "cost"
#     VALUE_AND_OPTIONAL_COST = r"(?:cost)?\s*(?:is|:)?\s*([\w\d,.]+)"
#
#     patterns = {
#         "male_labour_cost": r"(?:male|മെയിൽ)\s+(?:labou?r|ലേബർ|ലബര)\s+(?:cost|കോസ്റ്റ്)?\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "male_labour_count": r"(?:male|മെയിൽ)\s+(?:labou?r|ലേബർ|ലബര)\s+(?:count|കൗണ്ട്)\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "female_labour_cost": r"(?:female|ഫീമെയിൽ)\s+(?:labou?r|ലേബർ|ലബര)\s+(?:cost|കോസ്റ്റ്)?\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "female_labour_count": r"(?:female|ഫീമെയിൽ)\s+(?:labou?r|ലേബർ|ലബര)\s+(?:count|കൗണ്ട്)\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "machine": r"(?:machine|മെഷീൻ)\s+(?:cost|കോസ്റ്റ്)?\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "input": r"(?:input|ഇൻപുട്ട്)\s+(?:cost|കോസ്റ്റ്)?\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "miscellaneous": r"(?:miscellaneous|മിസലേനിയസ്|misc)\s+(?:cost|കോസ്റ്റ്)?\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#     }
#
#     # --- Labour Estimation ---
#     for field, pattern in patterns.items():
#         if "labou" not in field:
#             continue
#
#         match = re.search(pattern, text)
#         print(f"DEBUG: Checking {field} with regex {pattern} =>", match.group(1) if match else None)
#         if match:
#             raw_val = match.group(1).replace(',', '')
#             value = _to_number(raw_val)
#             print(f"DEBUG: Raw value for {field} => {raw_val}, Converted => {value}")
#
#             if "cost" in field:
#                 labour_data[field] = float(value)
#             else:
#                 labour_data[field] = int(value)
#
#             # Note: is_read is set to True if any labour component is successfully read
#             labour_data["is_read"] = True
#
#     parsed_data["labour_estimation"] = labour_data
#
#     # ---- Other costs ----
#     keywords_map = {
#         "machine": "machine_estimation",
#         "input": "input_estimation",
#         "miscellaneous": "miscellaneous",
#     }
#
#     for keyword, field in keywords_map.items():
#         pattern = patterns[keyword]
#         match = re.search(pattern, text)
#         print(f"DEBUG: Checking {keyword} =>", match.group(1) if match else None)
#         if match:
#             raw_val = match.group(1).replace(',', '')
#             value = _to_number(raw_val)
#             parsed_data[field] = {"data": float(value), "is_read": True}
#         else:
#             default_func = default_miscellaneous if field == "miscellaneous" else default_machine
#             parsed_data[field] = default_func()
#
#     print("DEBUG: Final parsed data =>", parsed_data)
#     return parsed_data
#
#
# class NudgesViewVoice(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [JSONParser, MultiPartParser, FormParser]
#
#     def _process_voice_input(self, request):
#         """Transcribe audio and parse cost details."""
#         audio_file = request.FILES.get("audio_file")
#         if not audio_file:
#             # Fallback for testing without actual file
#             return parse_cost_details_from_text(
#                 "male labour cost 500. male labour count 2. female labour cost 400. female labour count 3. machine is 500. input is 400. miscellaneous is 500.")
#
#         audio_data = audio_file.read()
#         transcription_result = transcribe_audio_with_sarvam(audio_data)
#
#         if "error" in transcription_result:
#             return transcription_result
#
#         transcribed_text = transcription_result.get("transcription") or transcription_result.get("text", "")
#         return parse_cost_details_from_text(transcribed_text)
#
#     def _get_crop_plan_row(self, user, row_number, zone_id, crop_id):
#         try:
#             row_index = int(row_number) - 1
#             crop_plan_rows = CropPlanRow.objects.filter(
#                 user_crop_plan__zone_id=zone_id,
#                 user_crop_plan__crop_id=crop_id,
#                 user_crop_plan__user=user,
#             ).order_by("id")
#             # 💡 NOTE: Assuming the correct CropPlanRow.DoesNotExist is imported
#             return crop_plan_rows[row_index]
#         except (IndexError, ValueError):
#             return None
#         except Exception:
#             # Catching generic error if CropPlanRow is not properly defined/imported
#             return None
#
#     def post(self, request):
#         voice_data = self._process_voice_input(request)
#         if "error" in voice_data:
#             return Response(
#                 {"error": f"Transcription failed: {voice_data['error']}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )
#
#         row_number = request.data.get("row_number")
#         zone_id = request.data.get("zone")
#         crop_id = request.data.get("crop")
#
#         if not (row_number and zone_id and crop_id):
#             return Response({"error": "row_number, zone, and crop are required"}, status=400)
#
#         crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
#         if not crop_plan_row:
#             return Response({"error": "Invalid row_number or no matching crop plan rows found"}, status=400)
#
#         data = request.data.dict()
#         data.update(voice_data)
#
#         # We don't need to manually add 'crop_plan_row' to 'data' if we pass it
#         # as a keyword argument to serializer.save() and it's in read_only_fields.
#         # data["crop_plan_row"] = crop_plan_row.id # (Alternative approach)
#
#         # JSON fields default handling (kept original logic)
#         json_fields = {
#             "labour_estimation": default_labour,
#             "machine_estimation": default_machine,
#             "input_estimation": default_input,
#             "miscellaneous": default_miscellaneous,
#         }
#
#         for field, default_func in json_fields.items():
#             value = data.get(field)
#             if value is not None and not isinstance(value, dict):
#                 try:
#                     data[field] = json.loads(value)
#                 except (json.JSONDecodeError, TypeError):
#                     try:
#                         numeric_value = _to_number(value)
#                         if field == "labour_estimation":
#                             labour_struct = default_labour()
#                             labour_struct["male_labour_cost"] = numeric_value
#                             labour_struct["is_read"] = True
#                             data[field] = labour_struct
#                         else:
#                             data[field] = {"data": float(numeric_value), "is_read": True}
#                     except Exception:
#                         data[field] = default_func()
#                         data[field]["is_read"] = True
#
#         serializer = NudgesVoiceSerializer(data=data, context={"request": request})
#         if serializer.is_valid():
#             # 🟢 FIX: Called .save() and explicitly passed the foreign key objects.
#             serializer.save(
#                 user=request.user,
#                 crop_plan_row=crop_plan_row  # Pass the model object
#             )
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         else:
#             print("DEBUG: Serializer errors =>", serializer.errors)
#             print("DEBUG: Input data =>", data)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def patch(self, request):
#         voice_data = self._process_voice_input(request)
#         if "error" in voice_data:
#             return Response(
#                 {"error": f"Transcription failed: {voice_data['error']}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )
#
#         row_number = request.data.get("row_number")
#         zone_id = request.data.get("zone")
#         crop_id = request.data.get("crop")
#
#         if not (row_number and zone_id and crop_id):
#             return Response({"error": "row_number, zone, and crop are required"}, status=400)
#
#         crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
#         if not crop_plan_row:
#             return Response({"error": "Invalid row_number or no matching crop plan rows found"}, status=400)
#
#         try:
#             nudges_obj = Nudges.objects.get(crop_plan_row=crop_plan_row, user=request.user)
#         except Nudges.DoesNotExist:
#             return Response({"error": "Nudges object not found for this crop_plan_row"}, status=404)
#
#         data = request.data.dict()
#         data.update(voice_data)
#
#         json_fields = {
#             "labour_estimation": default_labour,
#             "machine_estimation": default_machine,
#             "input_estimation": default_input,
#             "miscellaneous": default_miscellaneous,
#         }
#
#         for field, default_func in json_fields.items():
#             if field in data:
#                 value = data.get(field)
#                 if value is not None and not isinstance(value, dict):
#                     try:
#                         data[field] = json.loads(value)
#                     except (json.JSONDecodeError, TypeError):
#                         try:
#                             numeric_value = _to_number(value)
#                             if field == "labour_estimation":
#                                 labour_struct = default_labour()
#                                 labour_struct["male_labour_cost"] = numeric_value
#                                 labour_struct["is_read"] = True
#                                 data[field] = labour_struct
#                             else:
#                                 data[field] = {"data": float(numeric_value), "is_read": True}
#                         except Exception:
#                             data[field] = default_func()
#                             data[field]["is_read"] = True
#
#         serializer = NudgesVoiceSerializer(nudges_obj, data=data, partial=True, context={"request": request})
#         if serializer.is_valid():
#             # 🟢 FIX: .save() is correctly called for PATCH
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             print("DEBUG: Serializer errors =>", serializer.errors)
#             print("DEBUG: Input data =>", data)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def get(self, request):
#         crop_plan_row_id = request.query_params.get("crop_plan_row")
#
#         if crop_plan_row_id:
#             try:
#                 nudges_obj = Nudges.objects.get(crop_plan_row=crop_plan_row_id, user=request.user)
#                 serializer = NudgesVoiceSerializer(nudges_obj)
#                 return Response(serializer.data)
#             except Nudges.DoesNotExist:
#                 return Response({"error": "Nudges object not found"}, status=404)
#
#         nudges_objs = Nudges.objects.filter(user=request.user)
#         serializer = NudgesVoiceSerializer(nudges_objs, many=True)
#         return Response(serializer.data)


from .models import Nudges, CustomUser  # Assuming these models are defined elsewhere
from crops.models import CropPlanRow  # Assuming this model is defined elsewhere
from .serializers import NudgesVoiceSerializer  # Assuming this serializer is defined elsewhere
from .utils import transcribe_audio_with_sarvam  # Assuming this is the correct import

import re
import json
from word2number import w2n
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


# ======================
# Default JSON field structures
# ======================
#
# def default_labour():
#     return {
#         "male_labour_cost": 0.0,  # Changed to 0.0 for consistency
#         "male_labour_count": 0,
#         "female_labour_cost": 0.0,  # Changed to 0.0 for consistency
#         "female_labour_count": 0,
#         "is_read": False
#     }
#
#
# def default_machine():
#     return {"data": 0.0, "is_read": False}
#
#
# def default_input():
#     return {"data": 0.0, "is_read": False}
#
#
# def default_miscellaneous():
#     return {"data": 0.0, "is_read": False}
#
#
# # ======================
# # Helpers
# # ======================
#
# def _to_number(val: str) -> float:
#     """Convert digit or word into a number."""
#     try:
#         return float(val)
#     except ValueError:
#         try:
#             return float(w2n.word_to_num(val))
#         except Exception:
#             return 0.0  # Return 0.0 for safety
#
#
# # ======================
# # Parser function (MODIFIED TO PRESERVE DATA ON PATCH)
# # ======================
# def parse_cost_details_from_text(text: str) -> dict:
#     """
#     Extract numbers from speech text, handling both English and Transliterated (Malayalam) keywords.
#     Only returns fields that are successfully read from the text.
#     """
#     parsed_data = {}
#     text = text.lower().replace('.', '')
#     print("DEBUG: Transcribed text =>", text)
#
#     # Temporary holder for labour fields that are read
#     temp_labour_data = {}
#     labour_read = False  # Flag to track if ANY labour field was read
#
#     patterns = {
#         "male_labour_cost": r"(?:male|മെയിൽ)\s+(?:labou?r|ലേബർ|ലബര)\s+(?:cost|കോസ്റ്റ്)?\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "male_labour_count": r"(?:male|മെയിൽ)\s+(?:labou?r|ലേബർ|ലബര)\s+(?:count|കൗണ്ട്)\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "female_labour_cost": r"(?:female|ഫീമെയിൽ)\s+(?:labou?r|ലേബർ|ലബര)\s+(?:cost|കോസ്റ്റ്)?\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "female_labour_count": r"(?:female|ഫീമെയിൽ)\s+(?:labou?r|ലേബർ|ലബര)\s+(?:count|കൗണ്ട്)\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "machine": r"(?:machine|മെഷീൻ)\s+(?:cost|കോസ്റ്റ്)?\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "input": r"(?:input|ഇൻപുട്ട്)\s+(?:cost|കോസ്റ്റ്)?\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#         "miscellaneous": r"(?:miscellaneous|മിസലേനിയസ്|misc)\s+(?:cost|കോസ്റ്റ്)?\s*(?:is|:)?\s*([\d]+(?:\.\d+)?|\w+)",
#     }
#
#     # --- Labour Estimation ---
#     for field, pattern in patterns.items():
#         if "labou" not in field:
#             continue
#
#         match = re.search(pattern, text)
#         print(f"DEBUG: Checking {field} with regex {pattern} =>", match.group(1) if match else None)
#         if match:
#             raw_val = match.group(1).replace(',', '')
#             value = _to_number(raw_val)
#             print(f"DEBUG: Raw value for {field} => {raw_val}, Converted => {value}")
#             labour_read = True
#
#             if "cost" in field:
#                 temp_labour_data[field] = float(value)
#             else:
#                 # Ensure count is an integer
#                 temp_labour_data[field] = int(round(value))
#
#                 # Only add labour_estimation to parsed_data if any labour field was successfully read
#     if labour_read:
#         # Start with default structure, then update with extracted values
#         final_labour_data = default_labour()
#         final_labour_data.update(temp_labour_data)
#         final_labour_data["is_read"] = True
#         parsed_data["labour_estimation"] = final_labour_data
#
#     # ---- Other costs ----
#     keywords_map = {
#         "machine": "machine_estimation",
#         "input": "input_estimation",
#         "miscellaneous": "miscellaneous",
#     }
#
#     for keyword, field in keywords_map.items():
#         pattern = patterns[keyword]
#         match = re.search(pattern, text)
#         print(f"DEBUG: Checking {keyword} =>", match.group(1) if match else None)
#         if match:
#             raw_val = match.group(1).replace(',', '')
#             value = _to_number(raw_val)
#             # Only add the field to parsed_data if a value was found
#             parsed_data[field] = {"data": float(value), "is_read": True}
#         # FIX: DO NOT add the default value if it wasn't mentioned.
#         # This prevents accidental overwrites during PATCH.
#
#     print("DEBUG: Final parsed data =>", parsed_data)
#     return parsed_data
#
#
# # ----------------------------------------------------------------------
# class NudgesViewVoice(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [JSONParser, MultiPartParser, FormParser]
#
#     def _process_voice_input(self, request):
#         """Transcribe audio and parse cost details."""
#         audio_file = request.FILES.get("audio_file")
#         if not audio_file:
#             # Fallback for testing without actual file
#             return parse_cost_details_from_text(
#                 "male labour cost 500. male labour count 2. female labour cost 400. female labour count 3. machine is 500. input is 400. miscellaneous is 500.")
#
#         audio_data = audio_file.read()
#         transcription_result = transcribe_audio_with_sarvam(audio_data)
#
#         if "error" in transcription_result:
#             return transcription_result
#
#         transcribed_text = transcription_result.get("transcription") or transcription_result.get("text", "")
#         return parse_cost_details_from_text(transcribed_text)
#
#     def _get_crop_plan_row(self, user, row_number, zone_id, crop_id):
#         try:
#             row_index = int(row_number) - 1
#             crop_plan_rows = CropPlanRow.objects.filter(
#                 user_crop_plan__zone_id=zone_id,
#                 user_crop_plan__crop_id=crop_id,
#                 user_crop_plan__user=user,
#             ).order_by("id")
#             # 💡 NOTE: Assuming the correct CropPlanRow.DoesNotExist is imported
#             return crop_plan_rows[row_index]
#         except (IndexError, ValueError):
#             return None
#         except Exception:
#             # Catching generic error if CropPlanRow is not properly defined/imported
#             return None
#
#     def post(self, request):
#         voice_data = self._process_voice_input(request)
#         if "error" in voice_data:
#             return Response(
#                 {"error": f"Transcription failed: {voice_data['error']}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )
#
#         row_number = request.data.get("row_number")
#         zone_id = request.data.get("zone")
#         crop_id = request.data.get("crop")
#
#         if not (row_number and zone_id and crop_id):
#             return Response({"error": "row_number, zone, and crop are required"}, status=400)
#
#         crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
#         if not crop_plan_row:
#             return Response({"error": "Invalid row_number or no matching crop plan rows found"}, status=400)
#
#         # Start with request data, then update with extracted voice data
#         data = request.data.dict()
#         data.update(voice_data)
#
#         # JSON fields default handling: Must ensure all expected fields are present
#         # for a complete POST request, using defaults if not present in voice_data.
#         json_fields = {
#             "labour_estimation": default_labour,
#             "machine_estimation": default_machine,
#             "input_estimation": default_input,
#             "miscellaneous": default_miscellaneous,
#         }
#
#         for field, default_func in json_fields.items():
#             value = data.get(field)
#             if value is None:
#                 # If field not in request or voice_data, use the default structure for POST
#                 data[field] = default_func()
#                 continue
#
#             if not isinstance(value, dict):
#                 try:
#                     data[field] = json.loads(value)
#                 except (json.JSONDecodeError, TypeError):
#                     try:
#                         numeric_value = _to_number(value)
#                         if field == "labour_estimation":
#                             labour_struct = default_labour()
#                             labour_struct["male_labour_cost"] = numeric_value
#                             labour_struct["is_read"] = True
#                             data[field] = labour_struct
#                         else:
#                             data[field] = {"data": float(numeric_value), "is_read": True}
#                     except Exception:
#                         # Fallback for error in number conversion
#                         data[field] = default_func()
#                         data[field]["is_read"] = True  # Mark as read/attempted
#
#         serializer = NudgesVoiceSerializer(data=data, context={"request": request})
#         if serializer.is_valid():
#             # 🟢 FIX: Called .save() and explicitly passed the foreign key objects.
#             serializer.save(
#                 user=request.user,
#                 crop_plan_row=crop_plan_row  # Pass the model object
#             )
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         else:
#             print("DEBUG: Serializer errors =>", serializer.errors)
#             print("DEBUG: Input data =>", data)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     # ----------------------------------------------------------------------
#     # PATCH METHOD (FIXED FOR DATA PRESERVATION)
#     # ----------------------------------------------------------------------
#     def patch(self, request):
#         voice_data = self._process_voice_input(request)
#         if "error" in voice_data:
#             return Response(
#                 {"error": f"Transcription failed: {voice_data['error']}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )
#
#         row_number = request.data.get("row_number")
#         zone_id = request.data.get("zone")
#         crop_id = request.data.get("crop")
#
#         if not (row_number and zone_id and crop_id):
#             return Response({"error": "row_number, zone, and crop are required"}, status=400)
#
#         crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
#         if not crop_plan_row:
#             return Response({"error": "Invalid row_number or no matching crop plan rows found"}, status=400)
#
#         try:
#             # Get the existing object
#             nudges_obj = Nudges.objects.get(crop_plan_row=crop_plan_row, user=request.user)
#         except Nudges.DoesNotExist:
#             return Response({"error": "Nudges object not found for this crop_plan_row"}, status=404)
#
#         # Start with request data, then update with extracted voice data
#         data = request.data.dict()
#         data.update(voice_data)
#         # IMPORTANT: Since `voice_data` only contains fields that were read,
#         # any missing fields will be preserved by `partial=True`.
#
#         json_fields = {
#             "labour_estimation": default_labour,
#             "machine_estimation": default_machine,
#             "input_estimation": default_input,
#             "miscellaneous": default_miscellaneous,
#         }
#
#         # Handle JSON fields that might be strings (e.g., from form-data)
#         for field, default_func in json_fields.items():
#             # Only process fields present in the update data
#             if field in data:
#                 value = data.get(field)
#                 if value is not None and not isinstance(value, dict):
#                     try:
#                         data[field] = json.loads(value)
#                     except (json.JSONDecodeError, TypeError):
#                         try:
#                             numeric_value = _to_number(value)
#                             if field == "labour_estimation":
#                                 labour_struct = default_labour()
#                                 labour_struct["male_labour_cost"] = numeric_value
#                                 labour_struct["is_read"] = True
#                                 data[field] = labour_struct
#                             else:
#                                 data[field] = {"data": float(numeric_value), "is_read": True}
#                         except Exception:
#                             data[field] = default_func()
#                             data[field]["is_read"] = True
#
#         serializer = NudgesVoiceSerializer(nudges_obj, data=data, partial=True, context={"request": request})
#         if serializer.is_valid():
#             # 🟢 FIX: .save() is correctly called for PATCH
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             print("DEBUG: Serializer errors =>", serializer.errors)
#             print("DEBUG: Input data =>", data)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def get(self, request):
#         crop_plan_row_id = request.query_params.get("crop_plan_row")
#
#         if crop_plan_row_id:
#             try:
#                 nudges_obj = Nudges.objects.get(crop_plan_row=crop_plan_row_id, user=request.user)
#                 serializer = NudgesVoiceSerializer(nudges_obj)
#                 return Response(serializer.data)
#             except Nudges.DoesNotExist:
#                 return Response({"error": "Nudges object not found"}, status=404)
#
#         nudges_objs = Nudges.objects.filter(user=request.user)
#         serializer = NudgesVoiceSerializer(nudges_objs, many=True)
#         return Response(serializer.data)
# def default_labour():
#     return {
#         "male_labour_cost": 0.0,
#         "male_labour_count": 0,
#         "female_labour_cost": 0.0,
#         "female_labour_count": 0,
#         "is_read": False
#     }
#
#
# def default_machine():
#     return {"data": 0.0, "is_read": False}
#
#
# def default_input():
#     return {"data": 0.0, "is_read": False}
#
#
# def default_miscellaneous():
#     return {"data": 0.0, "is_read": False}
#
#
# # ======================
# # Helpers (UPDATED FOR RELIABLE NUMBER CONVERSION)
# # ======================
#
# # Map of common transliterated words to digits
# TRANSLITERATION_MAP = {
#     # English
#     "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
#     "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
#     # Malayalam Transliterations (adjust based on Sarvam's common output)
#     "വൺ": "1", "ടു": "2", "ത്രീ": "3", "ഫോർ": "4", "ഫൈവ്": "5",
#     "സെവൻ": "7",  # <--- NEW ENTRY TO FIX THE BUG
#     # You may need to add:
#     "സിക്സ്": "6", "എയിറ്റ്": "8", "നയൺ": "9", "ടെൻ": "10",
#     # Tamil
#     "ஒன்று": "1", "ரண்டு": "2", "மூன்று": "3", "நான்கு": "4", "ஐந்து": "5",
#     "ஆறு": "6", "ஏழு": "7", "எட்டு": "8", "ஒன்பது": "9", "பத்து": "10"
# }
#
#
# def _to_number(val: str) -> float:
#     """Convert digit, word, or transliteration into a number."""
#     val = val.lower().strip().replace(',', '')
#
#     # 1. Check for direct digit conversion
#     try:
#         return float(val)
#     except ValueError:
#         pass  # Not a digit/float, continue
#
#     # 2. Check for known transliterations/words (Normalize to digit string)
#     # This directly fixes the 'ത്രീ' -> 3 and 'ഫോർ' -> 4 issue.
#     for word, digit in TRANSLITERATION_MAP.items():
#         if val == word:
#             val = digit
#             break
#
#     # 3. Try to convert the (potentially normalized) string as a digit again
#     try:
#         return float(val)
#     except ValueError:
#         # 4. Fallback to w2n (mostly for English words that weren't in the map)
#         try:
#             return float(w2n.word_to_num(val))
#         except Exception:
#             return 0.0  # Return 0.0 for safety
#
#
# # ======================
# # Parser function (UPDATED REGEX)
# # ======================
# def parse_cost_details_from_text(text: str) -> dict:
#     """
#     Extract numbers from speech text, handling both English and Transliterated (Malayalam) keywords.
#     Only returns fields that are successfully read from the text.
#     """
#     parsed_data = {}
#     text = text.lower().replace('.', '')
#     print("DEBUG: Transcribed text =>", text)
#
#     # Temporary holder for labour fields that are read
#     temp_labour_data = {}
#     labour_read = False  # Flag to track if ANY labour field was read
#
#     # IMPROVED: Use [^\s]+ to capture a sequence of non-whitespace characters,
#     # ensuring full words like 'ത്രീ' or '400' are captured instead of 'ത'.
#     value_capture = r"([\d]+(?:\.\d+)?|[^\s]+)"
#
#     patterns = {
#         # ----------------------------------------------------------------------------------------------------
#         # LABOUR COST (male)
#         # EN: male, ML: മെയിൽ, TN: மேல்
#         # EN: labou?r, ML: ലേബർ, TN: லேபர்
#         # EN: cost, ML: കോസ്റ്റ്, TN: கோஸ்ட்
#         "male_labour_cost": r"(?:male|മെയിൽ|மேல்)\s+(?:labou?r|ലേബർ|லேபர்)\s+(?:cost|കോസ്റ്റ്|கோஸ்ட்)\s*(?:is|:)?\s*" + value_capture,
#
#         # LABOUR COUNT (male)
#         # EN: count, ML: കൗണ്ട്, TN: கவுண்ட்
#         "male_labour_count": r"(?:male|മെയിൽ|மேல்)\s+(?:labou?r|ലേബർ|லேபர்)\s+(?:count|കൗണ്ട്|கவுண்ட்)\s*(?:is|:)?\s*" + value_capture,
#
#         # ----------------------------------------------------------------------------------------------------
#         # LABOUR COST (female)
#         # EN: female, ML: ഫീമെയിൽ, TN: ஃபீமேல்
#         "female_labour_cost": r"(?:female|ഫീമെയിൽ|ஃபீமேல்)\s+(?:labou?r|ലേബർ|லேபர்)\s+(?:cost|കോസ്റ്റ്|கோஸ்ட்)\s*(?:is|:)?\s*" + value_capture,
#
#         # LABOUR COUNT (female)
#         "female_labour_count": r"(?:female|ഫീമെയിൽ|ஃபீமேல்)\s+(?:labou?r|ലേബർ|லேபர்)\s+(?:count|കൗണ്ട്|கவுண்ட்)\s*(?:is|:)?\s*" + value_capture,
#
#         # ----------------------------------------------------------------------------------------------------
#         # MACHINE
#         # EN: machine, ML: മെഷീൻ, TN: மிஷின்
#         "machine": r"(?:machine|മെഷീൻ|மிஷின்)\s+(?:cost|കോസ്റ്റ്|கோஸ்ட்)?\s*(?:is|:)?\s*" + value_capture,
#
#         # ----------------------------------------------------------------------------------------------------
#         # INPUT
#         # EN: input, ML: ഇൻപുട്ട്, TN: இன்புட்
#         "input": r"(?:input|ഇൻപുട്ട്|இன்புட்)\s+(?:cost|കോസ്റ്റ്|கோஸ்ட்)?\s*(?:is|:)?\s*" + value_capture,
#
#         # ----------------------------------------------------------------------------------------------------
#         # MISCELLANEOUS
#         # EN: miscellaneous|misc, ML: മിസലേനിയസ്, TN: மிசலேனியஸ்
#         "miscellaneous": r"(?:miscellaneous|മിസലേനിയസ്|misc|மிசலேനിയസ്)\s+(?:cost|കോസ്റ്റ്|கோസ്റ്റ്)?\s*(?:is|:)?\s*" + value_capture,
#
#         # ----------------------------------------------------------------------------------------------------
#     }
#
#     # --- Labour Estimation ---
#     for field, pattern in patterns.items():
#         if "labou" not in field:
#             continue
#
#         match = re.search(pattern, text)
#         print(f"DEBUG: Checking {field} with regex =>", match.group(1) if match else None)
#         if match:
#             raw_val = match.group(1)  # Removed .replace(',', '') as it's handled in _to_number
#             value = _to_number(raw_val)
#             print(f"DEBUG: Raw value for {field} => {raw_val}, Converted => {value}")
#
#             # Skip if conversion resulted in the default fallback
#             if value == 0.0 and raw_val not in ["0", "zero", "0.0"]:
#                 print(f"DEBUG: Skipping {field} as conversion to number failed or resulted in 0.0 unexpectedly.")
#                 continue
#
#             labour_read = True
#
#             if "cost" in field:
#                 temp_labour_data[field] = float(value)
#             else:
#                 # Ensure count is an integer
#                 temp_labour_data[field] = int(round(value))
#
#                 # Only add labour_estimation to parsed_data if any labour field was successfully read
#     if labour_read:
#         # Start with default structure, then update with extracted values
#         final_labour_data = default_labour()
#         final_labour_data.update(temp_labour_data)
#         final_labour_data["is_read"] = True
#         parsed_data["labour_estimation"] = final_labour_data
#
#     # ---- Other costs ----
#     keywords_map = {
#         "machine": "machine_estimation",
#         "input": "input_estimation",
#         "miscellaneous": "miscellaneous",
#     }
#
#     for keyword, field in keywords_map.items():
#         pattern = patterns[keyword]
#         match = re.search(pattern, text)
#         print(f"DEBUG: Checking {keyword} =>", match.group(1) if match else None)
#         if match:
#             raw_val = match.group(1)
#             value = _to_number(raw_val)
#
#             # Only add the field to parsed_data if a valid value was found
#             if value > 0.0 or raw_val in ["0", "zero", "0.0"]:
#                 parsed_data[field] = {"data": float(value), "is_read": True}
#
#     print("DEBUG: Final parsed data =>", parsed_data)
#     return parsed_data
#
#
# # ----------------------------------------------------------------------
# class NudgesViewVoice(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [JSONParser, MultiPartParser, FormParser]
#
#     def _process_voice_input(self, request):
#         """Transcribe audio and parse cost details."""
#         audio_file = request.FILES.get("audio_file")
#         if not audio_file:
#             # Fallback for testing without actual file
#             return parse_cost_details_from_text(
#                 "male labour cost 500. male labour count 2. female labour cost 400. female labour count 3. machine is 500. input is 400. miscellaneous is 500.")
#
#         audio_data = audio_file.read()
#         transcription_result = transcribe_audio_with_sarvam(audio_data)
#
#         if "error" in transcription_result:
#             return transcription_result
#
#         transcribed_text = transcription_result.get("transcription") or transcription_result.get("text", "")
#         return parse_cost_details_from_text(transcribed_text)
#
#     def _get_crop_plan_row(self, user, row_number, zone_id, crop_id):
#         try:
#             row_index = int(row_number) - 1
#             crop_plan_rows = CropPlanRow.objects.filter(
#                 user_crop_plan__zone_id=zone_id,
#                 user_crop_plan__crop_id=crop_id,
#                 user_crop_plan__user=user,
#             ).order_by("id")
#             # 💡 NOTE: Assuming the correct CropPlanRow.DoesNotExist is imported
#             return crop_plan_rows[row_index]
#         except (IndexError, ValueError):
#             return None
#         except Exception:
#             # Catching generic error if CropPlanRow is not properly defined/imported
#             return None
#
#     def post(self, request):
#         voice_data = self._process_voice_input(request)
#         if "error" in voice_data:
#             return Response(
#                 {"error": f"Transcription failed: {voice_data['error']}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )
#
#         row_number = request.data.get("row_number")
#         zone_id = request.data.get("zone")
#         crop_id = request.data.get("crop")
#
#         if not (row_number and zone_id and crop_id):
#             return Response({"error": "row_number, zone, and crop are required"}, status=400)
#
#         crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
#         if not crop_plan_row:
#             return Response({"error": "Invalid row_number or no matching crop plan rows found"}, status=400)
#
#         # Start with request data, then update with extracted voice data
#         data = request.data.dict()
#         data.update(voice_data)
#
#         # JSON fields default handling: Must ensure all expected fields are present
#         # for a complete POST request, using defaults if not present in voice_data.
#         json_fields = {
#             "labour_estimation": default_labour,
#             "machine_estimation": default_machine,
#             "input_estimation": default_input,
#             "miscellaneous": default_miscellaneous,
#         }
#
#         for field, default_func in json_fields.items():
#             value = data.get(field)
#             if value is None:
#                 # If field not in request or voice_data, use the default structure for POST
#                 data[field] = default_func()
#                 continue
#
#             if not isinstance(value, dict):
#                 try:
#                     data[field] = json.loads(value)
#                 except (json.JSONDecodeError, TypeError):
#                     # Handle cases where value is a raw string/number that failed to load as JSON
#                     try:
#                         numeric_value = _to_number(value)
#
#                         if field == "labour_estimation":
#                             labour_struct = default_labour()
#                             # Use the converted number for cost, since count requires specific parsing
#                             labour_struct["male_labour_cost"] = numeric_value
#                             labour_struct["is_read"] = True
#                             data[field] = labour_struct
#                         else:
#                             data[field] = {"data": float(numeric_value), "is_read": True}
#                     except Exception:
#                         # Fallback for error in number conversion
#                         data[field] = default_func()
#                         data[field]["is_read"] = True  # Mark as read/attempted
#
#         serializer = NudgesVoiceSerializer(data=data, context={"request": request})
#         if serializer.is_valid():
#             serializer.save(
#                 user=request.user,
#                 crop_plan_row=crop_plan_row  # Pass the model object
#             )
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         else:
#             print("DEBUG: Serializer errors =>", serializer.errors)
#             print("DEBUG: Input data =>", data)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     # ----------------------------------------------------------------------
#     # PATCH METHOD (FIXED FOR DATA PRESERVATION)
#     # ----------------------------------------------------------------------
#     def patch(self, request):
#         voice_data = self._process_voice_input(request)
#         if "error" in voice_data:
#             return Response(
#                 {"error": f"Transcription failed: {voice_data['error']}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )
#
#         row_number = request.data.get("row_number")
#         zone_id = request.data.get("zone")
#         crop_id = request.data.get("crop")
#
#         if not (row_number and zone_id and crop_id):
#             return Response({"error": "row_number, zone, and crop are required"}, status=400)
#
#         crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
#         if not crop_plan_row:
#             return Response({"error": "Invalid row_number or no matching crop plan rows found"}, status=400)
#
#         try:
#             # FIX: Use filter and order to retrieve the unique (latest) object
#             # This handles existing duplicate data in the database.
#             nudges_obj = Nudges.objects.filter(
#                 crop_plan_row=crop_plan_row,
#                 user=request.user
#             ).order_by('-id').first()  # Orders by most recent ID descending and takes the first one
#
#             if not nudges_obj:
#                 return Response({"error": "Nudges object not found for this crop_plan_row"}, status=404)
#
#         except Exception as e:
#             # Catches unexpected DB errors
#             print(f"Database retrieval error: {e}")
#             return Response({"error": "Database error while retrieving Nudges object"}, status=500)
#
#         # Start with request data, then update with extracted voice data
#         data = request.data.dict()
#         data.update(voice_data)
#
#         # ... (JSON field handling code remains the same)
#
#         json_fields = {
#             "labour_estimation": default_labour,
#             "machine_estimation": default_machine,
#             "input_estimation": default_input,
#             "miscellaneous": default_miscellaneous,
#         }
#
#         # Handle JSON fields that might be strings (e.g., from form-data)
#         for field, default_func in json_fields.items():
#             # Only process fields present in the update data
#             if field in data:
#                 value = data.get(field)
#                 if value is not None and not isinstance(value, dict):
#                     try:
#                         data[field] = json.loads(value)
#                     except (json.JSONDecodeError, TypeError):
#                         try:
#                             numeric_value = _to_number(value)
#                             if field == "labour_estimation":
#                                 labour_struct = default_labour()
#                                 labour_struct["male_labour_cost"] = numeric_value
#                                 labour_struct["is_read"] = True
#                                 data[field] = labour_struct
#                             else:
#                                 data[field] = {"data": float(numeric_value), "is_read": True}
#                         except Exception:
#                             data[field] = default_func()
#                             data[field]["is_read"] = True
#
#         serializer = NudgesVoiceSerializer(nudges_obj, data=data, partial=True, context={"request": request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             print("DEBUG: Serializer errors =>", serializer.errors)
#             print("DEBUG: Input data =>", data)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def get(self, request):
#         crop_plan_row_id = request.query_params.get("crop_plan_row")
#
#         if crop_plan_row_id:
#             try:
#                 nudges_obj = Nudges.objects.get(crop_plan_row=crop_plan_row_id, user=request.user)
#                 serializer = NudgesVoiceSerializer(nudges_obj)
#                 return Response(serializer.data)
#             except Nudges.DoesNotExist:
#                 return Response({"error": "Nudges object not found"}, status=404)
#
#         nudges_objs = Nudges.objects.filter(user=request.user)
#         serializer = NudgesVoiceSerializer(nudges_objs, many=True)
#         return Response(serializer.data)


def default_labour():
    return {
        "labour_cost": 0.0,  # SIMPLIFIED: Single cost field
        "is_read": False
    }


def default_machine():
    return {"data": 0.0, "is_read": False}


def default_input():
    return {"data": 0.0, "is_read": False}


def default_miscellaneous():
    return {"data": 0.0, "is_read": False}


# ======================
# Helpers (UNCHANGED)
# ======================

# Map of common transliterated words to digits
TRANSLITERATION_MAP = {
    # English
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    # Malayalam Transliterations (adjust based on Sarvam's common output)
    "വൺ": "1", "ടു": "2", "ത്രീ": "3", "ഫോർ": "4", "ഫൈവ്": "5",
    "സെവൻ": "7",
    # You may need to add:
    "സിക്സ്": "6", "എയിറ്റ്": "8", "നയൺ": "9", "ടെൻ": "10",
    # Tamil
    "ஒன்று": "1", "ரண்டு": "2", "மூன்று": "3", "நான்கு": "4", "ஐந்து": "5",
    "ஆறு": "6", "ஏழு": "7", "எட்டு": "8", "ஒன்பது": "9", "பத்து": "10"
}


def _to_number(val: str) -> float:
    """Convert digit, word, or transliteration into a number."""
    val = val.lower().strip().replace(',', '')

    # 1. Check for direct digit conversion
    try:
        return float(val)
    except ValueError:
        pass  # Not a digit/float, continue

    # 2. Check for known transliterations/words (Normalize to digit string)
    for word, digit in TRANSLITERATION_MAP.items():
        if val == word:
            val = digit
            break

    # 3. Try to convert the (potentially normalized) string as a digit again
    try:
        return float(val)
    except ValueError:
        # 4. Fallback to w2n (mostly for English words that weren't in the map)
        try:
            # NOTE: w2n needs to be imported, assuming it is.
            from word2number import w2n  # Assuming this is the correct library
            return float(w2n.word_to_num(val))
        except Exception:
            return 0.0  # Return 0.0 for safety


# ======================
# Parser function (UPDATED FOR SINGLE LABOUR COST)
# ======================
def parse_cost_details_from_text(text: str) -> dict:
    """
    Extract numbers from speech text, handling both English and Transliterated (Malayalam) keywords.
    Only returns fields that are successfully read from the text.
    """
    parsed_data = {}
    text = text.lower().replace('.', '')
    print("DEBUG: Transcribed text =>", text)

    labour_read = False
    temp_labour_cost = 0.0

    value_capture = r"([\d]+(?:\.\d+)?)"

    patterns = {
        # ---------------- LABOUR COST ----------------
        "labour_cost": r"(?:male|female|മെയിൽ|ഫീമെയിൽ|മേൽ|ஃபீമേൽ)?\s*" \
                       r"(?:labou?r|ലേബർ|ലേബര്‍|തൊഴിലാളി(?:കളുടെ)?|കൂലി|തൊഴിലാളി കൂലി|ലேபர்)\s*" \
                       r"(?:cost|കോസ്റ്റ്|വില|ചിലവ്|கோസ്റ്റ്)?\s*(?:is|ആണ്|:)?\s*" + value_capture,

        # ---------------- MACHINE COST ----------------
        "machine": r"(?:machine|മെഷീൻ|മെഷിന്‍|മിഷിൻ|യന്ത്രം|യന്ത്രത്തിന്റെ|மிஷின்)\s*" \
                   r"(?:cost|കോസ്റ്റ്|വില|ചിലവ്|கோസ്റ്റ്)?\s*(?:is|ആണ്|:)?\s*" + value_capture,

        # ---------------- INPUT COST ----------------
        "input": r"(?:input|ഇൻപുട്ട്|ഇൻപുട്ട് കോസ്റ്റ്|വിത്ത്|വിത്തിന്|വളം|മരുന്ന്|இன்புட்)\s*" \
                 r"(?:cost|കോസ്റ്റ്|വില|ചിലവ്|கோസ്റ്റ്)?\s*(?:is|ആണ്|:)?\s*" + value_capture,

        # ---------------- MISCELLANEOUS COST ----------------
        "miscellaneous": r"(?:miscellaneous|misc|മിസ്ലേനിയസ് |മിസലേനിയസ്|മറ്റുള്ള ചെലവ്|ബാക്കി ചെലവ്|അന്യ ചെലവ്|മറ്റുള്ളവ|മറ്റുള്ളവയുടെ|மிசலேനിയஸ்)\s*" \
                         r"(?:cost|കോസ്റ്റ്|വില|ചിലവ്|கோസ്റ്റ്)?\s*(?:is|ആണ്|:)?\s*" + value_capture,
    }

    # patterns = {
    #     # ----------------------------------------------------------------------------------------------------
    #     # LABOUR COST (COMBINED) - Updated regex
    #     # This will match phrases like "labour cost is 500" or "male labour is 500" or "female labour 400"
    #     # It's an aggressive simplification to capture the main labour value if the specifics are removed.
    #     # EN: labou?r, ML: ലേബർ, TN: லேபர்
    #     # EN: cost, ML: കോസ്റ്റ്, TN: கோஸ்ட்
    #     "labour_cost": r"(?:(?:male|മെയിൽ|மேൽ|female|ഫീമെയിൽ|ஃபീമേൽ)?\s*(?:labou?r|ലേബർ|லேബർ)(?:\s+(?:cost|കോസ്റ്റ്|கோസ്റ്റ്))?)\s*(?:is|:)?\s*" + value_capture,
    #
    #     # ----------------------------------------------------------------------------------------------------
    #     # MACHINE
    #     # EN: machine, ML: മെഷീൻ, TN: മിഷින්
    #     "machine": r"(?:machine|മെഷീൻ|മിഷින්)\s+(?:cost|കോസ്റ്റ്|கோஸ்ட்)?\s*(?:is|:)?\s*" + value_capture,
    #
    #     # ----------------------------------------------------------------------------------------------------
    #     # INPUT
    #     # EN: input, ML: ഇൻപുട്ട്, TN: இன்புட்
    #     "input": r"(?:input|ഇൻപുട്ട്|இன்பുട്ട്)\s+(?:cost|കോസ്റ്റ്|கோസ്റ്റ്)?\s*(?:is|:)?\s*" + value_capture,
    #
    #     # ----------------------------------------------------------------------------------------------------
    #     # MISCELLANEOUS
    #     # EN: miscellaneous|misc, ML: മിസലേനിയസ്, TN: மிസലേനിയസ്
    #     "miscellaneous": r"(?:miscellaneous|മിസലേനിയസ്|misc|மிസലേനിയസ്)\s+(?:cost|കോസ്റ്റ്|கோസ്റ്റ്)?\s*(?:is|:)?\s*" + value_capture,
    #
    #     # ----------------------------------------------------------------------------------------------------
    # }

    # --- Labour Estimation ---
    # Only one field to check now: "labour_cost"
    field = "labour_cost"
    pattern = patterns[field]
    match = re.search(pattern, text)
    print(f"DEBUG: Checking {field} with regex =>", match.group(1) if match else None)

    if match:
        raw_val = match.group(1)
        value = _to_number(raw_val)
        print(f"DEBUG: Raw value for {field} => {raw_val}, Converted => {value}")

        if value > 0.0 or raw_val in ["0", "zero", "0.0"]:
            labour_read = True
            temp_labour_cost = float(value)

    if labour_read:
        final_labour_data = default_labour()
        final_labour_data["labour_cost"] = temp_labour_cost
        final_labour_data["is_read"] = True
        parsed_data["labour_estimation"] = final_labour_data

    # ---- Other costs (UNCHANGED) ----
    keywords_map = {
        "machine": "machine_estimation",
        "input": "input_estimation",
        "miscellaneous": "miscellaneous",
    }

    for keyword, field in keywords_map.items():
        pattern = patterns[keyword]
        match = re.search(pattern, text)
        print(f"DEBUG: Checking {keyword} =>", match.group(1) if match else None)
        if match:
            raw_val = match.group(1)
            value = _to_number(raw_val)

            if value > 0.0 or raw_val in ["0", "zero", "0.0"]:
                parsed_data[field] = {"data": float(value), "is_read": True}

    print("DEBUG: Final parsed data =>", parsed_data)
    return parsed_data
class NudgesViewVoice(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _process_voice_input(self, request):
        """Transcribe audio and parse cost details."""
        audio_file = request.FILES.get("audio_file")
        if not audio_file:
            # Fallback for testing without actual file
            return parse_cost_details_from_text(
                "total labour cost 500. machine is 500. input is 400. miscellaneous is 500.")

        audio_data = audio_file.read()
        transcription_result = transcribe_audio_with_sarvam(audio_data)

        if "error" in transcription_result:
            return transcription_result

        transcribed_text = transcription_result.get("transcription") or transcription_result.get("text", "")
        return parse_cost_details_from_text(transcribed_text)

    def _get_crop_plan_row(self, user, row_number, zone_id, crop_id):
        try:
            row_index = int(row_number) - 1
            crop_plan_rows = CropPlanRow.objects.filter(
                user_crop_plan__zone_id=zone_id,
                user_crop_plan__crop_id=crop_id,
                user_crop_plan__user=user,
            ).order_by("id")
            # This line restores the original logic
            return crop_plan_rows[row_index]
        except (IndexError, ValueError):
            return None
        except Exception:
            return None

    def post(self, request):
        voice_data = self._process_voice_input(request)
        if "error" in voice_data:
            return Response(
                {"error": f"Transcription failed: {voice_data['error']}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        row_number = request.data.get("row_number")
        zone_id = request.data.get("zone")
        crop_id = request.data.get("crop")

        if not (row_number and zone_id and crop_id):
            return Response({"error": "row_number, zone, and crop are required"}, status=400)

        crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
        if not crop_plan_row:
            return Response({"error": "Invalid row_number or no matching crop plan rows found"}, status=400)

        # Start with request data, then update with extracted voice data
        data = request.data.dict()
        data.update(voice_data)

        # JSON fields default handling: Must ensure all expected fields are present
        json_fields = {
            "labour_estimation": default_labour,
            "machine_estimation": default_machine,
            "input_estimation": default_input,
            "miscellaneous": default_miscellaneous,
        }

        for field, default_func in json_fields.items():
            value = data.get(field)
            if value is None:
                data[field] = default_func()
                continue

            if not isinstance(value, dict):
                try:
                    data[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        numeric_value = _to_number(value)

                        if field == "labour_estimation":
                            labour_struct = default_labour()
                            # Use the converted number for the single labour_cost
                            labour_struct["labour_cost"] = numeric_value
                            labour_struct["is_read"] = True
                            data[field] = labour_struct
                        else:
                            data[field] = {"data": float(numeric_value), "is_read": True}
                    except Exception:
                        data[field] = default_func()
                        data[field]["is_read"] = True

        serializer = NudgesVoiceSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            # RESTORED ACTUAL SAVE LOGIC
            serializer.save(
                user=request.user,
                crop_plan_row=crop_plan_row  # Pass the model object
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("DEBUG: Serializer errors =>", serializer.errors)
            print("DEBUG: Input data =>", data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ----------------------------------------------------------------------
    # PATCH METHOD (RESTORED DB LOGIC)
    # ----------------------------------------------------------------------
    def patch(self, request):
        voice_data = self._process_voice_input(request)
        if "error" in voice_data:
            return Response(
                {"error": f"Transcription failed: {voice_data['error']}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        row_number = request.data.get("row_number")
        zone_id = request.data.get("zone")
        crop_id = request.data.get("crop")

        if not (row_number and zone_id and crop_id):
            return Response({"error": "row_number, zone, and crop are required"}, status=400)

        crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)
        if not crop_plan_row:
            return Response({"error": "Invalid row_number or no matching crop plan rows found"}, status=400)

        try:
            # RESTORED ACTUAL RETRIEVAL LOGIC
            nudges_obj = Nudges.objects.filter(
                crop_plan_row=crop_plan_row,
                user=request.user
            ).order_by('-id').first()

            if not nudges_obj:
                return Response({"error": "Nudges object not found for this crop_plan_row"}, status=404)

        except Exception as e:
            print(f"Database retrieval error: {e}")
            return Response({"error": "Database error while retrieving Nudges object"}, status=500)

        # Start with request data, then update with extracted voice data
        data = request.data.dict()
        data.update(voice_data)

        # JSON fields default handling
        json_fields = {
            "labour_estimation": default_labour,
            "machine_estimation": default_machine,
            "input_estimation": default_input,
            "miscellaneous": default_miscellaneous,
        }

        # Handle JSON fields that might be strings (e.g., from form-data)
        for field, default_func in json_fields.items():
            if field in data:
                value = data.get(field)
                if value is not None and not isinstance(value, dict):
                    try:
                        data[field] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            numeric_value = _to_number(value)
                            if field == "labour_estimation":
                                labour_struct = default_labour()
                                labour_struct["labour_cost"] = numeric_value
                                labour_struct["is_read"] = True
                                data[field] = labour_struct
                            else:
                                data[field] = {"data": float(numeric_value), "is_read": True}
                        except Exception:
                            data[field] = default_func()
                            data[field]["is_read"] = True

        serializer = NudgesVoiceSerializer(nudges_obj, data=data, partial=True, context={"request": request})
        if serializer.is_valid():
            # RESTORED ACTUAL SAVE LOGIC
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print("DEBUG: Serializer errors =>", serializer.errors)
            print("DEBUG: Input data =>", data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ----------------------------------------------------------------------
    # GET METHOD (RESTORED DB LOGIC)
    # ----------------------------------------------------------------------
    def get(self, request):
        # 1. Get the parameters required to find the CropPlanRow
        row_number = request.query_params.get("row_number")
        zone_id = request.query_params.get("zone")
        crop_id = request.query_params.get("crop")

        # If row_number, zone, and crop are provided, we look for a specific Nudges object
        if row_number and zone_id and crop_id:
            # Find the specific CropPlanRow
            crop_plan_row = self._get_crop_plan_row(request.user, row_number, zone_id, crop_id)

            if not crop_plan_row:
                return Response({"error": "Invalid row_number, zone, or crop ID, or no matching crop plan row found"},
                                status=status.HTTP_404_NOT_FOUND)

            try:
                # RETRIEVAL LOGIC: Use the found CropPlanRow object
                # Use filter().first() to get the most recent/unique Nudges object associated with that row
                nudges_obj = Nudges.objects.filter(
                    crop_plan_row=crop_plan_row,
                    user=request.user
                ).order_by('-id').first()  # Using order_by('-id').first() is safer for retrieval

                if not nudges_obj:
                    return Response({"error": "Nudges object not found for this specific crop plan row"},
                                    status=status.HTTP_404_NOT_FOUND)

                serializer = NudgesVoiceSerializer(nudges_obj)
                return Response(serializer.data)

            except Exception as e:
                # Catch any unexpected database error during retrieval
                print(f"Database error during Nudges retrieval: {e}")
                return Response({"error": "An internal error occurred during data retrieval"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # If no specific row parameters are provided, return all Nudges objects for the user (The original list view)
        nudges_objs = Nudges.objects.filter(user=request.user)
        serializer = NudgesVoiceSerializer(nudges_objs, many=True)
        return Response(serializer.data)
















