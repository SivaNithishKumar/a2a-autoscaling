"""
Streaming Conversation Client for Real-time A2A Interactions

Provides real-time streaming conversations with multiple agents,
live response generation, and event-driven communication.
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
import websockets
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of streaming events."""
    MESSAGE_START = "message_start"
    MESSAGE_CHUNK = "message_chunk" 
    MESSAGE_END = "message_end"
    AGENT_SWITCH = "agent_switch"
    THINKING = "thinking"
    ERROR = "error"
    STATUS = "status"


@dataclass
class StreamingEvent:
    """A streaming event in the conversation."""
    event_type: EventType
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: Optional[str] = None
    conversation_id: Optional[str] = None


@dataclass
class StreamingSession:
    """A streaming conversation session."""
    session_id: str
    user_id: str
    active_agents: List[str] = field(default_factory=list)
    connected_clients: List[str] = field(default_factory=list)
    message_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


class StreamingEventQueue:
    """Manages streaming events for multiple sessions."""
    
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.sessions: Dict[str, StreamingSession] = {}
        
    def create_session(self, user_id: str) -> str:
        """Create a new streaming session."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = StreamingSession(
            session_id=session_id,
            user_id=user_id
        )
        self.queues[session_id] = asyncio.Queue()
        
        logger.info(f"Created streaming session {session_id} for user {user_id}")
        return session_id
        
    async def emit_event(self, session_id: str, event: StreamingEvent):
        """Emit an event to a session."""
        if session_id in self.queues:
            event.conversation_id = session_id
            await self.queues[session_id].put(event)
            
            # Update session activity
            if session_id in self.sessions:
                self.sessions[session_id].last_activity = datetime.now()
                
    async def get_events(self, session_id: str) -> AsyncGenerator[StreamingEvent, None]:
        """Get streaming events for a session."""
        if session_id not in self.queues:
            return
            
        queue = self.queues[session_id]
        
        try:
            while True:
                event = await queue.get()
                yield event
                
                # Break on session end events
                if event.event_type == EventType.ERROR and "session_ended" in str(event.data):
                    break
                    
        except asyncio.CancelledError:
            logger.info(f"Event stream cancelled for session {session_id}")
            
    def end_session(self, session_id: str):
        """End a streaming session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.queues:
            del self.queues[session_id]
            
        logger.info(f"Ended streaming session {session_id}")


class StreamingAgentProxy:
    """Proxy for streaming communication with A2A agents."""
    
    def __init__(self, agent_name: str, agent_url: str):
        self.agent_name = agent_name
        self.agent_url = agent_url
        
    async def stream_query(self, query: str, session_id: str, 
                          event_queue: StreamingEventQueue) -> AsyncGenerator[str, None]:
        """Stream a query to an agent and yield response chunks."""
        
        try:
            # Emit thinking event
            await event_queue.emit_event(session_id, StreamingEvent(
                event_type=EventType.THINKING,
                data=f"Agent {self.agent_name} is processing your request...",
                agent_name=self.agent_name
            ))
            
            # Simulate streaming response (replace with actual A2A streaming calls)
            response_chunks = await self._simulate_streaming_response(query)
            
            # Emit message start
            await event_queue.emit_event(session_id, StreamingEvent(
                event_type=EventType.MESSAGE_START,
                data={"agent": self.agent_name, "query": query},
                agent_name=self.agent_name
            ))
            
            # Stream response chunks
            full_response = ""
            async for chunk in response_chunks:
                full_response += chunk
                
                await event_queue.emit_event(session_id, StreamingEvent(
                    event_type=EventType.MESSAGE_CHUNK,
                    data=chunk,
                    agent_name=self.agent_name
                ))
                
                yield chunk
                
                # Small delay to simulate realistic streaming
                await asyncio.sleep(0.05)
                
            # Emit message end
            await event_queue.emit_event(session_id, StreamingEvent(
                event_type=EventType.MESSAGE_END,
                data={"agent": self.agent_name, "full_response": full_response},
                agent_name=self.agent_name
            ))
            
        except Exception as e:
            logger.error(f"Streaming error for {self.agent_name}: {e}")
            
            await event_queue.emit_event(session_id, StreamingEvent(
                event_type=EventType.ERROR,
                data=f"Error from {self.agent_name}: {str(e)}",
                agent_name=self.agent_name
            ))
            
    async def _simulate_streaming_response(self, query: str) -> AsyncGenerator[str, None]:
        """Simulate streaming response from an agent."""
        
        # Generate agent-specific responses
        if self.agent_name == "calculator":
            response = f"Let me calculate that for you... The result of '{query}' is 42. Here's how I solved it step by step..."
        elif self.agent_name == "weather":
            response = f"Checking weather information for '{query}'... Current conditions are partly cloudy, 22°C. The forecast shows..."
        elif self.agent_name == "research":
            response = f"Researching '{query}'... I found several relevant sources. Here's what I discovered from my analysis..."
        elif self.agent_name == "base":
            response = f"I understand you're asking about '{query}'. Let me help you with that. Based on my analysis..."
        else:
            response = f"Agent {self.agent_name} is processing '{query}' and generating a comprehensive response..."
            
        # Split response into chunks for streaming
        words = response.split()
        chunk_size = 3  # Words per chunk
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            if i + chunk_size < len(words):
                chunk += " "
            yield chunk


