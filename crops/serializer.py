from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import *

class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = ['id', 'crop_id', 'crop_name', 'image', 'color', 'created_by', 'created', 'updated_by']
        read_only_fields = ['id', 'crop_id', 'created_by', 'created', 'updated_by']



class UserCropPlanSerializer(serializers.ModelSerializer):
    crop = serializers.PrimaryKeyRelatedField(queryset=Crop.objects.all(), write_only=True)
    crop_details = CropSerializer(source='crop', read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    class Meta:
        model = UserCropPlan
        fields = ('id', 'user', 'crop', 'crop_details', 'zone', 'crop_plan', 'start_date')


# class CropPlanRowSerializer(serializers.ModelSerializer):
#     user = serializers.SerializerMethodField()
#     zone = serializers.SerializerMethodField()
#     crop = serializers.SerializerMethodField()
#     row_number = serializers.SerializerMethodField()#newfieldadded
#
#     class Meta:
#         model = CropPlanRow
#         fields = ('row_number', 'user_crop_plan', 'date', 'day', 'stage', 'action', 'created', 'updated', 'user', 'zone', 'crop')
#
#     def get_user(self, obj):
#         return obj.user_crop_plan.user.id if obj.user_crop_plan.user else None
#
#     def get_zone(self, obj):
#         return obj.user_crop_plan.zone.id if obj.user_crop_plan.zone else None
#
#     def get_crop(self, obj):
#         return obj.user_crop_plan.crop.crop_name if obj.user_crop_plan.crop else None
#     def get_row_number(self, obj):
#         # Fetch all rows for this plan ordered by id
#         rows = CropPlanRow.objects.filter(
#             user_crop_plan=obj.user_crop_plan
#         ).order_by('id').values_list('id', flat=True)
#
#         try:
#             return list(rows).index(obj.id) + 1  # 1-based index
#         except ValueError:
#             return None
class CropPlanRowSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)  # Add this line
    user = serializers.SerializerMethodField()
    zone = serializers.SerializerMethodField()
    crop = serializers.SerializerMethodField()
    row_number = serializers.SerializerMethodField()  # new field added

    class Meta:
        model = CropPlanRow
        fields = (
            'id','row_number', 'user_crop_plan', 'date', 'day', 'stage',
            'action', 'created', 'updated', 'user', 'zone', 'crop'
        )

    def get_user(self, obj):
        return obj.user_crop_plan.user.id if obj.user_crop_plan.user else None

    def get_zone(self, obj):
        return obj.user_crop_plan.zone.id if obj.user_crop_plan.zone else None

    def get_crop(self, obj):
        return obj.user_crop_plan.crop.crop_name if obj.user_crop_plan.crop else None

    def get_row_number(self, obj):
        rows = CropPlanRow.objects.filter(
            user_crop_plan=obj.user_crop_plan
        ).order_by('id').values_list('id', flat=True)

        try:
            return list(rows).index(obj.id) + 1  # 1-based index
        except ValueError:
            return None

    def to_representation(self, instance):
        data = super().to_representation(instance)

        action = data.get("action")
        if action is None or str(action).strip().lower() == "nan":
            data["action"] = "No action is set for today"

        return data