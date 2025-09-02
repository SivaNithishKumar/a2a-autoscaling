"""
A2A Testing Framework

A comprehensive testing framework for Agent-to-Agent (A2A) protocol implementations.
This framework provides tools for testing individual agents, multi-agent orchestration,
protocol compliance, and interactive agent exploration.

Key Components:
- Agent Discovery: Automatically detect and connect to A2A agents
- Test Scenarios: Predefined tests for various agent capabilities
- Interactive Shell: Manual testing and exploration interface
- Orchestration Engine: Multi-agent workflow coordination
- Protocol Testing: A2A specification compliance validation

Usage:
    # Run interactive mode
    python -m multi_agent_a2a.testing.host.main --mode interactive
    
    # Execute test suite
    python -m multi_agent_a2a.testing.host.main --mode test-suite
    
    # Multi-agent orchestration testing
    python -m multi_agent_a2a.testing.host.main --mode orchestration
    
    # Agent discovery
    python -m multi_agent_a2a.testing.host.main --mode discovery
"""

__version__ = "1.0.0"
__author__ = "Multi-Agent A2A Team"

# Default agent endpoints for testing
DEFAULT_AGENT_ENDPOINTS = [
    "http://localhost:8000",  # Base Agent
    "http://localhost:8001",  # Weather Agent
    "http://localhost:8002",  # Calculator Agent  
    "http://localhost:8003",  # Research Agent
]

# Test configuration
TEST_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "discovery_timeout": 10,
    "streaming_timeout": 60,
}
