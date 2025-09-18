from django.db import models
from typing import Iterable, Optional
from accounts.models import CustomUser
from ckeditor.fields import RichTextField
from django.contrib.auth import get_user_model
from farmer import settings, utils

class Crop(models.Model):
    crop_id = models.CharField(max_length=255, null=True, blank=True)
    crop_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images/')
    color = models.CharField(max_length=7, default="#382AFF",null=True,blank=True)

    created_by = models.ForeignKey(CustomUser, blank=True, null=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)
    updated_by = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.crop_id = utils.random_string("CRCAT")
        super(Crop, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.crop_name)

    class Meta:
        verbose_name_plural = "Crop"


class UserCropPlan(models.Model):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    zone = models.ForeignKey('farmzone.Zone', on_delete=models.CASCADE)
    crop = models.ForeignKey('crops.Crop', on_delete=models.CASCADE)
    crop_plan = models.FileField(upload_to='crop_plans/', null=True, blank=True)
    start_date = models.DateField()

class CropPlanRow(models.Model):
    user_crop_plan = models.ForeignKey(UserCropPlan, related_name='plan_rows', on_delete=models.CASCADE)
    date = models.DateField()
    day = models.IntegerField()
    stage = models.CharField(max_length=255)
    action = models.TextField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    read = models.BooleanField(default=False)  # New field to mark as read

    def save(self, *args, **kwargs):
        if self.action and str(self.action).lower() == "nan":
            self.action = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.stage}"

    @property
    def user(self):
        return self.user_crop_plan.user

    @property
    def zone(self):
        return self.user_crop_plan.zone

    @property
    def crop(self):
        return self.user_crop_plan.crop

    class Meta:
        ordering = ['id']



class NudgeStageImage(models.Model):
    stage = models.CharField(max_length=100, unique=True)
    icon = models.ImageField(upload_to='nudge_stage_icons/')
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.stage
 