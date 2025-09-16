# masterdata/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MachineRegistrationListCreateAPIView, MachineRegistrationDetailView,
    InputViewSet, InputMasterListCreateAPIView, InputMasterDetailView, MachineTypeViewSet
)

router = DefaultRouter()
router.register(r'inputs', InputViewSet, basename='input')
router.register(r'machine-types', MachineTypeViewSet, basename='machinetype')

urlpatterns = [
    # Machine
    path('machines/', MachineRegistrationListCreateAPIView.as_view(), name='machine-list-create'),
    path('machines/<int:pk>/', MachineRegistrationDetailView.as_view(), name='machine-detail'),

    # Input Master
    path('input-masters/', InputMasterListCreateAPIView.as_view(), name='inputmaster-list-create'),
    path('input-masters/<int:pk>/', InputMasterDetailView.as_view(), name='inputmaster-detail'),

    # Input Items (lookup table)
    path('', include(router.urls)),
]
