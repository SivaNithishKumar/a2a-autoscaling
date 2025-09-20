#!/usr/bin/env python3
"""
Test script to understand how OpenMeteoPy actually works
"""

import sys
import os

# Add the virtual environment to the path
sys.path.insert(0, '/home/ubuntu/projects/a2a-autoscaling/venv/lib/python3.10/site-packages')

try:
    from openmeteopy import OpenMeteo
    from openmeteopy.hourly import HourlyForecast
    from openmeteopy.daily import DailyForecast
    from openmeteopy.options import ForecastOptions
    print("✅ Successfully imported OpenMeteoPy modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_basic_weather():
    """Test basic weather functionality."""
    print("\n🧪 Testing basic weather functionality...")
    
    # Coordinates for London
    latitude = 51.5074
    longitude = -0.1278
    
    try:
        # Method 1: Try with individual methods
        print("📍 Testing individual method chaining...")
        hourly = HourlyForecast()
        options = ForecastOptions(latitude, longitude)
        
        # Try just temperature first
        hourly_temp = hourly.temperature_2m()
        mgr_temp = OpenMeteo(options, hourly_temp)
        data_temp = mgr_temp.get_dict()
        print(f"Temperature-only data keys: {list(data_temp.keys()) if data_temp else 'No data'}")
        
        if data_temp and 'hourly' in data_temp:
            print(f"Hourly data keys: {list(data_temp['hourly'].keys())}")
            if 'temperature_2m' in data_temp['hourly']:
                temp = data_temp['hourly']['temperature_2m'][0]
                print(f"✅ Current temperature: {temp}°C")
        
    except Exception as e:
        print(f"❌ Error with individual methods: {e}")
    
    try:
        # Method 2: Try with .all() to see what happens
        print("\n📍 Testing .all() method...")
        hourly = HourlyForecast()
        options = ForecastOptions(latitude, longitude)
        
        # This might be the issue - let's see what .all() actually returns
        hourly_all = hourly.all()
        print(f"Type of hourly.all(): {type(hourly_all)}")
        print(f"Dir of hourly.all(): {[attr for attr in dir(hourly_all) if not attr.startswith('_')]}")
        
        mgr_all = OpenMeteo(options, hourly_all)
        data_all = mgr_all.get_dict()
        print(f"All data keys: {list(data_all.keys()) if data_all else 'No data'}")
        
        if data_all and 'hourly' in data_all:
            print(f"All hourly data keys: {list(data_all['hourly'].keys())}")
            
    except Exception as e:
        print(f"❌ Error with .all() method: {e}")
        import traceback
        traceback.print_exc()

    try:
        # Method 3: Try chaining multiple methods
        print("\n📍 Testing multiple method chaining...")
        hourly = HourlyForecast()
        options = ForecastOptions(latitude, longitude)
        
        # Chain methods one by one
        hourly = hourly.temperature_2m()
        print("✅ Added temperature_2m")
        
        # Check if relative_humidity_2m method exists
        if hasattr(hourly, 'relative_humidity_2m'):
            hourly = hourly.relative_humidity_2m()
            print("✅ Added relative_humidity_2m")
        else:
            print("❌ relative_humidity_2m method not found")
            print(f"Available methods: {[method for method in dir(hourly) if not method.startswith('_') and callable(getattr(hourly, method))]}")
        
        mgr_chain = OpenMeteo(options, hourly)
        data_chain = mgr_chain.get_dict()
        print(f"Chained data keys: {list(data_chain.keys()) if data_chain else 'No data'}")
        
        if data_chain and 'hourly' in data_chain:
            print(f"Chained hourly data keys: {list(data_chain['hourly'].keys())}")
            
    except Exception as e:
        print(f"❌ Error with method chaining: {e}")
        import traceback
        traceback.print_exc()

def test_available_methods():
    """Test what methods are actually available."""
    print("\n🔍 Investigating available methods...")
    
    try:
        hourly = HourlyForecast()
        print(f"HourlyForecast type: {type(hourly)}")
        
        # Get all methods that don't start with underscore
        methods = [method for method in dir(hourly) if not method.startswith('_') and callable(getattr(hourly, method))]
        print(f"Available methods ({len(methods)}): {methods}")
        
        # Check for humidity-related methods
        humidity_methods = [method for method in methods if 'humidity' in method.lower()]
        print(f"Humidity-related methods: {humidity_methods}")
        
        # Check for common weather variables
        common_vars = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'wind_direction_10m', 'pressure_msl', 'cloud_cover', 'weather_code']
        for var in common_vars:
            if hasattr(hourly, var):
                print(f"✅ {var} - available")
            else:
                print(f"❌ {var} - not available")
                
    except Exception as e:
        print(f"❌ Error investigating methods: {e}")

if __name__ == "__main__":
    print("🌤️ OpenMeteoPy Test Script")
    print("=" * 50)
    
    test_available_methods()
    test_basic_weather()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")