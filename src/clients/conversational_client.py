"""
Conversational A2A Client with Memory Management

Provides natural conversation capabilities with context preservation,
multi-turn interactions, and conversation memory.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A single message in a conversation."""
    id: str
    role: str  # 'user' or 'agent'
    content: str
    timestamp: datetime
    agent_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Context information for a conversation."""
    conversation_id: str
    user_id: str
    turn_count: int = 0
    topics: set = field(default_factory=set)
    active_agent: Optional[str] = None
    last_agent: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Conversation:
    """A complete conversation with messages and context."""
    id: str
    messages: List[Message] = field(default_factory=list)
    context: ConversationContext = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = ConversationContext(
                conversation_id=self.id,
                user_id="default_user"
            )


class ConversationMemory:
    """Manages conversation memory and context."""
    
    def __init__(self, max_conversations: int = 100, max_messages_per_conversation: int = 1000):
        self.conversations: Dict[str, Conversation] = {}
        self.max_conversations = max_conversations
        self.max_messages_per_conversation = max_messages_per_conversation
        
    def create_conversation(self, user_id: str = "default_user") -> Conversation:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(id=conversation_id)
        conversation.context.user_id = user_id
        
        self.conversations[conversation_id] = conversation
        
        # Clean up old conversations if we exceed the limit
        if len(self.conversations) > self.max_conversations:
            oldest_id = min(self.conversations.keys(), 
                          key=lambda x: self.conversations[x].context.created_at)
            del self.conversations[oldest_id]
            
        logger.info(f"Created conversation {conversation_id} for user {user_id}")
        return conversation
        
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self.conversations.get(conversation_id)
        
    def add_message(self, conversation_id: str, role: str, content: str, 
                   agent_name: Optional[str] = None, metadata: Dict = None) -> Message:
        """Add a message to a conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
            
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            agent_name=agent_name,
            metadata=metadata or {}
        )
        
        conversation.messages.append(message)
        conversation.context.turn_count += 1
        conversation.context.updated_at = datetime.now()
        
        if agent_name:
            conversation.context.last_agent = agent_name
            
        # Clean up old messages if we exceed the limit
        if len(conversation.messages) > self.max_messages_per_conversation:
            conversation.messages = conversation.messages[-self.max_messages_per_conversation:]
            
        return message
        
    def get_conversation_history(self, conversation_id: str, last_n: int = 10) -> List[Message]:
        """Get the last N messages from a conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
            
        return conversation.messages[-last_n:] if last_n > 0 else conversation.messages
        
    def extract_topics(self, text: str) -> List[str]:
        """Extract potential topics from text (simple keyword-based)."""
        # Simple topic extraction - in production, use NLP libraries
        keywords = ["weather", "calculation", "math", "research", "search", "help", "greeting"]
        found_topics = []
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                found_topics.append(keyword)
                
        return found_topics
        
    def update_context(self, conversation_id: str, **updates):
        """Update conversation context."""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            for key, value in updates.items():
                setattr(conversation.context, key, value)
            conversation.context.updated_at = datetime.now()


class ConversationalA2AClient:
    """
    A conversational A2A client that maintains context and memory
    across multi-turn interactions.
    """
    
    def __init__(self, agent_router=None):
        self.memory = ConversationMemory()
        self.agent_router = agent_router
        self.active_conversations: Dict[str, str] = {}  # user_id -> conversation_id
        
    def start_conversation(self, user_id: str = "default_user") -> str:
        """Start a new conversation for a user."""
        conversation = self.memory.create_conversation(user_id)
        self.active_conversations[user_id] = conversation.id
        
        # Add welcome message
        self.memory.add_message(
            conversation.id,
            role="agent",
            content="Hello! I'm your AI assistant. I can help you with calculations, weather information, research, and general assistance. What would you like to know?",
            agent_name="system"
        )
        
        return conversation.id
        
    def get_active_conversation(self, user_id: str = "default_user") -> Optional[str]:
        """Get the active conversation ID for a user."""
        return self.active_conversations.get(user_id)
        
    async def chat(self, message: str, user_id: str = "default_user", 
                  conversation_id: str = None) -> Dict[str, Any]:
        """
        Handle a conversational message with context and memory.
        """
        
        # Get or create conversation
        if conversation_id is None:
            conversation_id = self.get_active_conversation(user_id)
            if conversation_id is None:
                conversation_id = self.start_conversation(user_id)
                
        # Add user message to conversation
        user_message = self.memory.add_message(
            conversation_id, 
            role="user", 
            content=message
        )
        
        # Extract topics from the message
        topics = self.memory.extract_topics(message)
        conversation = self.memory.get_conversation(conversation_id)
        
        if conversation:
            conversation.context.topics.update(topics)
        
        # Generate contextual response
        response_content = await self._generate_response(conversation_id, message)
        
        # Add agent response to conversation
        agent_message = self.memory.add_message(
            conversation_id,
            role="agent", 
            content=response_content["content"],
            agent_name=response_content.get("agent_name", "assistant"),
            metadata=response_content.get("metadata", {})
        )
        
        return {
            "conversation_id": conversation_id,
            "user_message_id": user_message.id,
            "agent_message_id": agent_message.id,
            "response": response_content["content"],
            "agent_used": response_content.get("agent_name", "assistant"),
            "confidence": response_content.get("confidence", 1.0),
            "turn_count": conversation.context.turn_count if conversation else 0,
            "topics": list(conversation.context.topics) if conversation else []
        }
        
    async def _generate_response(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """Generate a contextual response based on conversation history."""
        
        conversation = self.memory.get_conversation(conversation_id)
        if not conversation:
            return {
                "content": "I'm sorry, I couldn't find the conversation context.",
                "agent_name": "system",
                "confidence": 0.1
            }
            
        # Get conversation history for context
        history = self.memory.get_conversation_history(conversation_id, last_n=5)
        
        # If we have an agent router, use it for intelligent routing
        if self.agent_router:
            try:
                # Build context from conversation history
                context = {
                    "conversation_history": [
                        {"role": msg.role, "content": msg.content, "agent": msg.agent_name}
                        for msg in history[-3:]  # Last 3 messages for context
                    ],
                    "topics": list(conversation.context.topics),
                    "turn_count": conversation.context.turn_count,
                    "last_agent": conversation.context.last_agent
                }
                
                # Route the query
                agent_name, confidence = await self.agent_router.route_query(message, context)
                
                # Simulate agent response (in real implementation, this would call the actual agent)
                response_content = await self._simulate_agent_response(agent_name, message, context)
                
                return {
                    "content": response_content,
                    "agent_name": agent_name,
                    "confidence": confidence,
                    "metadata": {"routing_context": context}
                }
                
            except Exception as e:
                logger.error(f"Agent routing failed: {e}")
                # Fallback to simple response
        
        # Fallback: Generate simple contextual response
        return await self._generate_simple_response(message, conversation.context)
        
    async def _simulate_agent_response(self, agent_name: str, message: str, context: Dict) -> str:
        """Simulate agent response (replace with actual A2A calls in production)."""
        
        agent_responses = {
            "base": f"I'm the base agent. Regarding '{message}', I can provide general assistance. {self._add_context_awareness(context)}",
            "calculator": f"I'm the calculator agent. Let me help you with calculations related to '{message}'. {self._get_math_response(message)}",
            "weather": f"I'm the weather agent. For weather information about '{message}', {self._get_weather_response(message)}",
            "research": f"I'm the research agent. I can help you research '{message}'. {self._get_research_response(message)}"
        }
        
        base_response = agent_responses.get(agent_name, f"Agent {agent_name} received: {message}")
        
        # Add conversation context awareness
        if context.get("turn_count", 0) > 1:
            base_response += f" (This is turn {context['turn_count']} of our conversation)"
            
        return base_response
        
    def _add_context_awareness(self, context: Dict) -> str:
        """Add context awareness to responses."""
        if context.get("topics"):
            return f"I see we've been discussing: {', '.join(list(context['topics'])[:3])}"
        return "How can I assist you today?"
        
    def _get_math_response(self, message: str) -> str:
        """Generate math-related response."""
        if any(op in message for op in ['+', '-', '*', '/', 'calculate', 'compute']):
            return "I can perform mathematical calculations for you."
        return "What mathematical operation would you like me to perform?"
        
    def _get_weather_response(self, message: str) -> str:
        """Generate weather-related response."""
        if any(word in message.lower() for word in ['weather', 'temperature', 'forecast', 'rain', 'sunny']):
            return "I can provide current weather conditions and forecasts."
        return "What weather information do you need?"
        
    def _get_research_response(self, message: str) -> str:
        """Generate research-related response."""
        if any(word in message.lower() for word in ['research', 'find', 'search', 'information', 'who', 'what', 'when', 'where']):
            return "I can help you research and find information on various topics."
        return "What would you like me to research for you?"
        
    async def _generate_simple_response(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Generate a simple contextual response without agent routing."""
        
        # Analyze message for intent
        message_lower = message.lower()
        
        # Greeting detection
        if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            if context.turn_count == 1:
                content = "Hello! Nice to meet you. How can I help you today?"
            else:
                content = f"Hello again! This is our {context.turn_count}th interaction. What can I do for you?"
                
        # Math detection  
        elif any(math_word in message_lower for math_word in ['calculate', 'compute', 'math', '+', '-', '*', '/']):
            content = "I can help you with mathematical calculations. What would you like me to calculate?"
            
        # Weather detection
        elif any(weather_word in message_lower for weather_word in ['weather', 'temperature', 'forecast']):
            content = "I can provide weather information. What location are you interested in?"
            
        # Research detection
        elif any(research_word in message_lower for research_word in ['research', 'find', 'search', 'who', 'what']):
            content = "I can help you research information. What topic would you like me to look into?"
            
        # Default response with context
        else:
            if context.topics:
                content = f"I see we've been discussing {', '.join(list(context.topics)[:2])}. How can I help you further with '{message}'?"
            else:
                content = f"I understand you're asking about '{message}'. Let me help you with that."
                
        return {
            "content": content,
            "agent_name": "assistant",
            "confidence": 0.8
        }
        
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        conversation = self.memory.get_conversation(conversation_id)
        if not conversation:
            return {"error": "Conversation not found"}
            
        return {
            "conversation_id": conversation_id,
            "user_id": conversation.context.user_id,
            "turn_count": conversation.context.turn_count,
            "topics": list(conversation.context.topics),
            "message_count": len(conversation.messages),
            "active_agent": conversation.context.active_agent,
            "last_agent": conversation.context.last_agent,
            "created_at": conversation.context.created_at.isoformat(),
            "updated_at": conversation.context.updated_at.isoformat(),
            "recent_messages": [
                {
                    "role": msg.role,
                    "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                    "agent": msg.agent_name,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in conversation.messages[-5:]
            ]
        }
        
    def list_conversations(self, user_id: str = None) -> List[Dict[str, Any]]:
        """List all conversations, optionally filtered by user."""
        conversations = []
        
        for conv_id, conversation in self.memory.conversations.items():
            if user_id is None or conversation.context.user_id == user_id:
                conversations.append({
                    "conversation_id": conv_id,
                    "user_id": conversation.context.user_id,
                    "turn_count": conversation.context.turn_count,
                    "message_count": len(conversation.messages),
                    "topics": list(conversation.context.topics),
                    "created_at": conversation.context.created_at.isoformat(),
                    "updated_at": conversation.context.updated_at.isoformat(),
                    "last_message": conversation.messages[-1].content[:50] + "..." if conversation.messages else "No messages"
                })
                
        return sorted(conversations, key=lambda x: x["updated_at"], reverse=True)


# Example usage and testing
async def main():
    """Example usage of the Conversational A2A Client."""
    
    print("🗣️ Conversational A2A Client Demo")
    print("=" * 50)
    
    # Create client
    client = ConversationalA2AClient()
    
    # Start a conversation
    conversation_id = client.start_conversation("demo_user")
    print(f"Started conversation: {conversation_id}")
    
    # Example conversation
    messages = [
        "Hello there!",
        "What's the weather like today?", 
        "Can you calculate 25 + 17?",
        "Thank you for your help!",
        "What topics have we discussed so far?"
    ]
    
    for message in messages:
        print(f"\n👤 User: {message}")
        
        response = await client.chat(message, "demo_user", conversation_id)
        
        print(f"🤖 Assistant: {response['response']}")
        print(f"   Agent: {response['agent_used']}")
        print(f"   Turn: {response['turn_count']}")
        
    # Show conversation summary
    print(f"\n📊 Conversation Summary:")
    summary = client.get_conversation_summary(conversation_id)
    for key, value in summary.items():
        if key != "recent_messages":
            print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())