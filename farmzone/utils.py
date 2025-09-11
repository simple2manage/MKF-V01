import requests
import json
import datetime
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
from django.conf import settings
from collections import defaultdict
from django.core.exceptions import ObjectDoesNotExist
from .models import ThirdPartyAPIKey, SoilData, SoilType, WeatherData, SatelliteImage


def get_api_key(service_name):
    """Get API key for a specific service."""
    try:
        api_key_obj = ThirdPartyAPIKey.objects.get(service_name=service_name, is_active=True)
        return api_key_obj.api_key
    except ObjectDoesNotExist:
        return None



def fetch_soil_data_for_zone(zone):
    """Fetch and save soil data for a single zone from SoilGrids v2.0."""
    centroid = zone.boundary.centroid
    lat, lon = centroid.y, centroid.x
    print("Centroid lat/lon:", lat, lon)

    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon": lon,
        "lat": lat
    }
    headers = {
        "Accept": "application/json"
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error from SoilGrids API: {response.text}")

    full_data = response.json()
    layers = full_data.get('properties', {}).get('layers', [])

    def extract_mean(layers, property_name):
        try:
            for layer in layers:
                if layer['name'] == property_name:
                    # Use top layer (0–5 cm)
                    return layer['depths'][0]['values']['mean']
            return None
        except Exception as e:
            print(f"Error extracting {property_name}: {e}")
            return None

    ph = extract_mean(layers, 'phh2o')
    soc = extract_mean(layers, 'ocd')
    nitrogen = extract_mean(layers, 'nitrogen')
    clay = extract_mean(layers, 'clay')
    sand = extract_mean(layers, 'sand')
    silt = extract_mean(layers, 'silt')
    cec = extract_mean(layers, 'cec')

    # Default SoilType or create generic
    soil_type, _ = SoilType.objects.get_or_create(name="Generic")

    soil_data_obj, _ = SoilData.objects.update_or_create(
        zone=zone,
        defaults={
            'soil_type': soil_type,
            'ph_value': ph,
            'organic_matter': soc,
            'nitrogen': nitrogen,
            'sand_percentage': sand,
            'silt_percentage': silt,
            'clay_percentage': clay,
            'cec': cec,
            'data_source': 'SoilGrids',
        }
    )

    return soil_data_obj


def fetch_soil_data(farm):
    """Fetch and save soil data for all zones in a farm."""
    results = []
    for zone in farm.zones.all():
        try:
            soil = fetch_soil_data_for_zone(zone)
            results.append(soil)
        except Exception as e:
            # Optionally log the error
            continue
    return results




def fetch_weather_data_for_farm(farm):
    """Fetch 5-day weather forecast data for a farm using OpenWeatherMap (free tier)."""
    api_key = get_api_key('OpenWeatherMap')
    if not api_key:
        raise Exception('OpenWeatherMap API key not found')

    centroid = farm.boundary.centroid
    lat, lon = centroid.y, centroid.x

    url = 'https://api.openweathermap.org/data/2.5/forecast'
    params = {
        'lat': lat,
        'lon': lon,
        'units': 'metric',
        'appid': api_key
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f'Error from OpenWeatherMap API: {response.text}')

    data = response.json()
    forecasts = data.get('list', [])

    if not forecasts:
        raise Exception("No forecast data available")

    daily_data = defaultdict(list)

    for entry in forecasts:
        dt = datetime.datetime.fromtimestamp(entry['dt'])
        date_str = dt.date().isoformat()
        daily_data[date_str].append(entry)

    result = []
    today = datetime.date.today()

    for i, (date_str, entries) in enumerate(daily_data.items()):
        if i > 7:  # limit to next 7 days
            break

        temps = [e['main']['temp'] for e in entries]
        min_temp = min(temps)
        max_temp = max(temps)
        avg_temp = sum(temps) / len(temps)
        humidity = sum(e['main']['humidity'] for e in entries) // len(entries)
        wind_speed = sum(e['wind']['speed'] for e in entries) / len(entries)

        weather_obj, _ = WeatherData.objects.update_or_create(
            farm=farm,
            date=datetime.date.fromisoformat(date_str),
            defaults={
                'temperature_min': min_temp,
                'temperature_max': max_temp,
                'temperature_avg': avg_temp,
                'humidity': humidity,
                'precipitation': 0,  # free tier does not always have this
                'wind_speed': wind_speed,
                'data_source': 'OpenWeatherMap'
            }
        )

        result.append(weather_obj)

    return result


def get_sentinel_token():
    """Get OAuth access token from Sentinel Hub."""
    from dotenv import load_dotenv
    load_dotenv()
    import os

    client_id = os.getenv('SENTINEL_CLIENT_ID')
    client_secret = os.getenv('SENTINEL_CLIENT_SECRET')

    response = requests.post(
        'https://services.sentinel-hub.com/oauth/token',
        data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
    )

    if response.status_code != 200:
        raise Exception(f'Failed to get Sentinel token: {response.text}')

    return response.json()['access_token']


def save_ndvi_colormap_image(ndvi_array, farm_id, date_str):
    """Save NDVI array as color image using colormap."""
    output_dir = Path(settings.MEDIA_ROOT) / 'ndvi_images'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f'ndvi_{farm_id}_{date_str}.png'

    # Normalize NDVI between -1 and 1
    ndvi_array = np.clip(ndvi_array, -1, 1)

    # Map values to 0-1 for plotting
    norm_ndvi = (ndvi_array + 1) / 2.0

    # Save using matplotlib colormap (green = healthy, red = dry)
    plt.imsave(output_path, norm_ndvi, cmap='RdYlGn')  # RdYlGn = Red Yellow Green

    return f'ndvi_images/ndvi_{farm_id}_{date_str}.png'  # relative to MEDIA_URL


def fetch_satellite_data(farm):
    """Fetch NDVI image from Sentinel Hub and store in SatelliteImage with color visualization."""
    token = get_sentinel_token()
    geojson = json.loads(farm.boundary.geojson)

    url = 'https://services.sentinel-hub.com/api/v1/process'

    payload = {
        "input": {
            "bounds": {
                "geometry": geojson
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": (datetime.datetime.utcnow() - datetime.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "to": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                    },
                    "maxCloudCoverage": 20
                }
            }]
        },
        "output": {
            "width": 512,
            "height": 512,
            "responses": [
                {
                    "identifier": "default",
                    "format": {
                        "type": "image/tiff"  # Fetch raw NDVI data
                    }
                }
            ]
        },
        "evalscript": """
            //VERSION=3
            function setup() {
                return {
                    input: ["B04", "B08"],
                    output: { bands: 1, sampleType: "FLOAT32" }
                };
            }

            function evaluatePixel(sample) {
                let ndvi = index(sample.B08, sample.B04);
                return [ndvi];
            }
        """
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f'Error from Sentinel API: {response.text}')

    # Read TIFF NDVI response as numpy array
    raw_ndvi_path = Path(settings.MEDIA_ROOT) / 'ndvi_images' / f"ndvi_raw_{farm.id}.tiff"
    raw_ndvi_path.parent.mkdir(parents=True, exist_ok=True)

    with open(raw_ndvi_path, "wb") as f:
        f.write(response.content)

    # Convert TIFF to NDVI array
    import rasterio
    with rasterio.open(raw_ndvi_path) as src:
        ndvi_array = src.read(1)

    # Normalize and apply color map
    ndvi_array = np.clip(ndvi_array, -1, 1)
    ndvi_norm = (ndvi_array + 1) / 2

    color_output_path = Path(settings.MEDIA_ROOT) / 'ndvi_images' / f"ndvi_{farm.id}_{datetime.date.today().isoformat()}.png"
    plt.imsave(color_output_path, ndvi_norm, cmap='RdYlGn')

    relative_path = f"ndvi_images/{color_output_path.name}"

    SatelliteImage.objects.create(
        farm=farm,
        image_date=datetime.date.today(),
        satellite_name="Sentinel-2",
        image_url=relative_path,
        ndvi_avg=float(np.mean(ndvi_array)),
        data_source="SentinelHub"
    )

    return settings.MEDIA_URL + relative_path

 


def calculate_centroid_from_geojson(geojson_data):
    """Calculate centroid from GeoJSON data."""
    # For simplicity, this function assumes a simple polygon
    # More complex geometries would require more sophisticated centroid calculation
    coordinates = geojson_data['coordinates'][0]
    x_sum = sum(point[0] for point in coordinates)
    y_sum = sum(point[1] for point in coordinates)
    count = len(coordinates)
    
    return {
        'lat': y_sum / count,
        'lng': x_sum / count
    }