from rest_framework import serializers
from .models import *
from masterdata.models import *
from crops.serializer import *

# class NudgesSerializer(serializers.ModelSerializer):
#     stage_name = serializers.CharField(source='crop_plan_row.stage', read_only=True)
#     action_name = serializers.CharField(source='crop_plan_row.action', read_only=True)
#     zone_name = serializers.SerializerMethodField()
#     crop_name = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Nudges
#         fields = [
#             'id',
#             'crop_plan_row',
#             'stage_name',
#             'action_name',
#             'zone',
#             'zone_name',
#             'crop',
#             'crop_name',
#             'labour_estimation',
#             'machine_estimation',
#             'input_estimation',
#             'miscellaneous',
#             'created_at',
#         ]
#         read_only_fields = [
#             'stage_name',
#             'action_name',
#             'zone_name',
#             'crop_name',
#             'created_at',
#         ]
#
#     def get_zone_name(self, obj):
#         return obj.zone.name if obj.zone else None
#
#     def get_crop_name(self, obj):
#         return obj.crop.crop_name if obj.crop else None
#
#     # ---------------- VALIDATIONS ---------------- #
#     def validate_machine_estimation(self, value):
#         """
#         Validate that machines exist in user's MachineRegistration
#         """
#         user = self.context['request'].user
#         machines = value.get('machines', [])
#         for m in machines:
#             if not MachineRegistration.objects.filter(id=m['machine_id'], user=user).exists():
#                 raise serializers.ValidationError(
#                     f"Machine with id {m['machine_id']} does not belong to user."
#                 )
#         return value
#
#     def validate_input_estimation(self, value):
#         """
#         Validate that inputs exist in user's InputMaster
#         """
#         user = self.context['request'].user
#         inputs = value.get('inputs', [])
#         for i in inputs:
#             if not InputMaster.objects.filter(id=i['input_id'], user=user).exists():
#                 raise serializers.ValidationError(
#                     f"Input with id {i['input_id']} does not belong to user."
#                 )
#         return value
#
#     # ---------------- RESPONSE ENRICHMENT ---------------- #
#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#
#         # ---- Expand machine details ---- #
#         machine_data = rep.get("machine_estimation", {}).get("data", {}).get("machines", [])
#         expanded_machines = []
#         for m in machine_data:
#             try:
#                 machine = MachineRegistration.objects.get(
#                     id=m["machine_id"], user=instance.user
#                 )
#                 expanded_machines.append({
#                     "machine_id": m["machine_id"],
#                     "machine_count": m.get("machine_count"),
#                     "working_hours": m.get("working_hours"),
#                     "rate_per_hour": m.get("rate_per_hour"),
#                     "machine_details": {
#                         "id": machine.id,
#                         "name": machine.name.name,
#                         "registration_number": machine.registration_number,
#                         "image": machine.image.url if machine.image else None,
#                     }
#                 })
#             except MachineRegistration.DoesNotExist:
#                 expanded_machines.append(m)
#
#         if "machine_estimation" in rep:
#             rep["machine_estimation"]["machines"] = expanded_machines
#             rep["machine_estimation"].pop("data", None)  # remove raw data
#
#         # ---- Expand input details ---- #
#         input_data = rep.get("input_estimation", {}).get("data", {}).get("inputs", [])
#         expanded_inputs = []
#         for i in input_data:
#             try:
#                 input_obj = InputMaster.objects.get(
#                     id=i["input_id"], user=instance.user
#                 )
#                 expanded_inputs.append({
#                     "input_id": i["input_id"],
#                     "quantity": i.get("quantity"),
#                     "unit_cost": i.get("unit_cost") or i.get("cost_per_unit"),
#                     "input_details": {
#                         "id": input_obj.id,
#                         "name": input_obj.name.name,
#                         "category": input_obj.category_name,
#                         "subcategory": input_obj.subcategory_name,
#                         "unit": input_obj.unit_display,
#                         "form_type": input_obj.form_type_display,
#                         "description": input_obj.description,
#                         "image": input_obj.image.url if input_obj.image else None,
#                     }
#                 })
#             except InputMaster.DoesNotExist:
#                 expanded_inputs.append(i)
#
#         if "input_estimation" in rep:
#             rep["input_estimation"]["inputs"] = expanded_inputs
#             rep["input_estimation"].pop("data", None)  # remove raw data
#
#         return rep

from rest_framework import serializers


# Assuming MachineRegistration and InputMaster are imported or defined elsewhere
# from your models import MachineRegistration, InputMaster
# ... and CustomUser, CropPlanRow, Crop, Zone

