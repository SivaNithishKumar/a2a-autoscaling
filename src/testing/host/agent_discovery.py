"""
Agent Discovery System

Automatically discovers and connects to A2A agents using proven patterns
from the a2a-samples repository.
"""

import asyncio
import logging
from typing import Dict, List, Optional
import httpx

from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import AgentCard, TransportProtocol

from ..config import DEFAULT_AGENTS, TEST_CONFIG
from ..utils.test_helpers import TestResult, TestStatus


logger = logging.getLogger(__name__)


class AgentDiscovery:
    """
    Discovers and manages connections to A2A agents.
    
    Uses the proven patterns from a2a-samples hosts for proper
    agent discovery and connection management.
    """
    
    def __init__(self, timeout: int = TEST_CONFIG["discovery_timeout"]):
        """Initialize the agent discovery system."""
        self.timeout = timeout
        self.discovered_agents: Dict[str, Dict] = {}
        self.agent_cards: Dict[str, AgentCard] = {}
        self.httpx_client: Optional[httpx.AsyncClient] = None
        self.client_factory: Optional[ClientFactory] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.httpx_client = httpx.AsyncClient(timeout=self.timeout)
        
        # Create client factory with proper configuration
        config = ClientConfig(
            httpx_client=self.httpx_client,
            supported_transports=[
                TransportProtocol.jsonrpc,
                TransportProtocol.http_json,
            ],
        )
        self.client_factory = ClientFactory(config)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.httpx_client:
            await self.httpx_client.aclose()
    
    async def discover_agents(self, endpoints: Optional[List[str]] = None) -> List[Dict]:
        """
        Discover agents from the given endpoints.
        
        Args:
            endpoints: List of agent endpoints to discover. If None, uses default agents.
            
        Returns:
            List of discovered agent information dictionaries.
        """
        if endpoints is None:
            endpoints = [agent["endpoint"] for agent in DEFAULT_AGENTS.values()]
        
        logger.info(f"🔍 Starting agent discovery for {len(endpoints)} endpoints...")
        
        # Use async context manager if not already initialized
        if self.httpx_client is None:
            async with self:
                return await self._discover_agents_internal(endpoints)
        else:
            return await self._discover_agents_internal(endpoints)
    
    async def _discover_agents_internal(self, endpoints: List[str]) -> List[Dict]:
        """Internal method to discover agents."""
        discovery_tasks = []
        
        for endpoint in endpoints:
            task = asyncio.create_task(
                self._discover_single_agent(endpoint),
                name=f"discover_{endpoint}"
            )
            discovery_tasks.append(task)
        
        # Wait for all discovery tasks to complete
        results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
        
        agents = []
        for i, result in enumerate(results):
            endpoint = endpoints[i]
            if isinstance(result, Exception):
                logger.error(f"❌ Failed to discover agent at {endpoint}: {result}")
                agents.append({
                    "name": f"Unknown Agent ({endpoint})",
                    "endpoint": endpoint,
                    "status": "error",
                    "error": str(result)
                })
            else:
                agents.append(result)
        
        logger.info(f"✅ Discovery complete: {len([a for a in agents if a['status'] == 'available'])} agents available")
        return agents
    
    async def _discover_single_agent(self, endpoint: str) -> Dict:
        """
        Discover a single agent using A2ACardResolver.
        
        Args:
            endpoint: The agent endpoint URL.
            
        Returns:
            Dictionary with agent information.
        """
        try:
            logger.debug(f"🔎 Discovering agent at {endpoint}")
            
            # Use A2ACardResolver to get the agent card (proven pattern)
            card_resolver = A2ACardResolver(self.httpx_client, endpoint)
            agent_card = await card_resolver.get_agent_card()
            
            # Store the agent card
            self.agent_cards[agent_card.name] = agent_card
            
            # Create agent info
            agent_info = {
                "name": agent_card.name,
                "endpoint": endpoint,
                "status": "available",
                "agent_card": agent_card.model_dump(exclude_none=True),
                "version": getattr(agent_card, 'version', 'unknown'),
                "description": getattr(agent_card, 'description', ''),
                "skills": [
                    {
                        "id": skill.id,
                        "name": skill.name,
                        "description": skill.description,
                        "examples": getattr(skill, 'examples', [])
                    }
                    for skill in (getattr(agent_card, 'skills', None) or [])
                ],
                "capabilities": {
                    "streaming": getattr(agent_card.capabilities, 'streaming', False) if agent_card.capabilities else False,
                    "extensions": [
                        {
                            "name": ext.name,
                            "version": getattr(ext, 'version', 'unknown')
                        }
                        for ext in (getattr(agent_card.capabilities, 'extensions', None) or [])
                    ] if agent_card.capabilities else []
                }
            }
            
            self.discovered_agents[agent_card.name] = agent_info
            logger.debug(f"✅ Successfully discovered {agent_card.name} at {endpoint}")
            
            return agent_info
            
        except Exception as e:
            logger.error(f"❌ Failed to discover agent at {endpoint}: {e}")
            return {
                "name": f"Unknown Agent ({endpoint})",
                "endpoint": endpoint, 
                "status": "unavailable",
                "error": str(e)
            }
    
    def get_agent_card(self, agent_name: str) -> Optional[AgentCard]:
        """Get the agent card for a discovered agent."""
        return self.agent_cards.get(agent_name)
    
    def get_discovered_agents(self) -> Dict[str, Dict]:
        """Get all discovered agents."""
        return self.discovered_agents.copy()
    
    def get_available_agents(self) -> List[Dict]:
        """Get only available agents."""
        return [
            agent for agent in self.discovered_agents.values()
            if agent["status"] == "available"
        ]
    
    async def test_agent_connectivity(self, agent_name: str) -> TestResult:
        """
        Test basic connectivity to a discovered agent.
        
        Args:
            agent_name: Name of the agent to test.
            
        Returns:
            TestResult with connectivity test results.
        """
        from datetime import datetime
        
        start_time = datetime.now()
        
        if agent_name not in self.discovered_agents:
            return TestResult(
                test_name=f"connectivity_{agent_name}",
                status=TestStatus.ERROR,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Agent {agent_name} not discovered",
                error=ValueError(f"Agent {agent_name} not found in discovered agents")
            )
        
        agent_info = self.discovered_agents[agent_name]
        
        if agent_info["status"] != "available":
            return TestResult(
                test_name=f"connectivity_{agent_name}",
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Agent {agent_name} is not available: {agent_info.get('error', 'Unknown error')}"
            )
        
        try:
            # Test basic HTTP connectivity
            response = await self.httpx_client.get(f"{agent_info['endpoint']}/.well-known/agent.json")
            response.raise_for_status()
            
            return TestResult(
                test_name=f"connectivity_{agent_name}",
                status=TestStatus.PASSED,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Successfully connected to {agent_name}",
                details={
                    "endpoint": agent_info["endpoint"],
                    "status_code": response.status_code,
                    "response_time": (datetime.now() - start_time).total_seconds()
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name=f"connectivity_{agent_name}",
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Failed to connect to {agent_name}: {str(e)}",
                error=e
            )
