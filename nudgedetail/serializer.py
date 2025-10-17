from rest_framework import serializers
from .models import Nudges
from masterdata.models import *

from .models import NudgesMachine

from .models import NudgesInput



from .models import Phase, SubPhase, NudgesPhase

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



class NudgesMachineSerializer(serializers.ModelSerializer):
    # Optional: to show machine registration details
    name_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NudgesMachine
        fields = [
            'id',
            'user',
            'zone',
            'crop',
            'name',              # ✅ Added
            'name_detail',       # ✅ Optional read-only detail
            'machine_count',
            'working_hours',
            'rate_per_hour',
            'total_machine_cost',
            'created_at',
        ]
        read_only_fields = ['total_machine_cost', 'created_at', 'user']

    def get_name_detail(self, obj):
        if obj.name:
            return {
                "machine_type": str(obj.name.name),  # MachineType object
                "registration_number": obj.name.registration_number,
            }
        return None





class NudgesInputSerializer(serializers.ModelSerializer):
    name = serializers.PrimaryKeyRelatedField(
        queryset=InputMaster.objects.all(), required=False, allow_null=True
    )
    name_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NudgesInput
        fields = [
            'id', 'user', 'zone', 'crop', 'name', 'name_detail',
            'input_quantity', 'input_cost', 'total_input_cost', 'created_at'
        ]
        read_only_fields = ['total_input_cost', 'created_at', 'user']

    def get_name_detail(self, obj):
        if obj.name:  # InputMaster instance
            input_obj = obj.name.name  # This is Input instance
            return {
                "id": obj.name.id,
                "input_name": input_obj.name if input_obj else None,
                "unit": input_obj.get_unit_display() if input_obj else None,
                "category": input_obj.category.name if input_obj and input_obj.category else None
            }
        return None

    def to_representation(self, instance):
        """Ensure all objects in output are JSON serializable."""
        data = super().to_representation(instance)
        # Make sure `name` is an ID, not a model object
        if instance.name:
            data['name'] = instance.name.id
        return data





class SubPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubPhase
        fields = ['id', 'name', 'phase']


class PhaseSerializer(serializers.ModelSerializer):
    subphases = SubPhaseSerializer(many=True, read_only=True)

    class Meta:
        model = Phase
        fields = ['id', 'name', 'subphases']


class NudgesPhaseSerializer(serializers.ModelSerializer):
    phase_name = serializers.CharField(source='phase.name', read_only=True)
    subphase_name = serializers.CharField(source='subphase.name', read_only=True)

    class Meta:
        model = NudgesPhase
        fields = [
            'id',

            'zone',
            'crop',
            'phase',
            'phase_name',
            'subphase',
            'subphase_name',
            'created_at'
        ]

