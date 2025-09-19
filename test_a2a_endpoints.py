#!/usr/bin/env python3
"""
Direct A2A Protocol Testing Script
"""
import asyncio
import httpx
import json
from datetime import datetime

# Test endpoints
AGENTS = {
    "base": "http://localhost:8080",
    "calculator": "http://localhost:8081", 
    "weather": "http://localhost:8082",
    "research": "http://localhost:8083"
}

async def test_a2a_endpoints(agent_name, base_url):
    """Test various A2A protocol endpoints"""
    print(f"\n🔍 Testing {agent_name} agent endpoints:")
    
    async with httpx.AsyncClient() as client:
        # Test various A2A endpoints
        endpoints_to_test = [
            ("/", "GET"),
            ("/card", "GET"),
            ("/health", "GET"),
            ("/capabilities", "GET"),
            ("/skills", "GET"),
            ("/v1/messages", "POST"),
            ("/messages", "POST"),
            ("/tasks", "POST"),
            ("/api/v1/tasks", "POST")
        ]
        
        for endpoint, method in endpoints_to_test:
            try:
                url = f"{base_url}{endpoint}"
                
                if method == "GET":
                    response = await client.get(url, timeout=5.0)
                else:
                    # Try A2A message format
                    test_data = {
                        "message": {
                            "parts": [{"text": f"Test message to {agent_name}"}]
                        }
                    }
                    response = await client.post(
                        url, 
                        json=test_data, 
                        headers={"Content-Type": "application/json"},
                        timeout=5.0
                    )
                
                if response.status_code in [200, 201]:
                    content = response.text[:100] if response.text else "Empty response"
                    print(f"   ✅ {method} {endpoint}: {response.status_code} - {content}...")
                elif response.status_code == 404:
                    print(f"   ❌ {method} {endpoint}: Not Found")
                elif response.status_code == 405:
                    print(f"   ⚠️  {method} {endpoint}: Method Not Allowed")
                else:
                    print(f"   ⚠️  {method} {endpoint}: {response.status_code}")
                    
            except httpx.TimeoutException:
                print(f"   ⏰ {method} {endpoint}: Timeout")
            except Exception as e:
                print(f"   ❌ {method} {endpoint}: {str(e)}")

async def test_agent_with_a2a_client():
    """Test agents using proper A2A client approach"""
    print(f"\n🤖 Testing agents with A2A SDK approach:")
    
    try:
        # Import A2A SDK components
        from a2a.client import A2ACardResolver
        from a2a.types import MessageSendParams, SendMessageRequest, Message, TextPart
        
        # Test each agent
        for agent_name, url in AGENTS.items():
            print(f"\n   Testing {agent_name} agent at {url}")
            
            try:
                # Try to resolve the agent card
                resolver = A2ACardResolver()
                # This would typically resolve from the agent's card endpoint
                print(f"   ✅ A2A SDK can be imported for {agent_name}")
                
            except Exception as e:
                print(f"   ❌ A2A SDK test failed for {agent_name}: {e}")
                
    except ImportError as e:
        print(f"   ❌ A2A SDK not available: {e}")

async def simple_message_test():
    """Simple message tests to verify agents respond"""
    print(f"\n💬 Testing agent responses with simple HTTP calls:")
    
    async with httpx.AsyncClient() as client:
        
        test_cases = {
            "calculator": [
                "What is 25 + 37?",
                "Calculate 10 * 5",
                "Square root of 64"
            ],
            "weather": [
                "Weather in New York",
                "Temperature in London", 
                "Forecast for Tokyo"
            ],
            "base": [
                "Hello there!",
                "Tell me about yourself",
                "What can you do?"
            ],
            "research": [
                "Research quantum computing",
                "Find AI trends",
                "Climate change info"
            ]
        }
        
        for agent_name, agent_url in AGENTS.items():
            if agent_name in test_cases:
                print(f"\n   Testing {agent_name} agent:")
                
                for test_query in test_cases[agent_name]:
                    try:
                        # Try simple JSON format
                        response = await client.post(
                            f"{agent_url}/tasks",
                            json={"query": test_query},
                            timeout=10.0
                        )
                        
                        if response.status_code in [200, 201]:
                            content = response.text[:150] if response.text else "Empty"
                            print(f"     ✅ '{test_query}' -> {content}...")
                        else:
                            print(f"     ❌ '{test_query}' -> HTTP {response.status_code}")
                            
                    except Exception as e:
                        print(f"     ❌ '{test_query}' -> Error: {e}")

async def main():
    print("🚀 A2A Protocol Endpoint Discovery & Testing")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    
    # Test each agent's endpoints
    for agent_name, url in AGENTS.items():
        await test_a2a_endpoints(agent_name, url)
    
    # Test with A2A SDK
    await test_agent_with_a2a_client()
    
    # Test simple messages
    await simple_message_test()
    
    print(f"\n🎉 Testing completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())