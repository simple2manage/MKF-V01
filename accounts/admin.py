from django.contrib import admin
from .models import CustomUser

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'name', 'is_verified', 'user_type', 'otp')


admin.site.register(CustomUser, CustomUserAdmin)
