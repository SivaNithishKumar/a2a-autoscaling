#!/usr/bin/env python3
"""
Comprehensive Kubernetes Agent Test Suite

Tests all agents deployed in the Kubernetes cluster including:
- Health checks
- Agent card endpoints
- Pod status verification
- Service connectivity
- Metrics endpoints
- A2A communication capabilities

Usage:
    python3 test_all_agents_kubernetes.py [--port-forward] [--cluster-direct] [--verbose]
"""

import asyncio
import sys
import json
import subprocess
import time
import signal
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import argparse

try:
    import httpx
    import yaml
except ImportError:
    print("❌ Missing dependencies. Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx", "pyyaml"], check=True)
    import httpx
    import yaml

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
class AgentConfig:
    """Agent configuration from Kubernetes manifests."""
    name: str
    service_name: str
    namespace: str
    port: int
    metrics_port: Optional[int] = None
    health_path: str = "/health"
    card_path: str = "/.well-known/agent-card.json"
    replicas: int = 1

# Define all agents based on Kubernetes deployment
AGENTS = [
    AgentConfig("Base Agent", "base-agent-service", "multi-agent-a2a", 8080),
    AgentConfig("Calculator Agent", "calculator-agent-service", "multi-agent-a2a", 8081),
    AgentConfig("Weather Agent", "weather-agent-service", "multi-agent-a2a", 8082),
    AgentConfig("Research Agent", "research-agent-service", "multi-agent-a2a", 8083),
    AgentConfig("Move Orchestrator", "move-orchestrator-service", "multi-agent-a2a", 8084),
    AgentConfig("Infrastructure Monitor", "infrastructure-monitor-service", "multi-agent-a2a", 8085),
]

MONITORING_SERVICES = [
    ("Prometheus", "prometheus-service", "multi-agent-a2a", 9090),
    ("Grafana", "grafana-service", "multi-agent-a2a", 3000),
    ("Alertmanager", "alertmanager-service", "multi-agent-a2a", 9093),
]

