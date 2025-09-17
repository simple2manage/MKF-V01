from django.contrib import admin
from .models import MachineType, MachineRegistration, Input, InputMaster


# ------------------ Machine ------------------
@admin.register(MachineType)
class MachineTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(MachineRegistration)
class MachineRegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'registration_number', 'created_at')
    list_filter = ('created_at', 'name')
    search_fields = ('registration_number', 'name__name', 'user__username')
    autocomplete_fields = ('name',)   # ✅ removed 'user'


# ------------------ Input ------------------
@admin.register(Input)
class InputAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(InputMaster)
class InputMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'created_at')
    list_filter = ('created_at', 'name')
    search_fields = ('name__name', 'user__username')
    autocomplete_fields = ('name',)   # ✅ removed 'user'
