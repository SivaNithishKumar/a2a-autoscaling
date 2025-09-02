#!/usr/bin/env python3
"""
Move Orchestration Agent - A2A Server Runner

Production-ready A2A server for the Move Orchestration Agent.
Designed to demonstrate advanced AI-Ops capabilities for Just Move In.
"""

import logging
import sys
import click
import uvicorn
from pathlib import Path

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from .agent import MoveOrchestrationExecutor


def create_agent_card(host: str = "localhost", port: int = 8004) -> AgentCard:
    """Create the agent card for the Move Orchestration Agent."""
    skills = [
        AgentSkill(
            id='orchestrate_move',
            name='Orchestrate Move',
            description='Plan and coordinate comprehensive home moving operations',
            tags=['move', 'orchestration', 'planning', 'coordination'],
            examples=[
                'Plan my move from London to Manchester',
                'Coordinate utility transfers for house move',
                'Create timeline for office relocation'
            ],
        ),
        AgentSkill(
            id='optimize_timeline',
            name='Optimize Timeline',
            description='AI-powered timeline optimization with critical path analysis',
            tags=['timeline', 'optimization', 'scheduling', 'ai'],
            examples=[
                'Optimize my moving timeline',
                'Find critical path dependencies',
                'Suggest timeline improvements'
            ],
        ),
        AgentSkill(
            id='coordinate_services',
            name='Coordinate Services',
            description='Multi-agent service provider coordination',
            tags=['services', 'coordination', 'providers'],
            examples=[
                'Coordinate utility providers',
                'Schedule moving services',
                'Manage service dependencies'
            ],
        ),
        AgentSkill(
            id='estimate_costs',
            name='Estimate Costs',
            description='Comprehensive cost estimation with breakdown analysis',
            tags=['costs', 'estimation', 'budgeting'],
            examples=[
                'Estimate total moving costs',
                'Break down service costs',
                'Provide cost optimization suggestions'
            ],
        ),
    ]
    
    capabilities = AgentCapabilities(
        streaming=True,
        push_notifications=False,
        state_transition_history=True,
    )
    
    return AgentCard(
        name='Move Orchestration Agent',
        description='AI-powered move orchestration with timeline optimization and service coordination',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=capabilities,
        skills=skills,
    )


@click.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=8004, help='Port to bind the server to')
@click.option('--log-level', default='info', help='Logging level')
def main(host: str, port: int, log_level: str) -> None:
    """Start the Move Orchestration Agent A2A server."""
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 Starting Move Orchestration Agent - AI-Ops Production Server")
        logger.info("🏠 Specialized for Just Move In complex moving operations")
        logger.info(f"📊 Metrics available on: http://{host}:8084/metrics")
        
        # Create agent card
        agent_card = create_agent_card(host, port)
        
        # Create agent executor
        agent_executor = MoveOrchestrationExecutor()
        
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
        import time

        async def health_check(request):
            return JSONResponse({
                "status": "healthy",
                "agent": "Move Orchestration Agent",
                "version": "1.0.0",
                "timestamp": str(time.time())
            })

        # Build the app and add health route
        app = server.build()
        app.add_route("/health", health_check, methods=["GET"])

        logger.info("Move Orchestration Agent server configuration complete")
        logger.info(f"Agent Card: {agent_card.name} v{agent_card.version}")
        logger.info(f"Capabilities: streaming={agent_card.capabilities.streaming}")
        logger.info(f"Skills: {[skill.name for skill in agent_card.skills]}")
        logger.info(f"Starting server on {host}:{port}")
        
        # Start the server
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