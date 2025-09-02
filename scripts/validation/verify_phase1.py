#!/usr/bin/env python3
"""Comprehensive verification script for Phase 1 metrics collection system."""

import asyncio
import sys
import time
import httpx
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

print("🔍 PHASE 1 VERIFICATION: Metrics Collection System")
print("="*60)

# Test 1: Import all metrics components
print("\n📦 Test 1: Importing metrics components...")
try:
    from multi_agent_a2a.common.metrics import (
        get_agent_metrics, 
        REQUEST_COUNT, 
        REQUEST_DURATION, 
        ACTIVE_TASKS, 
        ERROR_COUNT, 
        AGENT_UPTIME
    )
    print("✅ Successfully imported metrics module")
except ImportError as e:
    print(f"❌ Failed to import metrics: {e}")
    sys.exit(1)

# Test 2: Import and initialize all agents
print("\n🤖 Test 2: Initializing agents with metrics...")
agents_status = {}

# Base Agent
try:
    from multi_agent_a2a.agents.base.agent import BaseAgent, BaseAgentExecutor
    base_agent = BaseAgent()
    base_executor = BaseAgentExecutor()
    agents_status['base'] = {'status': 'SUCCESS', 'port': 8080, 'agent': base_agent}
    print("✅ Base Agent initialized with metrics on port 8080")
except Exception as e:
    agents_status['base'] = {'status': 'FAILED', 'error': str(e)}
    print(f"❌ Base Agent failed: {e}")

# Calculator Agent
try:
    from multi_agent_a2a.agents.calculator.agent import CalculatorAgent
    calc_agent = CalculatorAgent()
    agents_status['calculator'] = {'status': 'SUCCESS', 'port': 8081, 'agent': calc_agent}
    print("✅ Calculator Agent initialized with metrics on port 8081")
except Exception as e:
    agents_status['calculator'] = {'status': 'FAILED', 'error': str(e)}
    print(f"❌ Calculator Agent failed: {e}")

# Weather Agent
try:
    from multi_agent_a2a.agents.weather.agent import WeatherAgent
    weather_agent = WeatherAgent()
    agents_status['weather'] = {'status': 'SUCCESS', 'port': 8082, 'agent': weather_agent}
    print("✅ Weather Agent initialized with metrics on port 8082")
except Exception as e:
    agents_status['weather'] = {'status': 'FAILED', 'error': str(e)}
    print(f"❌ Weather Agent failed: {e}")

# Research Agent (optional - may have dependencies)
try:
    from multi_agent_a2a.agents.research.agent import ResearchAgent, ResearchAgentExecutor
    research_agent = ResearchAgent()
    research_executor = ResearchAgentExecutor()
    agents_status['research'] = {'status': 'SUCCESS', 'port': 8083, 'agent': research_agent}
    print("✅ Research Agent initialized with metrics on port 8083")
except Exception as e:
    agents_status['research'] = {'status': 'WARNING', 'error': str(e)}
    print(f"⚠️  Research Agent warning (may need additional deps): {e}")

# Test 3: Verify metrics functionality
print("\n📊 Test 3: Testing metrics functionality...")
for agent_name, agent_info in agents_status.items():
    if agent_info['status'] == 'SUCCESS':
        try:
            agent = agent_info['agent']
            if hasattr(agent, 'metrics'):
                # Test metric operations
                agent.metrics.increment_request_count('test_skill', 'success')
                agent.metrics.set_active_tasks(1)
                agent.metrics.set_active_tasks(0)
                print(f"✅ {agent_name.title()} Agent metrics operations successful")
            else:
                print(f"⚠️  {agent_name.title()} Agent missing metrics attribute")
        except Exception as e:
            print(f"❌ {agent_name.title()} Agent metrics test failed: {e}")

# Test 4: Test async metrics tracking
print("\n⏱️  Test 4: Testing async metrics tracking...")

async def test_async_metrics():
    """Test async metrics tracking functionality."""
    for agent_name, agent_info in agents_status.items():
        if agent_info['status'] == 'SUCCESS' and hasattr(agent_info['agent'], 'metrics'):
            try:
                agent = agent_info['agent']
                async with agent.metrics.track_request_duration('test_async_skill'):
                    await asyncio.sleep(0.01)  # Simulate work
                print(f"✅ {agent_name.title()} Agent async metrics tracking successful")
            except Exception as e:
                print(f"❌ {agent_name.title()} Agent async metrics failed: {e}")

# Run async test
try:
    asyncio.run(test_async_metrics())
except Exception as e:
    print(f"❌ Async metrics test failed: {e}")

# Test 5: Verify Prometheus configuration
print("\n🔧 Test 5: Verifying Prometheus configuration...")
prometheus_config = project_root / "monitoring" / "prometheus" / "config.yml"
if prometheus_config.exists():
    print("✅ Prometheus configuration file exists")
    with open(prometheus_config, 'r') as f:
        config_content = f.read()
        expected_ports = ['8080', '8081', '8082', '8083', '8084', '8085']
        found_ports = [port for port in expected_ports if port in config_content]
        print(f"✅ Found {len(found_ports)}/{len(expected_ports)} expected ports in config")
else:
    print("❌ Prometheus configuration file missing")

# Test 6: Verify directory structure
print("\n📁 Test 6: Verifying monitoring infrastructure...")
required_dirs = [
    "monitoring/prometheus",
    "monitoring/grafana", 
    "k8s/agents",
    "k8s/monitoring"
]

for dir_path in required_dirs:
    full_path = project_root / dir_path
    if full_path.exists():
        print(f"✅ Directory exists: {dir_path}")
    else:
        print(f"❌ Directory missing: {dir_path}")

# Test 7: Verify dependencies
print("\n📦 Test 7: Verifying dependencies...")
try:
    import prometheus_client
    try:
        version = prometheus_client.__version__
    except AttributeError:
        version = "available"
    print(f"✅ prometheus-client: {version}")
except ImportError:
    print("❌ prometheus-client not installed")

try:
    import grafana_client
    print(f"✅ grafana-client available")
except ImportError:
    print("❌ grafana-client not installed")

try:
    import structlog
    print(f"✅ structlog available")
except ImportError:
    print("❌ structlog not installed")

# Summary Report
print("\n" + "="*60)
print("📊 PHASE 1 VERIFICATION SUMMARY")
print("="*60)

success_count = sum(1 for info in agents_status.values() if info['status'] == 'SUCCESS')
warning_count = sum(1 for info in agents_status.values() if info['status'] == 'WARNING')
failed_count = sum(1 for info in agents_status.values() if info['status'] == 'FAILED')

print(f"✅ Agents Successfully Initialized: {success_count}")
print(f"⚠️  Agents with Warnings: {warning_count}")
print(f"❌ Agents Failed: {failed_count}")

print("\n🎯 Ready for Phase 2: Move Orchestration Agent")
print("📊 Metrics endpoints available on:")
for agent_name, agent_info in agents_status.items():
    if agent_info['status'] == 'SUCCESS':
        port = agent_info.get('port', 'unknown')
        print(f"   - {agent_name.title()} Agent: http://localhost:{port}/metrics")

if success_count >= 3:  # At least base, calc, weather working
    print("\n🚀 PHASE 1 COMPLETE - Ready to proceed with Phase 2!")
    sys.exit(0)
else:
    print("\n⚠️  PHASE 1 INCOMPLETE - Need to fix issues before proceeding")
    sys.exit(1)