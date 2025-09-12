from django.db import models
from accounts.models import *
from crops.models import *

class Nudges(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    crop_plan_row = models.ForeignKey('crops.CropPlanRow', on_delete=models.CASCADE, related_name='budgetings')
    zone = models.ForeignKey('farmzone.Zone', on_delete=models.CASCADE, null=True, blank=True)
    crop = models.ForeignKey('crops.Crop', on_delete=models.CASCADE, null=True, blank=True)

    labour_estimation = models.JSONField(default=dict)
    machine_estimation = models.JSONField(default=dict)
    input_estimation = models.JSONField(default=dict)
    miscellaneous = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nudges for {self.crop_plan_row.stage} on {self.crop_plan_row.date}"


