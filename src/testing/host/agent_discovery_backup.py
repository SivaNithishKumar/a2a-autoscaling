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
                    for skill in getattr(agent_card, 'skills', [])
                ],
                "capabilities": {
                    "streaming": getattr(agent_card.capabilities, 'streaming', False) if agent_card.capabilities else False,
                    "extensions": [
                        {
                            "name": ext.name,
                            "version": getattr(ext, 'version', 'unknown')
                        }
                        for ext in getattr(agent_card.capabilities, 'extensions', [])
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

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from urllib.parse import urljoin

import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard

from ..config import DEFAULT_AGENTS, TEST_CONFIG
from ..utils.test_helpers import TestResult, TestStatus


logger = logging.getLogger("a2a_testing.discovery")


@dataclass
class AgentInfo:
    """Information about a discovered agent."""
    name: str
    endpoint: str
    port: int
    agent_card: Optional[AgentCard] = None
    status: str = "unknown"  # unknown, online, offline, error
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    response_time: Optional[float] = None
    capabilities: Dict[str, Any] = field(default_factory=dict)
    skills: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "port": self.port,
            "status": self.status,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "error_message": self.error_message,
            "response_time": self.response_time,
            "capabilities": self.capabilities,
            "skills": self.skills,
            "agent_card": self.agent_card.model_dump() if self.agent_card else None
        }


class AgentDiscovery:
    """
    Agent Discovery System for A2A protocol.
    
    Discovers and monitors A2A agents by:
    1. Checking configured endpoints
    2. Fetching AgentCards from /.well-known/agent.json
    3. Validating protocol compliance
    4. Monitoring agent health
    """
    
    def __init__(self, 
                 timeout: int = TEST_CONFIG["discovery_timeout"],
                 max_retries: int = TEST_CONFIG["max_retries"]):
        """
        Initialize the discovery system.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.agents: Dict[str, AgentInfo] = {}
        self.discovery_results: List[TestResult] = []
        
        # Initialize with default agent configurations
        for agent_id, config in DEFAULT_AGENTS.items():
            self.agents[agent_id] = AgentInfo(
                name=config["name"],
                endpoint=config["endpoint"],
                port=config["port"]
            )
    
    async def discover_agents(self) -> List[Dict[str, Any]]:
        """
        Discover all agents from the configured endpoints.
        
        Returns:
            List of agent information dictionaries
        """
        agents = []
        
        for agent_config in DEFAULT_AGENTS.values():
            try:
                agent_info = await self._discover_agent(agent_config["endpoint"], agent_config["name"])
                agents.append(agent_info)
            except Exception as e:
                logger.error(f"Failed to discover agent at {agent_config['endpoint']}: {e}")
                # Add failed agent info
                agents.append({
                    "name": agent_config["name"],
                    "endpoint": agent_config["endpoint"], 
                    "status": "unreachable",
                    "error": str(e),
                    "agent_card": None
                })
        
        return agents
    
    async def discover_all_agents(self) -> List[Dict[str, Any]]:
        """Alias for discover_agents for backward compatibility."""
        return await self.discover_agents()
    
    async def _discover_agent(self, client: httpx.AsyncClient, agent_id: str) -> None:
        """
        Discover a single agent.
        
        Args:
            client: HTTP client for requests
            agent_id: Agent identifier
        """
        agent = self.agents[agent_id]
        start_time = datetime.now()
        
        logger.info(f"Discovering agent: {agent.name} at {agent.endpoint}")
        
        try:
            # Test basic connectivity
            await self._check_connectivity(client, agent)
            
            # Fetch and validate AgentCard
            await self._fetch_agent_card(client, agent)
            
            # Validate protocol compliance
            await self._validate_protocol_compliance(agent)
            
            agent.status = "online"
            agent.last_check = datetime.now()
            agent.response_time = (agent.last_check - start_time).total_seconds()
            
            # Create success result
            result = TestResult(
                test_name=f"discover_{agent_id}",
                status=TestStatus.PASSED,
                start_time=start_time,
                end_time=agent.last_check,
                message=f"Successfully discovered {agent.name}",
                details={
                    "endpoint": agent.endpoint,
                    "response_time": agent.response_time,
                    "capabilities": agent.capabilities,
                    "skills_count": len(agent.skills)
                }
            )
            
        except Exception as e:
            agent.status = "error"
            agent.error_message = str(e)
            agent.last_check = datetime.now()
            
            logger.error(f"Failed to discover {agent.name}: {e}")
            
            # Create failure result
            result = TestResult(
                test_name=f"discover_{agent_id}",
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=agent.last_check,
                message=f"Failed to discover {agent.name}",
                error=e,
                details={"endpoint": agent.endpoint}
            )
        
        self.discovery_results.append(result)
    
    async def _check_connectivity(self, client: httpx.AsyncClient, agent: AgentInfo) -> None:
        """
        Check basic connectivity to agent endpoint.
        
        Args:
            client: HTTP client
            agent: Agent information
        """
        try:
            # Try to reach the agent endpoint
            response = await client.get(agent.endpoint, timeout=self.timeout)
            
            # Accept any HTTP response (some agents may not have a root endpoint)
            if response.status_code >= 500:
                raise httpx.HTTPError(f"Server error: {response.status_code}")
                
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise ConnectionError(f"Cannot connect to {agent.endpoint}: {e}")
    
    async def _fetch_agent_card(self, client: httpx.AsyncClient, agent: AgentInfo) -> None:
        """
        Fetch and parse the agent's AgentCard.
        
        Args:
            client: HTTP client
            agent: Agent information
        """
        try:
            # Use A2A's built-in card resolver
            card_resolver = A2ACardResolver(client, agent.endpoint)
            agent_card = await card_resolver.get_agent_card()
            
            agent.agent_card = agent_card
            
            # Extract capabilities and skills
            if agent_card.capabilities:
                agent.capabilities = {
                    "streaming": getattr(agent_card.capabilities, "streaming", False),
                    "extensions": [ext.model_dump() if hasattr(ext, "model_dump") else ext 
                                 for ext in getattr(agent_card.capabilities, "extensions", [])]
                }
            
            if agent_card.skills:
                agent.skills = [skill.model_dump() if hasattr(skill, "model_dump") else skill 
                              for skill in agent_card.skills]
            
            logger.info(f"Fetched AgentCard for {agent.name}: {len(agent.skills)} skills")
            
        except Exception as e:
            raise ValueError(f"Failed to fetch AgentCard from {agent.endpoint}: {e}")
    
    async def _validate_protocol_compliance(self, agent: AgentInfo) -> None:
        """
        Validate that the agent follows A2A protocol standards.
        
        Args:
            agent: Agent information with loaded AgentCard
        """
        if not agent.agent_card:
            raise ValueError("No AgentCard available for validation")
        
        card = agent.agent_card
        
        # Validate required fields
        required_fields = ["name", "url", "version"]
        missing_fields = [field for field in required_fields 
                         if not getattr(card, field, None)]
        
        if missing_fields:
            raise ValueError(f"AgentCard missing required fields: {missing_fields}")
        
        # Validate URL matches endpoint
        if not card.url.startswith(agent.endpoint.rstrip("/")):
            logger.warning(f"AgentCard URL {card.url} doesn't match endpoint {agent.endpoint}")
        
        # Validate skills format
        if card.skills:
            for i, skill in enumerate(card.skills):
                if not hasattr(skill, "id") or not getattr(skill, "id"):
                    raise ValueError(f"Skill {i} missing required 'id' field")
                if not hasattr(skill, "name") or not getattr(skill, "name"):
                    raise ValueError(f"Skill {i} missing required 'name' field")
        
        logger.debug(f"Protocol validation passed for {agent.name}")
    
    async def health_check(self, agent_id: str) -> bool:
        """
        Perform health check on a specific agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if agent is healthy, False otherwise
        """
        if agent_id not in self.agents:
            return False
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                await self._discover_agent(client, agent_id)
                return self.agents[agent_id].status == "online"
            except Exception:
                return False
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all agents.
        
        Returns:
            Dictionary of agent_id -> health status
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = []
            for agent_id in self.agents.keys():
                task = self._discover_agent(client, agent_id)
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return {agent_id: agent.status == "online" 
                for agent_id, agent in self.agents.items()}
    
    def get_online_agents(self) -> Dict[str, AgentInfo]:
        """Get all agents that are currently online."""
        return {agent_id: agent for agent_id, agent in self.agents.items() 
                if agent.status == "online"}
    
    def get_agent_by_endpoint(self, endpoint: str) -> Optional[AgentInfo]:
        """Get agent information by endpoint URL."""
        for agent in self.agents.values():
            if agent.endpoint == endpoint:
                return agent
        return None
    
    def get_agents_with_skill(self, skill_id: str) -> List[AgentInfo]:
        """Get all agents that have a specific skill."""
        agents_with_skill = []
        for agent in self.agents.values():
            if agent.status == "online" and agent.skills:
                for skill in agent.skills:
                    if isinstance(skill, dict) and skill.get("id") == skill_id:
                        agents_with_skill.append(agent)
                        break
        return agents_with_skill
    
    def generate_discovery_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive discovery report.
        
        Returns:
            Dictionary containing discovery results and statistics
        """
        online_agents = self.get_online_agents()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_agents": len(self.agents),
                "online_agents": len(online_agents),
                "offline_agents": len(self.agents) - len(online_agents),
                "success_rate": len(online_agents) / len(self.agents) if self.agents else 0
            },
            "agents": {agent_id: agent.to_dict() 
                      for agent_id, agent in self.agents.items()},
            "capabilities_summary": self._summarize_capabilities(online_agents),
            "skills_summary": self._summarize_skills(online_agents),
            "test_results": [result.to_dict() for result in self.discovery_results]
        }
        
        return report
    
    def _summarize_capabilities(self, agents: Dict[str, AgentInfo]) -> Dict[str, Any]:
        """Summarize capabilities across all online agents."""
        streaming_count = sum(1 for agent in agents.values() 
                            if agent.capabilities.get("streaming", False))
        
        all_extensions = set()
        for agent in agents.values():
            extensions = agent.capabilities.get("extensions", [])
            for ext in extensions:
                if isinstance(ext, dict):
                    all_extensions.add(ext.get("name", "unknown"))
                else:
                    all_extensions.add(str(ext))
        
        return {
            "streaming_support": streaming_count,
            "unique_extensions": list(all_extensions),
            "total_extensions": len(all_extensions)
        }
    
    def _summarize_skills(self, agents: Dict[str, AgentInfo]) -> Dict[str, Any]:
        """Summarize skills across all online agents."""
        all_skills = {}
        total_skills = 0
        
        for agent in agents.values():
            for skill in agent.skills:
                if isinstance(skill, dict):
                    skill_id = skill.get("id", "unknown")
                    if skill_id not in all_skills:
                        all_skills[skill_id] = {
                            "name": skill.get("name", skill_id),
                            "agents": []
                        }
                    all_skills[skill_id]["agents"].append(agent.name)
                    total_skills += 1
        
        return {
            "total_skills": total_skills,
            "unique_skills": len(all_skills),
            "skills_by_id": all_skills
        }
