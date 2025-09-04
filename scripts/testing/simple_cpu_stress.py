#!/usr/bin/env python3
"""
Simple CPU stress test to trigger autoscaling
"""

import time
import threading
import requests
import sys
import signal

# Global flag to control the stress test
running = True

def signal_handler(sig, frame):
    global running
    print('\nStopping stress test...')
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def cpu_intensive_task():
    """CPU intensive task to stress the system"""
    while running:
        # Simple CPU intensive calculation
        result = 0
        for i in range(100000):
            result += i * i
        time.sleep(0.001)  # Small sleep to prevent complete CPU lockup

def http_stress_task(url, agent_name):
    """HTTP stress task to generate network load"""
    while running:
        try:
            response = requests.get(f"{url}/health", timeout=1)
            print(f"✓ {agent_name}: {response.status_code}")
        except Exception as e:
            print(f"✗ {agent_name}: {str(e)[:50]}")
        time.sleep(0.1)

def main():
    print("🔥 Starting CPU and HTTP stress test...")
    print("Press Ctrl+C to stop")
    
    # Agent endpoints (using port-forwarded services)
    agents = {
        "base": "http://localhost:8080",
        "calculator": "http://localhost:8081", 
        "weather": "http://localhost:8082",
        "research": "http://localhost:8083"
    }
    
    threads = []
    
    # Start CPU intensive threads (4 threads to stress CPU)
    for i in range(4):
        thread = threading.Thread(target=cpu_intensive_task)
        thread.daemon = True
        thread.start()
        threads.append(thread)
        print(f"Started CPU stress thread {i+1}")
    
    # Start HTTP stress threads
    for agent_name, url in agents.items():
        thread = threading.Thread(target=http_stress_task, args=(url, agent_name))
        thread.daemon = True
        thread.start()
        threads.append(thread)
        print(f"Started HTTP stress for {agent_name}")
    
    print(f"\n🚀 Running stress test with {len(threads)} threads...")
    print("Monitor with: kubectl top pods -n multi-agent-a2a")
    print("Check HPA: kubectl get hpa -n multi-agent-a2a")
    
    try:
        while running:
            time.sleep(5)
            print(".", end="", flush=True)
    except KeyboardInterrupt:
        print("\nStopping...")
        running = False

if __name__ == "__main__":
    main()
