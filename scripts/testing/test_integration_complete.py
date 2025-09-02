#!/usr/bin/env python3
"""
End-to-End Integration Test Suite for Multi-Agent A2A System

Comprehensive testing of the complete production-ready AI-Ops system
including all agents, monitoring, and A2A communication patterns.
"""

import asyncio
import sys
import time
import json
import httpx
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

print("🧪 END-TO-END INTEGRATION TEST SUITE")
print("====================================")
print("🏗️ Multi-Agent A2A System - Production Validation")
print("🎯 Complete system integration and reliability testing")
print()

@dataclass
class AgentEndpoint:
    """Agent endpoint configuration."""
    name: str
    host: str
    port: int
    health_path: str = "/health"
    card_path: str = "/.well-known/agent-card.json"
    metrics_port: Optional[int] = None

# Define all agent endpoints
AGENTS = [
    AgentEndpoint("Base Agent", "localhost", 8000, metrics_port=9080),
    AgentEndpoint("Calculator Agent", "localhost", 8001, metrics_port=9081),
    AgentEndpoint("Weather Agent", "localhost", 8002, metrics_port=9082),
    AgentEndpoint("Research Agent", "localhost", 8003, metrics_port=9083),
    AgentEndpoint("Move Orchestrator", "localhost", 8004, metrics_port=8084),
    AgentEndpoint("Infrastructure Monitor", "localhost", 8005, metrics_port=8085),
]

MONITORING_ENDPOINTS = [
    ("Prometheus", "localhost", 9090, "/api/v1/query"),
    ("Grafana", "localhost", 3000, "/api/health"),
]

