from django.db import models
from accounts.models import CustomUser
from crops.models import *


class Nudges(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='nudges_labour_details'
    )
    crop_plan_row = models.ForeignKey(
        'crops.CropPlanRow', on_delete=models.CASCADE, related_name='nudges_labour_estimations'
    )
    zone = models.ForeignKey(
        'farmzone.Zone', on_delete=models.CASCADE, null=True, blank=True, related_name='nudges_labour_zones'
    )
    crop = models.ForeignKey(
        'crops.Crop', on_delete=models.CASCADE, null=True, blank=True, related_name='nudges_labour_crops'
    )

    male_labour_cost = models.FloatField(default=0.0)
    male_labour_count = models.IntegerField(default=0)
    female_labour_cost = models.FloatField(default=0.0)
    female_labour_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nudges for {self.crop_plan_row.stage} on {self.crop_plan_row.date}"







class NudgesMachine(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='nudges_machine_details'
    )
    crop_plan_row = models.ForeignKey(
        'crops.CropPlanRow', on_delete=models.CASCADE, related_name='nudges_machine_estimations'
    )
    zone = models.ForeignKey(
        'farmzone.Zone', on_delete=models.CASCADE, null=True, blank=True, related_name='nudges_machine_zones'
    )
    crop = models.ForeignKey(
        'crops.Crop', on_delete=models.CASCADE, null=True, blank=True, related_name='nudges_machine_crops'
    )
    name = models.ForeignKey(
        'masterdata.MachineRegistration',  # adjust app name if different
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nudges_machine_entries'
    )

    machine_count = models.IntegerField(default=0)
    working_hours = models.FloatField(default=0.0)
    rate_per_hour = models.FloatField(default=0.0)
    total_machine_cost = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-calculate total machine cost
        self.total_machine_cost = self.machine_count * self.working_hours * self.rate_per_hour
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Machine Estimation for {self.crop_plan_row.stage} on {self.crop_plan_row.date}"
class NudgesInput(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='nudges_input_details'
    )
    crop_plan_row = models.ForeignKey(
        'crops.CropPlanRow', on_delete=models.CASCADE, related_name='nudges_input_estimations'
    )
    zone = models.ForeignKey(
        'farmzone.Zone', on_delete=models.CASCADE, null=True, blank=True, related_name='nudges_input_zones'
    )
    crop = models.ForeignKey(
        'crops.Crop', on_delete=models.CASCADE, null=True, blank=True, related_name='nudges_input_crops'
    )
    name = models.ForeignKey(
        'masterdata.InputMaster',  # adjust app name if different
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nudges_input_entries'
    )

    input_quantity = models.FloatField(default=0.0)
    input_cost = models.FloatField(default=0.0)
    total_input_cost = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-calculate total input cost
        self.total_input_cost = self.input_quantity * self.input_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Input Estimation for {self.crop_plan_row.stage} on {self.crop_plan_row.date}"


#####################
from django.db import models
from accounts.models import CustomUser  # adjust if needed


class Phase(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SubPhase(models.Model):
    phase = models.ForeignKey(
        Phase, on_delete=models.CASCADE, related_name='subphases'
    )
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('phase', 'name')

    def __str__(self):
        return f"{self.phase.name} - {self.name}"


class NudgesPhase(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='nudges_phase_details'
    )
    crop_plan_row = models.ForeignKey(
        'crops.CropPlanRow', on_delete=models.CASCADE, related_name='nudges_phase_estimations'
    )
    zone = models.ForeignKey(
        'farmzone.Zone', on_delete=models.CASCADE, null=True, blank=True, related_name='nudges_phase_zones'
    )
    crop = models.ForeignKey(
        'crops.Crop', on_delete=models.CASCADE, null=True, blank=True, related_name='nudges_phase_crops'
    )
    phase = models.ForeignKey(
        Phase, on_delete=models.CASCADE, related_name='nudges_phases'
    )
    subphase = models.ForeignKey(
        SubPhase, on_delete=models.CASCADE, null=True, blank=True, related_name='nudges_subphases'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        subphase_name = self.subphase.name if self.subphase else "No Subphase"
        return f"{self.phase.name} ({subphase_name}) - {self.user.phone_number}"
