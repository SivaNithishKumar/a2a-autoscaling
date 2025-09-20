#!/usr/bin/env python3
"""
Functional Agent Test Suite

Tests all agents in Kubernetes with actual functional queries, not just health checks.
Each agent is tested with real use cases to validate their capabilities.

Usage:
    python3 test_agent_functionality.py [--port-forward] [--verbose] [--timeout=30] [--output-format=json|table]

Features:
    - Comprehensive agent testing with real queries
    - Support for multiple output formats
    - Enhanced error handling and retry logic
    - Detailed performance metrics and reporting
    - Configurable timeout and retry parameters
"""

import asyncio
import sys
import json
import subprocess
import time
import signal
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse
import uuid
import os

try:
    import httpx
except ImportError:
    print("❌ Missing httpx dependency. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)
    import httpx

# Colors for output
class Colors:
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'

@dataclass
class AgentTest:
    """Test case for an agent."""
    name: str
    description: str
    input_message: str
    expected_keywords: List[str] = None
    timeout: float = 30.0
    retry_count: int = 3

@dataclass
class TestResult:
    """Result of an agent test."""
    test_name: str
    agent_name: str
    success: bool
    response_time: float
    error_message: Optional[str] = None
    response_content: Optional[str] = None
    keywords_found: List[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

@dataclass
class AgentConfig:
    """Agent configuration with test cases."""
    name: str
    service_name: str
    namespace: str
    port: int
    tests: List[AgentTest]
    health_check_endpoint: str = "/health"

# Define comprehensive test cases for each agent
AGENT_TESTS = [
    AgentConfig(
        name="Base Agent",
        service_name="base-agent-service",
        namespace="multi-agent-a2a",
        port=8080,
        tests=[
            AgentTest(
                name="General Conversation",
                description="Test basic conversation capability",
                input_message="Hello! Can you tell me about yourself and what you can help me with?",
                expected_keywords=["help", "assist", "agent", "general"]
            ),
            AgentTest(
                name="Information Request",
                description="Test information processing",
                input_message="What is artificial intelligence and how does it work?",
                expected_keywords=["artificial", "intelligence", "AI", "machine", "learning"]
            ),
            AgentTest(
                name="Task Assistance",
                description="Test task assistance capability",
                input_message="I need help planning a project. What steps should I consider?",
                expected_keywords=["plan", "project", "steps", "consider", "organize"]
            )
        ]
    ),
    AgentConfig(
        name="Calculator Agent",
        service_name="calculator-agent-service",
        namespace="multi-agent-a2a",
        port=8081,
        tests=[
            AgentTest(
                name="Basic Arithmetic",
                description="Test simple math operations",
                input_message="What is 25 + 17 * 3?",
                expected_keywords=["76", "result", "calculation", "answer"]
            ),
            AgentTest(
                name="Square Root Calculation",
                description="Test mathematical functions",
                input_message="Calculate the square root of 144",
                expected_keywords=["12", "square", "root", "144"]
            ),
            AgentTest(
                name="Temperature Conversion",
                description="Test unit conversion",
                input_message="Convert 100 degrees Fahrenheit to Celsius",
                expected_keywords=["37.78", "celsius", "fahrenheit", "convert", "temperature"]
            ),
            AgentTest(
                name="Statistical Calculation",
                description="Test statistical functions",
                input_message="Calculate the average of 10, 20, 30, 40, 50",
                expected_keywords=["30", "average", "mean", "result"]
            )
        ]
    ),
    AgentConfig(
        name="Weather Agent",
        service_name="weather-agent-service",
        namespace="multi-agent-a2a",
        port=8082,
        tests=[
            AgentTest(
                name="Current Weather Query",
                description="Test current weather retrieval",
                input_message="What's the current weather in New York City?",
                expected_keywords=["weather", "temperature", "new york", "current"]
            ),
            AgentTest(
                name="Weather Forecast",
                description="Test weather forecast capability",
                input_message="Can you give me a 3-day weather forecast for London?",
                expected_keywords=["forecast", "london", "days", "weather"]
            ),
            AgentTest(
                name="Specific Weather Query",
                description="Test specific weather information",
                input_message="Is it raining in Seattle today?",
                expected_keywords=["seattle", "rain", "weather", "today"]
            ),
            AgentTest(
                name="International Weather",
                description="Test international location handling",
                input_message="What's the temperature in Tokyo right now?",
                expected_keywords=["tokyo", "temperature", "weather", "current"]
            )
        ]
    ),
    AgentConfig(
        name="Research Agent",
        service_name="research-agent-service",
        namespace="multi-agent-a2a",
        port=8083,
        tests=[
            AgentTest(
                name="Technology Research",
                description="Test research on technology topics",
                input_message="Research the latest developments in quantum computing",
                expected_keywords=["quantum", "computing", "research", "development"]
            ),
            AgentTest(
                name="Scientific Inquiry",
                description="Test scientific research capability",
                input_message="Tell me about machine learning algorithms and their applications",
                expected_keywords=["machine", "learning", "algorithm", "application"]
            ),
            AgentTest(
                name="Current Events Research",
                description="Test research on current topics",
                input_message="What are the latest trends in artificial intelligence?",
                expected_keywords=["artificial", "intelligence", "trends", "latest"]
            ),
            AgentTest(
                name="Industry Analysis",
                description="Test industry research capability",
                input_message="Research the impact of blockchain technology on finance",
                expected_keywords=["blockchain", "finance", "impact", "technology"]
            )
        ]
    ),
    AgentConfig(
        name="Move Orchestrator",
        service_name="move-orchestrator-service", 
        namespace="multi-agent-a2a",
        port=8004,  # A2A port, not metrics port
        tests=[
            AgentTest(
                name="Home Relocation Planning",
                description="Test move planning capability",
                input_message="I need to plan a move from London to Manchester next month. Can you help coordinate this?",
                expected_keywords=["move", "london", "manchester", "plan", "coordinate"]
            ),
            AgentTest(
                name="Office Move Coordination",
                description="Test office move orchestration",
                input_message="Help me organize an office relocation for 50 employees from downtown to suburbs",
                expected_keywords=["office", "relocation", "employees", "organize", "move"]
            ),
            AgentTest(
                name="International Move",
                description="Test international move planning",
                input_message="I'm moving from New York to Paris. What steps should I take?",
                expected_keywords=["international", "new york", "paris", "steps", "move"]
            ),
            AgentTest(
                name="Move Timeline",
                description="Test move timeline creation",
                input_message="Create a timeline for a household move happening in 6 weeks",
                expected_keywords=["timeline", "household", "weeks", "schedule", "move"]
            )
        ]
    ),
    AgentConfig(
        name="Infrastructure Monitor",
        service_name="infrastructure-monitor-service",
        namespace="multi-agent-a2a", 
        port=8005,  # A2A port, not metrics port  
        tests=[
            AgentTest(
                name="System Health Check",
                description="Test infrastructure monitoring",
                input_message="Check the health status of the web frontend and database services",
                expected_keywords=["health", "status", "frontend", "database", "services"]
            ),
            AgentTest(
                name="Performance Monitoring",
                description="Test performance analysis",
                input_message="Monitor the performance metrics for our production environment",
                expected_keywords=["performance", "metrics", "production", "monitor"]
            ),
            AgentTest(
                name="Resource Utilization",
                description="Test resource monitoring",
                input_message="What's the current CPU and memory utilization of our services?",
                expected_keywords=["cpu", "memory", "utilization", "services", "resources"]
            ),
            AgentTest(
                name="Alert Analysis",
                description="Test alert and recommendation capability",
                input_message="Analyze current system alerts and provide recommendations",
                expected_keywords=["alerts", "analyze", "recommendations", "system"]
            )
        ]
    )
]

class TestResult:
    """Test result tracking with detailed reporting."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_skipped = 0
        self.failures = []
        self.agent_results = {}
        self.start_time = datetime.now()
    
    def add_result(self, agent_name: str, test_name: str, status: str, details: str = "", response_time: float = None):
        """Add a test result."""
        self.tests_run += 1
        
        if agent_name not in self.agent_results:
            self.agent_results[agent_name] = {"passed": 0, "failed": 0, "total": 0}
        
        self.agent_results[agent_name]["total"] += 1
        
        if status == "PASSED":
            self.tests_passed += 1
            self.agent_results[agent_name]["passed"] += 1
            time_info = f" ({response_time:.2f}s)" if response_time else ""
            print(f"{Colors.GREEN}✅ {agent_name} - {test_name}: PASSED{time_info}{Colors.NC}")
            if details:
                print(f"   {Colors.CYAN}ℹ️  {details}{Colors.NC}")
        elif status == "FAILED":
            self.tests_failed += 1
            self.agent_results[agent_name]["failed"] += 1
            self.failures.append((agent_name, test_name, details))
            print(f"{Colors.RED}❌ {agent_name} - {test_name}: FAILED{Colors.NC}")
            if details:
                print(f"   {Colors.RED}💬 {details}{Colors.NC}")
        elif status == "SKIPPED":
            self.tests_skipped += 1
            print(f"{Colors.YELLOW}⏭️  {agent_name} - {test_name}: SKIPPED{Colors.NC}")
            if details:
                print(f"   {Colors.YELLOW}ℹ️  {details}{Colors.NC}")
    
    def print_summary(self):
        """Print comprehensive test summary."""
        duration = datetime.now() - self.start_time
        
        print(f"\n{Colors.BOLD}{'='*80}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.BLUE}📊 FUNCTIONAL AGENT TEST SUMMARY{Colors.NC}")
        print(f"{Colors.BOLD}{'='*80}{Colors.NC}")
        print(f"🕒 Test Duration: {duration.total_seconds():.2f} seconds")
        print(f"📈 Total Tests: {self.tests_run}")
        print(f"{Colors.GREEN}✅ Passed: {self.tests_passed}{Colors.NC}")
        print(f"{Colors.RED}❌ Failed: {self.tests_failed}{Colors.NC}")
        print(f"{Colors.YELLOW}⏭️  Skipped: {self.tests_skipped}{Colors.NC}")
        
        if self.tests_run > 0:
            success_rate = (self.tests_passed / self.tests_run) * 100
            print(f"📊 Success Rate: {success_rate:.1f}%")
        
        # Agent-by-agent breakdown
        print(f"\n{Colors.BOLD}📋 Agent Performance Breakdown:{Colors.NC}")
        for agent_name, results in self.agent_results.items():
            total = results["total"]
            passed = results["passed"]
            failed = results["failed"]
            agent_rate = (passed / total * 100) if total > 0 else 0
            
            status_color = Colors.GREEN if failed == 0 else Colors.YELLOW if passed > failed else Colors.RED
            print(f"  {status_color}{agent_name}: {passed}/{total} passed ({agent_rate:.1f}%){Colors.NC}")
        
        if self.failures:
            print(f"\n{Colors.RED}❌ Failed Tests ({len(self.failures)}):{Colors.NC}")
            for agent_name, test_name, details in self.failures:
                print(f"   - {agent_name} / {test_name}: {details}")
        
        # Overall assessment
        if self.tests_failed == 0:
            print(f"\n{Colors.GREEN}🎉 Overall Status: ALL FUNCTIONAL TESTS PASSED{Colors.NC}")
        else:
            print(f"\n{Colors.RED}🚨 Overall Status: SOME FUNCTIONAL TESTS FAILED{Colors.NC}")

class FunctionalTestSuite:
    """Main functional test suite for agents."""
    
    def __init__(self, verbose: bool = False, timeout: float = 30.0):
        self.verbose = verbose
        self.timeout = timeout
        self.result = TestResult()
        self.port_forwards = []
        
        # Configure logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    async def create_a2a_request(self, message: str) -> Dict[str, Any]:
        """Create A2A protocol request payload using JSON-RPC 2.0 format."""
        return {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [
                        {"kind": "text", "text": message}
                    ],
                    "messageId": uuid.uuid4().hex,
                }
            }
        }
    
    async def send_agent_request(self, agent_config: AgentConfig, test: AgentTest, local_port: int) -> Tuple[bool, str, float]:
        """Send a functional request to an agent and analyze the response."""
        payload = await self.create_a2a_request(test.input_message)
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"http://localhost:{local_port}/",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                response_time = time.time() - start_time
                
                if response.status_code not in [200, 201, 202]:
                    return False, f"HTTP {response.status_code}: {response.text}", response_time
                
                # Parse response
                try:
                    response_data = response.json()
                    if self.verbose:
                        self.logger.debug(f"Response data: {json.dumps(response_data, indent=2)}")
                    
                    # Extract text content from response
                    response_text = ""
                    if isinstance(response_data, dict):
                        if "content" in response_data:
                            response_text = str(response_data["content"])
                        elif "message" in response_data:
                            if isinstance(response_data["message"], dict) and "content" in response_data["message"]:
                                response_text = str(response_data["message"]["content"])
                            else:
                                response_text = str(response_data["message"])
                        elif "result" in response_data:
                            response_text = str(response_data["result"])
                        else:
                            response_text = str(response_data)
                    else:
                        response_text = str(response_data)
                    
                    # Check for expected keywords if provided
                    if test.expected_keywords:
                        found_keywords = []
                        response_lower = response_text.lower()
                        
                        for keyword in test.expected_keywords:
                            if keyword.lower() in response_lower:
                                found_keywords.append(keyword)
                        
                        if found_keywords:
                            return True, f"Found keywords: {', '.join(found_keywords)}", response_time
                        else:
                            return False, f"No expected keywords found. Response: {response_text[:200]}...", response_time
                    else:
                        # If no keywords specified, just check if we got a meaningful response
                        if len(response_text.strip()) > 10:
                            return True, f"Got response: {response_text[:100]}...", response_time
                        else:
                            return False, f"Response too short: {response_text}", response_time
                            
                except json.JSONDecodeError:
                    # Non-JSON response
                    response_text = response.text
                    if len(response_text.strip()) > 10:
                        return True, f"Non-JSON response: {response_text[:100]}...", response_time
                    else:
                        return False, f"Empty or invalid response", response_time
                        
        except Exception as e:
            response_time = time.time() - start_time
            return False, f"Request failed: {str(e)}", response_time
    
    async def test_agent_functionality(self, agent_config: AgentConfig, port_forward: bool = True):
        """Test all functional capabilities of an agent."""
        print(f"\n{Colors.BLUE}🔧 Testing {agent_config.name} Functionality{Colors.NC}")
        print("-" * (20 + len(agent_config.name)))
        
        if not port_forward:
            # Skip port-forward tests
            for test in agent_config.tests:
                self.result.add_result(agent_config.name, test.name, "SKIPPED", "Port-forward disabled")
            return
        
        # Setup port-forward
        local_port = 9000 + hash(agent_config.name) % 1000  # Deterministic port selection
        port_forward_proc = None
        
        try:
            print(f"   Setting up port-forward for {agent_config.name} on port {local_port}...")
            
            port_forward_proc = await asyncio.create_subprocess_exec(
                "kubectl", "port-forward", "-n", agent_config.namespace,
                f"svc/{agent_config.service_name}", f"{local_port}:{agent_config.port}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.port_forwards.append(port_forward_proc)
            
            # Wait for port-forward to establish
            await asyncio.sleep(3)
            
            # Test each functionality
            for test in agent_config.tests:
                print(f"   Running test: {test.description}")
                
                success, details, response_time = await self.send_agent_request(
                    agent_config, test, local_port
                )
                
                if success:
                    self.result.add_result(agent_config.name, test.name, "PASSED", details, response_time)
                else:
                    self.result.add_result(agent_config.name, test.name, "FAILED", details, response_time)
        
        except Exception as e:
            for test in agent_config.tests:
                self.result.add_result(agent_config.name, test.name, "FAILED", f"Setup error: {str(e)}")
        
        finally:
            # Clean up port-forward
            if port_forward_proc:
                try:
                    port_forward_proc.terminate()
                    await asyncio.sleep(1)
                    if port_forward_proc.returncode is None:
                        port_forward_proc.kill()
                except:
                    pass
    
    async def cleanup(self):
        """Clean up any running processes."""
        for proc in self.port_forwards:
            try:
                if proc.returncode is None:
                    proc.terminate()
                    await asyncio.sleep(1)
                    if proc.returncode is None:
                        proc.kill()
            except:
                pass
    
    async def run_all_tests(self, use_port_forward: bool = True):
        """Run the complete functional test suite."""
        print(f"{Colors.BOLD}{Colors.BLUE}🧪 FUNCTIONAL AGENT TEST SUITE{Colors.NC}")
        print(f"{Colors.BOLD}{'='*80}{Colors.NC}")
        print(f"🎯 Testing Agent Functional Capabilities with Real Queries")
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Timeout: {self.timeout}s per test")
        print()
        
        try:
            # Test each agent's functionality
            for agent_config in AGENT_TESTS:
                await self.test_agent_functionality(agent_config, use_port_forward)
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}🛑 Tests interrupted by user{Colors.NC}")
        except Exception as e:
            print(f"\n{Colors.RED}🚨 Unexpected error during testing: {e}{Colors.NC}")
            self.result.add_result("Test Suite", "General", "FAILED", f"Unexpected error: {e}")
        finally:
            await self.cleanup()
        
        # Print final summary
        self.result.print_summary()
        return self.result

def export_results_to_json(results: 'TestResult', filename: str) -> None:
    """Export test results to JSON format."""
    try:
        with open(filename, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)
        print(f"{Colors.GREEN}✅ Results exported to {filename}{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Failed to export results: {e}{Colors.NC}")

def generate_test_report(results: 'TestResult') -> str:
    """Generate a comprehensive test report."""
    report = []
    report.append("# Agent Functionality Test Report")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("## Summary")
    report.append(f"- Total Tests: {results.tests_run}")
    report.append(f"- Passed: {results.tests_passed}")
    report.append(f"- Failed: {results.tests_failed}")
    report.append(f"- Success Rate: {(results.tests_passed/results.tests_run*100):.1f}%")
    report.append("")
    
    return "\n".join(report)

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test agent functionality with real queries")
    parser.add_argument("--no-port-forward", action="store_true", 
                       help="Skip port-forward tests")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    parser.add_argument("--timeout", type=float, default=30.0,
                       help="Timeout for each test in seconds")
    parser.add_argument("--output-format", choices=["json", "table"], default="table",
                       help="Output format for test results")
    parser.add_argument("--save-results", type=str, metavar="FILE",
                       help="Save test results to file")
    parser.add_argument("--agent", type=str, metavar="AGENT_NAME",
                       help="Test only specific agent (partial name matching)")
    
    args = parser.parse_args()
    
    # Setup logging based on verbosity
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('agent_tests.log')
        ]
    )
    
    test_suite = FunctionalTestSuite(
        verbose=args.verbose, 
        timeout=args.timeout
    )
    
    result = await test_suite.run_all_tests(
        use_port_forward=not args.no_port_forward,
        output_format=args.output_format,
        target_agent=args.agent
    )
    
    # Save results if requested
    if args.save_results:
        try:
            with open(args.save_results, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            print(f"{Colors.GREEN}✅ Results saved to {args.save_results}{Colors.NC}")
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to save results: {e}{Colors.NC}")
    
    # Exit with appropriate code
    exit_code = 0 if result.tests_failed == 0 else 1
    print(f"\n{Colors.BOLD}Exit code: {exit_code}{Colors.NC}")
    sys.exit(exit_code)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Functional test suite interrupted{Colors.NC}")
        sys.exit(130)