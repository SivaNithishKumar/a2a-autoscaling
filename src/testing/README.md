# A2A Testing Framework

## Overview

A comprehensive testing framework for Agent-to-Agent (A2A) protocol implementations. This framework provides tools for testing individual agents, multi-agent orchestration, protocol compliance, and interactive agent exploration.

## Structure

```
testing/
├── __init__.py                 # Framework initialization and configuration
├── config.py                  # Configuration settings
├── host/                      # Core host functionality  
│   ├── __init__.py
│   ├── main.py               # Main application entry point
│   ├── agent_discovery.py    # Agent discovery and connection
│   ├── test_runner.py        # Test execution engine
│   ├── interactive_shell.py  # Interactive CLI interface
│   └── orchestrator.py       # Multi-agent orchestration
├── scenarios/                 # Test scenarios
│   ├── __init__.py
│   ├── basic_tests.py        # Individual agent tests
│   ├── orchestration_tests.py # Multi-agent workflows  
│   └── protocol_tests.py     # Protocol compliance tests
└── utils/                     # Utilities and helpers
    ├── __init__.py
    ├── a2a_client.py         # Enhanced A2A client
    └── test_helpers.py       # Common test utilities
```

## Quick Start

```bash
# Make the runner executable
chmod +x run_test_host.py

# Run interactive mode
python run_test_host.py --mode interactive

# Execute test suite
python run_test_host.py --mode test-suite

# Multi-agent orchestration
python run_test_host.py --mode orchestration

# Agent discovery
python run_test_host.py --mode discovery
```

## Features

### Agent Discovery
- Automatically detect running A2A agents
- Fetch and validate Agent Cards
- Test basic connectivity and protocol compliance

### Individual Agent Testing  
- Weather Agent: Current conditions and forecasts
- Calculator Agent: Mathematical computations
- Research Agent: Web searches and fact-checking

### Multi-Agent Orchestration
- Travel Planning workflows
- Investment Analysis scenarios
- Complex task delegation

### Protocol Compliance
- JSON-RPC 2.0 validation
- A2A specification adherence
- Error handling verification
- Streaming capabilities testing

### Interactive Shell
- Real-time agent communication
- Manual testing and exploration
- Command-line interface for developers

## Dependencies

The framework requires the same dependencies as the multi-agent system:
- a2a-python
- httpx
- asyncio
- click (for CLI)
- uvicorn (for hosting)
