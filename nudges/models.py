from django.db import models

from crops.models import *




def default_labour():
    return {"data": {}, "is_read": False}

def default_machine():
    return {"data": {}, "is_read": False}

def default_input():
    return {"data": {}, "is_read": False}

def default_miscellaneous():
    return {"data": 0.0, "is_read": False}
class Nudges(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    crop_plan_row = models.ForeignKey('crops.CropPlanRow', on_delete=models.CASCADE, related_name='budgetings')
    zone = models.ForeignKey('farmzone.Zone', on_delete=models.CASCADE, null=True, blank=True)
    crop = models.ForeignKey('crops.Crop', on_delete=models.CASCADE, null=True, blank=True)

    labour_estimation = models.JSONField(default=default_labour)
    machine_estimation = models.JSONField(default=default_machine)
    input_estimation = models.JSONField(default=default_input)
    miscellaneous = models.JSONField(default=default_miscellaneous)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nudges for {self.crop_plan_row.stage} on {self.crop_plan_row.date}"
