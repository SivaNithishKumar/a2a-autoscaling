#!/usr/bin/env python3
"""
Test script to verify A2A agents provide dynamic responses
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Test endpoints
AGENTS = {
    "base": "http://localhost:8080",
    "calculator": "http://localhost:8081", 
    "weather": "http://localhost:8082",
    "research": "http://localhost:8083"
}

async def test_agent_health(session, name, url):
    """Test agent health endpoint"""
    try:
        async with session.get(f"{url}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ {name} agent: {data.get('status', 'unknown')} - {data.get('agent', 'unknown')} v{data.get('version', 'unknown')}")
                return True
            else:
                print(f"❌ {name} agent health check failed: HTTP {response.status}")
                return False
    except Exception as e:
        print(f"❌ {name} agent connection failed: {e}")
        return False

async def test_calculator_functionality(session):
    """Test calculator agent with actual math problems"""
    print("\n🧮 Testing Calculator Agent Functionality:")
    
    test_cases = [
        "Calculate 25 * 37 + 15",
        "What is the square root of 144?",
        "Convert 32 degrees Celsius to Fahrenheit",
        "Find the average of 10, 20, 30, 40, 50"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            # Create A2A message format
            message_data = {
                "message": {
                    "parts": [{"text": test_case}]
                }
            }
            
            async with session.post(
                f"{AGENTS['calculator']}/stream", 
                json=message_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    print(f"   Test {i}: {test_case}")
                    print(f"   Response: {content[:200]}...")
                    print()
                else:
                    print(f"   Test {i} failed: HTTP {response.status}")
        except Exception as e:
            print(f"   Test {i} error: {e}")

async def test_weather_functionality(session):
    """Test weather agent with location queries"""
    print("\n🌤️ Testing Weather Agent Functionality:")
    
    test_cases = [
        "What's the weather in New York?",
        "Show me the forecast for London",
        "Current weather conditions in Tokyo",
        "Weather forecast for the next 5 days in Paris"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            # Create A2A message format
            message_data = {
                "message": {
                    "parts": [{"text": test_case}]
                }
            }
            
            async with session.post(
                f"{AGENTS['weather']}/stream", 
                json=message_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    print(f"   Test {i}: {test_case}")
                    print(f"   Response: {content[:200]}...")
                    print()
                else:
                    print(f"   Test {i} failed: HTTP {response.status}")
        except Exception as e:
            print(f"   Test {i} error: {e}")

async def test_base_agent_functionality(session):
    """Test base agent with general queries"""
    print("\n🤖 Testing Base Agent Functionality:")
    
    test_cases = [
        "Hello, how are you doing today?",
        "Tell me about yourself",
        "What can you help me with?",
        "Explain the concept of artificial intelligence"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            # Create A2A message format
            message_data = {
                "message": {
                    "parts": [{"text": test_case}]
                }
            }
            
            async with session.post(
                f"{AGENTS['base']}/stream", 
                json=message_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    print(f"   Test {i}: {test_case}")
                    print(f"   Response: {content[:200]}...")
                    print()
                else:
                    print(f"   Test {i} failed: HTTP {response.status}")
        except Exception as e:
            print(f"   Test {i} error: {e}")

async def test_research_agent_functionality(session):
    """Test research agent with research queries"""
    print("\n🔍 Testing Research Agent Functionality:")
    
    test_cases = [
        "Research the latest developments in quantum computing",
        "Find information about renewable energy trends",
        "What are the current AI industry trends?",
        "Research climate change impact on agriculture"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            # Create A2A message format
            message_data = {
                "message": {
                    "parts": [{"text": test_case}]
                }
            }
            
            async with session.post(
                f"{AGENTS['research']}/stream", 
                json=message_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    print(f"   Test {i}: {test_case}")
                    print(f"   Response: {content[:200]}...")
                    print()
                else:
                    print(f"   Test {i} failed: HTTP {response.status}")
        except Exception as e:
            print(f"   Test {i} error: {e}")

async def main():
    print("🚀 A2A Multi-Agent System Testing")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoints
        print("🏥 Testing Agent Health:")
        healthy_agents = []
        for name, url in AGENTS.items():
            if await test_agent_health(session, name, url):
                healthy_agents.append(name)
        
        print(f"\n✅ {len(healthy_agents)}/{len(AGENTS)} agents are healthy")
        
        # Test functionality for healthy agents
        if "calculator" in healthy_agents:
            await test_calculator_functionality(session)
        
        if "weather" in healthy_agents:
            await test_weather_functionality(session)
            
        if "base" in healthy_agents:
            await test_base_agent_functionality(session)
            
        if "research" in healthy_agents:
            await test_research_agent_functionality(session)
        
        print("🎉 Testing completed!")
        print(f"Test ended at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())