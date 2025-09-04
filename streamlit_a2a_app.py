#!/usr/bin/env python3
"""
Enhanced A2A Multi-Agent Streamlit Client

Production-ready Streamlit interface for Google's A2A Protocol with:
- Multi-step intelligent orchestration
- Real-time agent discovery and health monitoring
- LLM-powered query routing and execution planning
- Comprehensive conversation management
- Integration with 6-agent A2A ecosystem

Author: Enhanced for Just Move In Interview Demo
"""

import asyncio
import json
import logging
import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import streamlit as st
import httpx
import time
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import A2A SDK components - using new non-deprecated APIs
from a2a.client import A2ACardResolver
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
    Message,
    TextPart,
    Part
)
from uuid import uuid4
import asyncio
import threading

# Import Azure OpenAI for intelligent routing
try:
    from openai import AzureOpenAI
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logger.warning("Azure OpenAI not available - using simple routing")

# Load environment variables
import os
from dotenv import load_dotenv
load_dotenv()

# Corrected Agent endpoints configuration based on actual startup scripts
# Agent endpoints configuration with Kubernetes support
# Supports both local development and Kubernetes deployment
def get_agent_endpoints():
    """Get agent endpoints based on environment (local or Kubernetes)"""
    
    # Check if running in Kubernetes environment
    in_k8s = os.getenv("KUBERNETES_SERVICE_HOST") is not None
    namespace = os.getenv("NAMESPACE", "multi-agent-a2a")
    
    if in_k8s:
        # Kubernetes internal service discovery
        base_url_template = "http://{service_name}.{namespace}.svc.cluster.local:{port}"
        endpoints = {
            "base": {
                "url": base_url_template.format(
                    service_name="base-agent-service", 
                    namespace=namespace, 
                    port=8080
                ),
                "name": "Base Agent",
                "description": "General-purpose conversational agent for basic queries and assistance",
                "specialties": ["general conversation", "basic questions", "help", "greetings", "coordination"]
            },
            "calculator": {
                "url": base_url_template.format(
                    service_name="calculator-agent-service", 
                    namespace=namespace, 
                    port=8081
                ),
                "name": "Calculator Agent", 
                "description": "Mathematical calculations, equations, and numerical analysis",
                "specialties": ["math", "calculations", "equations", "numbers", "arithmetic", "algebra", "statistics"]
            },
            "weather": {
                "url": base_url_template.format(
                    service_name="weather-agent-service", 
                    namespace=namespace, 
                    port=8082
                ),
                "name": "Weather Agent",
                "description": "Weather information, forecasts, and climate data", 
                "specialties": ["weather", "forecast", "temperature", "climate", "rain", "snow", "wind"]
            },
            "research": {
                "url": base_url_template.format(
                    service_name="research-agent-service", 
                    namespace=namespace, 
                    port=8083
                ),
                "name": "Research Agent",
                "description": "Research assistance, information gathering, and analysis",
                "specialties": ["research", "information", "analysis", "facts", "data", "investigation"]
            },
            "move_orchestrator": {
                "url": base_url_template.format(
                    service_name="move-orchestrator-agent-service", 
                    namespace=namespace, 
                    port=8004
                ),
                "name": "Move Orchestrator",
                "description": "Moving and relocation assistance, logistics coordination",
                "specialties": ["moving", "relocation", "logistics", "coordination", "planning", "organization"]
            },
            "infrastructure_monitor": {
                "url": base_url_template.format(
                    service_name="infrastructure-monitor-agent-service", 
                    namespace=namespace, 
                    port=8005
                ),
                "name": "Infrastructure Monitor",
                "description": "System monitoring, infrastructure health, and performance analysis",
                "specialties": ["monitoring", "infrastructure", "system health", "performance", "alerts", "metrics"]
            }
        }
    else:
        # Local development with environment variable overrides
        endpoints = {
            "base": {
                "url": os.getenv("BASE_AGENT_URL", "http://localhost:8080"),
                "name": "Base Agent",
                "description": "General-purpose conversational agent for basic queries and assistance",
                "specialties": ["general conversation", "basic questions", "help", "greetings", "coordination"]
            },
            "calculator": {
                "url": os.getenv("CALCULATOR_AGENT_URL", "http://localhost:8081"),
                "name": "Calculator Agent",
                "description": "Mathematical calculations, equations, and numerical analysis",
                "specialties": ["math", "calculations", "equations", "numbers", "arithmetic", "algebra", "statistics"]
            },
            "weather": {
                "url": os.getenv("WEATHER_AGENT_URL", "http://localhost:8082"),
                "name": "Weather Agent",
                "description": "Weather information, forecasts, and climate data",
                "specialties": ["weather", "forecast", "temperature", "climate", "rain", "snow", "wind"]
            },
            "research": {
                "url": os.getenv("RESEARCH_AGENT_URL", "http://localhost:8083"),
                "name": "Research Agent",
                "description": "Research assistance, information gathering, and analysis",
                "specialties": ["research", "information", "analysis", "facts", "data", "investigation"]
            },
            "move_orchestrator": {
                "url": os.getenv("MOVE_ORCHESTRATOR_URL", "http://localhost:8004"),
                "name": "Move Orchestrator",
                "description": "Moving and relocation assistance, logistics coordination",
                "specialties": ["moving", "relocation", "logistics", "coordination", "planning", "organization"]
            },
            "infrastructure_monitor": {
                "url": os.getenv("INFRASTRUCTURE_MONITOR_URL", "http://localhost:8005"),
                "name": "Infrastructure Monitor",
                "description": "System monitoring, infrastructure health, and performance analysis",
                "specialties": ["monitoring", "infrastructure", "system health", "performance", "alerts", "metrics"]
            }
        }
    
    return endpoints

