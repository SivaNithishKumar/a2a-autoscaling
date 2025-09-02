"""Test client for Research Agent."""

import asyncio
import httpx
from a2a.client.client import A2AClient


async def test_research_agent():
    """Test the Research Agent functionality."""
    
    # Initialize A2A client
    async with httpx.AsyncClient() as http_client:
        client = A2AClient(
            base_url="http://localhost:8003",
            http_client=http_client
        )
        
        # Test agent card retrieval
        print("Testing Research Agent...")
        try:
            agent_card = await client.get_agent_card()
            print(f"Agent: {agent_card.name}")
            print(f"Description: {agent_card.description}")
            print(f"Skills: {[skill.name for skill in agent_card.skills]}")
            print()
            
            # Test web search
            print("Testing web search...")
            response = await client.send_message("Search for information about artificial intelligence")
            print(f"Response: {response}")
            print()
            
            # Test fact checking
            print("Testing fact checking...")
            response = await client.send_message("Fact check: Python was created in 1991")
            print(f"Response: {response}")
            print()
            
            # Test content analysis
            print("Testing content analysis...")
            response = await client.send_message("Analyze the key themes in machine learning research")
            print(f"Response: {response}")
            print()
            
            # Test general research
            print("Testing general research...")
            response = await client.send_message("Research the latest developments in quantum computing")
            print(f"Response: {response}")
            print()
            
        except Exception as e:
            print(f"Error testing research agent: {e}")


if __name__ == "__main__":
    asyncio.run(test_research_agent())
