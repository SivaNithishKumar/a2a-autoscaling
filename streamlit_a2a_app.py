#!/usr/bin/env python3
"""
Clean A2A Multi-Agent Streamlit Interface

Streamlined, functional interface for Google's A2A Protocol with:
- Clean, modern design
- Agent discovery and communication
- Multi-agent orchestration
- Real-time conversation
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st
import httpx
from dataclasses import dataclass
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import A2A SDK components
from a2a.client import A2ACardResolver
from a2a.types import MessageSendParams, SendMessageRequest, Message, TextPart, Part

# Import Azure OpenAI for intelligent routing
try:
    from openai import AzureOpenAI
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

@dataclass
class ExecutionStep:
    agent: str
    task: str
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class ExecutionPlan:
    steps: List[ExecutionStep]
    execution_type: str = "sequential"

def get_agent_endpoints():
    """Get agent endpoints based on environment"""
    in_k8s = os.getenv("KUBERNETES_SERVICE_HOST") is not None
    namespace = os.getenv("NAMESPACE", "multi-agent-a2a")
    
    if in_k8s:
        base_url_template = "http://{service_name}.{namespace}.svc.cluster.local:{port}"
        endpoints = {
            "base": {
                "url": base_url_template.format(service_name="base-agent-service", namespace=namespace, port=8080),
                "name": "Base Agent",
                "description": "General conversation and assistance"
            },
            "calculator": {
                "url": base_url_template.format(service_name="calculator-agent-service", namespace=namespace, port=8081),
                "name": "Calculator",
                "description": "Mathematical calculations and analysis"
            },
            "weather": {
                "url": base_url_template.format(service_name="weather-agent-service", namespace=namespace, port=8082),
                "name": "Weather",
                "description": "Weather information and forecasts"
            },
            "research": {
                "url": base_url_template.format(service_name="research-agent-service", namespace=namespace, port=8083),
                "name": "Research",
                "description": "Information research and analysis"
            },
            "move_orchestrator": {
                "url": base_url_template.format(service_name="move-orchestrator-service", namespace=namespace, port=8004),
                "name": "Move Assistant",
                "description": "Moving and relocation planning"
            },
            "infrastructure_monitor": {
                "url": base_url_template.format(service_name="infrastructure-monitor-service", namespace=namespace, port=8005),
                "name": "Infrastructure",
                "description": "System monitoring and health"
            }
        }
    else:
        endpoints = {
            "base": {"url": "http://localhost:8080", "name": "Base Agent", "description": "General conversation"},
            "calculator": {"url": "http://localhost:8081", "name": "Calculator", "description": "Math calculations"},
            "weather": {"url": "http://localhost:8082", "name": "Weather", "description": "Weather information"},
            "research": {"url": "http://localhost:8083", "name": "Research", "description": "Information research"},
            "move_orchestrator": {"url": "http://localhost:8004", "name": "Move Assistant", "description": "Moving assistance"},
            "infrastructure_monitor": {"url": "http://localhost:8005", "name": "Infrastructure", "description": "System monitoring"}
        }
    
    return endpoints

AGENT_ENDPOINTS = get_agent_endpoints()

class A2AClient:
    """Simple A2A client for agent communication"""
    
    def __init__(self, agent_url: str):
        self.agent_url = agent_url
        self.agent_card = None
        self._httpx_client = None

    async def send_message(self, message: str) -> Dict[str, Any]:
        """Send message to agent"""
        try:
            if not self._httpx_client:
                self._httpx_client = httpx.AsyncClient(timeout=30.0)

            # Get agent card if needed
            if not self.agent_card:
                resolver = A2ACardResolver(httpx_client=self._httpx_client, base_url=self.agent_url)
                agent_card = await resolver.get_agent_card()
                self.agent_card = agent_card.model_dump()

            # Create JSON-RPC request
            request_data = {
                "jsonrpc": "2.0",
                "id": str(uuid4()),
                "method": "message/send",
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": message}],
                        "messageId": uuid4().hex,
                    }
                }
            }

            response = await self._httpx_client.post(
                f"{self.agent_url}/",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                json_response = response.json()
                
                # Extract content from response
                content = ""
                if "result" in json_response and "message" in json_response["result"]:
                    message_data = json_response["result"]["message"]
                    if "parts" in message_data:
                        for part in message_data["parts"]:
                            if part.get("kind") == "text":
                                content = part.get("text", "")
                                break

                return {
                    "success": True,
                    "response": content or str(json_response),
                    "raw_response": json_response
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response": f"Agent communication failed: {response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Error communicating with agent: {e}"
            }

    async def cleanup(self):
        if self._httpx_client:
            await self._httpx_client.aclose()

class AzureOpenAIClient:
    """Azure OpenAI client for intelligent routing"""
    
    def __init__(self):
        self.client = None
        self.available = False
        self._initialize()

    def _initialize(self):
        try:
            if AZURE_AVAILABLE:
                api_key = os.getenv("AZURE_OPENAI_API_KEY")
                endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                
                if api_key and endpoint:
                    self.client = AzureOpenAI(
                        api_key=api_key,
                        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                        azure_endpoint=endpoint
                    )
                    self.available = True
        except Exception as e:
            logger.error(f"Azure OpenAI initialization failed: {e}")

    async def complete(self, prompt: str, max_tokens: int = 500) -> str:
        if not self.available:
            raise Exception("Azure OpenAI not available")
        
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LLM completion failed: {e}")

class IntelligentOrchestrator:
    """Multi-agent orchestrator with LLM-powered planning"""
    
    def __init__(self):
        self.llm_client = AzureOpenAIClient()

    async def create_execution_plan(self, user_query: str) -> ExecutionPlan:
        """Create intelligent execution plan"""
        
        # Build agent descriptions
        agent_descriptions = []
        for agent_id, config in AGENT_ENDPOINTS.items():
            agent_descriptions.append(f"- {config['name']} ({agent_id}): {config['description']}")
        
        planning_prompt = f"""
        Analyze this user query and create an execution plan using available agents.

        Query: "{user_query}"

        Available Agents:
        {chr(10).join(agent_descriptions)}

        Return JSON format:
        {{
            "execution_type": "sequential|parallel",
            "steps": [
                {{"agent": "agent_id", "task": "specific_task"}}
            ]
        }}

        Examples:
        - "What's 15 + 25?" → single calculator step
        - "Weather in London and calculate 15% tip for £50 meal" → weather + calculator steps
        """

        try:
            response = await self.llm_client.complete(planning_prompt, max_tokens=800)
            
            # Parse JSON response
            try:
                plan_data = json.loads(response)
            except json.JSONDecodeError:
                # Fallback: extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
                else:
                    raise Exception("Could not parse execution plan")

            steps = [ExecutionStep(agent=step["agent"], task=step["task"]) for step in plan_data["steps"]]
            return ExecutionPlan(steps=steps, execution_type=plan_data.get("execution_type", "sequential"))

        except Exception as e:
            # Fallback: simple routing based on keywords
            return self._fallback_routing(user_query)

    def _fallback_routing(self, query: str) -> ExecutionPlan:
        """Simple keyword-based routing when LLM is not available"""
        query_lower = query.lower()
        
        # Math-related keywords
        if any(word in query_lower for word in ["calculate", "math", "+", "-", "*", "/", "percent", "%", "sum"]):
            return ExecutionPlan(steps=[ExecutionStep(agent="calculator", task=query)])
        
        # Weather-related keywords
        elif any(word in query_lower for word in ["weather", "temperature", "forecast", "rain", "sunny"]):
            return ExecutionPlan(steps=[ExecutionStep(agent="weather", task=query)])
        
        # Moving-related keywords
        elif any(word in query_lower for word in ["move", "moving", "relocation", "relocate", "plan my move"]):
            return ExecutionPlan(steps=[ExecutionStep(agent="move_orchestrator", task=query)])
        
        # Research-related keywords
        elif any(word in query_lower for word in ["research", "find", "information", "tell me about"]):
            return ExecutionPlan(steps=[ExecutionStep(agent="research", task=query)])
        
        # Default to base agent
        else:
            return ExecutionPlan(steps=[ExecutionStep(agent="base", task=query)])

class A2AStreamlitClient:
    """Main client for Streamlit interface"""
    
    def __init__(self):
        self.session_id = str(uuid4())
        self.orchestrator = IntelligentOrchestrator()

    async def initialize_agents(self) -> Dict[str, Dict]:
        """Discover and initialize agents"""
        agents = {}
        
        for agent_id, config in AGENT_ENDPOINTS.items():
            try:
                client = A2AClient(config["url"])
                
                # Test connection
                test_response = await client.send_message("Hello")
                
                if test_response["success"]:
                    agents[agent_id] = {
                        "name": config["name"],
                        "description": config["description"],
                        "url": config["url"],
                        "status": "online",
                        "agent_name": config["name"],
                        "agent_description": config["description"]
                    }
                else:
                    agents[agent_id] = {
                        "name": config["name"],
                        "description": config["description"],
                        "url": config["url"],
                        "status": "offline",
                        "error": test_response.get("error", "Connection failed")
                    }
                
                await client.cleanup()
                
            except Exception as e:
                agents[agent_id] = {
                    "name": config["name"],
                    "description": config["description"],
                    "url": config["url"],
                    "status": "error",
                    "error": str(e)
                }
        
        return agents

    async def send_message_with_orchestration(self, user_query: str) -> Dict[str, Any]:
        """Send message with intelligent orchestration"""
        try:
            # Create execution plan
            execution_plan = await self.orchestrator.create_execution_plan(user_query)
            
            results = []
            
            # Execute steps
            for i, step in enumerate(execution_plan.steps):
                if step.agent not in AGENT_ENDPOINTS:
                    continue
                
                config = AGENT_ENDPOINTS[step.agent]
                client = A2AClient(config["url"])
                
                # Send message to agent
                result = await client.send_message(step.task)
                results.append({
                    "agent": step.agent,
                    "task": step.task,
                    "result": result,
                    "step": i + 1,
                    "total_steps": len(execution_plan.steps)
                })
                
                await client.cleanup()
            
            # Synthesize response using LLM
            if len(results) == 1:
                # Single agent response - return directly
                final_response = results[0]["result"]["response"]
            else:
                # Multiple agents - use LLM to synthesize
                try:
                    final_response = await self._synthesize_multi_agent_response(user_query, results)
                except Exception as e:
                    # Fallback to simple concatenation if LLM synthesis fails
                    logger.warning(f"LLM synthesis failed, using fallback: {e}")
                    response_parts = []
                    for result in results:
                        if result["result"]["success"]:
                            agent_name = AGENT_ENDPOINTS[result["agent"]]["name"]
                            response_parts.append(f"**{agent_name}**: {result['result']['response']}")
                        else:
                            agent_name = AGENT_ENDPOINTS[result["agent"]]["name"]
                            response_parts.append(f"**{agent_name}**: Error - {result['result']['error']}")
                    
                    final_response = "\n\n".join(response_parts)
            
            return {
                "success": True,
                "response": final_response,
                "execution_plan": {
                    "type": execution_plan.execution_type,
                    "steps": len(execution_plan.steps),
                    "agents_used": [step.agent for step in execution_plan.steps]
                },
                "detailed_results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Orchestration failed: {e}"
            }

    async def _synthesize_multi_agent_response(self, user_query: str, results: List[Dict]) -> str:
        """Synthesize multiple agent responses into a coherent answer using LLM"""
        
        # Build context from agent responses
        agent_responses = []
        for result in results:
            agent_name = AGENT_ENDPOINTS[result["agent"]]["name"]
            if result["result"]["success"]:
                response_text = result["result"]["response"]
                # Clean up the response text
                if isinstance(response_text, str):
                    response_text = response_text.strip()
                else:
                    response_text = str(response_text)
                agent_responses.append(f"{agent_name}: {response_text}")
            else:
                error_text = result["result"].get("error", "Unknown error")
                agent_responses.append(f"{agent_name}: Error - {error_text}")
        
        # Create synthesis prompt
        synthesis_prompt = f"""
        You are an intelligent orchestrator assistant. A user asked: "{user_query}"

        I coordinated multiple AI agents to help answer this question, and here are their responses:

        {chr(10).join(agent_responses)}

        Your task is to synthesize these responses into a single, coherent, and helpful answer that directly addresses the user's question. 

        Guidelines:
        - Provide a clear, actionable response
        - Combine information from multiple agents where relevant
        - If agents provided data, organize it clearly
        - If there were errors, mention them briefly but focus on successful responses
        - Be conversational and helpful
        - Use proper formatting (headers, bullets, etc.) but avoid excessive line breaks
        - Write in a natural, flowing style with appropriate paragraph breaks
        - Avoid adding unnecessary blank lines between sentences

        Please provide a comprehensive response that helps the user with their request.
        """

        try:
            # Use the orchestrator's LLM client for synthesis
            synthesized_response = await self.orchestrator.llm_client.complete(synthesis_prompt, max_tokens=800)
            
            # Clean up the response to remove excessive line breaks
            cleaned_response = synthesized_response.strip()
            
            # Replace multiple consecutive newlines with double newlines (paragraph breaks)
            import re
            cleaned_response = re.sub(r'\n{3,}', '\n\n', cleaned_response)
            
            # Remove single newlines that create unnecessary line breaks (but keep double newlines for paragraphs)
            lines = cleaned_response.split('\n')
            processed_lines = []
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line:  # Non-empty line
                    processed_lines.append(line)
                    # Check if next line is empty (indicating paragraph break)
                    if i + 1 < len(lines) and not lines[i + 1].strip():
                        processed_lines.append('')  # Add paragraph break
                        i += 1  # Skip the empty line
                i += 1
            
            # Join lines back together
            final_response = '\n'.join(processed_lines)
            
            # Final cleanup - ensure we don't have more than 2 consecutive newlines
            final_response = re.sub(r'\n{3,}', '\n\n', final_response)
            
            return final_response
        except Exception as e:
            # If LLM synthesis fails, raise the error to use fallback
            raise Exception(f"Response synthesis failed: {e}")

# Streamlit Configuration
st.set_page_config(
    page_title="A2A Agent Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Clean CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main > div {
        font-family: 'Poppins', sans-serif;
        background: #fafbfc;
    }
    
    /* Clean Header */
    .clean-header {
        background: #ffffff;
        border: 1px solid #e3e8ef;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .clean-header h1 {
        color: #1a202c;
        margin: 0;
        font-weight: 600;
        font-size: 2rem;
    }
    
    .clean-header p {
        color: #718096;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    
    /* Modern Agent Cards */
    .modern-agent-card {
        background: #ffffff;
        border: 1px solid #e3e8ef;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .modern-agent-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }
    
    .agent-status-online { 
        border-left: 4px solid #48bb78; 
        background: linear-gradient(135deg, #ffffff 0%, #f0fff4 100%);
    }
    .agent-status-offline { 
        border-left: 4px solid #ed8936; 
        background: linear-gradient(135deg, #ffffff 0%, #fffaf0 100%);
    }
    .agent-status-error { 
        border-left: 4px solid #f56565; 
        background: linear-gradient(135deg, #ffffff 0%, #fff5f5 100%);
    }
    
    /* Clean Chat Messages */
    .clean-chat-message {
        background: #ffffff;
        border: 1px solid #e3e8ef;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .user-chat {
        border-left: 4px solid #4299e1;
        background: linear-gradient(135deg, #ffffff 0%, #ebf8ff 100%);
    }
    
    .agent-chat {
        border-left: 4px solid #48bb78;
        background: linear-gradient(135deg, #ffffff 0%, #f0fff4 100%);
    }
    
    .execution-plan {
        background: linear-gradient(135deg, #ffffff 0%, #faf5ff 100%);
        border: 1px solid #d6bcfa;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
    }
    
    /* Modern Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Clean Metrics */
    .metric-container {
        background: #ffffff;
        border: 1px solid #e3e8ef;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin: 0.5rem 0;
    }
    
    /* Section Headers */
    .section-header {
        color: #2d3748;
        font-weight: 600;
        font-size: 1.25rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e3e8ef;
    }
    
    /* Status Indicators */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-online { background: #48bb78; }
    .status-offline { background: #ed8936; }
    .status-error { background: #f56565; }
    
    /* Input Styling */
    .stTextArea > div > div > textarea {
        border: 1px solid #e3e8ef;
        border-radius: 8px;
        padding: 0.75rem;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header[data-testid="stHeader"] {display: none;}
    
    /* Container Styling */
    .main .block-container {
        padding-top: 1rem;
        max-width: 1200px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application"""
    
    # Clean Header
    st.markdown("""
    <div class="clean-header">
        <h1>🤖 A2A Agent Platform</h1>
        <p>Modern multi-agent communication interface</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'client' not in st.session_state:
        st.session_state.client = A2AStreamlitClient()
        st.session_state.agents_discovered = False
        st.session_state.conversation_history = []
        st.session_state.agent_status = {}
    
    # Layout
    col1, col2 = st.columns([2, 1], gap="large")
    
    with col1:
        st.markdown('<h2 class="section-header">💬 Conversation</h2>', unsafe_allow_html=True)
        
        # Display conversation history
        for message in st.session_state.conversation_history:
            if message['type'] == 'user':
                st.markdown(f"""
                <div class="clean-chat-message user-chat">
                    <div style="font-weight: 600; color: #2d3748; margin-bottom: 0.5rem;">👤 You</div>
                    <div style="color: #4a5568; line-height: 1.5;">{message['content']}</div>
                    <div style="color: #a0aec0; font-size: 0.875rem; margin-top: 0.5rem;">{message['timestamp']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            elif message['type'] == 'execution_plan':
                agents_list = ", ".join(message.get('agents_used', []))
                st.markdown(f"""
                <div class="execution-plan">
                    <div style="font-weight: 600; color: #553c9a; margin-bottom: 0.5rem;">🧠 Execution Plan</div>
                    <div style="color: #6b46c1;">
                        <strong>Strategy:</strong> {message.get('execution_type', 'sequential').title()} execution with {message.get('steps', 1)} steps<br>
                        <strong>Agents:</strong> {agents_list}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            elif message['type'] == 'agent_response':
                st.markdown(f"""
                <div class="clean-chat-message agent-chat">
                    <div style="font-weight: 600; color: #2d3748; margin-bottom: 0.5rem;">🤖 Agent Response</div>
                    <div style="color: #4a5568; line-height: 1.5; white-space: pre-wrap;">{message['content']}</div>
                    <div style="color: #a0aec0; font-size: 0.875rem; margin-top: 0.5rem;">{message['timestamp']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            elif message['type'] == 'error':
                st.error(f"❌ {message['content']}")
        
        # Message input with clean styling
        with st.form("message_form", clear_on_submit=True):
            st.markdown("**Your message:**")
            user_input = st.text_area(
                "",
                placeholder="Ask me anything! I'll intelligently route your question to the right agents...",
                height=100,
                label_visibility="collapsed"
            )
            
            col_send, col_help = st.columns([1, 4])
            with col_send:
                send_button = st.form_submit_button("📤 Send", type="primary")
            with col_help:
                st.markdown("💡 **Try:** *Calculate 15% of 250*, *Weather in London*, *Plan my move to Manchester*")
        
        # Process message
        if send_button and user_input.strip():
            if not st.session_state.agents_discovered:
                st.warning("Please discover agents first using the sidebar.")
            else:
                # Add user message
                user_message = {
                    'type': 'user',
                    'content': user_input,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                }
                st.session_state.conversation_history.append(user_message)
                
                # Process with orchestration
                with st.spinner("Processing your request..."):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        response = loop.run_until_complete(
                            st.session_state.client.send_message_with_orchestration(user_input)
                        )
                        
                        if response['success']:
                            # Add execution plan info
                            execution_plan = response.get('execution_plan', {})
                            plan_message = {
                                'type': 'execution_plan',
                                'execution_type': execution_plan.get('type', 'sequential'),
                                'steps': execution_plan.get('steps', 1),
                                'agents_used': execution_plan.get('agents_used', [])
                            }
                            st.session_state.conversation_history.append(plan_message)
                            
                            # Add agent response
                            agent_message = {
                                'type': 'agent_response',
                                'content': response['response'],
                                'timestamp': datetime.now().strftime("%H:%M:%S")
                            }
                            st.session_state.conversation_history.append(agent_message)
                            
                        else:
                            error_message = {
                                'type': 'error',
                                'content': response.get('error', 'Unknown error'),
                                'timestamp': datetime.now().strftime("%H:%M:%S")
                            }
                            st.session_state.conversation_history.append(error_message)
                        
                    except Exception as e:
                        error_message = {
                            'type': 'error',
                            'content': f"Processing error: {str(e)}",
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        }
                        st.session_state.conversation_history.append(error_message)
                
                st.rerun()
    
    with col2:
        st.markdown('<h2 class="section-header">🎛️ Control Panel</h2>', unsafe_allow_html=True)
        
        # Agent discovery with modern button
        if st.button("🔍 Discover Agents", type="primary", use_container_width=True):
            with st.spinner("Discovering agents..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    agents = loop.run_until_complete(st.session_state.client.initialize_agents())
                    st.session_state.agent_status = agents
                    st.session_state.agents_discovered = True
                    
                    online_count = sum(1 for agent in agents.values() if agent.get('status') == 'online')
                    total_count = len(agents)
                    
                    if online_count > 0:
                        st.success(f"✅ Connected to {online_count}/{total_count} agents!")
                    else:
                        st.warning("⚠️ No agents available.")
                        
                except Exception as e:
                    st.error(f"❌ Discovery failed: {e}")
        
        # Modern Agent status display
        if st.session_state.agents_discovered:
            st.markdown('<h3 class="section-header">📊 Agent Status</h3>', unsafe_allow_html=True)
            
            for agent_id, agent_info in st.session_state.agent_status.items():
                status = agent_info.get('status', 'unknown')
                
                if status == 'online':
                    status_class = "agent-status-online"
                    status_indicator = '<span class="status-indicator status-online"></span>'
                elif status == 'offline':
                    status_class = "agent-status-offline"
                    status_indicator = '<span class="status-indicator status-offline"></span>'
                else:
                    status_class = "agent-status-error"
                    status_indicator = '<span class="status-indicator status-error"></span>'
                
                agent_name = agent_info.get('name', 'Unknown')
                agent_desc = agent_info.get('description', 'No description')
                
                error_info = ""
                if status in ['error', 'offline'] and 'error' in agent_info:
                    error_info = f'<div style="color: #e53e3e; font-size: 0.875rem; margin-top: 0.5rem;">Error: {agent_info["error"]}</div>'
                
                st.markdown(f"""
                <div class="modern-agent-card {status_class}">
                    <div style="font-weight: 600; color: #2d3748; margin-bottom: 0.25rem;">
                        {status_indicator} {agent_name}
                    </div>
                    <div style="color: #718096; font-size: 0.875rem; margin-bottom: 0.25rem;">
                        {agent_desc}
                    </div>
                    <div style="color: #4a5568; font-size: 0.75rem; text-transform: uppercase; font-weight: 500;">
                        {status}
                    </div>
                    {error_info}
                </div>
                """, unsafe_allow_html=True)
        
        # Modern System info
        st.markdown('<h3 class="section-header">ℹ️ System Info</h3>', unsafe_allow_html=True)
        
        # AI System status with clean display
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        ai_status = "Ready" if (azure_key and azure_endpoint) else "Limited"
        ai_color = "#48bb78" if (azure_key and azure_endpoint) else "#ed8936"
        
        st.markdown(f"""
        <div class="metric-container">
            <div style="color: {ai_color}; font-weight: 600; margin-bottom: 0.5rem;">🤖 AI System</div>
            <div style="color: #4a5568; font-size: 1.25rem; font-weight: 500;">{ai_status}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Connection stats with modern layout
        if st.session_state.agents_discovered:
            online_agents = [name for name, info in st.session_state.agent_status.items() 
                           if info.get('status') == 'online']
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
                <div class="metric-container">
                    <div style="color: #48bb78; font-weight: 600; margin-bottom: 0.5rem;">Online</div>
                    <div style="color: #2d3748; font-size: 1.5rem; font-weight: 600;">{len(online_agents)}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""
                <div class="metric-container">
                    <div style="color: #4a5568; font-weight: 600; margin-bottom: 0.5rem;">Total</div>
                    <div style="color: #2d3748; font-size: 1.5rem; font-weight: 600;">{len(st.session_state.agent_status)}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Session stats with modern styling
        if st.session_state.conversation_history:
            st.markdown('<h3 class="section-header">📈 Session Stats</h3>', unsafe_allow_html=True)
            
            user_messages = sum(1 for msg in st.session_state.conversation_history if msg['type'] == 'user')
            agent_responses = sum(1 for msg in st.session_state.conversation_history if msg['type'] == 'agent_response')
            
            col_c, col_d = st.columns(2)
            with col_c:
                st.markdown(f"""
                <div class="metric-container">
                    <div style="color: #4299e1; font-weight: 600; margin-bottom: 0.5rem;">Messages</div>
                    <div style="color: #2d3748; font-size: 1.5rem; font-weight: 600;">{user_messages}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_d:
                st.markdown(f"""
                <div class="metric-container">
                    <div style="color: #48bb78; font-weight: 600; margin-bottom: 0.5rem;">Responses</div>
                    <div style="color: #2d3748; font-size: 1.5rem; font-weight: 600;">{agent_responses}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Modern Actions section
        st.markdown('<h3 class="section-header">🔧 Actions</h3>', unsafe_allow_html=True)
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.client.session_id = str(uuid4())
            st.rerun()
        
        if st.button("🔄 Refresh Agents", use_container_width=True):
            st.session_state.agents_discovered = False
            st.session_state.agent_status = {}
            st.rerun()

if __name__ == "__main__":
    main()