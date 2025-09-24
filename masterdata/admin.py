from django.contrib import admin
from .models import *


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
@admin.register(InputMaster)
class InputMasterAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_input_name', 'get_user', 'created_at']
    search_fields = ['name__name', 'user__name', 'user__phone_number']

    def get_input_name(self, obj):
        return obj.name.name if obj.name else "No Input"
    get_input_name.admin_order_field = 'name'
    get_input_name.short_description = 'Input'

    def get_user(self, obj):
        if obj.user:
            return obj.user.name or obj.user.phone_number
        return "No User"
    get_user.admin_order_field = 'user'
    get_user.short_description = 'User'
    
    
@admin.register(Input)
class InputAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'subcategory')
    search_fields = ('name', 'category__name', 'subcategory__name')


@admin.register(InputCategory)
class InputCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name", "description")
    ordering = ("name",)


@admin.register(InputSubCategory)
class InputSubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "description", "created_at")
    search_fields = ("name", "description", "category__name")
    list_filter = ("category",)
    ordering = ("category__name", "name")