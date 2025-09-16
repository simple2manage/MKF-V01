# masterdata/models.py
from django.db import models
from accounts.models import CustomUser


# ------------------ Machine Master ------------------
class MachineType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class MachineRegistration(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='machines')
    name = models.ForeignKey(MachineType, on_delete=models.CASCADE, related_name='registrations')

    registration_number = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='machine_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.registration_number or 'No Reg No'}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['registration_number'],
                name='unique_registration_number_not_null',
                condition=~models.Q(registration_number=None)
            )
        ]


# ------------------ Input Master ------------------
class Input(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class InputMaster(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='input')
    name = models.ForeignKey(Input, on_delete=models.CASCADE, related_name='input_masters')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)
