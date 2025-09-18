from django.urls import path
from . import views
from .views import *
from django.conf import settings
from django.conf.urls.static import static



app_name = 'crops'

urlpatterns = [
    path('get-crop/', views.CropAPIView.as_view(),name='category'),
    path('zone-crops/', ZoneCropAPIView.as_view(), name='zone-crops'),
    path('user-crop-plan/',UserCropPlanAPIView.as_view(),name='crop-plan'),
    path('cropplan-row-create/',CropPlanRowListCreateView.as_view(),name='crop-plan-row-create'),
    path('cropplan-row-update/',CropPlanRowFlexibleUpdateView.as_view(),name='crop-plan-row-update'),
    path('user-crop-plan/<int:pk>/', UserCropPlanDeleteAPIView.as_view(), name='cropplan-delete'),
    path('send-crop-action/', SendCropPlanActionView.as_view(), name='send-crop-action')

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)