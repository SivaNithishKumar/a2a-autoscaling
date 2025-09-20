#!/usr/bin/env python3
"""
Test script to verify A2A agent discovery and communication
"""

import asyncio
import httpx
import json
import os
from uuid import uuid4

async def test_agent_communication():
    """Test communication with A2A agents"""
    
    # Get agent endpoints
    namespace = "multi-agent-a2a"
    base_url_template = "http://{service_name}.{namespace}.svc.cluster.local:{port}"
    
    agents = {
        "base": {
            "url": base_url_template.format(service_name="base-agent-service", namespace=namespace, port=8080),
            "name": "Base Agent"
        },
        "calculator": {
            "url": base_url_template.format(service_name="calculator-agent-service", namespace=namespace, port=8081),
            "name": "Calculator"
        }
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for agent_id, config in agents.items():
            print(f"\n🧪 Testing {config['name']} ({agent_id})")
            print(f"   URL: {config['url']}")
            
            try:
                # Test 1: Get agent card
                card_response = await client.get(f"{config['url']}/.well-known/agent-card.json")
                if card_response.status_code == 200:
                    print("   ✅ Agent card: SUCCESS")
                    card_data = card_response.json()
                    print(f"   📋 Agent name: {card_data.get('name', 'Unknown')}")
                else:
                    print(f"   ❌ Agent card: FAILED ({card_response.status_code})")
                    continue
                
                # Test 2: Send test message using A2A protocol
                message_data = {
                    "jsonrpc": "2.0",
                    "id": str(uuid4()),
                    "method": "message/send",
                    "params": {
                        "message": {
                            "role": "user",
                            "parts": [{"kind": "text", "text": "Hello, test message"}],
                            "messageId": uuid4().hex,
                        }
                    }
                }
                
                # Send to root endpoint (correct A2A protocol)
                response = await client.post(
                    f"{config['url']}/",
                    json=message_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    print("   ✅ Message send: SUCCESS")
                    response_data = response.json()
                    if "result" in response_data:
                        print("   📝 Agent responded successfully")
                    else:
                        print("   ⚠️  Unexpected response format")
                else:
                    print(f"   ❌ Message send: FAILED ({response.status_code})")
                    print(f"   📄 Response: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Connection error: {e}")
    
    print("\n" + "="*50)
    print("🎯 Agent Discovery Test Complete")

if __name__ == "__main__":
    asyncio.run(test_agent_communication())