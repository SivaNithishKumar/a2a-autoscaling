"""A2A protocol utilities and helpers."""

from typing import List, Dict, Any, Optional
from a2a.types import (
    AgentCard,
    AgentSkill,
    AgentCapabilities,
    Message,
    TextPart,
    DataPart,
)
from . import get_logger

logger = get_logger(__name__)


def create_agent_card(
    name: str,
    description: str,
    url: str,
    skills: List[AgentSkill],
    version: str = "1.0.0",
    streaming: bool = True,
    push_notifications: bool = False
) -> AgentCard:
    """Create an A2A agent card with common configuration."""
    return AgentCard(
        name=name,
        description=description,
        url=url,
        version=version,
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["text/plain", "application/json"],
        capabilities=AgentCapabilities(
            streaming=streaming,
            push_notifications=push_notifications
        ),
        skills=skills,
    )


def create_skill(
    id: str,
    name: str,
    description: str,
    tags: List[str],
    examples: List[str],
    input_modes: Optional[List[str]] = None,
    output_modes: Optional[List[str]] = None
) -> AgentSkill:
    """Create an A2A agent skill."""
    return AgentSkill(
        id=id,
        name=name,
        description=description,
        tags=tags,
        examples=examples,
        input_modes=input_modes or ["text/plain", "application/json"],
        output_modes=output_modes or ["text/plain", "application/json"],
    )


def create_text_message(
    text: str,
    role: str = "agent",
    message_id: Optional[str] = None,
    task_id: Optional[str] = None,
    context_id: Optional[str] = None
) -> Message:
    """Create a text message for A2A communication."""
    return Message(
        role=role,
        parts=[TextPart(kind="text", text=text)],
        message_id=message_id,
        task_id=task_id,
        context_id=context_id,
        kind="message"
    )


def create_data_message(
    data: Dict[str, Any],
    role: str = "agent",
    mime_type: str = "application/json",
    message_id: Optional[str] = None,
    task_id: Optional[str] = None,
    context_id: Optional[str] = None
) -> Message:
    """Create a data message for A2A communication."""
    return Message(
        role=role,
        parts=[DataPart(kind="data", data=data, mime_type=mime_type)],
        message_id=message_id,
        task_id=task_id,
        context_id=context_id,
        kind="message"
    )


def extract_text_from_message(message: Message) -> Optional[str]:
    """Extract text content from an A2A message."""
    for part in message.parts:
        if hasattr(part, 'kind') and part.kind == "text":
            return part.text
    return None


def extract_data_from_message(message: Message) -> Optional[Dict[str, Any]]:
    """Extract data content from an A2A message."""
    for part in message.parts:
        if hasattr(part, 'kind') and part.kind == "data":
            return part.data
    return None


class A2AClientHelper:
    """Helper class for A2A client operations."""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
    
    def get_agent_url(self, port: int) -> str:
        """Get agent URL for a given port."""
        return f"{self.base_url}:{port}"
    
    async def check_agent_health(self, agent_url: str) -> bool:
        """Check if an agent is healthy and responding."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{agent_url}/.well-known/agent.json")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {agent_url}: {e}")
            return False
    
    async def discover_agent_capabilities(self, agent_url: str) -> Optional[AgentCard]:
        """Discover agent capabilities by fetching its agent card."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{agent_url}/.well-known/agent.json")
                if response.status_code == 200:
                    return AgentCard.model_validate(response.json())
        except Exception as e:
            logger.error(f"Failed to discover capabilities for {agent_url}: {e}")
        return None
