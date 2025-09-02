"""
AI Agent Router with LLM-powered intelligent agent selection.

This router uses Large Language Models to analyze user queries and 
intelligently route them to the most appropriate agent.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from openai import AzureOpenAI
import httpx

logger = logging.getLogger(__name__)


@dataclass
class AgentInfo:
    """Information about an available agent."""
    name: str
    url: str
    description: str
    capabilities: List[str]
    skills: List[str]
    
    
@dataclass 
class RoutingResult:
    """Result of agent routing decision."""
    agent_name: str
    confidence: float
    reasoning: str
    

class AgentNetwork:
    """Network of available A2A agents."""
    
    def __init__(self, name: str = "Multi-Agent Network"):
        self.name = name
        self.agents: Dict[str, AgentInfo] = {}
        
    def add(self, name: str, url: str, description: str = "", 
            capabilities: List[str] = None, skills: List[str] = None):
        """Add an agent to the network."""
        self.agents[name] = AgentInfo(
            name=name,
            url=url, 
            description=description,
            capabilities=capabilities or [],
            skills=skills or []
        )
        logger.info(f"Added agent '{name}' to network")
        
    def get_agent(self, name: str) -> Optional[AgentInfo]:
        """Get agent by name."""
        return self.agents.get(name)
        
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents with their information."""
        return [
            {
                "name": agent.name,
                "url": agent.url,
                "description": agent.description,
                "capabilities": agent.capabilities,
                "skills": agent.skills
            }
            for agent in self.agents.values()
        ]


class LLMClient:
    """LLM client for routing decisions using Azure OpenAI."""
    
    def __init__(self, azure_endpoint: str = None, api_key: str = None, 
                 deployment_name: str = "gpt-4", api_version: str = "2024-12-01-preview"):
        # Use environment variables or provided values
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment_name = deployment_name or os.getenv("AZURE_OPENAI_MODEL", "gpt-4")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        
        if not self.azure_endpoint or not self.api_key:
            raise ValueError("Azure OpenAI endpoint and API key are required. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables.")
        
        self.client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        self.model = self.deployment_name
        
    async def route_query(self, query: str, agents: Dict[str, AgentInfo]) -> RoutingResult:
        """Use LLM to determine the best agent for a query."""
        
        # Create agent context for the LLM
        agent_context = "\n".join([
            f"- {name}: {agent.description}\n  Capabilities: {', '.join(agent.capabilities)}\n  Skills: {', '.join(agent.skills)}"
            for name, agent in agents.items()
        ])
        
        prompt = f"""
You are an intelligent agent router. Analyze the user query and determine which agent should handle it.

Available Agents:
{agent_context}

User Query: "{query}"

Consider:
1. The specific task or question being asked
2. Which agent's capabilities best match the query
3. The likelihood of successful completion

Respond with a JSON object containing:
{{
    "agent_name": "exact_agent_name",
    "confidence": 0.95,
    "reasoning": "explanation of why this agent was chosen"
}}

Choose the agent most likely to successfully handle this query.
"""

        try:
            # Run the synchronous call in a thread pool to make it async
            import asyncio
            import concurrent.futures
            
            def make_openai_call():
                return self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                response = await loop.run_in_executor(executor, make_openai_call)
            
            import json
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            
            result_data = json.loads(result_text)
            
            return RoutingResult(
                agent_name=result_data["agent_name"],
                confidence=float(result_data["confidence"]),
                reasoning=result_data["reasoning"]
            )
            
        except Exception as e:
            logger.error(f"LLM routing failed: {e}")
            # Fallback to first available agent
            fallback_agent = list(agents.keys())[0]
            return RoutingResult(
                agent_name=fallback_agent,
                confidence=0.1,
                reasoning=f"Fallback routing due to error: {e}"
            )


