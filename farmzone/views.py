from rest_framework import viewsets,permissions,status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Q
import requests
import json
import datetime
from .models import (
    Farm, Zone, ZoneType, SoilType, SoilData, 
    WeatherData, SatelliteImage, ThirdPartyAPIKey
)
from .serializers import (
    FarmSerializer, farmGeoserializer, FarmDashboardSerializer, 
    ZoneSerializer, ZoneGeoSerializer, ZoneTypeSerializer,
    SoilTypeSerializer, SoilDataSerializer, WeatherDataSerializer,
    SatelliteImageSerializer, ThirdPartyAPIKeySerializer
)
from .utils import get_api_key, fetch_soil_data,fetch_soil_data_for_zone, fetch_weather_data_for_farm, fetch_satellite_data
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.contrib.gis.db.models.functions import Area
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import calculate_area_hectares
from .serializers import*



class FarmViewSet(viewsets.ModelViewSet):
    """api endpoint for managing farms."""
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer
    permission_classes = [IsAuthenticated]
    
    
    def get_queryset(self):
        """
        This view should return a list of all farms for currently authenticated user.
        Admin users can see all farms.
        """
        # return Farm.objects.all()
    
        user = self.request.user
        qs = Farm.objects.all()
        if not user.is_staff:
            qs = qs.filter(owner=user)
        return qs.annotate(area_m2=Area("boundary"))
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'geo_json':
            return farmGeoserializer
        elif self.action == 'dashboard':
            return FarmDashboardSerializer
        return  FarmSerializer
    
    @action(detail=True, methods=['get'])
    def geo_json(self, request, pk=None):
        """Return GeoJSON representation of the farm."""
        farm = self.get_object()
        serializer = self.get_serializer(farm)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Return all data needed for farm dashboard"""
        farm = self.get_object()
        serializer = self.get_serializer(farm)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_boundary(self, request, pk=None):
        """Upload and update farm boundary from GeoJSON."""
        farm = self.get_object()
        try:
            geojson = request.data.get('geojson')
            if not geojson:
                return Response({'error':'GeoJSON data is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            #convert GeoJSON to multipolygon
            geometry = GEOSGeometry(json.dumps(geojson))
            if geometry.geom_type != 'MultiPolygon':
                if geometry.geom_type == 'Polygon':
                    #convert polygon to multipolygon
                    geometry = GEOSGeometry(f'MULTIPOLYGON((({geometry.wkt})))')
                else:
                    return Response({'error':f'unsupported geometry type: {geometry.geom_type}'},
                                    status=status.HTTP_400_BAD_REQUEST)
            
            farm.boundary = geometry
            farm.save()
            return Response(FarmSerializer(farm).data)
        except Exception as e:
            return Response({'error':str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=['post'])
    def fetch_environmental_data(self, request, pk=None):
        """Fetch soil, weather, and satellite data for a farm."""
        farm = self.get_object()
        try:
            soil_data = fetch_soil_data(farm)  # This loops through zones
            weather_data = fetch_weather_data_for_farm(farm)
            satellite_image = fetch_satellite_data(farm)

            return Response({
                'soil_data': [SoilDataSerializer(obj).data for obj in soil_data],
                'weather_data': WeatherDataSerializer(weather_data, many=True).data,
                'satellite_image': satellite_image  # Return image path
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        
class ZoneViewSet(viewsets.ModelViewSet):
    """API endpoint for managing zones"""
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter zones by farm if specified."""
        # return Zone.objects.all()
        queryset = Zone.objects.all()
        
        farm_id = self.request.query_params.get('farm',None)
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
            
        #check if user has access to the farm
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(farm__owner=user)
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'geo_json':
            return ZoneGeoSerializer
        return ZoneSerializer
    
    @action(detail=True, methods=['get'])
    def geo_json(self, request, pk=None):
        """Return GeoJSON representation of the zone."""
        zone = self.get_object()
        serializer = self.get_serializer(zone)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_boundary(self, request, pk=None):
        """Upload and update zone boundary from GeoJSON."""
        zone = self.get_object()
        try:
            geojson = request.data.get('geojson')
            if not geojson:
                return Response({'error':'GeoJSON data is required'},status=status.HTTP_400_BAD_REQUEST)
            
            #convert GeoJSON to polygon
            geometry = GEOSGeometry(json.dumps(geojson))
            if geometry.geom_type != 'Polygon':
                return Response({'error':f'Unsupported geometry type: {geometry.geom_type}. Expected Polygon.'},
                                status=status.HTTP_400_BAD_REQUEST)
                
            zone.boundary = geometry
            zone.save()
            return Response(ZoneSerializer(zone).data)
            
        except Exception as e:
            return Response({'error':str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=['post'])
    def fetch_soil_data(self, request, pk=None):
        """Fetch soil data for this zone using SoilGrids API."""
        zone = self.get_object()
        try:
            soil_data = fetch_soil_data_for_zone(zone)
            return Response(SoilDataSerializer(soil_data).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        

class ZoneTypeViewSet(viewsets.ModelViewSet):
    """API endpoint for managing zone types."""
    queryset = ZoneType.objects.all()
    serializer_class = ZoneTypeSerializer
    permission_classes = [IsAuthenticated]
    
    
class SoilTypeViewSet(viewsets.ModelViewSet):
    """API endpoint for managing soil types."""
    queryset = SoilType.objects.all()
    serializer_class = SoilTypeSerializer
    permission_classes = [IsAuthenticated]
    
    
class SoilDataViewSet(viewsets.ModelViewSet):
    """API endpoint for managing soil data."""
    queryset = SoilData.objects.all()
    serializer_class = SoilDataSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter soil data by zone or farm if specified."""
        queryset = SoilData.objects.all()
        zone_id = self.request.query_params.get('zone', None)
        farm_id = self.request.query_params.get('farm', None)  
        
        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)
        elif farm_id:
            queryset = queryset.filter(farm_id=farm_id)
            
        #check if user has access to farm
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(zone__farm__owner=user)
        
        return queryset


class WeatherDataViewSet(viewsets.ModelViewSet):
    """API endpoint for managing weather data."""
    queryset = WeatherData.objects.all()
    serializer_class = WeatherDataSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter weather data by farm if specified."""
        queryset = WeatherData.objects.all()
        farm_id = self.request.query_params.get('farm', None)
        
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        
        # Check if user has access to the farm
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(farm__owner=user)
        
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def fetch_weather(self, request):
        farm_id = request.data.get('farm_id')
        if not farm_id:
            return Response({'error': 'Farm ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            farm = Farm.objects.get(id=farm_id)
            weather_objs = fetch_weather_data_for_farm(farm)

            return Response({
                'forecast': WeatherDataSerializer(weather_objs, many=True).data
            })

        except Farm.DoesNotExist:
            return Response({'error': 'Farm not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class SatelliteImageViewSet(viewsets.ModelViewSet):
    """API endpoint for managing satellite images."""
    queryset = SatelliteImage.objects.all()
    serializer_class = SatelliteImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter satellite images by farm and date range."""
        queryset = SatelliteImage.objects.all()
        farm_id = self.request.query_params.get('farm')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        if start_date:
            queryset = queryset.filter(image_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(image_date__lte=end_date)

        return queryset

    @action(detail=False, methods=['post'])
    def fetch_satellite_imagery(self, request):
        farm_id = request.data.get('farm_id')
        if not farm_id:
            return Response({'error': 'Farm ID is required'}, status=400)

        try:
            farm = Farm.objects.get(id=farm_id)
            image_path = fetch_satellite_data(farm)
            return Response({'message': 'Image fetched', 'image_path': image_path})
        except Farm.DoesNotExist:
            return Response({'error': 'Farm not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class ThirdPartyAPIKeyViewSet(viewsets.ModelViewSet):
    """API endpoint for managing third-party API keys."""
    queryset = ThirdPartyAPIKey.objects.all()
    serializer_class = ThirdPartyAPIKeySerializer
    permission_classes = [IsAdminUser]  # Only admin users can manage API keys
    
    def create(self, request, *args, **kwargs):
        """Create a new API key."""
        # Add the API key from the request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(api_key=request.data.get('api_key'))
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update an API key."""
        instance = self.get_object()
        # Update the API key if provided
        if 'api_key' in request.data:
            instance.api_key = request.data.get('api_key')
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_area_view(request):
    """
    Accepts GeoJSON (Polygon or MultiPolygon)
    and returns calculated area_value + area_unit.
    Works for both Farm and Zone.
    """
    try:
        geojson = request.data.get("geojson")
        if not geojson:
            return Response({"error": "GeoJSON data is required"}, status=400)

        # Convert input to GEOSGeometry with SRID=4326
        geometry = GEOSGeometry(json.dumps(geojson), srid=4326)

        if geometry.geom_type not in ["Polygon", "MultiPolygon"]:
            return Response({"error": f"Unsupported geometry type: {geometry.geom_type}"}, status=400)

        # Calculate area in hectares
        area_ha = calculate_area_hectares(geometry)

        return Response({
            "coordinates": geojson.get("coordinates"),
            "area_value": round(area_ha, 2),
            "area_unit": "hectare"
        })
    except Exception as e:
        return Response({"error": str(e)}, status=400)

    
class SoilTestViewSet(viewsets.ModelViewSet):
    serializer_class = SoilTestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SoilTest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        zone = self.request.data.get("zone")
        crop = self.request.data.get("crop")

        if SoilTest.objects.filter(user=user, zone=zone, crop=crop).exists():
            raise serializers.ValidationError(
                {"error": "Soil test already exists for this user, zone and crop. Please delete it before uploading a new one."}
            )

        serializer.save(user=user)

    def perform_update(self, serializer):
      
        if serializer.instance.user != self.request.user:
            raise serializers.ValidationError({"error": "You cannot update this soil test."})
        serializer.save()

    def perform_destroy(self, instance):
     
        if instance.user != self.request.user:
            raise serializers.ValidationError({"error": "You cannot delete this soil test."})
        instance.delete()
        
    