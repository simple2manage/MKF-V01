from rest_framework import serializers
from .models import *
from masterdata.models import MachineRegistration, InputMaster
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

    # ---------------- VALIDATIONS ---------------- #
    def validate_machine_estimation(self, value):
        """
        Validate that machines exist in user's MachineRegistration
        """
        user = self.context['request'].user
        machines = value.get('machines', [])
        for m in machines:
            if not MachineRegistration.objects.filter(id=m['machine_id'], user=user).exists():
                raise serializers.ValidationError(
                    f"Machine with id {m['machine_id']} does not belong to user."
                )
        return value

    def validate_input_estimation(self, value):
        """
        Validate that inputs exist in user's InputMaster
        """
        user = self.context['request'].user
        inputs = value.get('inputs', [])
        for i in inputs:
            if not InputMaster.objects.filter(id=i['input_id'], user=user).exists():
                raise serializers.ValidationError(
                    f"Input with id {i['input_id']} does not belong to user."
                )
        return value

    # ---------------- RESPONSE ENRICHMENT ---------------- #
    def to_representation(self, instance):
        """
        Expand machine_estimation and input_estimation with details.
        """
        rep = super().to_representation(instance)

        # ---- Expand machine details ---- #
        machine_data = rep.get("machine_estimation", {}).get("machines", [])
        expanded_machines = []
        for m in machine_data:
            try:
                machine = MachineRegistration.objects.get(
                    id=m["machine_id"], user=instance.user
                )
                expanded_machines.append({
                    "machine_id": m["machine_id"],
                    "machine_count": m.get("machine_count"),
                    "working_hours": m.get("working_hours"),
                    "rate_per_hour": m.get("rate_per_hour"),
                    "machine_details": {
                        "id": machine.id,
                        "name": machine.name.name,
                        "registration_number": machine.registration_number,
                        "image": machine.image.url if machine.image else None,
                    }
                })
            except MachineRegistration.DoesNotExist:
                expanded_machines.append(m)  # keep original if not found
        rep["machine_estimation"]["machines"] = expanded_machines

        # ---- Expand input details ---- #
        input_data = rep.get("input_estimation", {}).get("inputs", [])
        expanded_inputs = []
        for i in input_data:
            try:
                input_obj = InputMaster.objects.get(
                    id=i["input_id"], user=instance.user
                )
                expanded_inputs.append({
                    "input_id": i["input_id"],
                    "quantity": i.get("quantity"),
                    "unit_cost": i.get("unit_cost"),
                    "input_details": {
                        "id": input_obj.id,
                        "name": input_obj.name.name,
                    }
                })
            except InputMaster.DoesNotExist:
                expanded_inputs.append(i)
        rep["input_estimation"]["inputs"] = expanded_inputs

        return rep
