"""
Multi-Agent A2A Conversational Clients

This module provides various conversational A2A clients with LLM integration:

1. AIAgentRouter - LLM-powered intelligent agent routing
2. ConversationalA2AClient - Natural conversation with memory management  
3. SmartRoutingClient - Context-aware multi-agent orchestration
4. StreamingConversationClient - Real-time streaming conversations
"""

from .ai_agent_router import AIAgentRouter
from .conversational_client import ConversationalA2AClient
from .smart_routing_client import SmartRoutingClient
from .streaming_conversation_client import StreamingConversationClient

__all__ = [
    "AIAgentRouter",
    "ConversationalA2AClient", 
    "SmartRoutingClient",
    "StreamingConversationClient"
]