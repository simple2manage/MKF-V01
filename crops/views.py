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