# Get agent endpoints based on environment
AGENT_ENDPOINTS = get_agent_endpoints()

@dataclass
class ExecutionStep:
    """Represents a single step in multi-agent execution plan."""
    agent: str
    task: str
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class ExecutionPlan:
    """Represents complete execution plan for multi-agent orchestration."""
    steps: List[ExecutionStep]
    execution_type: str = "sequential"  # sequential, parallel, hybrid

class AzureOpenAIClient:
    """Azure OpenAI client for intelligent routing and planning with robust fallback."""

    def __init__(self):
        self.client = None
        self.azure_available = False

        if AZURE_AVAILABLE:
            try:
                # Get credentials from environment
                api_key = os.getenv("AZURE_OPENAI_API_KEY")
                endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

                if api_key and endpoint:
                    # Validate API key format (Azure OpenAI keys can be 32, 64, or 84 characters)
                    if len(api_key) not in [32, 64, 84]:
                        logger.warning(f"Unusual Azure OpenAI API key length: {len(api_key)}. Expected 32, 64, or 84 characters.")

                    self.client = AzureOpenAI(
                        api_key=api_key,
                        api_version=api_version,
                        azure_endpoint=endpoint
                    )

                    # Test the connection
                    self._test_connection()

                else:
                    logger.warning("Azure OpenAI credentials not found in environment")
                    self.client = None
            except Exception as e:
                logger.warning(f"Failed to initialize Azure OpenAI: {e}")
                self.client = None

        if self.client and self.azure_available:
            logger.info("✅ Azure OpenAI client initialized and tested successfully")
        else:
            logger.info("🔄 Using intelligent fallback routing (Azure OpenAI not available)")

    def _test_connection(self):
        """Test Azure OpenAI connection with a simple request."""
        try:
            # Simple test to verify the connection works
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1"),
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
                temperature=0
            )
            self.azure_available = True
            logger.info("Azure OpenAI connection test successful")
        except Exception as e:
            logger.warning(f"Azure OpenAI connection test failed: {e}")
            self.azure_available = False
            self.client = None

    async def complete(self, prompt: str, max_tokens: int = 1000) -> str:
        """Complete a prompt using Azure OpenAI with structured response."""
        if not self.client:
            # Fallback to simple routing
            return self._simple_routing_fallback(prompt)

        try:
            # Get the deployment name (this is the key fix!)
            deployment_name = os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1")

            # Use structured response format for better JSON parsing
            response = self.client.chat.completions.create(
                model=deployment_name,  # This should be the deployment name, not model name
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that responds only in valid JSON format. Always return properly formatted JSON without any additional text or formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI completion failed: {e}")
            return self._simple_routing_fallback(prompt)

    def _simple_routing_fallback(self, prompt: str) -> str:
        """Simple fallback routing when Azure OpenAI is not available."""
        prompt_lower = prompt.lower()

        # Create proper JSON structure
        import json

        if any(word in prompt_lower for word in ['calculate', 'math', 'compute', 'number']):
            agent = "calculator"
        elif any(word in prompt_lower for word in ['weather', 'temperature', 'forecast']):
            agent = "weather"
        elif any(word in prompt_lower for word in ['research', 'search', 'find', 'information']):
            agent = "research"
        elif any(word in prompt_lower for word in ['move', 'moving', 'relocation', 'orchestrate']):
            agent = "move_orchestrator"
        elif any(word in prompt_lower for word in ['monitor', 'infrastructure', 'system', 'health']):
            agent = "infrastructure_monitor"
        else:
            agent = "base"

        # Return properly formatted JSON
        response = {
            "execution_type": "sequential",
            "steps": [
                {
                    "agent": agent,
                    "task": prompt,
                    "dependencies": []
                }
            ]
        }

        return json.dumps(response)

class A2AAgentClient:
    """Modern A2A client that avoids deprecated APIs and handles asyncio properly."""

    def __init__(self, agent_url: str, agent_card: Any = None):
        self.agent_url = agent_url
        self.agent_card = agent_card
        self._httpx_client = None

    def send_message(self, message: str, context_id: str = None) -> Dict[str, Any]:
        """Send message using thread-safe async execution."""
        # Run async code in a separate thread to avoid event loop conflicts
        import concurrent.futures

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._send_message_async(message, context_id))
            finally:
                loop.close()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result()

    async def _send_message_async(self, message: str, context_id: str = None) -> Dict[str, Any]:
        """Send message using direct HTTP calls to avoid deprecated A2AClient."""
        try:
            if not self._httpx_client:
                self._httpx_client = httpx.AsyncClient(timeout=30.0)

            # Get agent card if not already cached
            if not self.agent_card:
                resolver = A2ACardResolver(
                    httpx_client=self._httpx_client,
                    base_url=self.agent_url
                )
                agent_card = await resolver.get_agent_card()
                self.agent_card = agent_card.model_dump()

            # Create JSON-RPC request directly (using correct A2A method name)
            request_data = {
                "jsonrpc": "2.0",
                "id": str(uuid4()),
                "method": "send_message",  # Fixed: use snake_case method name
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [
                            {"kind": "text", "text": message}
                        ],
                        "messageId": uuid4().hex,
                    }
                }
            }

            # Send HTTP request directly
            response = await self._httpx_client.post(
                f"{self.agent_url}/",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            # Parse JSON-RPC response
            json_response = response.json()

            if "error" in json_response:
                return {
                    "success": False,
                    "error": json_response["error"]["message"],
                    "response": json_response
                }

            # Extract content from A2A response structure
            content = None

            # A2A responses have this structure:
            # {"jsonrpc": "2.0", "id": "...", "result": {...}}
            if isinstance(json_response, dict) and 'result' in json_response:
                result = json_response['result']

                if isinstance(result, dict):
                    # Path 1: Task response with artifacts - combine all artifact texts
                    if 'artifacts' in result and result['artifacts']:
                        artifact_texts = []
                        for artifact in result['artifacts']:
                            if 'parts' in artifact and artifact['parts']:
                                for part in artifact['parts']:
                                    if 'kind' in part and part['kind'] == 'text' and 'text' in part:
                                        text = part['text'].strip()
                                        if text:  # Only add non-empty text
                                            artifact_texts.append(text)

                        if artifact_texts:
                            content = '\n'.join(artifact_texts)

                    # Path 2: Task with status message (for errors or input required)
                    if not content and 'status' in result:
                        status = result['status']
                        if isinstance(status, dict) and 'message' in status:
                            message_obj = status['message']
                            if 'parts' in message_obj and message_obj['parts']:
                                part = message_obj['parts'][0]
                                if 'text' in part:
                                    content = part['text']

                    # Path 3: Direct message response - result.parts[0].text
                    if not content and 'parts' in result and result['parts']:
                        part = result['parts'][0]
                        if 'type' in part and part['type'] == 'text' and 'text' in part:
                            content = part['text']
                        elif 'kind' in part and part['kind'] == 'text' and 'text' in part:
                            content = part['text']

            if content:
                return {
                    "success": True,
                    "response": content,  # Put extracted content in response field for orchestration
                    "raw_response": json_response,  # Keep raw response for debugging
                    "content": content  # Keep content field for backward compatibility
                }
            else:
                # If we can't extract content, return the full response as string
                response_str = str(json_response)
                return {
                    "success": True,
                    "response": response_str,  # Put string representation in response field
                    "raw_response": json_response,
                    "content": response_str
                }

        except Exception as e:
            logger.error(f"Error sending message to {self.agent_url}: {e}")
            error_msg = f"Error communicating with agent: {e}"
            return {
                "success": False,
                "error": str(e),
                "response": error_msg,  # Put error message in response field
                "content": error_msg,
                "context_id": context_id or str(uuid4()),
                "timestamp": datetime.now().isoformat()
            }

    async def cleanup(self):
        """Clean up resources."""
        if self._httpx_client:
            await self._httpx_client.aclose()
            self._httpx_client = None

class IntelligentOrchestrator:
    """
    Enhanced multi-agent orchestrator with LLM-powered planning and execution.
    Supports single-agent routing and multi-step orchestration.
    """

    def __init__(self):
        self.agent_descriptions = self._build_agent_descriptions()
        self.llm_client = AzureOpenAIClient()

    def _build_agent_descriptions(self) -> str:
        """Build a comprehensive description of all available agents."""
        descriptions = []
        for agent_id, config in AGENT_ENDPOINTS.items():
            desc = f"- {config['name']} ({agent_id}): {config['description']}"
            desc += f"\n  Specialties: {', '.join(config['specialties'])}"
            descriptions.append(desc)
        return "\n".join(descriptions)

    async def create_execution_plan(self, user_query: str) -> ExecutionPlan:
        """Create intelligent execution plan for complex queries."""

        planning_prompt = f"""
        Analyze this user query and create an execution plan using available agents.

        Query: "{user_query}"

        Available Agents:
        {self.agent_descriptions}

        Determine:
        1. Is this a simple query (single agent) or complex query (multiple agents)?
        2. Which agents are needed and in what order?
        3. What specific tasks should each agent perform?
        4. Are there dependencies between tasks?

        For simple queries, return a single step.
        For complex queries, break down into logical steps.

        Return JSON format:
        {{
            "execution_type": "sequential|parallel|hybrid",
            "steps": [
                {{"agent": "agent_id", "task": "specific_task", "dependencies": ["agent_id1", "agent_id2"]}}
            ]
        }}

        Examples:
        - "What's 15 + 25?" → single calculator step
        - "Plan my move from London to Manchester on Oct 15, budget £2500" → multiple steps (weather, research, calculator, move_orchestrator)
        """

        try:
            response = await self.llm_client.complete(planning_prompt, max_tokens=800)

            # Parse JSON response more robustly
            import json

            try:
                # Try to parse the response directly as JSON
                plan_data = json.loads(response)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")

            # Create execution steps
            steps = []
            for step_data in plan_data.get("steps", []):
                step = ExecutionStep(
                    agent=step_data["agent"],
                    task=step_data["task"],
                    dependencies=step_data.get("dependencies", [])
                )
                steps.append(step)

            return ExecutionPlan(
                steps=steps,
                execution_type=plan_data.get("execution_type", "sequential")
            )

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return self._simple_routing_fallback(user_query)

    def _simple_routing_fallback(self, user_query: str) -> ExecutionPlan:
        """Fallback to simple single-agent routing."""
        query_lower = user_query.lower()

        if any(word in query_lower for word in ['calculate', 'math', 'compute', 'number']):
            agent = "calculator"
        elif any(word in query_lower for word in ['weather', 'temperature', 'forecast']):
            agent = "weather"
        elif any(word in query_lower for word in ['research', 'search', 'find', 'information']):
            agent = "research"
        elif any(word in query_lower for word in ['move', 'moving', 'relocation', 'orchestrate']):
            agent = "move_orchestrator"
        elif any(word in query_lower for word in ['monitor', 'infrastructure', 'system', 'health']):
            agent = "infrastructure_monitor"
        else:
            agent = "base"

        return ExecutionPlan(
            steps=[ExecutionStep(agent=agent, task=user_query)],
            execution_type="sequential"
        )

    async def _send_a2a_message(self, agent_client: A2AAgentClient, message_text: str) -> Dict[str, Any]:
        """Send message using modern A2A client."""
        try:
            # Use the new client's send_message method (it handles async internally)
            return agent_client.send_message(message_text)

        except Exception as e:
            logger.error(f"A2A message send failed: {e}")
            error_msg = f"Error communicating with agent: {e}"
            return {
                "success": False,
                "error": str(e),
                "response": error_msg,
                "content": error_msg
            }

    async def execute_plan(self, plan: ExecutionPlan, agent_clients: Dict[str, A2AAgentClient]) -> Dict[str, Any]:
        """Execute the multi-agent plan and return consolidated results."""

        results = {}
        executed_steps = set()

        if plan.execution_type == "sequential":
            # Execute steps in order
            for i, step in enumerate(plan.steps):
                # Wait for dependencies
                for dep in step.dependencies:
                    if dep not in results:
                        logger.warning(f"Dependency {dep} not found for step {i}")

                # Execute step with context from previous results
                enhanced_task = self._enhance_task_with_context(step.task, step.dependencies, results)

                if step.agent in agent_clients:
                    result = await self._send_a2a_message(agent_clients[step.agent], enhanced_task)
                    results[step.agent] = result
                    executed_steps.add(i)
                else:
                    logger.error(f"Agent {step.agent} not available")
                    results[step.agent] = {"success": False, "error": f"Agent {step.agent} not available"}

        elif plan.execution_type == "parallel":
            # Execute independent steps concurrently
            tasks = []
            for i, step in enumerate(plan.steps):
                if not step.dependencies:  # No dependencies = can run in parallel
                    if step.agent in agent_clients:
                        task = asyncio.create_task(
                            self._send_a2a_message(agent_clients[step.agent], step.task)
                        )
                        tasks.append((step.agent, task))

            # Wait for all parallel tasks
            for agent_name, task in tasks:
                try:
                    result = await task
                    results[agent_name] = result
                except Exception as e:
                    results[agent_name] = {"success": False, "error": str(e)}

        return results

    def _enhance_task_with_context(self, task: str, dependencies: List[str], results: Dict[str, Any]) -> str:
        """Enhance task with context from dependency results."""
        if not dependencies or not results:
            return task

        context_parts = []
        for dep in dependencies:
            if dep in results and results[dep].get("success"):
                response_text = results[dep].get("response", "")
                if response_text:
                    context_parts.append(f"{dep}_result: {response_text[:200]}")

        if context_parts:
            context = "\n".join(context_parts)
            return f"{task}\n\nContext from previous steps:\n{context}"

        return task

    async def synthesize_response(self, query: str, results: Dict[str, Any]) -> str:
        """Synthesize final response from multiple agent results."""

        if len(results) == 1:
            # Single agent response
            agent_result = list(results.values())[0]
            if agent_result.get("success"):
                response_content = agent_result.get("response", "No response available")
                # Safely convert to string
                if isinstance(response_content, str):
                    return response_content
                else:
                    return str(response_content)
            else:
                return f"Error: {agent_result.get('error', 'Unknown error')}"

        # Multi-agent synthesis
        synthesis_prompt = f"""
        Original Query: "{query}"

        Results from multiple agents:
        """

        for agent, result in results.items():
            if result.get("success"):
                response_content = result.get("response", "No response")
                # Safely convert to string and truncate
                if isinstance(response_content, str):
                    response_text = response_content[:300]
                else:
                    response_text = str(response_content)[:300]
                synthesis_prompt += f"\n{agent}: {response_text}"
            else:
                synthesis_prompt += f"\n{agent}: Error - {result.get('error', 'Unknown error')}"

        synthesis_prompt += """

        Synthesize these results into a coherent, comprehensive response that fully answers the original query.
        Include specific details and actionable recommendations.
        """

        try:
            synthesized = await self.llm_client.complete(synthesis_prompt, max_tokens=1000)
            return synthesized
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            # Fallback: concatenate results
            response_parts = []
            for agent, result in results.items():
                if result.get("success"):
                    response_content = result.get('response', '')
                    # Safely convert to string
                    if isinstance(response_content, str):
                        response_text = response_content
                    else:
                        response_text = str(response_content)
                    response_parts.append(f"**{agent}**: {response_text}")

            return "\n\n".join(response_parts) if response_parts else "No successful responses received"

class EnhancedA2AStreamlitClient:
    """
    Enhanced A2A client for Streamlit with multi-agent orchestration capabilities.
    Supports both simple routing and complex multi-step workflows.
    """

    def __init__(self):
        self.orchestrator = IntelligentOrchestrator()
        self.agent_clients: Dict[str, A2AAgentClient] = {}
        self.agent_cards: Dict[str, Dict] = {}
        self.session_id = str(uuid.uuid4())
        self.httpx_client = None  # Keep httpx client alive

    async def initialize_agents(self) -> Dict[str, Dict]:
        """Discover and initialize connections to all available agents using real A2A SDK."""
        discovered_agents = {}

        # Create persistent httpx client
        if not self.httpx_client:
            self.httpx_client = httpx.AsyncClient(timeout=30.0)

        httpx_client = self.httpx_client

        for agent_id, config in AGENT_ENDPOINTS.items():
            try:
                # Get agent card using A2ACardResolver (correct A2A SDK pattern)
                resolver = A2ACardResolver(
                    httpx_client=httpx_client,
                    base_url=config['url']
                )
                agent_card = await resolver.get_agent_card()
                agent_card_data = agent_card.model_dump()

                # Create A2A client using the modern approach (no deprecated APIs)
                agent_client = A2AAgentClient(
                    agent_url=config['url'],
                    agent_card=agent_card_data
                )

                # Store agent card and create client
                self.agent_cards[agent_id] = agent_card_data
                self.agent_clients[agent_id] = agent_client

                discovered_agents[agent_id] = {
                    **config,
                    "status": "online",
                    "card": agent_card_data,
                    "last_seen": datetime.now().isoformat(),
                    "agent_name": agent_card_data.get('name', config['name']),
                    "agent_description": agent_card_data.get('description', config['description']),
                    "skills": agent_card_data.get('skills', [])
                }

                logger.info(f"Successfully connected to {agent_id} at {config['url']}")

            except Exception as e:
                logger.error(f"Failed to connect to {agent_id} at {config['url']}: {e}")
                discovered_agents[agent_id] = {
                    **config,
                    "status": "error",
                    "error": str(e)
                }

        return discovered_agents

    async def cleanup(self):
        """Clean up resources."""
        if self.httpx_client:
            await self.httpx_client.aclose()
            self.httpx_client = None
    
    async def send_message_with_orchestration(self, user_message: str) -> Dict[str, Any]:
        """
        Send message with intelligent multi-agent orchestration.
        Supports both simple routing and complex multi-step workflows.
        """
        try:
            # Create execution plan
            execution_plan = await self.orchestrator.create_execution_plan(user_message)

            # Execute the plan
            results = await self.orchestrator.execute_plan(execution_plan, self.agent_clients)

            # Synthesize final response
            final_response = await self.orchestrator.synthesize_response(user_message, results)

            return {
                "success": True,
                "response": final_response,
                "execution_plan": {
                    "type": execution_plan.execution_type,
                    "steps": len(execution_plan.steps),
                    "agents_used": [step.agent for step in execution_plan.steps]
                },
                "agent_results": results,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id
            }

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id
            }

    async def send_message_with_routing(self, user_message: str) -> Dict[str, Any]:
        """
        Legacy method - now uses orchestration for backward compatibility.
        """
        return await self.send_message_with_orchestration(user_message)

    async def get_agent_health(self) -> Dict[str, Dict]:
        """Check health status of all agents."""
        health_status = {}

        async with httpx.AsyncClient(timeout=10.0) as httpx_client:
            for agent_id, config in AGENT_ENDPOINTS.items():
                try:
                    health_url = f"{config['url']}/health"
                    response = await httpx_client.get(health_url)

                    if response.status_code == 200:
                        health_data = response.json()
                        health_status[agent_id] = {
                            "status": "healthy",
                            "response_time": response.elapsed.total_seconds(),
                            "details": health_data
                        }
                    else:
                        health_status[agent_id] = {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status_code}"
                        }

                except Exception as e:
                    health_status[agent_id] = {
                        "status": "error",
                        "error": str(e)
                    }

        return health_status

