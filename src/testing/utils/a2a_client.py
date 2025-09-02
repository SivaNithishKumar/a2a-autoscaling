"""
Enhanced A2A Client

A comprehensive A2A client implementation for testing purposes,
based on proven patterns from a2a-samples.
"""

import asyncio
import logging
from typing import Dict, List, Optional, AsyncIterator, Union
from datetime import datetime
import uuid

import httpx
from a2a.client import Client, ClientFactory, ClientConfig
from a2a.types import (
    AgentCard,
    Message,
    Task,
    TaskState,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TextPart,
    Part,
    Role,
    TransportProtocol
)

from .test_helpers import TestResult, TestStatus


logger = logging.getLogger(__name__)


class AgentConnection:
    """
    A connection to a single A2A agent.
    
    Based on the RemoteAgentConnections pattern from a2a-samples.
    """
    
    def __init__(self, client: Client, agent_card: AgentCard):
        """Initialize the agent connection."""
        self.client = client
        self.agent_card = agent_card
        self.pending_tasks = set()
        
    async def send_message(
        self, 
        text: str, 
        context_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Union[Task, Message, None]:
        """
        Send a message to the agent and handle the response.
        
        Args:
            text: The message text to send.
            context_id: Optional context ID for conversation continuity.
            task_id: Optional task ID for task continuation.
            
        Returns:
            The final task, message, or None if no response.
        """
        # Create the message using proper A2A message structure
        message = Message(
            role=Role.user,
            parts=[TextPart(text=text)],
            message_id=str(uuid.uuid4()),
            context_id=context_id,
            task_id=task_id
        )
        
        last_task: Optional[Task] = None
        
        try:
            # Send message and iterate over events (proven pattern)
            async for event in self.client.send_message(message):
                if isinstance(event, Message):
                    return event
                
                # event is a tuple (Task, Optional[event])
                task, update_event = event
                
                if self._is_terminal_or_interrupted(task):
                    return task
                    
                last_task = task
                
        except Exception as e:
            logger.error(f"Exception in send_message to {self.agent_card.name}: {e}")
            raise e
            
        return last_task
    
    def _is_terminal_or_interrupted(self, task: Task) -> bool:
        """Check if a task is in a terminal or interrupted state."""
        return task.status.state in [
            TaskState.completed,
            TaskState.canceled,
            TaskState.failed,
            TaskState.input_required,
            TaskState.unknown,
        ]
    
    async def send_message_streaming(
        self,
        text: str,
        context_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> AsyncIterator[Union[Task, Message, TaskStatusUpdateEvent, TaskArtifactUpdateEvent]]:
        """
        Send a message with streaming response.
        
        Args:
            text: The message text to send.
            context_id: Optional context ID for conversation continuity.
            task_id: Optional task ID for task continuation.
            
        Yields:
            Task updates, messages, or events as they arrive.
        """
        message = Message(
            role=Role.user,
            parts=[TextPart(text=text)],
            message_id=str(uuid.uuid4()),
            context_id=context_id,
            task_id=task_id
        )
        
        try:
            async for event in self.client.send_message(message):
                if isinstance(event, Message):
                    yield event
                else:
                    # event is a tuple (Task, Optional[event])
                    task, update_event = event
                    yield task
                    if update_event:
                        yield update_event
                        
        except Exception as e:
            logger.error(f"Exception in streaming send_message to {self.agent_card.name}: {e}")
            raise e


class EnhancedA2AClient:
    """
    Enhanced A2A client with comprehensive testing capabilities.
    
    Uses proven patterns from a2a-samples for robust agent communication.
    """
    
    def __init__(self, timeout: int = 30):
        """Initialize the enhanced A2A client."""
        self.timeout = timeout
        self.httpx_client: Optional[httpx.AsyncClient] = None
        self.client_factory: Optional[ClientFactory] = None
        self.agent_connections: Dict[str, AgentConnection] = {}
        
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
    
    def register_agent(self, agent_card: AgentCard) -> AgentConnection:
        """
        Register an agent and create a connection.
        
        Args:
            agent_card: The agent card from discovery.
            
        Returns:
            AgentConnection for the registered agent.
        """
        if not self.client_factory:
            raise RuntimeError("Client not initialized. Use as async context manager.")
            
        # Create client for this agent using the factory
        client = self.client_factory.create(agent_card)
        
        # Create connection wrapper
        connection = AgentConnection(client, agent_card)
        self.agent_connections[agent_card.name] = connection
        
        logger.debug(f"✅ Registered agent: {agent_card.name}")
        return connection
    
    def get_agent_connection(self, agent_name: str) -> Optional[AgentConnection]:
        """Get the connection for a registered agent."""
        return self.agent_connections.get(agent_name)
    
    async def test_agent_message(
        self, 
        agent_name: str, 
        message: str,
        expected_keywords: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> TestResult:
        """
        Test sending a message to an agent and validate the response.
        
        Args:
            agent_name: Name of the agent to test.
            message: Message to send to the agent.
            expected_keywords: Optional keywords to look for in response.
            timeout: Optional timeout override.
            
        Returns:
            TestResult with test outcome.
        """
        start_time = datetime.now()
        test_timeout = timeout or self.timeout
        
        if agent_name not in self.agent_connections:
            return TestResult(
                test_name=f"message_{agent_name}",
                status=TestStatus.ERROR,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Agent {agent_name} not registered",
                error=ValueError(f"Agent {agent_name} not found in registered agents")
            )
        
        connection = self.agent_connections[agent_name]
        
        try:
            # Send message with timeout
            response = await asyncio.wait_for(
                connection.send_message(message),
                timeout=test_timeout
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if response is None:
                return TestResult(
                    test_name=f"message_{agent_name}",
                    status=TestStatus.FAILED,
                    start_time=start_time,
                    end_time=end_time,
                    message="No response received from agent"
                )
            
            # Extract response text for validation
            response_text = ""
            if isinstance(response, Message):
                response_text = " ".join([
                    part.text for part in response.parts 
                    if hasattr(part, 'text')
                ])
            elif isinstance(response, Task):
                # Extract text from task artifacts
                if response.artifacts:
                    for artifact in response.artifacts:
                        for part in artifact.parts:
                            if hasattr(part, 'text'):
                                response_text += part.text + " "
            
            # Validate expected keywords if provided
            validation_passed = True
            missing_keywords = []
            
            if expected_keywords:
                for keyword in expected_keywords:
                    if keyword.lower() not in response_text.lower():
                        validation_passed = False
                        missing_keywords.append(keyword)
            
            # Determine test status
            if validation_passed:
                status = TestStatus.PASSED
                message_text = f"Successfully sent message and received valid response"
            else:
                status = TestStatus.FAILED
                message_text = f"Response missing expected keywords: {missing_keywords}"
            
            return TestResult(
                test_name=f"message_{agent_name}",
                status=status,
                start_time=start_time,
                end_time=end_time,
                message=message_text,
                details={
                    "sent_message": message,
                    "response_text": response_text[:500],  # Truncate for readability
                    "response_type": type(response).__name__,
                    "duration": duration,
                    "expected_keywords": expected_keywords,
                    "missing_keywords": missing_keywords if not validation_passed else []
                }
            )
            
        except asyncio.TimeoutError:
            return TestResult(
                test_name=f"message_{agent_name}",
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Request timed out after {test_timeout} seconds",
                error=asyncio.TimeoutError(f"Timeout after {test_timeout}s")
            )
            
        except Exception as e:
            return TestResult(
                test_name=f"message_{agent_name}",
                status=TestStatus.ERROR,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Error sending message: {str(e)}",
                error=e
            )
    
    async def test_agent_streaming(
        self,
        agent_name: str,
        message: str,
        max_events: int = 10,
        timeout: Optional[int] = None
    ) -> TestResult:
        """
        Test streaming message capability of an agent.
        
        Args:
            agent_name: Name of the agent to test.
            message: Message to send to the agent.
            max_events: Maximum number of events to collect.
            timeout: Optional timeout override.
            
        Returns:
            TestResult with streaming test outcome.
        """
        start_time = datetime.now()
        test_timeout = timeout or self.timeout
        
        if agent_name not in self.agent_connections:
            return TestResult(
                test_name=f"streaming_{agent_name}",
                status=TestStatus.ERROR,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Agent {agent_name} not registered"
            )
        
        connection = self.agent_connections[agent_name]
        events_collected = []
        
        try:
            # Test streaming with timeout
            async with asyncio.timeout(test_timeout):
                async for event in connection.send_message_streaming(message):
                    events_collected.append({
                        "type": type(event).__name__,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Stop after collecting enough events
                    if len(events_collected) >= max_events:
                        break
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if events_collected:
                return TestResult(
                    test_name=f"streaming_{agent_name}",
                    status=TestStatus.PASSED,
                    start_time=start_time,
                    end_time=end_time,
                    message=f"Successfully received {len(events_collected)} streaming events",
                    details={
                        "events_count": len(events_collected),
                        "events": events_collected,
                        "duration": duration
                    }
                )
            else:
                return TestResult(
                    test_name=f"streaming_{agent_name}",
                    status=TestStatus.FAILED,
                    start_time=start_time,
                    end_time=end_time,
                    message="No streaming events received"
                )
                
        except asyncio.TimeoutError:
            return TestResult(
                test_name=f"streaming_{agent_name}",
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Streaming test timed out after {test_timeout} seconds",
                details={"events_collected": len(events_collected)}
            )
            
        except Exception as e:
            return TestResult(
                test_name=f"streaming_{agent_name}",
                status=TestStatus.ERROR,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Error in streaming test: {str(e)}",
                error=e
            )
