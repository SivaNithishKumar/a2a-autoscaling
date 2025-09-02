"""
Calculator Agent Server

Main entry point for the Calculator Agent A2A server.
A specialized mathematical calculator agent that performs arithmetic operations, unit conversions, and statistical calculations.
"""

import logging
import sys
import time
import click
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

from .agent_executor import CalculatorAgentExecutor


# Load environment variables
load_dotenv()


def create_agent_card(host: str = "localhost", port: int = 8001) -> AgentCard:
    """Create the agent card for the Calculator Agent."""
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
    
    capabilities = AgentCapabilities(
        streaming=True,
        push_notifications=True,
        state_transition_history=True,
    )
    
    return AgentCard(
        name='Calculator Agent',
        description='A specialized mathematical calculator agent that performs arithmetic operations, unit conversions, and statistical calculations',
        url=f'http://{host}:{port}/',
        version='2.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=capabilities,
        skills=[calculation_skill],
    )


@click.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=8001, help='Port to bind the server to')
@click.option('--log-level', default='info', help='Logging level')
def main(host: str, port: int, log_level: str) -> None:
    """Start the Calculator Agent A2A server."""
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Calculator Agent server...")
        
        # Create agent card
        agent_card = create_agent_card(host, port)
        
        # Create HTTP client for push notifications
        import httpx
        httpx_client = httpx.AsyncClient()
        
        # Set up push notification components
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(
            httpx_client=httpx_client,
            config_store=push_config_store
        )
        
        # Create agent executor
        agent_executor = CalculatorAgentExecutor()
        
        # Create task store
        task_store = InMemoryTaskStore()
        
        # Create request handler with all A2A components
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=task_store,
            push_config_store=push_config_store,
            push_sender=push_sender
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
                "agent": "Calculator Agent",
                "version": "2.0.0",
                "timestamp": str(time.time())
            })
        
        # Build the app and add health route
        app = server.build()
        app.add_route("/health", health_check, methods=["GET"])

        logger.info("Calculator Agent server configuration complete")
        logger.info(f"Agent Card: {agent_card.name} v{agent_card.version}")
        logger.info(f"Capabilities: streaming={agent_card.capabilities.streaming}, push_notifications={agent_card.capabilities.push_notifications}")
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