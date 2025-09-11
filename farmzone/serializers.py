from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer,GeometryField
from django.conf import settings
from crops.serializer import CropSerializer
from .models import *
from rest_framework.views import APIView



class ZoneTypeSerializer(serializers.ModelSerializer):
    """serializer for ZoneType model"""
    class Meta:
        model = ZoneType
        fields = ['id', 'name', 'description']
        
        
class SoilTypeSerializer(serializers.ModelSerializer):
    """serializer for SoilType model"""
    class Meta:
        model = SoilType
        fields = '__all__'
        
        
class SoilDataSerializer(serializers.ModelSerializer):
    """serializer for SoilData model"""
    soil_type_name = serializers.ReadOnlyField(source='soil_type.name')
    
    class Meta:
        model = SoilData
        fields = [
            'id', 'zone', 'soil_type', 'soil_type_name', 'ph_value',
            'organic_matter', 'nitrogen', 'phosphorus', 'potassium',
            'sand_percentage', 'silt_percentage', 'clay_percentage',
            'cec', 'ec', 'data_source', 'created_at', 'updated_at' 
        ]
        
        
class WeatherDataSerializer(serializers.ModelSerializer):
    """serializer for WeatherData model"""
    class Meta:
        model = WeatherData
        fields = '__all__'
        

class SatelliteImageSerializer(serializers.ModelSerializer):
    """serializer for SatelliteImage model"""
    image_url = serializers.SerializerMethodField()
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image_url and request:
            return request.build_absolute_uri(settings.MEDIA_URL + obj.image_url.split('/')[-1])
        return None
    
    class Meta:
        model = SatelliteImage
        fields = '__all__'
        
        
class ZoneGeoSerializer(GeoFeatureModelSerializer):
    """GeoJSON serializer for Zone model"""
    # zone_type_name = serializers.ReadOnlyField(source='zone_type.name')
    crop_name = serializers.ReadOnlyField(source='crop.crop_name')
    farm_name = serializers.ReadOnlyField(source='farm.name')
    
    class Meta:
        model = Zone
        geo_fields = 'boundary'
        fields = [
            'id', 'name', 'farm', 'farm_name', 'crop', 'crop_name', 
            'area_value', 'area_unit', 'description', 'active',
            'created_at', 'updated_at'
        ]    
        
        
class ZoneSerializer(serializers.ModelSerializer):
    """serializer for zone model(without GeoJSON)"""
    # zone_type_name = serializers.ReadOnlyField(source='zone_type.name')
    # crop_name = serializers.ReadOnlyField(source='crop.crop_name')
    crop_names = serializers.SerializerMethodField()
    soil_data = SoilDataSerializer(many=True, read_only=True)
    boundary = GeometryField()
    area_value = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, allow_null=True)    
    zone_color = serializers.ReadOnlyField()
    class Meta:
        model = Zone
        fields = [
            'id', 'name', 'farm', 'crops', 'crop_names', 'boundary',
            'area_value', 'area_unit', 'description', 'active', 'soil_data', 
            'created_at', 'updated_at',
            'zone_color'
        ]
        
    def get_crop_names(self, obj):
        return [crop.crop_name for crop in obj.crops.all()]
        

class farmGeoserializer(GeoFeatureModelSerializer):
    """GeoJSON serializer for farm model."""
    owner_name = serializers.ReadOnlyField(source='owner.username')
    
    class Meta:
        model = Farm
        geo_field = 'boundary'
        fields = [
            'id', 'name', 'description', 'area_value', 'area_unit',
            'address', 'owner', 'owner_name', 'elevation',
            'created_at', 'updated_at'
        ]
        

class FarmSerializer(serializers.ModelSerializer):
    """serializers for Farm model with related zones."""
    zones = ZoneSerializer(many=True, read_only=True)
    owner_name = serializers.ReadOnlyField(source='owner.username')
    boundary = GeometryField()
    area_value = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, allow_null=True)       
    class Meta:
        model = Farm
        fields = [
            'id', 'name', 'description', 'boundary', 'area_value', 'area_unit',
            'address', 'owner', 'owner_name', 'elevation', 'zones',
            'created_at', 'updated_at'
        ] 
    

class FarmDashboardSerializer(serializers.ModelSerializer):
    """serializer for farm model with all related data for dashboard."""
    zones = ZoneSerializer(many=True, read_only=True)
    weather_data = serializers.SerializerMethodField()
    satellite_images = serializers.SerializerMethodField()
    owner_name = serializers.ReadOnlyField(source='owner.username')
    boundary = GeometryField()
    
    class Meta:
        model = Farm
        fields = [
            'id', 'name', 'description', 'boundary', 'area_value', 'area_unit',
            'address', 'owner', 'owner_name', 'elevation', 'zones',
            'weather_data', 'satellite_images', 'created_at', 'updated_at'
        ]
        
    def get_weather_data(self,obj):
        """get the latest weather data for the farm."""
        latest_weather = obj.weather_data.order_by('-date').first()
        if latest_weather:
            return WeatherDataSerializer(latest_weather).data
        return None
    
    def get_satellite_images(self,obj):
        """get the latest satellite image for the farm."""
        latest_image = obj.satellite_images.order_by('-image_date').first()
        if latest_image:
            return SatelliteImageSerializer(latest_image).data
        return None
    

class ThirdPartyAPIKeySerializer(serializers.ModelSerializer):
    """serializer for ThirdPartyAPIKey model"""
    class Meta:
        model = ThirdPartyAPIKey
        fields = ['id', 'service_name', 'api_url', 'is_active', 'created_at', 'updated_at']
class SoilTestSerializer(serializers.ModelSerializer):
    crop = serializers.PrimaryKeyRelatedField(queryset=Crop.objects.all(), write_only=True)
    crop_details = CropSerializer(source='crop', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    # File upload
    soil_test = serializers.FileField(write_only=True, required=True)
    # Explicit URL for response
    soil_test_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SoilTest
        fields = ('id', 'user', 'zone', 'crop', 'crop_details', 'soil_test', 'soil_test_url', 'uploaded_at')

    def validate(self, data):
        request = self.context.get("request")
        user = request.user
        if SoilTest.objects.filter(user=user, zone=data["zone"], crop=data["crop"]).exists():
            raise serializers.ValidationError(
                "Soil test already exists for this user, zone and crop. Please delete it before uploading a new one."
            )
        return data

    def get_soil_test_url(self, obj):
        if obj.soil_test and hasattr(obj.soil_test, 'url'):
            return f"https://apiserver.matsolutions.in:8091{obj.soil_test.url}"
        return None

     
# class SoilTestSerializer(serializers.ModelSerializer):
#     crop = serializers.PrimaryKeyRelatedField(queryset=Crop.objects.all(), write_only=True)
#     crop_details = CropSerializer(source='crop', read_only=True)
#     user = serializers.PrimaryKeyRelatedField(read_only=True)
#     soil_test = serializers.SerializerMethodField()  

#     class Meta:
#         model = SoilTest
#         fields = ('id', 'user', 'zone', 'crop', 'crop_details', 'soil_test', 'uploaded_at')

#     def validate(self, data):
#         request = self.context.get("request")
#         user = request.user 

#         if SoilTest.objects.filter(user=user, zone=data["zone"], crop=data["crop"]).exists():
#             raise serializers.ValidationError(
#                 "Soil test already exists for this user, zone and crop. Please delete it before uploading a new one."
#             )
#         return data
    
#     def get_soil_test(self, obj):
#         if obj.soil_test and hasattr(obj.soil_test, 'url'):
#             return f"https://apiserver.matsolutions.in:8091{obj.soil_test.url}"
#         return None