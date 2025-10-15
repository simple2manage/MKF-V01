from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Nudges)
from django.contrib import admin
from .models import NudgesMachine

@admin.register(NudgesMachine)
class NudgesMachineAdmin(admin.ModelAdmin):
    list_display = [
        "id", "user", "crop_plan_row", "zone", "crop",
        "machine_count", "working_hours", "rate_per_hour", "total_machine_cost", "created_at"
    ]
    list_filter = ["zone", "crop", "user"]
    search_fields = ["crop_plan_row__stage", "user__username"]

admin.site.register(NudgesInput)
admin.site.register(Phase)
admin.site.register(SubPhase)

admin.site.register(NudgesPhase)