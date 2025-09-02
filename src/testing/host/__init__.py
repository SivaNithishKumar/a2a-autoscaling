"""
A2A Testing Host

Core host functionality for A2A testing framework.
"""

from .main import main
from .agent_discovery import AgentDiscovery
from .test_runner import TestRunner
from .interactive_shell import InteractiveShell
from .orchestrator import MultiAgentOrchestrator

__all__ = [
    "main",
    "AgentDiscovery", 
    "TestRunner",
    "InteractiveShell",
    "MultiAgentOrchestrator"
]

