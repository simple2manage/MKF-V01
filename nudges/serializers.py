from rest_framework import serializers
from .models import *
from crops.serializer import *

class NudgesSerializer(serializers.ModelSerializer):
    stage_name = serializers.CharField(source='crop_plan_row.stage', read_only=True)
    action_name = serializers.CharField(source='crop_plan_row.action', read_only=True)
    zone_name = serializers.SerializerMethodField()
    crop_name = serializers.SerializerMethodField()

    class Meta:
        model = Nudges
        fields = [
            'id',
            'crop_plan_row',
            'stage_name',
            'action_name',
            'zone',
            'zone_name',
            'crop',
            'crop_name',
            'labour_estimation',
            'machine_estimation',
            'input_estimation',
            'miscellaneous',
            'created_at',
        ]
        read_only_fields = [
            'stage_name',
            'action_name',
            'zone_name',
            'crop_name',
            'created_at',
        ]

    def get_zone_name(self, obj):
        return obj.zone.name if obj.zone else None

    def get_crop_name(self, obj):
        return obj.crop.crop_name if obj.crop else None