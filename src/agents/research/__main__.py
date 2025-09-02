"""
Research Agent Server

Main entry point for the Research Agent A2A server.
A specialized agent for web searches, fact checking, and research tasks.
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

from .agent_executor import ResearchAgentExecutor


def create_agent_card(host: str = "localhost", port: int = 8003) -> AgentCard:
    """Create the agent card for the Research Agent."""
    skills = [
        AgentSkill(
            id='web_search',
            name='Web Search',
            description='Search the web for information and return relevant results',
            tags=['search', 'web', 'information', 'research'],
            examples=[
                'Search for information about artificial intelligence',
                'Find recent news about climate change',
                'Look up facts about space exploration',
                'Search for Python programming tutorials'
            ],
        ),
        AgentSkill(
            id='fact_checking',
            name='Fact Checking',
            description='Verify facts and claims with evidence-based analysis',
            tags=['facts', 'verification', 'analysis', 'truth'],
            examples=[
                'Verify this claim about renewable energy',
                'Check if this scientific statement is accurate',
                'Is it true that Python was created in 1991?',
                'Fact-check this news claim'
            ],
        ),
        AgentSkill(
            id='content_analysis',
            name='Content Analysis',
            description='Analyze and summarize content from web sources',
            tags=['content', 'analysis', 'summary', 'research'],
            examples=[
                'Summarize this article about machine learning',
                'Analyze the main points in this research paper',
                'Extract key information from this webpage',
                'What are the main themes in this content?'
            ],
        ),
        AgentSkill(
            id='research_topics',
            name='Research Topics',
            description='Conduct comprehensive research on specific topics',
            tags=['research', 'topics', 'comprehensive', 'analysis'],
            examples=[
                'Research the latest developments in quantum computing',
                'Investigate the effects of social media on mental health',
                'Research sustainable energy solutions',
                'Study the history of artificial intelligence'
            ],
        ),
    ]
    
    capabilities = AgentCapabilities(
        streaming=True,
        push_notifications=False,
        state_transition_history=True,
    )
    
    return AgentCard(
        name='Research Agent',
        description='A specialized research agent for web searches, fact checking, and information analysis',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=capabilities,
        skills=skills,
    )


@click.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=8003, help='Port to bind the server to')
@click.option('--log-level', default='info', help='Logging level')
def main(host: str, port: int, log_level: str) -> None:
    """Start the Research Agent A2A server."""
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Research Agent server...")
        
        # Create agent card
        agent_card = create_agent_card(host, port)
        
        # Create agent executor
        agent_executor = ResearchAgentExecutor()
        
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
                "agent": "Research Agent",
                "version": "1.0.0",
                "timestamp": str(time.time())
            })
        
        # Build the app and add health route
        app = server.build()
        app.add_route("/health", health_check, methods=["GET"])

        logger.info("Research Agent server configuration complete")
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


if __name__ == "__main__":
    main()
