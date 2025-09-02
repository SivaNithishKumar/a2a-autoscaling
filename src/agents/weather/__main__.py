"""
Weather Agent Server

Main entry point for the Weather Agent A2A server.
A specialized agent for weather information and forecasts.
"""

import logging
import sys
import time
import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

# Use safer import pattern
try:
    from .agent_executor import WeatherAgentExecutor
except ImportError:
    from agent_executor import WeatherAgentExecutor


def create_agent_card(host: str = "localhost", port: int = 8002) -> AgentCard:
    """Create the agent card for the Weather Agent."""
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

    capabilities = AgentCapabilities(
        streaming=True,
        push_notifications=False,
        state_transition_history=True,
    )
    
    return AgentCard(
        name='Weather Agent',
        description='A weather information agent that provides current weather conditions and forecasts',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=capabilities,
        skills=[current_weather_skill, forecast_skill],
    )


@click.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=8002, help='Port to bind the server to')
@click.option('--log-level', default='info', help='Logging level')
def main(host: str, port: int, log_level: str) -> None:
    """Start the Weather Agent A2A server."""
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Weather Agent server...")
        
        # Create agent card
        agent_card = create_agent_card(host, port)
        
        # Create agent executor
        agent_executor = WeatherAgentExecutor()
        
        # Create task store
        task_store = InMemoryTaskStore()
        
        # Create request handler
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=task_store,
        )
        
        # Create A2A Starlette application
        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )
        
        # Add health endpoint to the Starlette app
        from starlette.responses import JSONResponse
        
        async def health_check(request):
            return JSONResponse({
                "status": "healthy",
                "agent": "Weather Agent",
                "version": "1.0.0",
                "timestamp": str(time.time())
            })
        
        # Build the app and add health route
        app = server.build()
        app.add_route("/health", health_check, methods=["GET"])

        logger.info("Weather Agent server configuration complete")
        logger.info(f"Agent Card: {agent_card.name} v{agent_card.version}")
        logger.info(f"Capabilities: streaming={agent_card.capabilities.streaming}")
        logger.info(f"Skills: {[skill.name for skill in agent_card.skills]}")
        logger.info(f"Starting server on {host}:{port}")
        
        # Start the server with health endpoint
        uvicorn.run(
            app, 
            host=host, 
            port=port,
            log_level=log_level
        )

    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}', exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
