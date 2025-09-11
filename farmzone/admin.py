from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from .models import (
    Farm, Zone, ZoneType, SoilType, SoilData, 
    WeatherData, SatelliteImage, ThirdPartyAPIKey
)


@admin.register(Farm)
class FarmAdmin(LeafletGeoAdmin):
    list_display = ('name', 'owner', 'area_value', 'area_unit',  'created_at')
    search_fields = ('name', 'owner__username')
    list_filter = ('created_at',)
    readonly_fields = ('area_value', 'area_unit',)


@admin.register(Zone)
class ZoneAdmin(LeafletGeoAdmin):
    list_display = ('name', 'farm', 'get_crops', 'area_value', 'area_unit',  'active')
    search_fields = ('name', 'farm__name')
    list_filter = ('active', 'created_at')
    readonly_fields = ('area_value', 'area_unit',)
    
    def get_crops(self, obj):
        return ", ".join([crop.crop_name for crop in obj.crops.all()])
    get_crops.short_description = "Crops"


@admin.register(ZoneType)
class ZoneTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(SoilType)
class SoilTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'texture', 'ph_min', 'ph_max')
    search_fields = ('name',)


@admin.register(SoilData)
class SoilDataAdmin(admin.ModelAdmin):
    list_display = ('zone', 'soil_type', 'ph_value', 'created_at', 'data_source')
    search_fields = ('zone__name', 'zone__farm__name')
    list_filter = ('soil_type', 'data_source', 'created_at')


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ('farm', 'date', 'temperature_min', 'temperature_max', 'precipitation', 'data_source')
    search_fields = ('farm__name',)
    list_filter = ('date', 'data_source')


@admin.register(SatelliteImage)
class SatelliteImageAdmin(admin.ModelAdmin):
    list_display = ('farm', 'image_date', 'satellite_name', 'cloud_cover_percentage', 'ndvi_avg')
    search_fields = ('farm__name',)
    list_filter = ('image_date', 'satellite_name', 'data_source')


@admin.register(ThirdPartyAPIKey)
class ThirdPartyAPIKeyAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'is_active', 'created_at')
    search_fields = ('service_name',)
    list_filter = ('is_active', 'service_name')
    exclude = ('api_key',)  # Don't show API key in the list view for security
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('api_key',)
        return self.readonly_fields

# admin.py
from django.contrib import admin
from .models import SoilTest

@admin.register(SoilTest)
class SoilTestAdmin(admin.ModelAdmin):
    list_display = ('user', 'zone', 'crop', 'soil_test', 'uploaded_at')
    list_filter = ('zone', 'crop', 'uploaded_at')
    search_fields = ('user__username', 'user__phone_number', 'crop__crop_name', 'zone__zone_name')
    ordering = ('-uploaded_at',)
