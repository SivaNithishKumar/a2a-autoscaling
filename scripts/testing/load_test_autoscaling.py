#!/usr/bin/env python3
"""
Load Testing Script for A2A Agent Autoscaling Demo

This script generates load against A2A agents to demonstrate Kubernetes
Horizontal Pod Autoscaler (HPA) in action.
"""

import asyncio
import aiohttp
import time
import json
import argparse
import sys
from typing import Dict, List, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LoadTestConfig:
    """Configuration for load testing"""
    duration_seconds: int = 300
    requests_per_second: int = 10
    concurrent_workers: int = 5
    ramp_up_seconds: int = 60
    target_agents: List[str] = None
    
    def __post_init__(self):
        if self.target_agents is None:
            self.target_agents = ["base", "calculator", "weather", "research", "move-orchestrator"]

@dataclass
class TestResults:
    """Results from load testing"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class A2ALoadTester:
    """Load tester for A2A agents with autoscaling demonstration"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results = {agent: TestResults() for agent in config.target_agents}
        self.session = None
        self.running = False
        
        # Agent endpoints with Kubernetes support
        self.agent_endpoints = self._get_agent_endpoints()
        
        # Test messages for each agent
        self.test_messages = {
            "base": [
                "Hello, how are you today?",
                "What can you help me with?",
                "Tell me about yourself",
                "What are your capabilities?"
            ],
            "calculator": [
                "What is 25 + 17?",
                "Calculate 100 * 45",
                "What is the square root of 144?",
                "Convert 75 fahrenheit to celsius"
            ],
            "weather": [
                "What's the weather like in New York?",
                "Weather forecast for London",
                "Is it raining in Seattle?",
                "Temperature in Tokyo"
            ],
            "research": [
                "Tell me about artificial intelligence",
                "Research quantum computing",
                "What is machine learning?",
                "Explain blockchain technology"
            ],
            "move-orchestrator": [
                "Plan my move from London to Manchester",
                "Help me organize a relocation",
                "Moving timeline for next month",
                "Coordinate my office move"
            ]
        }
    
    def _get_agent_endpoints(self) -> Dict[str, str]:
        """Get agent endpoints based on environment (local or Kubernetes)"""
        import os
        
        # Check if running in Kubernetes environment or if K8s endpoints are specified
        in_k8s = os.getenv("KUBERNETES_SERVICE_HOST") is not None
        use_k8s_services = os.getenv("USE_K8S_SERVICES", "false").lower() == "true"
        namespace = os.getenv("NAMESPACE", "multi-agent-a2a")
        
        if in_k8s or use_k8s_services:
            # Kubernetes internal service discovery
            base_url_template = "http://{service_name}.{namespace}.svc.cluster.local:{port}"
            return {
                "base": base_url_template.format(
                    service_name="base-agent-service", 
                    namespace=namespace, 
                    port=8080
                ),
                "calculator": base_url_template.format(
                    service_name="calculator-agent-service", 
                    namespace=namespace, 
                    port=8081
                ),
                "weather": base_url_template.format(
                    service_name="weather-agent-service", 
                    namespace=namespace, 
                    port=8082
                ),
                "research": base_url_template.format(
                    service_name="research-agent-service", 
                    namespace=namespace, 
                    port=8083
                ),
                "move-orchestrator": base_url_template.format(
                    service_name="move-orchestrator-agent-service", 
                    namespace=namespace, 
                    port=8004
                ),
                "infrastructure-monitor": base_url_template.format(
                    service_name="infrastructure-monitor-agent-service", 
                    namespace=namespace, 
                    port=8005
                )
            }
        else:
            # Local development with environment variable overrides or port-forwarded services
            return {
                "base": os.getenv("BASE_AGENT_URL", "http://localhost:8080"),
                "calculator": os.getenv("CALCULATOR_AGENT_URL", "http://localhost:8081"),
                "weather": os.getenv("WEATHER_AGENT_URL", "http://localhost:8082"),
                "research": os.getenv("RESEARCH_AGENT_URL", "http://localhost:8083"),
                "move-orchestrator": os.getenv("MOVE_ORCHESTRATOR_URL", "http://localhost:8004"),
                "infrastructure-monitor": os.getenv("INFRASTRUCTURE_MONITOR_URL", "http://localhost:8005")
            }
    
    async def create_session(self):
        """Create aiohttp session with proper configuration"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={"User-Agent": "A2A-LoadTester/1.0"}
        )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def send_a2a_request(self, agent_name: str, message: str) -> Dict[str, Any]:
        """Send A2A request to agent"""
        endpoint = self.agent_endpoints.get(agent_name)
        if not endpoint:
            return {"success": False, "error": f"Unknown agent: {agent_name}"}
        
        # A2A message format
        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": message}],
                "messageId": f"load-test-{int(time.time() * 1000)}"
            }
        }
        
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{endpoint}/a2a/tasks",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "response_time": response_time,
                        "status": response.status,
                        "result": result
                    }
                else:
                    return {
                        "success": False,
                        "response_time": response_time,
                        "status": response.status,
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "success": False,
                "response_time": response_time,
                "error": str(e)
            }
    
    async def worker(self, agent_name: str, worker_id: int):
        """Worker coroutine for sending requests"""
        messages = self.test_messages.get(agent_name, ["Hello"])
        message_index = 0
        
        while self.running:
            message = messages[message_index % len(messages)]
            message_index += 1
            
            result = await self.send_a2a_request(agent_name, message)
            
            # Update results
            results = self.results[agent_name]
            results.total_requests += 1
            
            if result["success"]:
                results.successful_requests += 1
                response_time = result["response_time"]
                results.min_response_time = min(results.min_response_time, response_time)
                results.max_response_time = max(results.max_response_time, response_time)
                
                # Update average response time
                total_successful = results.successful_requests
                if total_successful == 1:
                    results.average_response_time = response_time
                else:
                    results.average_response_time = (
                        (results.average_response_time * (total_successful - 1) + response_time) 
                        / total_successful
                    )
            else:
                results.failed_requests += 1
                results.errors.append(f"Worker {worker_id}: {result.get('error', 'Unknown error')}")
            
            # Control request rate
            await asyncio.sleep(1.0 / self.config.requests_per_second)
    
    async def monitor_progress(self):
        """Monitor and display progress"""
        start_time = time.time()
        
        while self.running:
            elapsed = time.time() - start_time
            remaining = max(0, self.config.duration_seconds - elapsed)
            
            print(f"\n⏱️  Time: {elapsed:.1f}s / {self.config.duration_seconds}s (Remaining: {remaining:.1f}s)")
            
            for agent_name in self.config.target_agents:
                results = self.results[agent_name]
                success_rate = (results.successful_requests / max(1, results.total_requests)) * 100
                
                print(f"🤖 {agent_name:15} | "
                      f"Requests: {results.total_requests:4d} | "
                      f"Success: {success_rate:5.1f}% | "
                      f"Avg RT: {results.average_response_time:.3f}s")
            
            await asyncio.sleep(5)
    
    async def run_load_test(self):
        """Run the complete load test"""
        print(f"🚀 Starting A2A Load Test for Autoscaling Demo")
        print(f"Duration: {self.config.duration_seconds}s")
        print(f"Requests/sec: {self.config.requests_per_second}")
        print(f"Concurrent workers: {self.config.concurrent_workers}")
        print(f"Target agents: {', '.join(self.config.target_agents)}")
        print(f"Ramp-up: {self.config.ramp_up_seconds}s")
        print()
        
        await self.create_session()
        
        try:
            self.running = True
            
            # Start workers for each agent
            tasks = []
            
            # Create workers
            for agent_name in self.config.target_agents:
                for worker_id in range(self.config.concurrent_workers):
                    task = asyncio.create_task(self.worker(agent_name, worker_id))
                    tasks.append(task)
            
            # Start progress monitor
            monitor_task = asyncio.create_task(self.monitor_progress())
            tasks.append(monitor_task)
            
            # Run for specified duration
            await asyncio.sleep(self.config.duration_seconds)
            
            # Stop all tasks
            self.running = False
            
            # Wait for tasks to complete
            for task in tasks:
                task.cancel()
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        finally:
            await self.close_session()
    
    def print_results(self):
        """Print final test results"""
        print("\n" + "="*80)
        print("🎯 LOAD TEST RESULTS")
        print("="*80)
        
        total_requests = sum(r.total_requests for r in self.results.values())
        total_successful = sum(r.successful_requests for r in self.results.values())
        total_failed = sum(r.failed_requests for r in self.results.values())
        
        overall_success_rate = (total_successful / max(1, total_requests)) * 100
        
        print(f"📊 Overall Statistics:")
        print(f"   Total Requests: {total_requests}")
        print(f"   Successful: {total_successful}")
        print(f"   Failed: {total_failed}")
        print(f"   Success Rate: {overall_success_rate:.2f}%")
        print()
        
        print(f"🤖 Per-Agent Results:")
        for agent_name, results in self.results.items():
            if results.total_requests > 0:
                success_rate = (results.successful_requests / results.total_requests) * 100
                print(f"   {agent_name:20} | "
                      f"Requests: {results.total_requests:4d} | "
                      f"Success: {success_rate:5.1f}% | "
                      f"Avg RT: {results.average_response_time:.3f}s | "
                      f"Min: {results.min_response_time:.3f}s | "
                      f"Max: {results.max_response_time:.3f}s")
        
        # Show errors if any
        all_errors = []
        for results in self.results.values():
            all_errors.extend(results.errors)
        
        if all_errors:
            print(f"\n❌ Errors ({len(all_errors)} total):")
            for error in all_errors[:10]:  # Show first 10 errors
                print(f"   {error}")
            if len(all_errors) > 10:
                print(f"   ... and {len(all_errors) - 10} more errors")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="A2A Agent Load Testing for Autoscaling Demo")
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds")
    parser.add_argument("--rps", type=int, default=10, help="Requests per second")
    parser.add_argument("--workers", type=int, default=5, help="Concurrent workers per agent")
    parser.add_argument("--agents", nargs="+", default=None, help="Target agents")
    parser.add_argument("--ramp-up", type=int, default=60, help="Ramp-up time in seconds")
    parser.add_argument("--k8s", action="store_true", help="Use Kubernetes service endpoints")
    parser.add_argument("--namespace", default="multi-agent-a2a", help="Kubernetes namespace")
    
    args = parser.parse_args()
    
    # Set environment variables for Kubernetes if specified
    if args.k8s:
        import os
        os.environ["USE_K8S_SERVICES"] = "true"
        os.environ["NAMESPACE"] = args.namespace
        print(f"🔧 Using Kubernetes services in namespace: {args.namespace}")
    
    config = LoadTestConfig(
        duration_seconds=args.duration,
        requests_per_second=args.rps,
        concurrent_workers=args.workers,
        ramp_up_seconds=args.ramp_up,
        target_agents=args.agents
    )
    
    tester = A2ALoadTester(config)
    
    # Show endpoint configuration
    print(f"\n🎯 Target Endpoints:")
    for agent, url in tester.agent_endpoints.items():
        if agent in (args.agents or config.target_agents):
            print(f"   {agent:20} -> {url}")
    print()
    
    try:
        await tester.run_load_test()
        tester.print_results()
        
        print("\n🎯 Kubernetes Monitoring Commands:")
        print(f"   kubectl get hpa -n {args.namespace}")
        print(f"   kubectl top pods -n {args.namespace}")
        print(f"   kubectl get pods -l component=agent -n {args.namespace}")
        
        if args.k8s:
            print(f"\n📊 Check Prometheus metrics:")
            print(f"   kubectl port-forward svc/prometheus-service 9090:9090 -n {args.namespace}")
            print(f"   Open: http://localhost:9090")
        
    except KeyboardInterrupt:
        print("\n⏹️  Load test interrupted by user")
        tester.running = False
        tester.print_results()
    except Exception as e:
        print(f"\n❌ Load test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