class AIAgentRouter:
    """
    AI-powered agent router that uses LLMs to intelligently 
    select the best agent for each query.
    """
    
    def __init__(self, agent_network: AgentNetwork, llm_client: LLMClient):
        self.network = agent_network
        self.llm_client = llm_client
        self.routing_history: List[Dict] = []
        
    async def route_query(self, query: str, context: Dict = None) -> Tuple[str, float]:
        """
        Route a query to the most appropriate agent.
        
        Args:
            query: User query to route
            context: Additional context for routing decision
            
        Returns:
            Tuple of (agent_name, confidence_score)
        """
        
        # Use LLM to make routing decision
        routing_result = await self.llm_client.route_query(query, self.network.agents)
        
        # Log routing decision
        routing_record = {
            "query": query,
            "selected_agent": routing_result.agent_name,
            "confidence": routing_result.confidence,
            "reasoning": routing_result.reasoning,
            "context": context or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        
        self.routing_history.append(routing_record)
        
        logger.info(
            f"Routed query to '{routing_result.agent_name}' "
            f"(confidence: {routing_result.confidence:.2f}) - {routing_result.reasoning}"
        )
        
        return routing_result.agent_name, routing_result.confidence
        
    async def ask_agent(self, agent_name: str, query: str) -> str:
        """Send a query to a specific agent."""
        agent = self.network.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found in network")
            
        # In a real implementation, this would use the A2A protocol
        # For now, we'll simulate the response
        async with httpx.AsyncClient() as client:
            try:
                # This would be the actual A2A call
                response = await client.post(
                    f"{agent.url}/query",
                    json={"query": query},
                    timeout=30.0
                )
                return f"Response from {agent_name}: {response.text}"
            except Exception as e:
                return f"Error querying {agent_name}: {e}"
                
    async def smart_query(self, query: str, context: Dict = None) -> Dict[str, Any]:
        """
        Perform intelligent query routing and execution.
        
        Returns complete information about the routing decision and response.
        """
        
        # Route the query
        agent_name, confidence = await self.route_query(query, context)
        
        # Execute the query
        try:
            response = await self.ask_agent(agent_name, query)
            success = True
            error = None
        except Exception as e:
            response = None
            success = False
            error = str(e)
            
        return {
            "query": query,
            "routed_to": agent_name,
            "confidence": confidence,
            "response": response,
            "success": success,
            "error": error,
            "routing_history": self.routing_history[-1] if self.routing_history else None
        }
        
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        if not self.routing_history:
            return {"total_routes": 0}
            
        agent_usage = {}
        total_confidence = 0
        
        for record in self.routing_history:
            agent = record["selected_agent"]
            agent_usage[agent] = agent_usage.get(agent, 0) + 1
            total_confidence += record["confidence"]
            
        return {
            "total_routes": len(self.routing_history),
            "agent_usage": agent_usage,
            "average_confidence": total_confidence / len(self.routing_history),
            "most_used_agent": max(agent_usage.items(), key=lambda x: x[1])[0] if agent_usage else None
        }


# Factory function for easy setup
def create_ai_router(azure_endpoint: str = None, api_key: str = None, 
                    deployment_name: str = None) -> AIAgentRouter:
    """
    Create a pre-configured AI Agent Router for our multi-agent system using Azure OpenAI.
    """
    
    # Try to import Azure OpenAI utilities from common module
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from common.azure_openai import create_azure_openai_client
        
        # Use the configured Azure OpenAI client
        client = create_azure_openai_client()
        
        # Create LLM client with Azure OpenAI configuration
        llm_client = LLMClient(
            azure_endpoint=client.base_url,
            api_key=client.api_key,
            deployment_name=deployment_name or os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
            api_version=client.api_version
        )
        
    except ImportError as e:
        logger.warning(f"Could not import Azure OpenAI utilities: {e}")
        
        # Fallback to direct configuration
        azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        deployment_name = deployment_name or os.getenv("AZURE_OPENAI_MODEL", "gpt-4")
        
        if not azure_endpoint or not api_key:
            raise ValueError(
                "Azure OpenAI configuration is required. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables."
            )
        
        # Create LLM client
        llm_client = LLMClient(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            deployment_name=deployment_name
        )
    
    # Create agent network with our available agents
    network = AgentNetwork("Multi-Agent A2A System")
    
    # Add our agents
    network.add(
        "base",
        "http://localhost:8000",
        "General assistance and conversation agent with coordination capabilities",
        capabilities=["general_assistance", "conversation", "agent_coordination"],
        skills=["General Assistance", "Conversation"]
    )
    
    network.add(
        "calculator", 
        "http://localhost:8002",
        "Mathematical calculation and computation agent",
        capabilities=["mathematical_calculator", "basic_math", "advanced_calculations"],
        skills=["Mathematical Calculator"]
    )
    
    network.add(
        "weather",
        "http://localhost:8001", 
        "Weather information and forecasting agent",
        capabilities=["current_weather", "weather_forecast", "climate_info"],
        skills=["Current Weather", "Weather Forecast"]
    )
    
    network.add(
        "research",
        "http://localhost:8003",
        "Research and information gathering agent",
        capabilities=["web_search", "fact_checking", "information_gathering"],
        skills=["Web Search", "Research"]
    )
    
    # Create and return router
    router = AIAgentRouter(network, llm_client)
    
    logger.info("AI Agent Router created with Azure OpenAI and 4 agents")
    return router


# Example usage
async def main():
    """Example usage of the AI Agent Router with Azure OpenAI."""
    
    print("🤖 AI Agent Router Demo (Azure OpenAI)")
    print("=" * 50)
    
    try:
        # Create router with Azure OpenAI
        router = create_ai_router()
        
        # Example queries
        queries = [
            "What's the weather like in New York today?",
            "Calculate the square root of 144",
            "Who wrote The Great Gatsby?", 
            "Hello, how are you?",
            "What is 25 + 17 multiplied by 3?"
        ]
        
        for query in queries:
            print(f"\n📝 Query: {query}")
            
            result = await router.smart_query(query)
            
            print(f"🎯 Routed to: {result['routed_to']}")
            print(f"🎲 Confidence: {result['confidence']:.2f}")
            print(f"💬 Response: {result['response']}")
            
        # Show routing statistics
        print("\n📊 Routing Statistics:")
        stats = router.get_routing_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 To fix this, set your Azure OpenAI environment variables:")
        print("   export AZURE_OPENAI_ENDPOINT='your-endpoint'")
        print("   export AZURE_OPENAI_API_KEY='your-api-key'")
        print("   export AZURE_OPENAI_MODEL='your-deployment-name'")
    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())