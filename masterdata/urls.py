from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'machine-types', MachineTypeViewSet, basename='machinetype')

urlpatterns = [
    # ---------------- Machine ----------------
    path('machines/', MachineRegistrationListCreateAPIView.as_view(), name='machine-list-create'),
    path('machines/<int:pk>/', MachineRegistrationDetailView.as_view(), name='machine-detail'),

    # ---------------- Input ----------------
    path('input-categories/', InputCategoryListCreateAPIView.as_view(), name='input-category-list-create'),
    path('input-subcategories/', InputSubCategoryListCreateAPIView.as_view(), name='input-subcategory-list-create'),
    path('inputs/', InputView.as_view(), name='input-list-create'),

    # ---------------- Input Master ----------------
    path('input-masters/', InputMasterListCreateAPIView.as_view(), name='input-master-list-create'),
    path('input-masters/<int:pk>/', InputMasterDetailView.as_view(), name='input-master-detail'),

    # ---------------- Router ----------------
    path('', include(router.urls)),
]
