from django.db import connection
from django.conf import settings
from .models import NudgeStageImage
from django.core.exceptions import ObjectDoesNotExist

def reset_cropplanrow_id():
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE crops_cropplanrow RESTART IDENTITY CASCADE;")



# def get_icon_for_stage(stage_name):
#     try:
#         nudge_image = NudgeStageImage.objects.get(stage__iexact=stage_name)
#         return nudge_image.icon.url
#     except NudgeStageImage.DoesNotExist:
#         return settings.DEFAULT_NUDGE_ICON_URL


def get_icon_for_stage(stage_name, request=None):
    from .models import NudgeStageImage
    try:
        nudge_image = NudgeStageImage.objects.get(stage__iexact=stage_name)
        if request:
            return request.build_absolute_uri(nudge_image.icon.url)
        return nudge_image.icon.url  # fallback
    except ObjectDoesNotExist:
        if request:
            return request.build_absolute_uri(settings.DEFAULT_NUDGE_ICON_URL)
        return settings.DEFAULT_NUDGE_ICON_URL