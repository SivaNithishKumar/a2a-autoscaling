"""
Base Agent Server

Main entry point for the Base Agent A2A server.
A general purpose AI assistant that can handle various queries and conversations.
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

from .agent_executor import BaseAgentExecutor


def create_agent_card(host: str = "localhost", port: int = 8000) -> AgentCard:
    """Create the agent card for the Base Agent."""
    skills = [
        AgentSkill(
            id='general_assistance',
            name='General Assistance',
            description='Provide helpful responses to general questions and tasks',
            tags=['general', 'assistance', 'chat', 'help'],
            examples=[
                'Help me understand a concept',
                'Answer a question about a topic',
                'Provide information or advice',
                'Assist with general tasks'
            ],
        ),
        AgentSkill(
            id='conversation',
            name='Conversation',
            description='Engage in natural conversation and dialogue',
            tags=['conversation', 'chat', 'dialogue'],
            examples=[
                'Hello, how are you?',
                'Tell me about yourself',
                'What can you help me with?',
                'Have a conversation with me'
            ],
        ),
    ]
    
    capabilities = AgentCapabilities(
        streaming=True,
        push_notifications=False,
        state_transition_history=True,
    )
    
    return AgentCard(
        name='Base Agent',
        description='A general purpose AI assistant that can help with various questions and tasks',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=capabilities,
        skills=skills,
    )


@click.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=8000, help='Port to bind the server to')
@click.option('--log-level', default='info', help='Logging level')
def main(host: str, port: int, log_level: str) -> None:
    """Start the Base Agent A2A server."""
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Base Agent server...")
        
        # Create agent card
        agent_card = create_agent_card(host, port)
        
        # Create agent executor
        agent_executor = BaseAgentExecutor()
        
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
                "agent": "Base Agent",
                "version": "1.0.0",
                "timestamp": str(time.time())
            })
        
        # Build the app and add health route
        app = server.build()
        app.add_route("/health", health_check, methods=["GET"])

        logger.info("Base Agent server configuration complete")
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
