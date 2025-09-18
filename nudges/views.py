from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from rest_framework.views import APIView
from .models import *
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.http import JsonResponse
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
                user_crop_plan__crop_id=crop_id
            ).order_by('id')
            crop_plan_row = crop_plan_rows[row_index]
            data['crop_plan_row'] = crop_plan_row.id
        except (IndexError, ValueError):
            return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)

        serializer = NudgesSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def post(self, request):
    #     data = request.data.copy()
    #     row_number = data.get('row_number')
    #     zone_id = data.get('zone')
    #     crop_id = data.get('crop')
    #
    #     if not (row_number and zone_id and crop_id):
    #         return Response({'error': 'row_number, zone, and crop are required'}, status=400)
    #
    #     try:
    #         row_index = int(row_number) - 1
    #         crop_plan_rows = CropPlanRow.objects.filter(
    #             user_crop_plan__zone_id=zone_id,
    #             user_crop_plan__crop_id=crop_id
    #         ).order_by('id')
    #         crop_plan_row = crop_plan_rows[row_index]
    #         data['crop_plan_row'] = crop_plan_row.id
    #     except (IndexError, ValueError):
    #         return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)
    #
    #     serializer = NudgesSerializer(data=data)
    #     if serializer.is_valid():
    #         serializer.save(user=request.user)
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        data = request.data.copy()
        budgeting_id = data.get('id')

        if not budgeting_id:
            return Response({'error': 'ID is required for PATCH'}, status=400)

        try:
            budgeting = Nudges.objects.get(id=budgeting_id, user=request.user)
        except Nudges.DoesNotExist:
            return Response({'error': 'Budgeting object not found or not owned by the user'}, status=404)

        # If all estimations in instance are empty, allow setting any of them
        estimations_exist = any([
            bool(budgeting.labour_estimation),
            bool(budgeting.machine_estimation),
            bool(budgeting.input_estimation),
            budgeting.miscellaneous != 0
        ])

        # The first estimation to be added can be any of the fields
        updating_fields = ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']
        incoming_estimations = {k: data.get(k) for k in updating_fields if data.get(k) is not None}

        if not estimations_exist and not incoming_estimations:
            return Response({
                'error': 'At least one estimation (labour, machine, input, or miscellaneous) must be provided first.'
            }, status=400)

        row_number = data.get('row_number')
        zone_id = data.get('zone')
        crop_id = data.get('crop')

        if row_number and zone_id and crop_id:
            try:
                row_index = int(row_number) - 1
                crop_plan_rows = CropPlanRow.objects.filter(
                    user_crop_plan__zone_id=zone_id,
                    user_crop_plan__crop_id=crop_id
                ).order_by('id')
                crop_plan_row = crop_plan_rows[row_index]
                data['crop_plan_row'] = crop_plan_row.id
            except (IndexError, ValueError):
                return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)

        data['user'] = request.user.id  # Reassign user

        serializer = NudgesSerializer(budgeting, data=data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def patch(self, request):
    #     data = request.data.copy()
    #     budgeting_id = data.get('id')
    #
    #     if not budgeting_id:
    #         return Response({'error': 'ID is required for PATCH'}, status=400)
    #
    #     try:
    #         budgeting = Nudges.objects.get(id=budgeting_id, user=request.user)
    #     except Nudges.DoesNotExist:
    #         return Response({'error': 'Budgeting object not found or not owned by the user'}, status=404)
    #
    #     row_number = data.get('row_number')
    #     zone_id = data.get('zone')
    #     crop_id = data.get('crop')
    #
    #     if row_number and zone_id and crop_id:
    #         try:
    #             row_index = int(row_number) - 1
    #             crop_plan_rows = CropPlanRow.objects.filter(
    #                 user_crop_plan__zone_id=zone_id,
    #                 user_crop_plan__crop_id=crop_id
    #             ).order_by('id')
    #             crop_plan_row = crop_plan_rows[row_index]
    #             data['crop_plan_row'] = crop_plan_row.id
    #         except (IndexError, ValueError):
    #             return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)
    #
    #     data['user'] = request.user.id  # Reassign user for patch as well
    #
    #     serializer = NudgesSerializer(budgeting, data=data, partial=True, context={'request': request}  )
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        budgets =Nudges.objects.filter(user=request.user)
        serializer = NudgesSerializer(budgets, many=True)
        return Response(serializer.data)
#
# class NudgesView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     # Create a new empty Nudges record (without estimations)
#     def post(self, request):
#         data = request.data.copy()
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
#                 user_crop_plan__crop_id=crop_id
#             ).order_by('id')
#             crop_plan_row = crop_plan_rows[row_index]
#             data['crop_plan_row'] = crop_plan_row.id
#         except (IndexError, ValueError):
#             return Response({'error': 'Invalid row_number or no matching crop plan rows found'}, status=400)
#
#         # Remove estimation fields from initial creation
#         data.pop('labour_estimation', None)
#         data.pop('machine_estimation', None)
#         data.pop('input_estimation', None)
#         data.pop('miscellaneous', None)
#
#         serializer = NudgesSerializer(data=data)
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     # Update a single estimation field (PATCH method)
#     def patch(self, request):
#         data = request.data.copy()
#         budgeting_id = data.get('id')
#
#         if not budgeting_id:
#             return Response({'error': 'ID is required for PATCH'}, status=400)
#
#         try:
#             budgeting = Nudges.objects.get(id=budgeting_id, user=request.user)
#         except Nudges.DoesNotExist:
#             return Response({'error': 'Budgeting object not found or not owned by the user'}, status=404)
#
#         # Only allow updating one or more of these fields
#         allowed_fields = ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous']
#
#         update_data = {}
#         for field in allowed_fields:
#             if field in data:
#                 update_data[field] = data[field]
#
#         if not update_data:
#             return Response({'error': 'At least one estimation field must be provided for update'}, status=400)
#
#         serializer = NudgesSerializer(budgeting, data=update_data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     # Get all nudges of the authenticated user
#     def get(self, request):
#         budgets = Nudges.objects.filter(user=request.user)
#         serializer = NudgesSerializer(budgets, many=True)
#         return Response(serializer.data)
#
#
class NudgesViewSupervisor(APIView):
    permission_classes = [IsAuthenticated]
    
    def calculate_summary(self, budgets):
        total_labour_cost = Decimal(0)
        total_machine_cost = Decimal(0)
        total_input_cost = Decimal(0)
        total_miscellaneous = Decimal(0)

        for budget in budgets:

            # ✅ Labour cost
            try:
                labour = budget.labour_estimation or {}
                male = Decimal(labour.get('male_labour_cost', 0)) * int(labour.get('male_labour_count', 0))
                female = Decimal(labour.get('female_labour_cost', 0)) * int(labour.get('female_labour_count', 0))
                total_labour_cost += male + female
            except Exception:
                pass

            # ✅ Machine cost (loop through list)
            try:
                machine_data = budget.machine_estimation or {}
                for m in machine_data.get("machines", []):
                    mc = Decimal(m.get("machine_count", 0))
                    hrs = Decimal(m.get("working_hours", 0))
                    rate = Decimal(m.get("rate_per_hour", 0))
                    total_machine_cost += mc * hrs * rate
            except Exception:
                pass

            # ✅ Input cost (loop through list)
            try:
                input_data = budget.input_estimation or {}
                for inp in input_data.get("inputs", []):
                    qty = Decimal(inp.get("quantity", 0))
                    cost = Decimal(inp.get("cost_per_unit", 0))
                    total_input_cost += qty * cost
            except Exception:
                pass


            # ✅ Miscellaneous
            try:
                total_miscellaneous += Decimal(budget.miscellaneous or 0)
            except Exception:
                pass

        total = total_labour_cost + total_machine_cost + total_input_cost + total_miscellaneous

        return {
            "total_labour_cost": str(total_labour_cost),
            "total_machine_cost": str(total_machine_cost),
            "total_input_cost": str(total_input_cost),
            "total_miscellaneous": str(total_miscellaneous),
            "total_budget_cost": str(total)
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


class TodayCropPlanActivityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        zone_id = request.query_params.get('zone')
        crop_id = request.query_params.get('crop')

        if not (zone_id and crop_id):
            return Response({'error': 'zone and crop query parameters are required'}, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.now().date()

        crop_plan_rows = CropPlanRow.objects.filter(
            user_crop_plan__user=user,
            user_crop_plan__zone_id=zone_id,
            user_crop_plan__crop_id=crop_id,
            date=today 
        ).order_by('id')

        serializer = CropPlanRowSerializer(crop_plan_rows, many=True, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)