# Legacy class name for backward compatibility
A2AStreamlitClient = EnhancedA2AStreamlitClient

def check_agent_availability(agent_id: str) -> bool:
    """Check if specific agent is available."""
    return agent_id in AGENT_ENDPOINTS

# Streamlit App Configuration
st.set_page_config(
    page_title="A2A Multi-Agent Chat Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 600;
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }

    .agent-card {
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
    }

    .agent-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }

    .agent-online {
        border-left: 4px solid #28a745;
    }

    .agent-offline {
        border-left: 4px solid #ffc107;
    }

    .agent-error {
        border-left: 4px solid #dc3545;
    }

    .chat-message {
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .user-message {
        background: linear-gradient(145deg, #e3f2fd 0%, #f3e5f5 100%);
        margin-left: 2rem;
        border-left: 4px solid #2196f3;
    }

    .agent-message {
        background: linear-gradient(145deg, #f8f9fa 0%, #ffffff 100%);
        margin-right: 2rem;
        border-left: 4px solid #28a745;
    }

    .routing-info {
        background: linear-gradient(145deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-size: 0.95rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    .orchestration-features {
        background: linear-gradient(145deg, #fff3e0 0%, #fce4ec 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid #ffcc02;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }

    .feature-item {
        display: flex;
        align-items: center;
        margin: 0.8rem 0;
        font-size: 1rem;
    }

    .feature-icon {
        margin-right: 0.8rem;
        font-size: 1.2rem;
    }

    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e9ecef;
        padding: 0.75rem;
        font-size: 1rem;
    }

    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        font-size: 1rem;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Enhanced A2A Multi-Agent Orchestration Interface</h1>
        <p>Intelligent multi-step workflows powered by Google's A2A Protocol SDK</p>
        <small>✅ Multi-Agent Orchestration • LLM Planning • Real-time Execution</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'a2a_client' not in st.session_state:
        st.session_state.a2a_client = A2AStreamlitClient()
        st.session_state.agents_discovered = False
        st.session_state.conversation_history = []
        st.session_state.agent_status = {}
    
    # Sidebar for agent status and controls
    with st.sidebar:
        st.header("🔧 Agent Status & Controls")
        
        # Agent discovery button
        if st.button("🔍 Discover Agents", type="primary"):
            with st.spinner("Discovering A2A agents using real SDK..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    agents = loop.run_until_complete(
                        st.session_state.a2a_client.initialize_agents()
                    )
                    st.session_state.agent_status = agents
                    st.session_state.agents_discovered = True

                    # Count successful connections
                    online_count = sum(1 for agent in agents.values() if agent.get('status') == 'online')
                    total_count = len(agents)

                    if online_count > 0:
                        st.success(f"✅ Connected to {online_count}/{total_count} agents!")
                    else:
                        st.warning(f"⚠️ No agents available. Please start the agents first.")
                        st.info("Run: `cd super-agent-a2a && ./quick_start_agents.sh`")
                except Exception as e:
                    st.error(f"❌ Error discovering agents: {e}")
                    st.info("Make sure agents are running on the correct ports.")
        
        # Display agent status
        if st.session_state.agents_discovered:
            st.subheader("📊 Agent Status")

            for agent_id, agent_info in st.session_state.agent_status.items():
                status = agent_info.get('status', 'unknown')

                if status == 'online':
                    status_icon = "🟢"
                    css_class = "agent-online"
                elif status == 'offline':
                    status_icon = "🟡"
                    css_class = "agent-offline"
                else:
                    status_icon = "🔴"
                    css_class = "agent-error"

                # Use real agent name from card if available
                agent_name = agent_info.get('agent_name', agent_info['name'])
                agent_desc = agent_info.get('agent_description', agent_info['description'])
                skills_count = len(agent_info.get('skills', []))

                st.markdown(f"""
                <div class="agent-card {css_class}">
                    <strong>{status_icon} {agent_name}</strong><br>
                    <small>Status: {status} • URL: {agent_info['url']}</small><br>
                    <small>{agent_desc}</small><br>
                    {f'<small>🛠️ Skills: {skills_count}</small>' if skills_count > 0 else ''}
                    {f'<br><small>❌ Error: {agent_info["error"]}</small>' if status == 'error' else ''}
                </div>
                """, unsafe_allow_html=True)
        
        # Session information
        st.subheader("📝 Session Info")
        st.text(f"Session ID: {st.session_state.a2a_client.session_id[:8]}...")
        st.text(f"Messages: {len(st.session_state.conversation_history)}")

        # Show connection status
        if st.session_state.agents_discovered:
            online_agents = [name for name, info in st.session_state.agent_status.items()
                           if info.get('status') == 'online']
            st.text(f"Connected Agents: {len(online_agents)}")

        if st.button("🗑️ Clear Conversation"):
            st.session_state.conversation_history = []
            st.session_state.a2a_client.session_id = str(uuid4())
            st.rerun()

        # Add refresh agents button
        if st.button("🔄 Refresh Agents"):
            st.session_state.agents_discovered = False
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("💬 Conversation")
        
        # Display conversation history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.conversation_history:
                if message['type'] == 'user':
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong> {message['content']}
                        <br><small>{message['timestamp']}</small>
                    </div>
                    """, unsafe_allow_html=True)

                elif message['type'] == 'orchestration':
                    agents_list = ", ".join(message.get('agents_used', []))
                    st.markdown(f"""
                    <div class="routing-info" style="background: #e8f5e8; border: 1px solid #4caf50;">
                        🧠 <strong>Execution Plan:</strong> {message['execution_type']} execution with {message['steps']} steps
                        <br>🤖 <strong>Agents:</strong> {agents_list}
                        <br><small>{message['timestamp']}</small>
                    </div>
                    """, unsafe_allow_html=True)

                elif message['type'] == 'agent':
                    agents_list = ", ".join(message.get('agents_used', ['unknown']))
                    st.markdown(f"""
                    <div class="chat-message agent-message">
                        <strong>🤖 Multi-Agent Response:</strong> {message['content']}
                        <br><small>{message['timestamp']} • Agents: {agents_list} • Type: {message.get('execution_type', 'sequential')}</small>
                    </div>
                    """, unsafe_allow_html=True)

                elif message['type'] == 'error':
                    st.markdown(f"""
                    <div class="chat-message" style="background: #ffebee; border-left: 4px solid #f44336;">
                        <strong>❌ Error:</strong> {message['content']}
                        <br><small>{message['timestamp']}</small>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Message input
        with st.form("message_form", clear_on_submit=True):
            user_input = st.text_area(
                "Type your message:",
                placeholder="Ask me anything! I'll intelligently route your question to the best agent...",
                height=100
            )
            
            col_send, col_example = st.columns([1, 2])
            
            with col_send:
                send_button = st.form_submit_button("📤 Send Message", type="primary")
            
            with col_example:
                st.caption("💡 Try: 'Calculate 15% of 250', 'Weather in San Francisco', 'Plan my move from London to Manchester on Oct 15, budget £2500'")

        # Process message
        if send_button and user_input.strip():
            if not st.session_state.agents_discovered:
                st.warning("Please discover agents first using the sidebar button.")
            else:
                # Add user message to history
                user_message = {
                    'type': 'user',
                    'content': user_input,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                }
                st.session_state.conversation_history.append(user_message)

                # Send message with intelligent orchestration
                with st.spinner("🧠 Creating execution plan and orchestrating agents..."):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        response = loop.run_until_complete(
                            st.session_state.a2a_client.send_message_with_orchestration(user_input)
                        )

                        if response['success']:
                            # Show execution plan details
                            execution_plan = response.get('execution_plan', {})

                            # Add orchestration info to history
                            orchestration_info = {
                                'type': 'orchestration',
                                'execution_type': execution_plan.get('type', 'sequential'),
                                'agents_used': execution_plan.get('agents_used', []),
                                'steps': execution_plan.get('steps', 1),
                                'timestamp': datetime.now().strftime("%H:%M:%S")
                            }
                            st.session_state.conversation_history.append(orchestration_info)

                            # Add final response to history
                            agent_message = {
                                'type': 'agent',
                                'content': response['response'],
                                'agents_used': execution_plan.get('agents_used', ['unknown']),
                                'execution_type': execution_plan.get('type', 'sequential'),
                                'timestamp': datetime.now().strftime("%H:%M:%S")
                            }
                            st.session_state.conversation_history.append(agent_message)

                            # Show success with orchestration details
                            agents_str = ", ".join(execution_plan.get('agents_used', []))
                            st.success(f"✅ Multi-agent response from: {agents_str}")

                        else:
                            st.error(f"❌ Orchestration Error: {response['error']}")
                            # Still add error to history for debugging
                            error_message = {
                                'type': 'error',
                                'content': f"Orchestration Error: {response['error']}",
                                'timestamp': datetime.now().strftime("%H:%M:%S")
                            }
                            st.session_state.conversation_history.append(error_message)
                            
                    except Exception as e:
                        st.error(f"Error processing message: {e}")
                
                st.rerun()
    
    with col2:
        st.header("🧠 Multi-Agent Orchestration")

        st.markdown("""
        <div class="orchestration-features">
            <h3>🚀 Enhanced Orchestration Features</h3>
            <div class="feature-item">
                <span class="feature-icon">🎯</span>
                <strong>Intelligent Planning:</strong> LLM analyzes queries and creates execution plans
            </div>
            <div class="feature-item">
                <span class="feature-icon">🔄</span>
                <strong>Multi-Step Workflows:</strong> Coordinates multiple agents for complex tasks
            </div>
            <div class="feature-item">
                <span class="feature-icon">⚡</span>
                <strong>Parallel Execution:</strong> Runs independent tasks concurrently for speed
            </div>
            <div class="feature-item">
                <span class="feature-icon">🔗</span>
                <strong>Dependency Management:</strong> Handles task dependencies and data flow
            </div>
            <div class="feature-item">
                <span class="feature-icon">📝</span>
                <strong>Response Synthesis:</strong> Combines results into coherent answers
            </div>
        </div>

        <h4>🌐 Agent Endpoints (Connected):</h4>

        - 💬 **Base Agent** (Port 8080): General conversation & coordination
        - 🧮 **Calculator** (Port 8081): Math and calculations
        - 🌤️ **Weather** (Port 8082): Weather and forecasts
        - 🔍 **Research** (Port 8083): Information and analysis
        - 📦 **Move Orchestrator** (Port 8004): Moving assistance & logistics
        - 📊 **Infrastructure Monitor** (Port 8005): System monitoring

        <h4>💡 Demo Queries:</h4>

        - **Simple**: "What's 15 + 25?" → Single agent
        - **Complex**: "Plan my move from London to Manchester on Oct 15, budget £2500" → Multi-agent workflow

        **A2A Protocol Features:**
        - ✅ Official Google A2A SDK
        - ✅ Real agent card discovery
        - ✅ Multi-step orchestration
        - ✅ Intelligent query planning
        - ✅ Production-ready workflows
        """)

        if st.session_state.conversation_history:
            st.subheader("📈 Orchestration Statistics")

            # Calculate orchestration stats
            total_queries = sum(1 for msg in st.session_state.conversation_history if msg['type'] == 'user')
            orchestration_count = sum(1 for msg in st.session_state.conversation_history if msg['type'] == 'orchestration')

            # Execution type breakdown
            execution_types = {}
            agent_usage = {}

            for msg in st.session_state.conversation_history:
                if msg['type'] == 'orchestration':
                    exec_type = msg.get('execution_type', 'sequential')
                    execution_types[exec_type] = execution_types.get(exec_type, 0) + 1

                    # Count agent usage
                    for agent in msg.get('agents_used', []):
                        agent_usage[agent] = agent_usage.get(agent, 0) + 1

            # Display metrics
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Total Queries", total_queries)
                st.metric("Multi-Agent Workflows", orchestration_count)

            with col_b:
                if execution_types:
                    for exec_type, count in execution_types.items():
                        st.metric(f"{exec_type.title()} Execution", count)

            if agent_usage:
                st.write("**Agent Usage:**")
                for agent, count in sorted(agent_usage.items()):
                    st.metric(agent.replace('_', ' ').title(), count)

if __name__ == "__main__":
    main()
