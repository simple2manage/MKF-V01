from django.urls import path
from . import views
from .views import *


urlpatterns = [

    path('nudges-cost-labor/', NudgesLaborVoiceView.as_view(), name='nudges-cost-labor'),

    path('nudges-cost-machine/', NudgesMachineVoiceView.as_view(), name='nudges-cost-machine'),
    path('nudges-cost-input/', NudgesInputVoiceView.as_view(), name='nudges-cost-input'),
    path('nudges-cost-labor-text/', NudgesView.as_view(), name='nudges-list-create'),
    path('nudges-cost-machine-text/', NudgesMachineView.as_view(), name='nudges-machine-list-create'),
    path('nudges-cost-input-text/', NudgesInputView.as_view(), name='nudges-input-list-create'),
    path('phases/', PhaseListAPIView.as_view(), name='phase-list'),
    path('nudges-phase/', NudgesPhaseAPIView.as_view(), name='nudges-phase'),
    path('nudges-phase-summary/', NudgesPhaseSummaryAPIView.as_view(), name='nudges-phase-summary'),
]