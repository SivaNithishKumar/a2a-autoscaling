import json
import asyncio
from datetime import datetime, timedelta
from collections.abc import AsyncGenerator
from typing import Any

# Real weather API integration
from openmeteopy import OpenMeteo
from openmeteopy.hourly import HourlyForecast
from openmeteopy.daily import DailyForecast
from openmeteopy.options import ForecastOptions

# Import metrics collection
from common.metrics import get_agent_metrics


class WeatherAgent:
    """Weather Agent with real OpenMeteo API integration."""

    def __init__(self):
        """Initialize the weather agent with real weather API capability."""
        # Initialize metrics collection with separate metrics port
        self.metrics = get_agent_metrics("weather", metrics_port=9082)
        
        # Geocoding database for location coordinates
        self.location_coords = {
            "new york": {"lat": 40.7128, "lon": -74.0060},
            "london": {"lat": 51.5074, "lon": -0.1278},
            "tokyo": {"lat": 35.6762, "lon": 139.6503},
            "mumbai": {"lat": 19.0760, "lon": 72.8777},
            "miami": {"lat": 25.7617, "lon": -80.1918},
            "seattle": {"lat": 47.6062, "lon": -122.3321},
            "sydney": {"lat": -33.8688, "lon": 151.2093},
            "paris": {"lat": 48.8566, "lon": 2.3522},
            "berlin": {"lat": 52.5200, "lon": 13.4050},
            "moscow": {"lat": 55.7558, "lon": 37.6176},
            "beijing": {"lat": 39.9042, "lon": 116.4074},
            "los angeles": {"lat": 34.0522, "lon": -118.2437},
            "chicago": {"lat": 41.8781, "lon": -87.6298},
            "toronto": {"lat": 43.6532, "lon": -79.3832},
            "dublin": {"lat": 53.3498, "lon": -6.2603},
            "amsterdam": {"lat": 52.3676, "lon": 4.9041},
            "barcelona": {"lat": 41.3851, "lon": 2.1734},
            "rome": {"lat": 41.9028, "lon": 12.4964}
        }

    async def stream(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream the response back to the client following A2A pattern."""
        # Determine skill type from query
        location, request_type = self._parse_weather_request(query)
        skill = "current_weather" if request_type == "current" else "weather_forecast"
        
        async with self.metrics.track_request_duration(skill):
            try:
                # Parse the weather request
                location, request_type = self._parse_weather_request(query)
                
                if request_type == "current":
                    async for chunk in self._stream_current_weather(location):
                        yield chunk
                elif request_type == "forecast":
                    async for chunk in self._stream_forecast(location):
                        yield chunk
                else:
                    async for chunk in self._stream_current_weather(location):
                        yield chunk
                        
            except Exception as e:
                yield {
                    'content': f'Sorry, I encountered an error while getting weather information: {str(e)}',
                    'done': True,
                }

    def _parse_weather_request(self, query: str) -> tuple[str, str]:
        """Parse the weather request to extract location and type."""
        query_lower = query.lower()
        
        # Extract location - look for common patterns
        location = "new york"  # default
        
        # Simple location extraction
        if "in " in query_lower:
            parts = query_lower.split("in ")
            if len(parts) > 1:
                potential_location = parts[1].strip().split()[0] if parts[1].strip() else "new york"
                # Check if it's a known location
                for known_location in self.location_coords.keys():
                    if potential_location in known_location or known_location in potential_location:
                        location = known_location
                        break
                else:
                    location = potential_location
        elif "for " in query_lower:
            parts = query_lower.split("for ")
            if len(parts) > 1:
                potential_location = parts[1].strip().split()[0] if parts[1].strip() else "new york"
                for known_location in self.location_coords.keys():
                    if potential_location in known_location or known_location in potential_location:
                        location = known_location
                        break
                else:
                    location = potential_location
        else:
            # Look for any known location mentioned in the query
            for known_location in self.location_coords.keys():
                if known_location in query_lower:
                    location = known_location
                    break
        
        # Determine request type
        request_type = "current"
        if any(word in query_lower for word in ["forecast", "tomorrow", "week", "next", "future"]):
            request_type = "forecast"
            
        return location, request_type

    def _get_coordinates(self, location: str) -> tuple[float, float]:
        """Get coordinates for a location."""
        location_lower = location.lower()
        
        # Check if we have exact coordinates
        if location_lower in self.location_coords:
            coords = self.location_coords[location_lower]
            return coords["lat"], coords["lon"]
        
        # Try partial matching
        for known_location, coords in self.location_coords.items():
            if location_lower in known_location or known_location in location_lower:
                return coords["lat"], coords["lon"]
        
        # Default to New York if location not found
        default_coords = self.location_coords["new york"]
        return default_coords["lat"], default_coords["lon"]

    async def _get_current_weather(self, location: str) -> dict[str, Any]:
        """Get current weather data from OpenMeteo API."""
        try:
            latitude, longitude = self._get_coordinates(location)
            print(f"Getting weather for {location} at coordinates: {latitude}, {longitude}")
            
            # Set up OpenMeteo client for current weather
            hourly = HourlyForecast()
            options = ForecastOptions(latitude, longitude)
            
            # Use the correct method names from OpenMeteoPy
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
                    'location': location
                }
                
                # Extract available weather variables with correct names
                if 'temperature_2m' in hourly_data and hourly_data['temperature_2m']:
                    current_data['temperature'] = round(hourly_data['temperature_2m'][0], 1)
                else:
                    current_data['temperature'] = "N/A"
                
                if 'relativehumidity_2m' in hourly_data and hourly_data['relativehumidity_2m']:
                    current_data['humidity'] = hourly_data['relativehumidity_2m'][0]
                else:
                    current_data['humidity'] = "N/A"
                
                if 'windspeed_10m' in hourly_data and hourly_data['windspeed_10m']:
                    current_data['wind_speed'] = round(hourly_data['windspeed_10m'][0], 1)
                else:
                    current_data['wind_speed'] = "N/A"
                
                if 'winddirection_10m' in hourly_data and hourly_data['winddirection_10m']:
                    current_data['wind_direction'] = hourly_data['winddirection_10m'][0]
                    current_data['wind_direction_text'] = self._degrees_to_compass(current_data['wind_direction'])
                else:
                    current_data['wind_direction_text'] = "N/A"
                
                if 'pressure_msl' in hourly_data and hourly_data['pressure_msl']:
                    current_data['pressure'] = round(hourly_data['pressure_msl'][0], 1)
                else:
                    current_data['pressure'] = "N/A"
                
                if 'cloudcover' in hourly_data and hourly_data['cloudcover']:
                    current_data['cloud_cover'] = hourly_data['cloudcover'][0]
                else:
                    current_data['cloud_cover'] = "N/A"
                
                if 'weathercode' in hourly_data and hourly_data['weathercode']:
                    current_data['weather_code'] = hourly_data['weathercode'][0]
                    current_data['conditions'] = self._weather_code_to_description(current_data['weather_code'])
                else:
                    current_data['conditions'] = "Clear"
                
                return current_data
            else:
                raise ValueError("No weather data received from API")
                
        except Exception as e:
            print(f"Error in _get_current_weather: {e}")
            raise ValueError(f"Failed to fetch weather data: {str(e)}")

    async def _get_forecast_weather(self, location: str) -> list[dict[str, Any]]:
        """Get weather forecast data from OpenMeteo API."""
        try:
            latitude, longitude = self._get_coordinates(location)
            
            # Set up OpenMeteo client for forecast
            daily = DailyForecast()
            options = ForecastOptions(latitude, longitude)
            
            # Add variables to the daily class
            daily = daily.temperature_2m_max()
            daily = daily.temperature_2m_min()
            daily = daily.weather_code()
            daily = daily.wind_speed_10m_max()
            daily = daily.precipitation_sum()
            
            # Request 5-day forecast data
            mgr = OpenMeteo(options, daily)
            
            # Get data as dictionary
            data = mgr.get_dict()
            
            forecast_data = []
            if data and 'daily' in data:
                daily_data = data['daily']
                dates = daily_data.get('time', [])
                
                for i in range(min(5, len(dates))):  # 5-day forecast
                    day_data = {
                        'date': self._format_date(dates[i]),
                        'high': round(daily_data.get('temperature_2m_max', [0])[i], 1),
                        'low': round(daily_data.get('temperature_2m_min', [0])[i], 1),
                        'weather_code': daily_data.get('weather_code', [0])[i],
                        'wind_speed': round(daily_data.get('wind_speed_10m_max', [0])[i], 1),
                        'precipitation': round(daily_data.get('precipitation_sum', [0])[i], 1)
                    }
                    
                    # Convert weather code to description
                    day_data['conditions'] = self._weather_code_to_description(day_data['weather_code'])
                    
                    # Calculate rain chance based on precipitation
                    day_data['rain_chance'] = min(int(day_data['precipitation'] * 10), 100)
                    
                    forecast_data.append(day_data)
            
            return forecast_data
            
        except Exception as e:
            raise ValueError(f"Failed to fetch forecast data: {str(e)}")

    def _weather_code_to_description(self, code: int) -> str:
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
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return weather_codes.get(code, "Unknown")

    def _degrees_to_compass(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction."""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]

    def _format_date(self, date_str: str) -> str:
        """Format date string to readable format."""
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime("%A, %B %d")
        except:
            return date_str

    async def _stream_current_weather(self, location: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream current weather information."""
        try:
            yield {'content': f'🌤️ Getting current weather for {location.title()}...\n\n', 'done': False}
            
            # Get real weather data
            weather_data = await self._get_current_weather(location)
            
            yield {'content': f'🌡️ Temperature: {weather_data["temperature"]}°C\n', 'done': False}
            
            if weather_data.get("conditions") != "N/A":
                yield {'content': f'☁️ Conditions: {weather_data["conditions"]}\n', 'done': False}
            
            if weather_data.get("wind_speed") != "N/A":
                yield {'content': f'💨 Wind: {weather_data["wind_speed"]} km/h {weather_data["wind_direction_text"]}\n', 'done': False}
            
            if weather_data.get("humidity") != "N/A":
                yield {'content': f'💧 Humidity: {weather_data["humidity"]}%\n', 'done': False}
            
            if weather_data.get("pressure") != "N/A":
                yield {'content': f'📊 Pressure: {weather_data["pressure"]} hPa\n', 'done': False}
            
            if weather_data.get("cloud_cover") != "N/A":
                yield {'content': f'☁️ Cloud Cover: {weather_data["cloud_cover"]}%\n', 'done': False}
            
            yield {'content': f'\n🕒 Last updated: {weather_data["timestamp"]}\n', 'done': False}
            
            yield {'content': f'\n📍 Location: {location.title()} (Real data from OpenMeteo)\n', 'done': False}
            
            if weather_data.get("message"):
                yield {'content': f'\n⚠️ Note: {weather_data["message"]}\n', 'done': False}
            
            yield {'content': '', 'done': True}
            
        except Exception as e:
            yield {'content': f'❌ Error fetching current weather: {str(e)}\n', 'done': False}
            yield {'content': 'Please try again or check if the location is valid.\n', 'done': True}

    async def _stream_forecast(self, location: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream weather forecast information."""
        try:
            yield {'content': f'📅 Getting 5-day forecast for {location.title()}...\n\n', 'done': False}
            
            # Get real forecast data
            forecast_data = await self._get_forecast_weather(location)
            
            for day in forecast_data:
                yield {'content': f'📆 {day["date"]}\n', 'done': False}
                yield {'content': f'   🌡️ High: {day["high"]}°C, Low: {day["low"]}°C\n', 'done': False}
                yield {'content': f'   ☁️ {day["conditions"]}\n', 'done': False}
                yield {'content': f'   💧 Precipitation: {day["precipitation"]}mm (Rain chance: {day["rain_chance"]}%)\n', 'done': False}
                yield {'content': f'   💨 Max Wind: {day["wind_speed"]} km/h\n\n', 'done': False}
            
            yield {'content': f'📍 Location: {location.title()} (Real forecast data from OpenMeteo)\n', 'done': False}
            yield {'content': '', 'done': True}
            
        except Exception as e:
            yield {'content': f'❌ Error fetching forecast: {str(e)}\n', 'done': False}
            yield {'content': 'Please try again or check if the location is valid.\n', 'done': True}