class StreamingConversationClient:
    """
    Streaming conversation client for real-time A2A interactions.
    
    Provides real-time streaming conversations with multiple agents,
    live response generation, and event-driven communication.
    """
    
    def __init__(self, agent_router=None):
        self.agent_router = agent_router
        self.event_queue = StreamingEventQueue()
        self.agent_proxies: Dict[str, StreamingAgentProxy] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Initialize agent proxies
        self._setup_agent_proxies()
        
    def _setup_agent_proxies(self):
        """Set up streaming proxies for available agents."""
        
        agents_config = [
            ("base", "http://localhost:8000"),
            ("calculator", "http://localhost:8002"),
            ("weather", "http://localhost:8001"),
            ("research", "http://localhost:8003")
        ]
        
        for agent_name, agent_url in agents_config:
            self.agent_proxies[agent_name] = StreamingAgentProxy(agent_name, agent_url)
            
        logger.info(f"Set up {len(self.agent_proxies)} streaming agent proxies")
        
    def create_streaming_session(self, user_id: str = "default_user") -> str:
        """Create a new streaming conversation session."""
        
        session_id = self.event_queue.create_session(user_id)
        
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "conversation_context": {},
            "message_history": [],
            "active_agents": []
        }
        
        # Send welcome event
        asyncio.create_task(self.event_queue.emit_event(session_id, StreamingEvent(
            event_type=EventType.STATUS,
            data="Welcome! Your streaming conversation session is ready. Type your message to start chatting!",
            agent_name="system"
        )))
        
        return session_id
        
    async def stream_chat(self, message: str, session_id: str) -> AsyncGenerator[StreamingEvent, None]:
        """
        Handle a streaming chat message and yield events as they occur.
        """
        
        if session_id not in self.active_sessions:
            yield StreamingEvent(
                event_type=EventType.ERROR,
                data="Session not found",
                conversation_id=session_id
            )
            return
            
        session_data = self.active_sessions[session_id]
        
        # Add user message to history
        session_data["message_history"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # Determine which agent to use
            if self.agent_router:
                # Use AI routing
                agent_name, confidence = await self.agent_router.route_query(
                    message, 
                    session_data["conversation_context"]
                )
            else:
                # Simple fallback routing
                agent_name = self._simple_route(message)
                confidence = 0.8
                
            # Emit agent switch event if different from last agent
            last_agent = session_data.get("last_agent")
            if agent_name != last_agent:
                await self.event_queue.emit_event(session_id, StreamingEvent(
                    event_type=EventType.AGENT_SWITCH,
                    data={
                        "from_agent": last_agent,
                        "to_agent": agent_name,
                        "confidence": confidence,
                        "reasoning": f"Routing '{message}' to {agent_name}"
                    },
                    agent_name=agent_name
                ))
                
                session_data["last_agent"] = agent_name
                
            # Stream response from selected agent
            if agent_name in self.agent_proxies:
                proxy = self.agent_proxies[agent_name]
                
                full_response = ""
                async for chunk in proxy.stream_query(message, session_id, self.event_queue):
                    full_response += chunk
                    
                # Add agent response to history
                session_data["message_history"].append({
                    "role": "agent",
                    "content": full_response,
                    "agent": agent_name,
                    "timestamp": datetime.now().isoformat()
                })
                
            else:
                # Agent not available
                await self.event_queue.emit_event(session_id, StreamingEvent(
                    event_type=EventType.ERROR,
                    data=f"Agent {agent_name} is not available",
                    agent_name=agent_name
                ))
                
        except Exception as e:
            logger.error(f"Streaming chat error: {e}")
            await self.event_queue.emit_event(session_id, StreamingEvent(
                event_type=EventType.ERROR,
                data=f"Error processing message: {str(e)}",
                conversation_id=session_id
            ))
            
        # Yield all events that occurred during this message
        async for event in self.event_queue.get_events(session_id):
            yield event
            
    def _simple_route(self, message: str) -> str:
        """Simple routing logic when no AI router is available."""
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['calculate', 'compute', 'math', '+', '-', '*', '/']):
            return "calculator"
        elif any(word in message_lower for word in ['weather', 'temperature', 'forecast']):
            return "weather"
        elif any(word in message_lower for word in ['research', 'find', 'search', 'who', 'what']):
            return "research"
        else:
            return "base"
            
    async def get_session_events(self, session_id: str) -> AsyncGenerator[StreamingEvent, None]:
        """Get real-time events for a session."""
        
        async for event in self.event_queue.get_events(session_id):
            yield event
            
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a streaming session."""
        
        if session_id not in self.active_sessions:
            return None
            
        session_data = self.active_sessions[session_id]
        event_session = self.event_queue.sessions.get(session_id)
        
        return {
            "session_id": session_id,
            "user_id": session_data["user_id"],
            "message_count": len(session_data["message_history"]),
            "active_agents": session_data.get("active_agents", []),
            "last_agent": session_data.get("last_agent"),
            "created_at": event_session.created_at.isoformat() if event_session else None,
            "last_activity": event_session.last_activity.isoformat() if event_session else None,
            "recent_messages": session_data["message_history"][-3:]  # Last 3 messages
        }
        
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active streaming sessions."""
        
        sessions = []
        for session_id in self.active_sessions:
            info = self.get_session_info(session_id)
            if info:
                sessions.append(info)
                
        return sorted(sessions, key=lambda x: x.get("last_activity", ""), reverse=True)
        
    def end_session(self, session_id: str):
        """End a streaming session."""
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            
        self.event_queue.end_session(session_id)
        
        logger.info(f"Ended streaming session {session_id}")
        
    async def run_websocket_server(self, host: str = "localhost", port: int = 8765):
        """Run a WebSocket server for real-time communication."""
        
        async def handle_client(websocket, path):
            """Handle a WebSocket client connection."""
            
            client_id = str(uuid.uuid4())
            session_id = None
            
            try:
                logger.info(f"Client {client_id} connected")
                
                await websocket.send(json.dumps({
                    "type": "connection_established",
                    "client_id": client_id,
                    "message": "Connected to streaming conversation server"
                }))
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type")
                        
                        if msg_type == "start_session":
                            user_id = data.get("user_id", client_id)
                            session_id = self.create_streaming_session(user_id)
                            
                            await websocket.send(json.dumps({
                                "type": "session_started",
                                "session_id": session_id,
                                "user_id": user_id
                            }))
                            
                        elif msg_type == "chat_message" and session_id:
                            user_message = data.get("message", "")
                            
                            # Stream response
                            async for event in self.stream_chat(user_message, session_id):
                                event_data = {
                                    "type": "streaming_event",
                                    "event_type": event.event_type.value,
                                    "data": event.data,
                                    "agent_name": event.agent_name,
                                    "timestamp": event.timestamp.isoformat(),
                                    "event_id": event.event_id
                                }
                                
                                await websocket.send(json.dumps(event_data))
                                
                        elif msg_type == "get_session_info" and session_id:
                            info = self.get_session_info(session_id)
                            await websocket.send(json.dumps({
                                "type": "session_info",
                                "data": info
                            }))
                            
                    except json.JSONDecodeError:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }))
                        
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"Client {client_id} disconnected")
                
            finally:
                if session_id:
                    self.end_session(session_id)
                    
        logger.info(f"Starting WebSocket server on {host}:{port}")
        
        start_server = websockets.serve(handle_client, host, port)
        await start_server
        
        logger.info("WebSocket server started successfully")


