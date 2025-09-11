from django.contrib.gis.db import models
from django.conf import settings
from crops.models import Crop
from accounts.models import CustomUser
import uuid
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.validation import make_valid
from pyproj import Geod, CRS, Transformer
import json


def calculate_area_hectares(geometry):
    """
    Calculate farm area in hectares.
    - Uses local UTM projection for small parcels (< 10 ha)
    - Uses geodesic method (WGS84 ellipsoid) for larger parcels
    """
    geod = Geod(ellps="WGS84")

    # Convert GEOSGeometry → Shapely
    shapely_geom = shape(json.loads(geometry.geojson))
    shapely_geom = make_valid(shapely_geom)

    # --- Step 1: Geodesic area (always safe globally)
    geod_area, _ = geod.geometry_area_perimeter(shapely_geom)
    geod_area_ha = abs(geod_area) / 10000

    # --- Step 2: UTM-based area (better for small parcels)
    centroid = shapely_geom.centroid
    lon, lat = centroid.x, centroid.y

    # Pick UTM zone dynamically
    utm_zone = (int((lon + 180) / 6) % 60) + 1
    utm_crs = CRS.from_proj4(f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs")
    wgs84 = CRS.from_epsg(4326)

    transformer = Transformer.from_crs(wgs84, utm_crs, always_xy=True)

    def transform_coords(coords):
        return [transformer.transform(x, y) for x, y in coords]

    if shapely_geom.geom_type == "Polygon":
        exterior = transform_coords(shapely_geom.exterior.coords)
        interiors = [transform_coords(ring.coords) for ring in shapely_geom.interiors]
        utm_poly = Polygon(exterior, interiors)
        utm_area_ha = abs(utm_poly.area) / 10000
    elif shapely_geom.geom_type == "MultiPolygon":
        utm_area_ha = 0
        for poly in shapely_geom.geoms:
            exterior = transform_coords(poly.exterior.coords)
            interiors = [transform_coords(ring.coords) for ring in poly.interiors]
            utm_poly = Polygon(exterior, interiors)
            utm_area_ha += abs(utm_poly.area) / 10000
    else:
        return geod_area_ha  # fallback

    # --- Decision: pick UTM for small parcels, geod for large
    if geod_area_ha < 10:  # threshold in hectares
        return utm_area_ha
    return geod_area_ha


AREA_UNITS = [
        ("hectare", "Hectare"),
        ("acre", "Acre"),
        ("cent", "Cent"),
    ]


class Farm(models.Model):
    """model representing a farm entity"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True,null=True)
    boundary = models.MultiPolygonField(srid=4326, geography=True)
    area_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    area_unit = models.CharField(max_length=20, choices=AREA_UNITS, default="hectare")
    address = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='farms')
    elevation = models.FloatField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.boundary:
            try:
                # Only calculate if area_value was not provided
                if self.area_value is None:
                    self.area_value = calculate_area_hectares(self.boundary)
            except Exception as e:
                if self.area_value is None:  # keep manual if user set
                    self.area_value = None
                print(f"Area calculation failed: {e}")
        super().save(*args, **kwargs)






class ZoneType(models.Model):
    """model representing different types of zones"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    

class Zone(models.Model):
    """model representing a specific zone within a farm"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='zones')
    # zone_type = models.ForeignKey(ZoneType, on_delete=models.CASCADE, related_name='zones')
    # crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True, blank=True, related_name='zones')
    crops = models.ManyToManyField(Crop, related_name='zones', blank=True)
    boundary = models.PolygonField(geography=True)
    area_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    area_unit = models.CharField(max_length=20, choices=AREA_UNITS, default="hectare")
    description = models.TextField(blank=True,null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.farm.name}"
    
    @property
    def zone_color(self):
        first_crop = self.crops.first()
        return first_crop.color if first_crop else "#382AFF" 
    
    def save(self, *args, **kwargs):
        if self.boundary:
            try:
                # Only calculate if area_value was not provided
                if self.area_value is None:
                    self.area_value = calculate_area_hectares(self.boundary)
            except Exception as e:
                if self.area_value is None:  # keep manual if user set
                    self.area_value = None
                print(f"Area calculation failed: {e}")
        super().save(*args, **kwargs)


        

class SoilType(models.Model):
    """model representing soil type information"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    texture = models.CharField(max_length=100, blank=True, null=True)
    ph_min = models.FloatField(blank=True, null=True)
    ph_max = models.FloatField(blank=True, null=True)
    organic_matter_percentage = models.FloatField(blank=True, null=True)
    drainage_rate = models.CharField(max_length=50,blank=True, null=True)
    water_holding_capacity = models.FloatField(blank=True,null=True)
    
    def __str__(self):
        return self.name
    

class SoilData(models.Model):
    """model representing soil data for a specific zone"""
    zone = models.ForeignKey(Zone,on_delete=models.CASCADE, related_name='soil_data')
    soil_type = models.ForeignKey(SoilType,on_delete=models.CASCADE)
    ph_value = models.FloatField(blank=True, null=True)
    organic_matter = models.FloatField(blank=True, null=True)
    nitrogen = models.FloatField(blank=True, null=True)
    phosphorus = models.FloatField(blank=True, null=True)
    potassium = models.FloatField(blank=True, null=True)
    sand_percentage = models.FloatField(blank=True, null=True)
    silt_percentage = models.FloatField(blank=True, null=True)
    clay_percentage = models.FloatField(blank=True, null=True)
    cec = models.FloatField(blank=True, null=True)
    ec = models.FloatField(blank=True, null=True)
    data_source = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"soil data for {self.zone.name}"
    

class WeatherData(models.Model):
    """model for storing weather data for a farm"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE,related_name='weather_data')
    date = models.DateField()
    temperature_min = models.FloatField(blank=True, null=True)
    temperature_max = models.FloatField(blank=True, null=True)
    temperature_avg = models.FloatField(blank=True, null=True)
    humidity = models.FloatField(blank=True, null=True)
    precipitation = models.FloatField(blank=True, null=True)
    wind_speed = models.FloatField(blank=True, null=True)
    wind_direction = models.CharField(max_length=50, blank=True, null=True)
    cloud_cover = models.FloatField(blank=True, null=True)
    solar_radiation = models.FloatField(blank=True, null=True)
    evapotranspiration = models.FloatField(blank=True, null=True)
    data_source = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('farm', 'date') 
    
    def __str__(self):
        return f"weather data for {self.farm.name} on {self.date}"
    

class SatelliteImage(models.Model):
    """model for storing satellite imagery data"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='satellite_images')
    image_url = models.URLField()
    image_date = models.URLField()
    satellite_name = models.CharField(max_length=100)
    cloud_cover_percentage = models.FloatField(blank=True, null=True)
    resolution = models.CharField(max_length=50, blank=True, null=True)
    bands = models.CharField(max_length=255, blank=True, null=True)
    ndvi_avg = models.FloatField(blank=True, null=True) 
    evi_avg = models.FloatField(blank=True,null=True)
    data_source = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"satellite image for {self.farm.name} on {self.image_date}"
    
    
class ThirdPartyAPIKey(models.Model):
    """model for storing API keys for third-party services."""
    service_name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=255)
    api_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at =models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.service_name} API key"
    
    
class SoilTest(models.Model):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    zone = models.ForeignKey('farmzone.Zone', on_delete=models.CASCADE)
    crop = models.ForeignKey('crops.Crop', on_delete=models.CASCADE)
    soil_test = models.FileField(upload_to='soil_tests/', null=True, blank=True)  
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'zone', 'crop')  # ✅ Only one soil test per user-zone-crop
        verbose_name = "Soil Test"
        verbose_name_plural = "Soil Tests"
