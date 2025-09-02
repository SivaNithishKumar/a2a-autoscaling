#!/usr/bin/env python3
"""
Infrastructure Monitoring Agent - A2A Server Runner

Production-ready A2A server for the Infrastructure Monitoring Agent.
Designed to demonstrate advanced AI-Ops capabilities for production monitoring.
"""

import logging
import sys
import click
import uvicorn
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from .agent import InfrastructureMonitoringExecutor



def create_agent_card(host: str = "localhost", port: int = 8005) -> AgentCard:
    """Create the agent card for the Infrastructure Monitoring Agent."""
    skills = [
        AgentSkill(
            id='monitor_infrastructure',
            name='Monitor Infrastructure',
            description='Comprehensive infrastructure monitoring with real-time health analysis',
            tags=['monitoring', 'infrastructure', 'health', 'ai-ops'],
            examples=[
                'Monitor infrastructure health and performance across all services',
                'Provide comprehensive status report with performance insights',
                'Analyze current infrastructure metrics and identify issues'
            ],
        ),
        AgentSkill(
            id='detect_anomalies',
            name='Detect Anomalies',
            description='AI-powered anomaly detection with intelligent pattern recognition',
            tags=['anomaly-detection', 'ai-ops', 'patterns', 'alerts'],
            examples=[
                'Detect anomalies in service performance and behavior',
                'Identify unusual patterns in infrastructure metrics',
                'Analyze system behavior for abnormal conditions'
            ],
        ),
        AgentSkill(
            id='predict_failures',
            name='Predict Failures',
            description='Predictive failure analysis using machine learning models',
            tags=['prediction', 'failure-analysis', 'ml', 'proactive'],
            examples=[
                'Predict potential system failures before they occur',
                'Analyze failure risks and provide early warnings',
                'Generate proactive maintenance recommendations'
            ],
        ),
    ]
    
    capabilities = AgentCapabilities(
        streaming=True,
        push_notifications=False,
        state_transition_history=True,
    )
    
    return AgentCard(
        name='Infrastructure Monitoring Agent',
        description='AI-powered infrastructure monitoring with anomaly detection and predictive analytics',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=capabilities,
        skills=skills,
    )


@click.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=8005, help='Port to bind the server to')
@click.option('--log-level', default='info', help='Logging level')
def main(host: str, port: int, log_level: str) -> None:
    """Start the Infrastructure Monitoring Agent A2A server."""
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🏗️ Starting Infrastructure Monitoring Agent - AI-Ops Production Server")
        logger.info("🔍 Specialized for real-time monitoring and anomaly detection")
        logger.info(f"📊 Metrics available on: http://{host}:8085/metrics")
        
        # Create agent card
        agent_card = create_agent_card(host, port)
        
        # Create agent executor
        agent_executor = InfrastructureMonitoringExecutor()
        
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
                "agent": "Infrastructure Monitoring Agent",
                "version": "1.0.0",
                "timestamp": str(time.time())
            })

        # Build the app and add health route
        app = server.build()
        app.add_route("/health", health_check, methods=["GET"])

        logger.info("Infrastructure Monitoring Agent server configuration complete")
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