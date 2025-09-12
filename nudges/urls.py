from django.urls import path
from . import views
from .views import *


urlpatterns = [
    path('nudges-cost/', NudgesView.as_view(), name='nudge-cost'),
    path('nudges-cost-report/', NudgesViewSupervisor.as_view(), name='nudge-cost-summary'),
    path('today-activity/', TodayCropPlanActivityAPIView.as_view(), name='today-crop-plan-activity')
]