class TestResult:
    """Test result tracking with detailed reporting."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_skipped = 0
        self.failures = []
        self.warnings = []
        self.start_time = datetime.now()
    
    def add_result(self, test_name: str, status: str, details: str = "", warning: bool = False):
        """Add a test result."""
        self.tests_run += 1
        
        if status == "PASSED":
            self.tests_passed += 1
            print(f"{Colors.GREEN}✅ {test_name}: PASSED{Colors.NC}")
            if details:
                print(f"   {Colors.CYAN}ℹ️  {details}{Colors.NC}")
        elif status == "FAILED":
            self.tests_failed += 1
            self.failures.append((test_name, details))
            print(f"{Colors.RED}❌ {test_name}: FAILED{Colors.NC}")
            if details:
                print(f"   {Colors.RED}💬 {details}{Colors.NC}")
        elif status == "SKIPPED":
            self.tests_skipped += 1
            print(f"{Colors.YELLOW}⏭️  {test_name}: SKIPPED{Colors.NC}")
            if details:
                print(f"   {Colors.YELLOW}ℹ️  {details}{Colors.NC}")
        
        if warning:
            self.warnings.append((test_name, details))
            print(f"   {Colors.YELLOW}⚠️  WARNING: {details}{Colors.NC}")
    
    def print_summary(self):
        """Print comprehensive test summary."""
        duration = datetime.now() - self.start_time
        
        print(f"\n{Colors.BOLD}{'='*80}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.BLUE}📊 KUBERNETES AGENT TEST SUMMARY{Colors.NC}")
        print(f"{Colors.BOLD}{'='*80}{Colors.NC}")
        print(f"🕒 Test Duration: {duration.total_seconds():.2f} seconds")
        print(f"📈 Total Tests: {self.tests_run}")
        print(f"{Colors.GREEN}✅ Passed: {self.tests_passed}{Colors.NC}")
        print(f"{Colors.RED}❌ Failed: {self.tests_failed}{Colors.NC}")
        print(f"{Colors.YELLOW}⏭️  Skipped: {self.tests_skipped}{Colors.NC}")
        
        if self.tests_run > 0:
            success_rate = (self.tests_passed / self.tests_run) * 100
            print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}⚠️  Warnings ({len(self.warnings)}):{Colors.NC}")
            for name, details in self.warnings:
                print(f"   - {name}: {details}")
        
        if self.failures:
            print(f"\n{Colors.RED}❌ Failed Tests ({len(self.failures)}):{Colors.NC}")
            for name, details in self.failures:
                print(f"   - {name}: {details}")
        
        # Overall assessment
        if self.tests_failed == 0:
            if self.warnings:
                print(f"\n{Colors.YELLOW}🎗️  Overall Status: PASSED WITH WARNINGS{Colors.NC}")
            else:
                print(f"\n{Colors.GREEN}🎉 Overall Status: ALL TESTS PASSED{Colors.NC}")
        else:
            print(f"\n{Colors.RED}🚨 Overall Status: SOME TESTS FAILED{Colors.NC}")

class KubernetesTestSuite:
    """Main test suite for Kubernetes agents."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.result = TestResult()
        self.port_forwards = []
        
        # Configure logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    async def run_kubectl_command(self, args: List[str]) -> Tuple[bool, str]:
        """Run kubectl command and return success status and output."""
        try:
            cmd = ["kubectl"] + args
            if self.verbose:
                self.logger.debug(f"Running: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            success = process.returncode == 0
            output = stdout.decode() if success else stderr.decode()
            
            if not success and self.verbose:
                self.logger.debug(f"kubectl command failed: {output}")
                
            return success, output
        except Exception as e:
            self.logger.error(f"Error running kubectl: {e}")
            return False, str(e)
    
    async def check_cluster_connection(self):
        """Test 1: Verify kubectl can connect to cluster."""
        print(f"\n{Colors.BLUE}🔗 Test 1: Kubernetes Cluster Connection{Colors.NC}")
        print("-" * 50)
        
        success, output = await self.run_kubectl_command(["cluster-info"])
        if success:
            self.result.add_result("Cluster Connection", "PASSED", "kubectl can connect to cluster")
        else:
            self.result.add_result("Cluster Connection", "FAILED", f"kubectl error: {output}")
            return False
        
        # Check namespace exists
        success, output = await self.run_kubectl_command(["get", "namespace", "multi-agent-a2a"])
        if success:
            self.result.add_result("Namespace Check", "PASSED", "multi-agent-a2a namespace exists")
        else:
            self.result.add_result("Namespace Check", "FAILED", "multi-agent-a2a namespace not found")
            return False
        
        return True
    
    async def check_pod_status(self):
        """Test 2: Check all agent pods are running."""
        print(f"\n{Colors.BLUE}🚀 Test 2: Agent Pod Status{Colors.NC}")
        print("-" * 50)
        
        success, output = await self.run_kubectl_command([
            "get", "pods", "-n", "multi-agent-a2a", "-o", "json"
        ])
        
        if not success:
            self.result.add_result("Pod Status Check", "FAILED", f"Failed to get pods: {output}")
            return
        
        try:
            pods_data = json.loads(output)
            agent_pods = {}
            
            for pod in pods_data.get("items", []):
                pod_name = pod["metadata"]["name"]
                status = pod["status"]["phase"]
                ready = False
                
                # Check if pod is ready
                if "containerStatuses" in pod["status"]:
                    ready = all(cs.get("ready", False) for cs in pod["status"]["containerStatuses"])
                
                # Group by agent type
                for agent in AGENTS:
                    agent_key = agent.service_name.replace("-service", "")
                    if agent_key in pod_name:
                        if agent_key not in agent_pods:
                            agent_pods[agent_key] = []
                        agent_pods[agent_key].append({
                            "name": pod_name,
                            "status": status,
                            "ready": ready
                        })
                        break
            
            # Check each agent
            for agent in AGENTS:
                agent_key = agent.service_name.replace("-service", "")
                pods = agent_pods.get(agent_key, [])
                
                if not pods:
                    self.result.add_result(f"{agent.name} Pods", "FAILED", "No pods found")
                    continue
                
                running_pods = [p for p in pods if p["status"] == "Running" and p["ready"]]
                total_pods = len(pods)
                
                if running_pods:
                    details = f"{len(running_pods)}/{total_pods} pods running and ready"
                    self.result.add_result(f"{agent.name} Pods", "PASSED", details)
                else:
                    failed_pods = [p["name"] for p in pods if not (p["status"] == "Running" and p["ready"])]
                    details = f"No ready pods. Failed: {', '.join(failed_pods)}"
                    self.result.add_result(f"{agent.name} Pods", "FAILED", details)
                    
        except json.JSONDecodeError as e:
            self.result.add_result("Pod Status Check", "FAILED", f"JSON parse error: {e}")
    
    async def check_services(self):
        """Test 3: Check all services are available."""
        print(f"\n{Colors.BLUE}🌐 Test 3: Service Availability{Colors.NC}")
        print("-" * 50)
        
        success, output = await self.run_kubectl_command([
            "get", "services", "-n", "multi-agent-a2a", "-o", "json"
        ])
        
        if not success:
            self.result.add_result("Service Check", "FAILED", f"Failed to get services: {output}")
            return
        
        try:
            services_data = json.loads(output)
            existing_services = {svc["metadata"]["name"] for svc in services_data.get("items", [])}
            
            # Check agent services
            for agent in AGENTS:
                if agent.service_name in existing_services:
                    self.result.add_result(f"{agent.name} Service", "PASSED", f"{agent.service_name} exists")
                else:
                    self.result.add_result(f"{agent.name} Service", "FAILED", f"{agent.service_name} not found")
            
            # Check monitoring services
            for name, service_name, namespace, port in MONITORING_SERVICES:
                if service_name in existing_services:
                    self.result.add_result(f"{name} Service", "PASSED", f"{service_name} exists")
                else:
                    self.result.add_result(f"{name} Service", "FAILED", f"{service_name} not found")
                    
        except json.JSONDecodeError as e:
            self.result.add_result("Service Check", "FAILED", f"JSON parse error: {e}")
    
    async def test_agent_health_direct(self):
        """Test 4: Test agent health endpoints via port-forward."""
        print(f"\n{Colors.BLUE}🏥 Test 4: Agent Health Checks (Port-Forward){Colors.NC}")
        print("-" * 50)
        
        port_forward_base = 9000
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for i, agent in enumerate(AGENTS):
                local_port = port_forward_base + i
                
                # Start port-forward
                port_forward_proc = None
                try:
                    print(f"   Setting up port-forward for {agent.name}...")
                    port_forward_proc = await asyncio.create_subprocess_exec(
                        "kubectl", "port-forward", "-n", agent.namespace,
                        f"svc/{agent.service_name}", f"{local_port}:{agent.port}",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    self.port_forwards.append(port_forward_proc)
                    
                    # Wait a moment for port-forward to establish
                    await asyncio.sleep(2)
                    
                    # Test health endpoint
                    health_url = f"http://localhost:{local_port}{agent.health_path}"
                    try:
                        response = await client.get(health_url)
                        if response.status_code == 200:
                            self.result.add_result(f"{agent.name} Health", "PASSED", f"Status: {response.status_code}")
                        else:
                            self.result.add_result(f"{agent.name} Health", "FAILED", f"Status: {response.status_code}")
                    except Exception as e:
                        self.result.add_result(f"{agent.name} Health", "FAILED", f"Connection error: {str(e)}")
                    
                    # Test agent card endpoint
                    card_url = f"http://localhost:{local_port}{agent.card_path}"
                    try:
                        response = await client.get(card_url)
                        if response.status_code == 200:
                            try:
                                card_data = response.json()
                                agent_name = card_data.get("name", "Unknown")
                                self.result.add_result(f"{agent.name} Agent Card", "PASSED", f"Agent: {agent_name}")
                            except:
                                self.result.add_result(f"{agent.name} Agent Card", "PASSED", "Valid response (non-JSON)")
                        else:
                            self.result.add_result(f"{agent.name} Agent Card", "FAILED", f"Status: {response.status_code}")
                    except Exception as e:
                        self.result.add_result(f"{agent.name} Agent Card", "FAILED", f"Connection error: {str(e)}")
                
                except Exception as e:
                    self.result.add_result(f"{agent.name} Port-Forward", "FAILED", f"Setup error: {str(e)}")
                
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
    
    async def test_cluster_direct_access(self):
        """Test 5: Test agent endpoints directly within cluster using kubectl proxy."""
        print(f"\n{Colors.BLUE}🔄 Test 5: Cluster-Direct Agent Access{Colors.NC}")
        print("-" * 50)
        
        # Start kubectl proxy
        proxy_proc = None
        try:
            print("   Starting kubectl proxy...")
            proxy_proc = await asyncio.create_subprocess_exec(
                "kubectl", "proxy", "--port=8888",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for proxy to start
            await asyncio.sleep(3)
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                for agent in AGENTS:
                    # Construct cluster URL via kubectl proxy
                    base_url = f"http://localhost:8888/api/v1/namespaces/{agent.namespace}/services/{agent.service_name}:{agent.port}/proxy"
                    
                    # Test health endpoint
                    health_url = f"{base_url}{agent.health_path}"
                    try:
                        response = await client.get(health_url)
                        if response.status_code == 200:
                            self.result.add_result(f"{agent.name} Cluster Health", "PASSED", "Direct cluster access successful")
                        else:
                            self.result.add_result(f"{agent.name} Cluster Health", "FAILED", f"Status: {response.status_code}")
                    except Exception as e:
                        self.result.add_result(f"{agent.name} Cluster Health", "FAILED", f"Error: {str(e)}")
        
        except Exception as e:
            self.result.add_result("Cluster Direct Access", "FAILED", f"Proxy setup error: {str(e)}")
        
        finally:
            # Clean up proxy
            if proxy_proc:
                try:
                    proxy_proc.terminate()
                    await asyncio.sleep(1)
                    if proxy_proc.returncode is None:
                        proxy_proc.kill()
                except:
                    pass
    
    async def test_monitoring_stack(self):
        """Test 6: Test monitoring services."""
        print(f"\n{Colors.BLUE}📊 Test 6: Monitoring Stack{Colors.NC}")
        print("-" * 50)
        
        port_base = 9100
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for i, (name, service_name, namespace, port) in enumerate(MONITORING_SERVICES):
                local_port = port_base + i
                
                port_forward_proc = None
                try:
                    print(f"   Testing {name}...")
                    port_forward_proc = await asyncio.create_subprocess_exec(
                        "kubectl", "port-forward", "-n", namespace,
                        f"svc/{service_name}", f"{local_port}:{port}",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    await asyncio.sleep(2)
                    
                    # Test based on service type
                    if name == "Prometheus":
                        test_url = f"http://localhost:{local_port}/api/v1/query?query=up"
                    elif name == "Grafana":
                        test_url = f"http://localhost:{local_port}/api/health"
                    else:  # Alertmanager
                        test_url = f"http://localhost:{local_port}/api/v1/status"
                    
                    try:
                        response = await client.get(test_url)
                        if response.status_code == 200:
                            self.result.add_result(f"{name} Health", "PASSED", f"API responding")
                        else:
                            self.result.add_result(f"{name} Health", "FAILED", f"Status: {response.status_code}")
                    except Exception as e:
                        self.result.add_result(f"{name} Health", "FAILED", f"Connection error: {str(e)}")
                
                except Exception as e:
                    self.result.add_result(f"{name} Setup", "FAILED", f"Port-forward error: {str(e)}")
                
                finally:
                    if port_forward_proc:
                        try:
                            port_forward_proc.terminate()
                            await asyncio.sleep(1)
                        except:
                            pass
    
    async def test_pod_logs(self):
        """Test 7: Check recent pod logs for errors."""
        print(f"\n{Colors.BLUE}📜 Test 7: Pod Log Analysis{Colors.NC}")
        print("-" * 50)
        
        for agent in AGENTS:
            # Get one pod for each agent
            success, output = await self.run_kubectl_command([
                "get", "pods", "-n", agent.namespace, "-l", f"app={agent.service_name.replace('-service', '')}",
                "-o", "jsonpath={.items[0].metadata.name}"
            ])
            
            if not success or not output.strip():
                self.result.add_result(f"{agent.name} Log Check", "SKIPPED", "No pod found")
                continue
            
            pod_name = output.strip()
            
            # Get recent logs
            success, logs = await self.run_kubectl_command([
                "logs", "-n", agent.namespace, pod_name, "--tail=20"
            ])
            
            if success:
                # Check for common error patterns
                error_patterns = ["ERROR", "FATAL", "Exception", "Traceback", "Failed"]
                errors_found = []
                
                for line in logs.split('\n'):
                    for pattern in error_patterns:
                        if pattern in line:
                            errors_found.append(line.strip())
                            break
                
                if errors_found:
                    error_summary = f"Found {len(errors_found)} error(s)"
                    self.result.add_result(f"{agent.name} Logs", "FAILED", error_summary, warning=True)
                    if self.verbose:
                        for error in errors_found[:3]:  # Show first 3 errors
                            print(f"     {Colors.YELLOW}⚠️  {error}{Colors.NC}")
                else:
                    self.result.add_result(f"{agent.name} Logs", "PASSED", "No obvious errors in recent logs")
            else:
                self.result.add_result(f"{agent.name} Log Check", "FAILED", f"Could not retrieve logs: {logs}")
    
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
    
    async def run_all_tests(self, test_port_forward: bool = True, test_cluster_direct: bool = True):
        """Run the complete test suite."""
        print(f"{Colors.BOLD}{Colors.BLUE}🧪 KUBERNETES AGENT TEST SUITE{Colors.NC}")
        print(f"{Colors.BOLD}{'='*80}{Colors.NC}")
        print(f"🎯 Testing Multi-Agent A2A System in Kubernetes")
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Run tests in sequence
            if not await self.check_cluster_connection():
                print(f"{Colors.RED}🚨 Cannot connect to cluster. Aborting tests.{Colors.NC}")
                return self.result
            
            await self.check_pod_status()
            await self.check_services()
            
            if test_port_forward:
                await self.test_agent_health_direct()
            
            if test_cluster_direct:
                await self.test_cluster_direct_access()
            
            await self.test_monitoring_stack()
            await self.test_pod_logs()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}🛑 Tests interrupted by user{Colors.NC}")
        except Exception as e:
            print(f"\n{Colors.RED}🚨 Unexpected error during testing: {e}{Colors.NC}")
            self.result.add_result("Test Suite", "FAILED", f"Unexpected error: {e}")
        finally:
            await self.cleanup()
        
        # Print final summary
        self.result.print_summary()
        return self.result

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test all agents in Kubernetes cluster")
    parser.add_argument("--no-port-forward", action="store_true", 
                       help="Skip port-forward tests")
    parser.add_argument("--no-cluster-direct", action="store_true", 
                       help="Skip cluster-direct tests")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    test_suite = KubernetesTestSuite(verbose=args.verbose)
    
    result = await test_suite.run_all_tests(
        test_port_forward=not args.no_port_forward,
        test_cluster_direct=not args.no_cluster_direct
    )
    
    # Exit with appropriate code
    sys.exit(0 if result.tests_failed == 0 else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Test suite interrupted{Colors.NC}")
        sys.exit(130)