##############################
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
        # Expecting the structure: {"data": {"machines": [...]}, "is_read": False}
        machines = value.get('data', {}).get('machines', [])
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
        # Expecting the structure: {"data": {"inputs": [...]}, "is_read": False}
        inputs = value.get('data', {}).get('inputs', [])
        for i in inputs:
            if not InputMaster.objects.filter(id=i['input_id'], user=user).exists():
                raise serializers.ValidationError(
                    f"Input with id {i['input_id']} does not belong to user."
                )
        return value

    # ---------------- RESPONSE ENRICHMENT ---------------- #
    def to_representation(self, instance):
        rep = super().to_representation(instance)

        # ---- Expand machine details ---- #
        machine_estimation = rep.get("machine_estimation", {})

        # 🛡️ Defense 1: Ensure machine_estimation is a dictionary
        if not isinstance(machine_estimation, dict):
            machine_estimation = {}

        machine_data_container = machine_estimation.get("data", {})

        # 🛡️ Defense 2: Ensure 'data' field is a dictionary (where the float error occurred)
        if not isinstance(machine_data_container, dict):
            machine_data_container = {}

        machine_data = machine_data_container.get("machines", [])
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
                expanded_machines.append(m)

        # Update the representation
        if "machine_estimation" in rep and isinstance(rep["machine_estimation"], dict):
            rep["machine_estimation"]["machines"] = expanded_machines
            rep["machine_estimation"].pop("data", None)  # remove raw data

        # ---- Expand input details ---- #
        input_estimation = rep.get("input_estimation", {})

        # 🛡️ Defense 3: Ensure input_estimation is a dictionary
        if not isinstance(input_estimation, dict):
            input_estimation = {}

        input_data_container = input_estimation.get("data", {})

        # 🛡️ Defense 4: Ensure 'data' field is a dictionary
        if not isinstance(input_data_container, dict):
            input_data_container = {}

        input_data = input_data_container.get("inputs", [])
        expanded_inputs = []

        for i in input_data:
            try:
                input_obj = InputMaster.objects.get(
                    id=i["input_id"], user=instance.user
                )
                expanded_inputs.append({
                    "input_id": i["input_id"],
                    "quantity": i.get("quantity"),
                    "unit_cost": i.get("unit_cost") or i.get("cost_per_unit"),
                    "input_details": {
                        "id": input_obj.id,
                        "name": input_obj.name.name,
                        "category": input_obj.category_name,
                        "subcategory": input_obj.subcategory_name,
                        "unit": input_obj.unit_display,
                        "form_type": input_obj.form_type_display,
                        "description": input_obj.description,
                        "image": input_obj.image.url if input_obj.image else None,
                    }
                })
            except InputMaster.DoesNotExist:
                expanded_inputs.append(i)

        # Update the representation
        if "input_estimation" in rep and isinstance(rep["input_estimation"], dict):
            rep["input_estimation"]["inputs"] = expanded_inputs
            rep["input_estimation"].pop("data", None)  # remove raw data

        return rep
#
# class NudgesVoiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Nudges
#         fields = ['labour_estimation', 'machine_estimation', 'input_estimation', 'miscellaneous', 'zone', 'crop']


# class NudgesVoiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Nudges
#         fields = [
#             'labour_estimation',
#             'machine_estimation',
#             'input_estimation',
#             'miscellaneous',
#             'zone',
#             'crop',
#         ]
#
#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#
#         # ---- Expand machine details ---- #
#         machine_estimation = rep.get("machine_estimation", {})
#         if not isinstance(machine_estimation, dict):
#             machine_estimation = {}
#
#         machine_data_container = machine_estimation.get("data", {})
#         if not isinstance(machine_data_container, dict):
#             machine_data_container = {}
#
#         machine_data = machine_data_container.get("machines", [])
#         expanded_machines = []
#
#         for m in machine_data:
#             try:
#                 machine = MachineRegistration.objects.get(
#                     id=m["machine_id"], user=instance.user
#                 )
#                 expanded_machines.append({
#                     "machine_id": m["machine_id"],
#                     "machine_count": m.get("machine_count"),
#                     "working_hours": m.get("working_hours"),
#                     "rate_per_hour": m.get("rate_per_hour"),
#                     "machine_name": machine.name.name,  # ✅ Only name (for voice)
#                 })
#             except MachineRegistration.DoesNotExist:
#                 expanded_machines.append(m)
#
#         if "machine_estimation" in rep and isinstance(rep["machine_estimation"], dict):
#             rep["machine_estimation"]["machines"] = expanded_machines
#             rep["machine_estimation"].pop("data", None)
#
#         # ---- Expand input details ---- #
#         input_estimation = rep.get("input_estimation", {})
#         if not isinstance(input_estimation, dict):
#             input_estimation = {}
#
#         input_data_container = input_estimation.get("data", {})
#         if not isinstance(input_data_container, dict):
#             input_data_container = {}
#
#         input_data = input_data_container.get("inputs", [])
#         expanded_inputs = []
#
#         for i in input_data:
#             try:
#                 input_obj = InputMaster.objects.get(
#                     id=i["input_id"], user=instance.user
#                 )
#                 expanded_inputs.append({
#                     "input_id": i["input_id"],
#                     "quantity": i.get("quantity"),
#                     "unit_cost": i.get("unit_cost") or i.get("cost_per_unit"),
#                     "input_name": input_obj.name.name,  # ✅ Only name (for voice)
#                 })
#             except InputMaster.DoesNotExist:
#                 expanded_inputs.append(i)
#
#         if "input_estimation" in rep and isinstance(rep["input_estimation"], dict):
#             rep["input_estimation"]["inputs"] = expanded_inputs
#             rep["input_estimation"].pop("data", None)
#
#         return rep


class NudgesVoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nudges
        fields = [
            'labour_estimation',
            'machine_estimation',
            'input_estimation',
            'miscellaneous',
            'zone',
            'crop',
        ]

    def _expand_estimation_field(self, rep, field_name, items_key, model_class):
        """
        Helper to process machine_estimation and input_estimation fields.
        - Extracts simple numeric cost if present (from voice).
        - Expands detailed lists (if present).
        - Removes the internal 'data' key.
        """
        estimation = rep.get(field_name, {})
        if not isinstance(estimation, dict):
            return

        # 1. Check for the single numeric value saved by the voice parser
        data_field = estimation.get("data")

        # The simple parser saves {'data': 300.0, 'is_read': True}
        if isinstance(data_field, (int, float)):
            # If it's a number, save it as a top-level 'cost' for the response
            estimation["cost"] = data_field
            # Note: We don't return yet, as it might also contain an empty 'inputs'/'machines' key

        # 2. Handle the detailed list structure (e.g., 'inputs' or 'machines')
        items_list = []
        if isinstance(data_field, dict):
            items_list = data_field.get(items_key, [])

        expanded_items = []

        if items_list and model_class:
            for item in items_list:
                item_id = item.get("machine_id" if field_name == "machine_estimation" else "input_id")
                try:
                    # Logic for fetching related object based on model_class
                    if field_name == "machine_estimation":
                        obj = model_class.objects.get(id=item_id, user=self.instance.user)
                        expanded_items.append({
                            "machine_id": item_id,
                            "machine_count": item.get("machine_count"),
                            "working_hours": item.get("working_hours"),
                            "rate_per_hour": item.get("rate_per_hour"),
                            "machine_name": obj.name.name,
                        })
                    elif field_name == "input_estimation":
                        obj = model_class.objects.get(id=item_id, user=self.instance.user)
                        expanded_items.append({
                            "input_id": item_id,
                            "quantity": item.get("quantity"),
                            "unit_cost": item.get("unit_cost") or item.get("cost_per_unit"),
                            "input_name": obj.name.name,
                        })
                except model_class.DoesNotExist:
                    expanded_items.append(item)

        # 3. Finalize the output structure
        if expanded_items:
            estimation[items_key] = expanded_items

        # 4. Remove the internal 'data' key that holds either the simple cost or the detailed structure
        estimation.pop("data", None)

        rep[field_name] = estimation

    def to_representation(self, instance):
        # NOTE: Ensure you have access to MachineRegistration and InputMaster models here
        # If they are not globally imported, they must be imported inside this method or defined.

        rep = super().to_representation(instance)

        # ------------------------------------------------------------------------------------------------
        # MACHINE ESTIMATION
        # Pass the representation dictionary, the field name, the key for the item list, and the related model
        self._expand_estimation_field(
            rep,
            "machine_estimation",
            "machines",
            MachineRegistration  # Model class
        )

        # ------------------------------------------------------------------------------------------------
        # INPUT ESTIMATION
        self._expand_estimation_field(
            rep,
            "input_estimation",
            "inputs",
            InputMaster  # Model class
        )

        # ------------------------------------------------------------------------------------------------
        # MISCELLANEOUS (Simple Cost Only - No Expansion Logic Needed)
        # This uses the same principle of extracting 'data' to 'cost'
        miscellaneous = rep.get("miscellaneous", {})
        if isinstance(miscellaneous, dict):
            cost_data = miscellaneous.get("data")
            if isinstance(cost_data, (int, float)):
                miscellaneous["cost"] = cost_data  # <-- Saved as 'cost'
            miscellaneous.pop("data", None)
            rep["miscellaneous"] = miscellaneous

        return rep