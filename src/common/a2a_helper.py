"""
A2A Client Helper

Helper functions to work with the new A2A SDK.
"""

from typing import Any, Dict, Optional
from a2a.client.client_factory import ClientFactory
from a2a.types import AgentCard
from a2a.client import ClientConfig


async def call_agent(
    agent_url: str,
    message: Dict[str, Any],
    agent_card: Optional[AgentCard] = None
) -> Any:
    """
    Call an agent using the new A2A SDK.
    
    This is a compatibility function to replace the old call_agent import.
    """
    # Create a minimal config
    config = ClientConfig()
    
    # Create client factory
    factory = ClientFactory(config)
    
    # If no agent card provided, create a minimal one
    if agent_card is None:
        # This is a simplified approach - in practice you'd want to 
        # fetch the actual agent card from the agent
        from a2a.client.client_factory import minimal_agent_card
        agent_card = minimal_agent_card(agent_url)
    
    # Create client
    client = factory.create(agent_card)
    
    try:
        # Send message
        result = await client.send_message(message)
        return result
    finally:
        # Clean up
        await client.close()
