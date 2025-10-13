from rest_framework import serializers
from .models import Nudges


class NudgesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nudges
        fields = [
            'id',
            'user',
            'zone',
            'crop',
            'male_labour_cost',
            'male_labour_count',
            'female_labour_cost',
            'female_labour_count',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at','user']
from rest_framework import serializers
from .models import NudgesMachine

class NudgesMachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = NudgesMachine
        fields = [
            'id',
            'user',
            'zone',
            'crop',
            'machine_count',
            'working_hours',
            'rate_per_hour',
            'total_machine_cost',
            'created_at',
        ]
        read_only_fields = ['total_machine_cost', 'created_at','user']
from rest_framework import serializers
from .models import NudgesInput

class NudgesInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = NudgesInput
        fields = [
            'id',
            'user',
            'zone',
            'crop',
            'input_quantity',
            'input_cost',
            'total_input_cost',
            'created_at'
        ]
        read_only_fields = ['total_input_cost', 'created_at', 'user']
