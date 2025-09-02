"""
Calculator Agent Server - A2A Standard Implementation

Main entry point for the Calculator Agent A2A server following samples patterns.
"""

import logging
import os
import sys

import click
import httpx
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv

from multi_agent_a2a.agents.calculator.agent import CalculatorAgent
from multi_agent_a2a.agents.calculator.agent_executor import CalculatorAgentExecutor


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingConfigError(Exception):
    """Exception for missing configuration."""


@click.command()
@click.option('--host', 'host', default='localhost', help='Host to run the server on')
@click.option('--port', 'port', default=8002, help='Port to run the server on')
def main(host, port):
    """Starts the Calculator Agent A2A server."""
    try:
        logger.info(f"Starting Calculator Agent server on {host}:{port}")
        
        # Create agent capabilities
        capabilities = AgentCapabilities(
            streaming=True, 
            push_notifications=True
        )
        
        # Define agent skills
        calculation_skill = AgentSkill(
            id='mathematical_calculation',
            name='Mathematical Calculator',
            description='Performs mathematical calculations including arithmetic, unit conversions, and statistical analysis',
            tags=['math', 'arithmetic', 'calculator', 'statistics', 'unit conversion'],
            examples=[
                'Calculate 15 + 25 * 3',
                'What is the square root of 144?',
                'Convert 100°F to Celsius',
                'Find the average of 10, 20, 30, 40',
                'What is 15% of 240?'
            ],
        )
        
        # Create agent card
        agent_card = AgentCard(
            name='Calculator Agent',
            description='A specialized mathematical calculator agent that performs arithmetic operations, unit conversions, and statistical calculations',
            url=f'http://{host}:{port}/',
            version='2.0.0',  # Updated version for A2A compliance
            default_input_modes=CalculatorAgent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=CalculatorAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[calculation_skill],
        )

        # Create HTTP client for push notifications
        httpx_client = httpx.AsyncClient()
        
        # Set up push notification components
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(
            httpx_client=httpx_client,
            config_store=push_config_store
        )
        
        # Create request handler with all A2A components
        request_handler = DefaultRequestHandler(
            agent_executor=CalculatorAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_config_store=push_config_store,
            push_sender=push_sender
        )
        
        # Create A2A Starlette application
        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )

        logger.info("Calculator Agent server configuration complete")
        logger.info(f"Agent Card: {agent_card.name} v{agent_card.version}")
        logger.info(f"Capabilities: streaming={capabilities.streaming}, push_notifications={capabilities.push_notifications}")
        logger.info(f"Skills: {[skill.name for skill in agent_card.skills]}")
        
        # Start the server
        uvicorn.run(
            server.build(), 
            host=host, 
            port=port,
            log_level="info"
        )

    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}', exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
