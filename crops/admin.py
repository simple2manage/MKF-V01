from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.html import format_html
from .models import *


class CustomAdminFileWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        result = []
        print("value", value)
        if value:
            result.append(
                f'''<a href="{value.url}" target="_blank">
                      <img 
                        src="{value.url}" alt="{value}" 
                        width="100" height="100"
                        style="object-fit: cover;"\
                      />
                    </a>'''
            )
        result.append(super().render(name, value, attrs, renderer))
        return format_html("".join(result))


class CustomAdminFileWidgetAudio(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        result = []

        if value:
            result.append(
                f'''<a href="{value.url}" target="_blank">
                      <audio controls name="media"><source src="{value.url}" type="audio/mpeg"></audio>
                    </a>'''
            )

        result.append(super().render(name, value, attrs, renderer))
        return format_html("".join(result))

# admin.py

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    search_fields = ['crop_id', 'crop_name', 'created_by__username']
    list_display = ['crop_id', 'crop_name', 'created_by']

class CropPlanRowInline(admin.TabularInline):
    model = CropPlanRow
    extra = 1  # Number of empty rows for adding new
    fields = ('date', 'day', 'stage', 'action', 'created', 'updated','read')
    readonly_fields = ('created', 'updated')

@admin.register(UserCropPlan)
class UserCropPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'crop', 'start_date', 'crop_plan']
    search_fields = ['user__username', 'crop__crop_name']
    inlines = [CropPlanRowInline]

