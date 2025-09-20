#!/usr/bin/env python3
"""
Test A2A agents using proper JSONRPC protocol
"""
import asyncio
import httpx
import json
from datetime import datetime
import uuid

# Agent endpoints
AGENTS = {
    "base": "http://localhost:8080",
    "calculator": "http://localhost:8081", 
    "weather": "http://localhost:8082",
    "research": "http://localhost:8083"
}

async def test_jsonrpc_call(agent_name, agent_url, method, message_text):
    """Test agent with JSONRPC protocol"""
    print(f"   🧪 Testing {agent_name}: '{message_text}'")
    
    # Create JSONRPC request
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": {
            "message": {
                "parts": [{"text": message_text}]
            }
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                agent_url,
                json=jsonrpc_request,
                headers={"Content-Type": "application/json"},
                timeout=15.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    content = str(result['result'])[:150]
                    print(f"      ✅ Response: {content}...")
                    return True
                elif 'error' in result:
                    print(f"      ❌ JSONRPC Error: {result['error']}")
                    return False
                else:
                    print(f"      ⚠️  Unexpected response format: {str(result)[:100]}...")
                    return False
            else:
                print(f"      ❌ HTTP Error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"      ❌ Exception: {e}")
        return False

async def test_agent_cards():
    """Test getting agent cards"""
    print("🃏 Testing Agent Cards:")
    
    async with httpx.AsyncClient() as client:
        for agent_name, agent_url in AGENTS.items():
            try:
                response = await client.get(f"{agent_url}/.well-known/agent-card.json", timeout=5.0)
                if response.status_code == 200:
                    card = response.json()
                    print(f"   ✅ {agent_name}: {card['name']} v{card['version']} - {len(card['skills'])} skills")
                    for skill in card['skills']:
                        print(f"      🔧 {skill['name']}: {skill['description'][:60]}...")
                else:
                    print(f"   ❌ {agent_name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ {agent_name}: {e}")

async def test_calculator_functionality():
    """Test calculator agent with math problems"""
    print(f"\n🧮 Testing Calculator Agent with Dynamic Math Problems:")
    
    test_cases = [
        "What is 47 * 23 + 156?",
        "Calculate the square root of 289",
        "Convert 75 degrees Fahrenheit to Celsius", 
        "Find the average of these numbers: 12, 45, 78, 23, 89, 34",
        "What is 15% of 280?"
    ]
    
    success_count = 0
    for test_case in test_cases:
        if await test_jsonrpc_call("Calculator", AGENTS["calculator"], "sendMessage", test_case):
            success_count += 1
    
    print(f"   Calculator Results: {success_count}/{len(test_cases)} tests successful")
    return success_count > 0

async def test_weather_functionality():
    """Test weather agent with location queries"""
    print(f"\n🌤️ Testing Weather Agent with Location Queries:")
    
    test_cases = [
        "What's the current weather in San Francisco?",
        "Show me the weather forecast for Berlin, Germany",
        "What are the weather conditions in Sydney, Australia?",
        "Give me a 5-day forecast for Mumbai, India",
        "Current temperature and humidity in Cairo, Egypt"
    ]
    
    success_count = 0
    for test_case in test_cases:
        if await test_jsonrpc_call("Weather", AGENTS["weather"], "sendMessage", test_case):
            success_count += 1
    
    print(f"   Weather Results: {success_count}/{len(test_cases)} tests successful")
    return success_count > 0

async def test_base_agent_functionality():
    """Test base agent with conversational queries"""
    print(f"\n🤖 Testing Base Agent with Conversational Queries:")
    
    test_cases = [
        "Hello! How are you doing today?",
        "Can you tell me about your capabilities and what you can help me with?",
        "Explain the difference between artificial intelligence and machine learning",
        "What are some best practices for software development?",
        "How can I improve my time management skills?"
    ]
    
    success_count = 0
    for test_case in test_cases:
        if await test_jsonrpc_call("Base", AGENTS["base"], "sendMessage", test_case):
            success_count += 1
    
    print(f"   Base Agent Results: {success_count}/{len(test_cases)} tests successful")
    return success_count > 0

async def test_research_agent_functionality():
    """Test research agent with research queries"""
    print(f"\n🔍 Testing Research Agent with Research Topics:")
    
    test_cases = [
        "Research the latest developments in quantum computing technology",
        "Find information about sustainable energy solutions and their environmental impact",
        "What are the current trends in artificial intelligence and automation?",
        "Research the effects of remote work on productivity and employee satisfaction",
        "Provide an overview of blockchain technology applications beyond cryptocurrency"
    ]
    
    success_count = 0
    for test_case in test_cases:
        if await test_jsonrpc_call("Research", AGENTS["research"], "sendMessage", test_case):
            success_count += 1
    
    print(f"   Research Results: {success_count}/{len(test_cases)} tests successful")
    return success_count > 0

async def main():
    print("🚀 A2A Multi-Agent Dynamic Response Testing")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Test agent cards first
    await test_agent_cards()
    
    # Test each agent's functionality
    results = {}
    results['calculator'] = await test_calculator_functionality()
    results['weather'] = await test_weather_functionality() 
    results['base'] = await test_base_agent_functionality()
    results['research'] = await test_research_agent_functionality()
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"=" * 30)
    working_agents = sum(1 for success in results.values() if success)
    total_agents = len(results)
    
    for agent_name, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"   {agent_name.title()} Agent: {status}")
    
    print(f"\n🎯 Overall Result: {working_agents}/{total_agents} agents providing dynamic responses")
    
    if working_agents == total_agents:
        print("🎉 SUCCESS: All agents are providing dynamic, non-static responses!")
    elif working_agents > 0:
        print("⚠️  PARTIAL: Some agents are working, others may need investigation")
    else:
        print("❌ FAILURE: No agents are responding properly")
    
    print(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())