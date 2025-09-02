from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from multi_agent_a2a.agents.weather.agent_executor import WeatherAgentExecutor


if __name__ == '__main__':
    # Current weather skill
    current_weather_skill = AgentSkill(
        id='current_weather',
        name='Current Weather',
        description='Get current weather conditions for any location',
        tags=['weather', 'current', 'temperature', 'conditions', 'now'],
        examples=[
            'What\'s the weather like in New York right now?',
            'Current weather in London',
            'How\'s the weather today in Tokyo?',
            'Temperature in Miami now'
        ],
    )

    # Weather forecast skill
    forecast_skill = AgentSkill(
        id='weather_forecast',
        name='Weather Forecast',
        description='Get weather forecasts for upcoming days',
        tags=['weather', 'forecast', 'prediction', 'future', 'days'],
        examples=[
            'Weather forecast for London',
            'What will the weather be like next week?',
            'Five day forecast for San Francisco',
            'Will it rain tomorrow in Seattle?'
        ],
    )

    agent_card = AgentCard(
        name='Weather Agent',
        description='A weather information agent that provides current weather conditions and forecasts',
        url='http://localhost:8001/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[current_weather_skill, forecast_skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=WeatherAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    import uvicorn

    uvicorn.run(server.build(), host='0.0.0.0', port=8001)