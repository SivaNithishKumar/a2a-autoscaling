#!/usr/bin/env python3
"""
Dashboard Load Test - Generate load to populate Grafana dashboard
"""

import time
import threading
import requests
import subprocess
import logging
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DashboardLoadTest:
    def __init__(self, duration=600):
        self.duration = duration
        self.running = True
        self.start_time = time.time()
        
        # Agent endpoints via port-forward
        self.agent_endpoints = {
            "base-agent": "http://localhost:8080",
            "calculator-agent": "http://localhost:8081",
            "weather-agent": "http://localhost:8082",
            "research-agent": "http://localhost:8083"
        }
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle interrupt signals"""
        logger.info("Stopping load test...")
        self.running = False
        sys.exit(0)
    
    def setup_port_forwards(self):
        """Setup port forwards for agent access"""
        logger.info("Setting up port forwards for agents...")
        
        port_forwards = [
            ("base-agent-service", 8080),
            ("calculator-agent-service", 8081),
            ("weather-agent-service", 8082),
            ("research-agent-service", 8083)
        ]
        
        for service, port in port_forwards:
            try:
                # Kill existing port-forward if any
                subprocess.run(
                    ["pkill", "-f", f"port-forward.*{service}"],
                    capture_output=True
                )
                
                # Start new port-forward in background
                subprocess.Popen([
                    "kubectl", "port-forward", "-n", "multi-agent-a2a",
                    f"svc/{service}", f"{port}:{port}"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                time.sleep(2)  # Wait for port-forward to establish
                logger.info(f"Port-forward setup for {service}:{port}")
                
            except Exception as e:
                logger.warning(f"Failed to setup port-forward for {service}: {e}")
    
    def http_load_worker(self, agent_name, url):
        """Generate HTTP load to a specific agent"""
        logger.info(f"Starting HTTP load worker for {agent_name}")
        request_count = 0
        success_count = 0
        
        while self.running and (time.time() - self.start_time) < self.duration:
            try:
                response = requests.get(f"{url}/health", timeout=2)
                request_count += 1
                
                if response.status_code == 200:
                    success_count += 1
                
                if request_count % 50 == 0:
                    logger.info(f"{agent_name}: {success_count}/{request_count} requests successful")
                
            except Exception as e:
                request_count += 1
                if request_count % 50 == 0:
                    logger.debug(f"{agent_name}: Error - {str(e)[:50]}")
            
            time.sleep(0.1)  # 10 RPS per agent
        
        logger.info(f"HTTP worker for {agent_name} finished: {success_count}/{request_count} successful")
    
    def scale_agents_dynamically(self):
        """Dynamically scale agents to generate scaling events"""
        logger.info("Starting dynamic scaling worker")
        
        scaling_sequence = [
            ("base-agent", 3),
            ("calculator-agent", 3),
            ("weather-agent", 3),
            ("base-agent", 4),
            ("calculator-agent", 4),
            ("base-agent", 2),
            ("calculator-agent", 2),
            ("weather-agent", 2)
        ]
        
        for deployment, replicas in scaling_sequence:
            if not self.running:
                break
            
            try:
                logger.info(f"Scaling {deployment} to {replicas} replicas")
                result = subprocess.run([
                    "kubectl", "scale", "deployment", deployment,
                    "--replicas", str(replicas), "-n", "multi-agent-a2a"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Successfully scaled {deployment} to {replicas}")
                else:
                    logger.warning(f"Failed to scale {deployment}: {result.stderr}")
                
                # Wait between scaling operations
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error scaling {deployment}: {e}")
        
        logger.info("Dynamic scaling worker finished")
    
    def monitor_metrics(self):
        """Monitor and log metrics during the test"""
        logger.info("Starting metrics monitoring")
        
        while self.running and (time.time() - self.start_time) < self.duration:
            try:
                # Get pod metrics
                result = subprocess.run(
                    ["kubectl", "top", "pods", "-n", "multi-agent-a2a"],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    logger.info("Current pod metrics:")
                    for line in result.stdout.strip().split('\n')[1:]:
                        if any(agent in line for agent in ['base-agent', 'calculator-agent', 'weather-agent']):
                            logger.info(f"  {line}")
                
                # Get HPA status
                result = subprocess.run(
                    ["kubectl", "get", "hpa", "-n", "multi-agent-a2a"],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    logger.info("HPA Status:")
                    for line in result.stdout.strip().split('\n')[1:]:
                        logger.info(f"  {line}")
                
                # Test Prometheus queries
                self.test_prometheus_queries()
                
            except Exception as e:
                logger.warning(f"Failed to get metrics: {e}")
            
            time.sleep(30)
    
    def test_prometheus_queries(self):
        """Test the dashboard queries against Prometheus"""
        queries = [
            "up{job=\"kubernetes-pods\"}",
            "container_memory_working_set_bytes",
            "container_cpu_usage_seconds_total",
            "kube_pod_info"
        ]
        
        for query in queries:
            try:
                response = requests.get(
                    f"http://localhost:9090/api/v1/query",
                    params={"query": query},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result_count = len(data.get('data', {}).get('result', []))
                    logger.debug(f"Query '{query}': {result_count} results")
                else:
                    logger.warning(f"Query '{query}' failed: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Failed to test query '{query}': {e}")
    
    def run_load_test(self):
        """Run the complete load test"""
        logger.info(f"🔥 Starting dashboard load test for {self.duration} seconds")
        logger.info("This will generate load and scaling events to populate the dashboard")
        
        # Setup port forwards
        self.setup_port_forwards()
        time.sleep(10)  # Wait for port forwards to be ready
        
        threads = []
        
        # Start HTTP load workers
        for agent_name, url in self.agent_endpoints.items():
            thread = threading.Thread(
                target=self.http_load_worker,
                args=(agent_name, url)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Start dynamic scaling worker
        scaling_thread = threading.Thread(target=self.scale_agents_dynamically)
        scaling_thread.daemon = True
        scaling_thread.start()
        threads.append(scaling_thread)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_metrics)
        monitor_thread.daemon = True
        monitor_thread.start()
        threads.append(monitor_thread)
        
        logger.info(f"🚀 Load test running with {len(threads)} workers")
        logger.info("📊 Monitor dashboard at: http://152.67.4.15:3000")
        logger.info("📈 Monitor Prometheus at: http://152.67.4.15:9090")
        
        # Main monitoring loop
        try:
            while self.running and (time.time() - self.start_time) < self.duration:
                elapsed = time.time() - self.start_time
                remaining = self.duration - elapsed
                logger.info(f"⏱️  Load test progress: {elapsed:.1f}s elapsed, {remaining:.1f}s remaining")
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Load test interrupted by user")
        
        self.running = False
        logger.info("🏁 Load test completed")
        
        # Final status
        logger.info("Final system state:")
        try:
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "multi-agent-a2a"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info("Pod status:")
                for line in result.stdout.strip().split('\n'):
                    if any(agent in line for agent in ['base-agent', 'calculator-agent', 'weather-agent']):
                        logger.info(f"  {line}")
        except Exception as e:
            logger.warning(f"Failed to get final status: {e}")

def main():
    logger.info("🎯 Dashboard Load Test - Generating metrics for Grafana dashboard")
    logger.info("This test will:")
    logger.info("  - Generate HTTP traffic to all A2A agents")
    logger.info("  - Dynamically scale deployments to create scaling events")
    logger.info("  - Monitor metrics and populate dashboard panels")
    logger.info("  - Run for 10 minutes to ensure sufficient data")
    
    load_test = DashboardLoadTest(duration=600)  # 10 minutes
    load_test.run_load_test()
    
    logger.info("🎊 Load test complete! Check your Grafana dashboard:")
    logger.info("📊 Grafana: http://152.67.4.15:3000 (admin/admin)")
    logger.info("📈 Prometheus: http://152.67.4.15:9090")

if __name__ == "__main__":
    main()
