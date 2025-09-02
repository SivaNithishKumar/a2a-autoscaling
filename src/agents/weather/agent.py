import json
import random
from datetime import datetime, timedelta
from collections.abc import AsyncGenerator
from typing import Any

# Import metrics collection
from ...common.metrics import get_agent_metrics


class WeatherAgent:
    """Weather Agent following A2A samples pattern."""

    def __init__(self):
        """Initialize the weather agent with mock data capability."""
        # Using mock data for demonstration - in production this would use real weather APIs
        self.mock_mode = True
        
        # Initialize metrics collection with separate metrics port
        self.metrics = get_agent_metrics("weather", metrics_port=9082)

    async def stream(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream the response back to the client following A2A pattern."""
        # Determine skill type from query
        _, request_type = self._parse_weather_request(query)
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
        location = "New York"  # default
        
        # Simple location extraction
        if "in " in query_lower:
            parts = query_lower.split("in ")
            if len(parts) > 1:
                location = parts[1].split()[0].title()
        elif "for " in query_lower:
            parts = query_lower.split("for ")
            if len(parts) > 1:
                location = parts[1].split()[0].title()
        
        # Determine request type
        request_type = "current"
        if any(word in query_lower for word in ["forecast", "tomorrow", "week", "next"]):
            request_type = "forecast"
            
        return location, request_type

    async def _stream_current_weather(self, location: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream current weather information."""
        # Generate mock current weather data
        weather_data = self._generate_mock_current_weather(location)
        
        yield {'content': f'🌤️ Current weather for {location}:\n\n', 'done': False}
        
        yield {'content': f'🌡️ Temperature: {weather_data["temperature"]}°C\n', 'done': False}
        
        yield {'content': f'☁️ Conditions: {weather_data["conditions"]}\n', 'done': False}
        
        yield {'content': f'💨 Wind: {weather_data["wind_speed"]} km/h {weather_data["wind_direction"]}\n', 'done': False}
        
        yield {'content': f'💧 Humidity: {weather_data["humidity"]}%\n', 'done': False}
        
        yield {'content': f'📊 Pressure: {weather_data["pressure"]} hPa\n', 'done': False}
        
        yield {'content': f'\n🕒 Last updated: {weather_data["timestamp"]}\n', 'done': False}
        
        yield {'content': '', 'done': True}

    async def _stream_forecast(self, location: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream weather forecast information."""
        forecast_data = self._generate_mock_forecast(location)
        
        yield {'content': f'📅 5-day weather forecast for {location}:\n\n', 'done': False}
        
        for day in forecast_data:
            yield {'content': f'📆 {day["date"]}\n', 'done': False}
            yield {'content': f'   🌡️ High: {day["high"]}°C, Low: {day["low"]}°C\n', 'done': False}
            yield {'content': f'   ☁️ {day["conditions"]}\n', 'done': False}
            yield {'content': f'   💧 Rain chance: {day["rain_chance"]}%\n\n', 'done': False}
        
        yield {'content': '', 'done': True}

    def _generate_mock_current_weather(self, location: str) -> dict[str, Any]:
        """Generate mock current weather data."""
        # Use location hash for consistent "random" data
        random.seed(hash(location))
        
        # Location-specific temperature ranges and conditions
        location_data = {
            "new york": {"temp_range": (10, 25), "conditions": ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain"]},
            "london": {"temp_range": (5, 18), "conditions": ["Cloudy", "Light Rain", "Overcast", "Partly Cloudy"]},
            "tokyo": {"temp_range": (15, 30), "conditions": ["Clear", "Sunny", "Partly Cloudy", "Light Rain"]},
            "miami": {"temp_range": (20, 35), "conditions": ["Sunny", "Partly Cloudy", "Thunderstorms", "Clear"]},
            "seattle": {"temp_range": (8, 20), "conditions": ["Light Rain", "Cloudy", "Overcast", "Partly Cloudy"]},
            "sydney": {"temp_range": (12, 28), "conditions": ["Sunny", "Clear", "Partly Cloudy", "Light Rain"]},
        }
        
        location_key = location.lower()
        if location_key in location_data:
            temp_range = location_data[location_key]["temp_range"]
            conditions = location_data[location_key]["conditions"]
        else:
            temp_range = (10, 25)
            conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Clear", "Overcast"]
        
        wind_directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        
        return {
            "temperature": random.randint(temp_range[0], temp_range[1]),
            "conditions": random.choice(conditions),
            "wind_speed": random.randint(5, 25),
            "wind_direction": random.choice(wind_directions),
            "humidity": random.randint(30, 90),
            "pressure": random.randint(980, 1030),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        }

    def _generate_mock_forecast(self, location: str) -> list[dict[str, Any]]:
        """Generate mock 5-day forecast data."""
        random.seed(hash(location))
        
        # Get current weather as baseline
        current = self._generate_mock_current_weather(location)
        base_temp = current["temperature"]
        
        # Location-specific conditions
        location_conditions = {
            "new york": ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Clear"],
            "london": ["Cloudy", "Light Rain", "Overcast", "Partly Cloudy", "Drizzle"],
            "tokyo": ["Clear", "Sunny", "Partly Cloudy", "Light Rain", "Overcast"],
            "miami": ["Sunny", "Partly Cloudy", "Thunderstorms", "Clear", "Hot"],
            "seattle": ["Light Rain", "Cloudy", "Overcast", "Partly Cloudy", "Drizzle"],
        }
        
        location_key = location.lower()
        conditions = location_conditions.get(location_key, ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Showers", "Clear"])
        
        forecast = []
        
        for i in range(5):
            # Add some realistic temperature variation
            temp_variation = random.randint(-5, 5)
            high_temp = max(base_temp + temp_variation + random.randint(2, 8), base_temp + 1)
            low_temp = min(base_temp + temp_variation - random.randint(2, 8), high_temp - 3)
            
            date = (datetime.now() + timedelta(days=i+1)).strftime("%A, %B %d")
            forecast.append({
                "date": date,
                "high": high_temp,
                "low": low_temp,
                "conditions": random.choice(conditions),
                "rain_chance": random.randint(0, 80) if "rain" in random.choice(conditions).lower() else random.randint(0, 40)
            })
        
        return forecast

