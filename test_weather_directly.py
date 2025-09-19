#!/usr/bin/env python3
"""
Direct test of weather agent using proper A2A protocol
"""
import asyncio
import httpx
import json

async def test_weather_direct():
    """Test weather agent directly using A2A protocol"""
    
    # Test with the actual A2A protocol format
    test_requests = [
        {
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "tasks.create",
            "params": {
                "message": {
                    "parts": [{"text": "What's the weather in New York?"}]
                }
            }
        },
        {
            "jsonrpc": "2.0", 
            "id": "test-2",
            "method": "sendMessage",
            "params": {
                "message": {
                    "parts": [{"text": "Weather forecast for London"}]
                }
            }
        },
        {
            "jsonrpc": "2.0",
            "id": "test-3", 
            "method": "process_message",
            "params": {
                "message": "Current weather in Tokyo"
            }
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for i, request in enumerate(test_requests):
            print(f"\n🧪 Test {i+1}: {request['method']}")
            print(f"   Message: {request['params']}")
            
            try:
                response = await client.post(
                    "http://localhost:8082/jsonrpc",
                    json=request,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"   Response: {json.dumps(result, indent=2)}")
                else:
                    print(f"   Error: {response.text}")
                    
            except Exception as e:
                print(f"   Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_weather_direct())