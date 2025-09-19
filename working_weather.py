#!/usr/bin/env python3
"""
Working OpenMeteoPy implementation for weather agent
"""

import sys
sys.path.insert(0, '/home/ubuntu/projects/a2a-autoscaling/venv/lib/python3.10/site-packages')

from openmeteopy import OpenMeteo
from openmeteopy.hourly import HourlyForecast
from openmeteopy.daily import DailyForecast
from openmeteopy.options import ForecastOptions
from datetime import datetime

def get_current_weather(location_name, latitude, longitude):
    """Get current weather using correct OpenMeteoPy methods."""
    try:
        print(f"Getting weather for {location_name} at coordinates: {latitude}, {longitude}")
        
        # Set up OpenMeteo client for current weather
        hourly = HourlyForecast()
        options = ForecastOptions(latitude, longitude)
        
        # Use the correct method names we discovered
        hourly = hourly.temperature_2m()
        hourly = hourly.relativehumidity_2m()  # Correct name!
        hourly = hourly.windspeed_10m()        # Correct name!
        hourly = hourly.winddirection_10m()    # Correct name!
        hourly = hourly.pressure_msl()
        hourly = hourly.cloudcover()           # Correct name!
        hourly = hourly.weathercode()          # Correct name!
        
        mgr = OpenMeteo(options, hourly)
        
        # Get data as dictionary
        data = mgr.get_dict()
        print(f"Raw weather data keys: {list(data.keys()) if data else 'No data'}")
        
        # Extract current hour data (first available data point)
        if data and 'hourly' in data:
            hourly_data = data['hourly']
            print(f"Available hourly data keys: {list(hourly_data.keys())}")
            
            # Try to extract what we can from available data
            current_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
                'location': location_name
            }
            
            # Extract available weather variables with correct names
            if 'temperature_2m' in hourly_data and hourly_data['temperature_2m']:
                current_data['temperature'] = round(hourly_data['temperature_2m'][0], 1)
            
            if 'relativehumidity_2m' in hourly_data and hourly_data['relativehumidity_2m']:
                current_data['humidity'] = hourly_data['relativehumidity_2m'][0]
            
            if 'windspeed_10m' in hourly_data and hourly_data['windspeed_10m']:
                current_data['wind_speed'] = round(hourly_data['windspeed_10m'][0], 1)
            
            if 'winddirection_10m' in hourly_data and hourly_data['winddirection_10m']:
                current_data['wind_direction'] = hourly_data['winddirection_10m'][0]
                current_data['wind_direction_text'] = degrees_to_compass(current_data['wind_direction'])
            
            if 'pressure_msl' in hourly_data and hourly_data['pressure_msl']:
                current_data['pressure'] = round(hourly_data['pressure_msl'][0], 1)
            
            if 'cloudcover' in hourly_data and hourly_data['cloudcover']:
                current_data['cloud_cover'] = hourly_data['cloudcover'][0]
            
            if 'weathercode' in hourly_data and hourly_data['weathercode']:
                current_data['weather_code'] = hourly_data['weathercode'][0]
                current_data['conditions'] = weather_code_to_description(current_data['weather_code'])
            
            return current_data
        else:
            raise ValueError("No weather data received from API")
            
    except Exception as e:
        print(f"Error in get_current_weather: {e}")
        raise ValueError(f"Failed to fetch weather data: {str(e)}")

def weather_code_to_description(code):
    """Convert WMO weather code to human readable description."""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy", 
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(code, "Unknown")

def degrees_to_compass(degrees):
    """Convert wind direction degrees to compass direction."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]

if __name__ == "__main__":
    print("🌤️ Testing Working OpenMeteoPy Implementation")
    print("=" * 50)
    
    # Test with London coordinates
    try:
        weather_data = get_current_weather("London", 51.5074, -0.1278)
        print("\n✅ Weather data retrieved successfully:")
        for key, value in weather_data.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print("\n" + "=" * 50)
    print("✅ Test completed!")