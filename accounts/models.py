from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.db import models
from django.utils import timezone
from datetime import timedelta, date

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number must be provided.")
        if not password:
            raise ValueError("MPIN must be provided.")

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        # Expect 'mpin' to be passed from command line
        mpin = extra_fields.pop('password', None)

        return self.create_user(phone_number, password=mpin, **extra_fields)



class CustomUser(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    unverified_phone_number = models.CharField(max_length=15, blank=True, null=True)
    user_type = models.CharField(max_length=20)
    fcm_token = models.CharField(max_length=255, null=True, blank=True, help_text="Firebase Cloud Messaging token")
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email', 'name', 'user_type']  # You can remove any if optional

    objects = UserManager()

    def is_otp_valid(self):
        if not self.otp_created_at:
            return False
        expiration_time = self.otp_created_at + timedelta(minutes=10)
        return timezone.now() <= expiration_time

    def __str__(self):
        return self.phone_number or f"User {self.id}"