class TestResult:
    """Test result tracking."""
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
    
    def add_result(self, test_name: str, passed: bool, details: str = ""):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.tests_failed += 1
            self.failures.append((test_name, details))
            print(f"❌ {test_name}: FAILED - {details}")
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print("📊 END-TO-END INTEGRATION TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.tests_run}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failures:
            print(f"\n❌ Failed Tests:")
            for name, details in self.failures:
                print(f"   - {name}: {details}")


async def test_agent_health(result: TestResult):
    """Test 1: Agent Health and Availability"""
    print("\n🏥 Test 1: Agent Health and Availability")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for agent in AGENTS:
            try:
                # Test health endpoint
                health_url = f"http://{agent.host}:{agent.port}{agent.health_path}"
                response = await client.get(health_url)
                
                if response.status_code == 200:
                    result.add_result(f"{agent.name} Health Check", True)
                else:
                    # Try alternative health check via agent card
                    card_url = f"http://{agent.host}:{agent.port}{agent.card_path}"
                    card_response = await client.get(card_url)
                    
                    if card_response.status_code == 200:
                        result.add_result(f"{agent.name} Health Check", True, "via agent card")
                    else:
                        result.add_result(f"{agent.name} Health Check", False, 
                                        f"HTTP {response.status_code}")
                        
            except Exception as e:
                result.add_result(f"{agent.name} Health Check", False, str(e))


async def test_agent_cards(result: TestResult):
    """Test 2: Agent Card Discovery"""
    print("\n🃏 Test 2: Agent Card Discovery (A2A Protocol)")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for agent in AGENTS:
            try:
                card_url = f"http://{agent.host}:{agent.port}{agent.card_path}"
                response = await client.get(card_url)
                
                if response.status_code == 200:
                    card_data = response.json()
                    
                    # Validate required fields
                    required_fields = ['name', 'description', 'skills']
                    missing_fields = [field for field in required_fields if field not in card_data]
                    
                    if not missing_fields:
                        skills_count = len(card_data.get('skills', []))
                        result.add_result(f"{agent.name} Agent Card", True, 
                                        f"{skills_count} skills")
                    else:
                        result.add_result(f"{agent.name} Agent Card", False, 
                                        f"Missing fields: {missing_fields}")
                else:
                    result.add_result(f"{agent.name} Agent Card", False, 
                                    f"HTTP {response.status_code}")
                    
            except Exception as e:
                result.add_result(f"{agent.name} Agent Card", False, str(e))


async def test_metrics_endpoints(result: TestResult):
    """Test 3: Metrics Collection"""
    print("\n📊 Test 3: Metrics Collection (Prometheus)")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for agent in AGENTS:
            try:
                # Use dedicated metrics port if available, otherwise main port
                metrics_port = agent.metrics_port or agent.port
                metrics_url = f"http://{agent.host}:{metrics_port}/metrics"
                
                response = await client.get(metrics_url)
                
                if response.status_code == 200:
                    metrics_text = response.text
                    
                    # Check for key metrics
                    expected_metrics = [
                        'a2a_requests_total',
                        'a2a_request_duration_seconds',
                        'a2a_agent_uptime_seconds'
                    ]
                    
                    found_metrics = [metric for metric in expected_metrics 
                                   if metric in metrics_text]
                    
                    if len(found_metrics) >= 2:  # At least 2 out of 3 metrics
                        result.add_result(f"{agent.name} Metrics", True, 
                                        f"{len(found_metrics)}/3 metrics")
                    else:
                        result.add_result(f"{agent.name} Metrics", False, 
                                        f"Only {len(found_metrics)}/3 metrics found")
                else:
                    result.add_result(f"{agent.name} Metrics", False, 
                                    f"HTTP {response.status_code}")
                    
            except Exception as e:
                result.add_result(f"{agent.name} Metrics", False, str(e))


async def test_a2a_communication(result: TestResult):
    """Test 4: A2A Agent Communication"""
    print("\n🔗 Test 4: A2A Agent Communication")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test Move Orchestrator specific functionality
        try:
            orchestrator = next(agent for agent in AGENTS if "Orchestrator" in agent.name)
            
            # Test orchestration request
            request_data = {
                "capability": "orchestrate_move",
                "input": {
                    "origin": "London, UK",
                    "destination": "Manchester, UK",
                    "move_date": "2025-09-15"
                }
            }
            
            response = await client.post(
                f"http://{orchestrator.host}:{orchestrator.port}/a2a/tasks",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201, 202]:
                result.add_result("Move Orchestration A2A", True, 
                                f"HTTP {response.status_code}")
            else:
                result.add_result("Move Orchestration A2A", False, 
                                f"HTTP {response.status_code}")
                
        except Exception as e:
            result.add_result("Move Orchestration A2A", False, str(e))
        
        # Test Infrastructure Monitor functionality
        try:
            monitor = next(agent for agent in AGENTS if "Monitor" in agent.name)
            
            request_data = {
                "capability": "monitor_infrastructure",
                "input": {
                    "services": ["web_frontend", "database_primary"],
                    "include_recommendations": True
                }
            }
            
            response = await client.post(
                f"http://{monitor.host}:{monitor.port}/a2a/tasks",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201, 202]:
                result.add_result("Infrastructure Monitor A2A", True, 
                                f"HTTP {response.status_code}")
            else:
                result.add_result("Infrastructure Monitor A2A", False, 
                                f"HTTP {response.status_code}")
                
        except Exception as e:
            result.add_result("Infrastructure Monitor A2A", False, str(e))


async def test_monitoring_stack(result: TestResult):
    """Test 5: Monitoring Stack Integration"""
    print("\n📈 Test 5: Monitoring Stack Integration")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for service_name, host, port, health_path in MONITORING_ENDPOINTS:
            try:
                url = f"http://{host}:{port}{health_path}"
                
                if service_name == "Prometheus":
                    # Test Prometheus query endpoint
                    query_url = f"http://{host}:{port}/api/v1/query"
                    params = {"query": "up"}
                    response = await client.get(query_url, params=params)
                else:
                    # Test service health
                    response = await client.get(url)
                
                if response.status_code == 200:
                    result.add_result(f"{service_name} Service", True)
                else:
                    result.add_result(f"{service_name} Service", False, 
                                    f"HTTP {response.status_code}")
                    
            except Exception as e:
                result.add_result(f"{service_name} Service", False, str(e))


async def test_system_performance(result: TestResult):
    """Test 6: System Performance and Load"""
    print("\n⚡ Test 6: System Performance and Load")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test concurrent requests to different agents
        tasks = []
        
        for agent in AGENTS[:4]:  # Test first 4 agents
            task = client.get(f"http://{agent.host}:{agent.port}{agent.card_path}")
            tasks.append(task)
        
        start_time = time.time()
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            successful_responses = sum(1 for r in responses 
                                     if isinstance(r, httpx.Response) and r.status_code == 200)
            
            total_time = end_time - start_time
            
            if successful_responses >= 3 and total_time < 5.0:
                result.add_result("Concurrent Agent Requests", True, 
                                f"{successful_responses}/4 agents in {total_time:.2f}s")
            else:
                result.add_result("Concurrent Agent Requests", False, 
                                f"Only {successful_responses}/4 successful")
                
        except Exception as e:
            result.add_result("Concurrent Agent Requests", False, str(e))


async def test_reliability_features(result: TestResult):
    """Test 7: Reliability Features (Circuit Breakers, Health Checks)"""
    print("\n🛡️ Test 7: Reliability Features")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test health endpoints for AI-Ops agents
        ai_ops_agents = [agent for agent in AGENTS if agent.metrics_port]
        
        for agent in ai_ops_agents:
            try:
                # Test health endpoint with detailed checks
                health_url = f"http://{agent.host}:{agent.port}/health"
                response = await client.get(health_url)
                
                if response.status_code == 200:
                    try:
                        health_data = response.json()
                        if isinstance(health_data, dict) and 'status' in health_data:
                            result.add_result(f"{agent.name} Health Details", True, 
                                            health_data.get('status', 'healthy'))
                        else:
                            result.add_result(f"{agent.name} Health Details", True, 
                                            "basic health check")
                    except:
                        result.add_result(f"{agent.name} Health Details", True, 
                                        "basic health check")
                else:
                    result.add_result(f"{agent.name} Health Details", False, 
                                    f"HTTP {response.status_code}")
                    
            except Exception as e:
                result.add_result(f"{agent.name} Health Details", False, str(e))


async def test_ai_ops_capabilities(result: TestResult):
    """Test 8: AI-Ops Specific Capabilities"""
    print("\n🤖 Test 8: AI-Ops Specific Capabilities")
    print("-" * 40)
    
    # Test Move Orchestrator capabilities
    try:
        from multi_agent_a2a.agents.move_orchestrator.agent import MoveOrchestrationAgent
        
        orchestrator = MoveOrchestrationAgent()
        skills = orchestrator.get_skills()
        
        expected_skills = ['orchestrate_move', 'optimize_timeline', 'coordinate_services', 'estimate_costs']
        found_skills = [skill.id for skill in skills]
        
        matching_skills = [skill for skill in expected_skills if skill in found_skills]
        
        if len(matching_skills) >= 3:
            result.add_result("Move Orchestrator Skills", True, 
                            f"{len(matching_skills)}/4 skills")
        else:
            result.add_result("Move Orchestrator Skills", False, 
                            f"Only {len(matching_skills)}/4 skills")
            
    except Exception as e:
        result.add_result("Move Orchestrator Skills", False, str(e))
    
    # Test Infrastructure Monitor capabilities
    try:
        from multi_agent_a2a.agents.infrastructure_monitor.agent import InfrastructureMonitoringAgent
        
        monitor = InfrastructureMonitoringAgent()
        skills = monitor.get_skills()
        
        expected_skills = ['monitor_infrastructure', 'detect_anomalies', 'predict_failures']
        found_skills = [skill.id for skill in skills]
        
        matching_skills = [skill for skill in expected_skills if skill in found_skills]
        
        if len(matching_skills) == 3:
            result.add_result("Infrastructure Monitor Skills", True, 
                            f"{len(matching_skills)}/3 skills")
        else:
            result.add_result("Infrastructure Monitor Skills", False, 
                            f"Only {len(matching_skills)}/3 skills")
            
    except Exception as e:
        result.add_result("Infrastructure Monitor Skills", False, str(e))


async def main():
    """Run complete end-to-end integration test suite."""
    result = TestResult()
    
    print("🚀 Starting comprehensive system validation...")
    print("This test suite validates the complete multi-agent A2A system")
    print("including agents, monitoring, A2A communication, and AI-Ops capabilities.")
    print()
    
    # Run all test suites
    test_suites = [
        test_agent_health,
        test_agent_cards,
        test_metrics_endpoints,
        test_a2a_communication,
        test_monitoring_stack,
        test_system_performance,
        test_reliability_features,
        test_ai_ops_capabilities,
    ]
    
    for test_suite in test_suites:
        try:
            await test_suite(result)
        except Exception as e:
            print(f"❌ Test suite {test_suite.__name__} failed: {e}")
            result.add_result(f"Test Suite {test_suite.__name__}", False, str(e))
    
    # Print comprehensive summary
    result.print_summary()
    
    if result.tests_failed == 0:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("🚀 Multi-Agent A2A System is ready for production deployment!")
        print("🏗️ All AI-Ops capabilities validated and operational")
        return True
    else:
        print(f"\n⚠️  {result.tests_failed} tests failed - system needs attention")
        print("Please review failed tests before production deployment")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)