# Example usage and testing
async def main():
    """Example usage of the Streaming Conversation Client."""
    
    print("📡 Streaming Conversation Client Demo")
    print("=" * 50)
    
    # Create streaming client
    client = StreamingConversationClient()
    
    # Create a session
    session_id = client.create_streaming_session("demo_user")
    print(f"Created session: {session_id}")
    
    # Test messages
    test_messages = [
        "Hello there!",
        "What's 25 + 17?",
        "What's the weather like in Paris?",
        "Can you research the population of Tokyo?"
    ]
    
    for message in test_messages:
        print(f"\n👤 User: {message}")
        print("🤖 Streaming response:")
        
        current_agent = None
        response_chunks = []
        
        # Note: In a real scenario, this would use the async generator properly
        # For demo purposes, we'll simulate the behavior
        
        try:
            # Simulate streaming response
            agent = client._simple_route(message)
            if agent != current_agent:
                print(f"   🔄 Switching to {agent} agent")
                current_agent = agent
                
            print(f"   💭 {agent} agent is thinking...")
            
            # Simulate response chunks
            if agent == "calculator":
                chunks = ["Let", "me", "calculate", "that...", "The", "result", "is", "42!"]
            elif agent == "weather":
                chunks = ["Checking", "weather", "data...", "It's", "sunny", "and", "22°C"]
            elif agent == "research":
                chunks = ["Researching", "your", "query...", "Found", "relevant", "information"]
            else:
                chunks = ["I", "understand", "your", "question.", "Let", "me", "help!"]
                
            print("   📝 Response: ", end="")
            for chunk in chunks:
                print(chunk + " ", end="", flush=True)
                await asyncio.sleep(0.1)  # Simulate streaming delay
                
            print()  # New line after response
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
    # Show session info
    print(f"\n📊 Session Info:")
    info = client.get_session_info(session_id)
    if info:
        for key, value in info.items():
            if key != "recent_messages":
                print(f"  {key}: {value}")
                
    # Clean up
    client.end_session(session_id)
    print(f"\n✅ Demo completed and session cleaned up")


# WebSocket client example
async def websocket_client_demo():
    """Example WebSocket client for testing."""
    
    import websockets
    
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to WebSocket server")
            
            # Start session
            await websocket.send(json.dumps({
                "type": "start_session", 
                "user_id": "demo_user"
            }))
            
            # Listen for responses
            async for message in websocket:
                data = json.loads(message)
                print(f"📨 Received: {data}")
                
                if data.get("type") == "session_started":
                    # Send a test message
                    await websocket.send(json.dumps({
                        "type": "chat_message",
                        "message": "Hello, can you calculate 25 + 17?"
                    }))
                    
    except Exception as e:
        print(f"WebSocket client error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Run WebSocket server
        async def run_server():
            client = StreamingConversationClient()
            await client.run_websocket_server()
            
        asyncio.run(run_server())
    elif len(sys.argv) > 1 and sys.argv[1] == "client":
        # Run WebSocket client demo
        asyncio.run(websocket_client_demo())
    else:
        # Run basic demo
        asyncio.run(main())