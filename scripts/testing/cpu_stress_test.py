#!/usr/bin/env python3
"""
CPU Stress Test for A2A Kubernetes Autoscaling Demo

This script generates CPU load to trigger HPA scaling and verify dashboard metrics.
"""

import time
import threading
import multiprocessing
import argparse
import signal
import sys
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CPUStressTest:
    def __init__(self, duration=300, cpu_workers=4, http_workers=2):
        self.duration = duration
        self.cpu_workers = cpu_workers
        self.http_workers = http_workers
        self.running = True
        self.start_time = time.time()
        
        # Agent endpoints for HTTP load
        self.agent_endpoints = {
            "base": "http://localhost:8080",
            "calculator": "http://localhost:8081",
            "weather": "http://localhost:8082",
            "research": "http://localhost:8083"
        }
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle interrupt signals"""
        logger.info("Stopping stress test...")
        self.running = False
        sys.exit(0)
    
    def cpu_intensive_task(self, worker_id):
        """CPU intensive task to stress the system"""
        logger.info(f"Starting CPU worker {worker_id}")
        
        while self.running and (time.time() - self.start_time) < self.duration:
            # CPU intensive calculation
            result = 0
            for i in range(1000000):
                result += i * i * 0.5
                if not self.running:
                    break
            
            # Small sleep to prevent complete CPU lockup
            time.sleep(0.001)
        
        logger.info(f"CPU worker {worker_id} finished")
    
    def http_stress_task(self, worker_id):
        """HTTP stress task to generate network load"""
        logger.info(f"Starting HTTP worker {worker_id}")
        
        while self.running and (time.time() - self.start_time) < self.duration:
            for agent_name, url in self.agent_endpoints.items():
                if not self.running:
                    break
                
                try:
                    response = requests.get(f"{url}/health", timeout=2)
                    if response.status_code == 200:
                        logger.debug(f"✓ {agent_name}: {response.status_code}")
                    else:
                        logger.debug(f"⚠ {agent_name}: {response.status_code}")
                except Exception as e:
                    logger.debug(f"✗ {agent_name}: {str(e)[:50]}")
                
                time.sleep(0.1)
        
        logger.info(f"HTTP worker {worker_id} finished")
    
    def monitor_metrics(self):
        """Monitor system metrics during the test"""
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
                    for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                        if any(agent in line for agent in ['base-agent', 'calculator-agent', 'weather-agent']):
                            logger.info(f"  {line}")
                
                # Get HPA status
                result = subprocess.run(
                    ["kubectl", "get", "hpa", "-n", "multi-agent-a2a"],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    logger.info("HPA Status:")
                    for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                        logger.info(f"  {line}")
                
            except Exception as e:
                logger.warning(f"Failed to get metrics: {e}")
            
            time.sleep(30)  # Monitor every 30 seconds
    
    def run_stress_test(self):
        """Run the complete stress test"""
        logger.info(f"🔥 Starting CPU stress test for {self.duration} seconds")
        logger.info(f"CPU workers: {self.cpu_workers}")
        logger.info(f"HTTP workers: {self.http_workers}")
        logger.info("Press Ctrl+C to stop early")
        
        threads = []
        
        # Start CPU stress threads
        for i in range(self.cpu_workers):
            thread = threading.Thread(target=self.cpu_intensive_task, args=(i,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Start HTTP stress threads
        for i in range(self.http_workers):
            thread = threading.Thread(target=self.http_stress_task, args=(i,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_metrics)
        monitor_thread.daemon = True
        monitor_thread.start()
        threads.append(monitor_thread)
        
        logger.info(f"🚀 Stress test running with {len(threads)} threads...")
        
        # Wait for completion or interruption
        try:
            while self.running and (time.time() - self.start_time) < self.duration:
                elapsed = time.time() - self.start_time
                remaining = self.duration - elapsed
                logger.info(f"⏱️  Elapsed: {elapsed:.1f}s, Remaining: {remaining:.1f}s")
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        self.running = False
        logger.info("🏁 Stress test completed")
        
        # Final metrics check
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
    parser = argparse.ArgumentParser(description="CPU Stress Test for A2A Autoscaling")
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds")
    parser.add_argument("--cpu-workers", type=int, default=4, help="Number of CPU stress workers")
    parser.add_argument("--http-workers", type=int, default=2, help="Number of HTTP stress workers")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.duration <= 0:
        logger.error("Duration must be positive")
        sys.exit(1)
    
    if args.cpu_workers <= 0 or args.http_workers <= 0:
        logger.error("Worker counts must be positive")
        sys.exit(1)
    
    # Create and run stress test
    stress_test = CPUStressTest(
        duration=args.duration,
        cpu_workers=args.cpu_workers,
        http_workers=args.http_workers
    )
    
    stress_test.run_stress_test()
    
    logger.info("🎯 Stress test complete! Check Grafana dashboard for metrics.")
    logger.info("📊 Grafana: http://localhost:3000 (admin/admin)")
    logger.info("📈 Prometheus: http://localhost:9090")

if __name__ == "__main__":
    main()
