from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import calculate_area_view  

router = DefaultRouter()
router.register(r'farms', views.FarmViewSet)
router.register(r'zones', views.ZoneViewSet)
router.register(r'zone-types', views.ZoneTypeViewSet)
router.register(r'soil-types', views.SoilTypeViewSet)
router.register(r'soil-data', views.SoilDataViewSet)
router.register(r'weather-data', views.WeatherDataViewSet)
router.register(r'satellite-images', views.SatelliteImageViewSet)
router.register(r'api-keys', views.ThirdPartyAPIKeyViewSet)
router.register(r'soil-tests', views.SoilTestViewSet, basename="soil-tests")  


urlpatterns = [
    path('', include(router.urls)),
    path("calculate-area/", calculate_area_view, name="calculate_area"),
]