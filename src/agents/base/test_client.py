"""Test client for Base Agent."""

import asyncio
import httpx
from a2a.client.client import A2AClient


async def test_base_agent():
    """Test the Base Agent functionality."""
    
    # Initialize A2A client
    async with httpx.AsyncClient() as http_client:
        client = A2AClient(
            base_url="http://localhost:8000",
            http_client=http_client
        )
        
        # Test agent card retrieval
        print("Testing Base Agent...")
        try:
            agent_card = await client.get_agent_card()
            print(f"Agent: {agent_card.name}")
            print(f"Description: {agent_card.description}")
            print(f"Skills: {[skill.name for skill in agent_card.skills]}")
            print()
            
            # Test general assistance
            print("Testing general assistance...")
            response = await client.send_message("Hello! Can you tell me about yourself?")
            print(f"Response: {response}")
            print()
            
            # Test conversation
            print("Testing conversation...")
            response = await client.send_message("What can you help me with?")
            print(f"Response: {response}")
            print()
            
            # Test general query
            print("Testing general query...")
            response = await client.send_message("Explain what artificial intelligence is")
            print(f"Response: {response}")
            print()
            
        except Exception as e:
            print(f"Error testing base agent: {e}")


if __name__ == "__main__":
    asyncio.run(test_base_agent())
