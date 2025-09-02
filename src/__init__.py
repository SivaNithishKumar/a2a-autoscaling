"""
Multi-Agent A2A System - Distributed Architecture

A distributed multi-agent system using the A2A (Agent-to-Agent) protocol
following the patterns demonstrated in A2A samples.

This version has been migrated from a centralized hub-and-spoke architecture
to a distributed peer-to-peer communication model.
"""

__version__ = "0.3.0"
__author__ = "Multi-Agent A2A Team"
__email__ = "team@multi-agent-a2a.com"

# Export key components for the distributed architecture
# Note: Only importing what's safe to avoid dependency issues
try:
    from .agents.base import BaseAgent, BaseAgentExecutor
    from .agents.calculator import CalculatorAgent, CalculatorAgentExecutor
    from .agents.weather import WeatherAgent, WeatherAgentExecutor  
    from .agents.research import ResearchAgent, ResearchAgentExecutor
    
    __all__ = [
        "BaseAgent", "BaseAgentExecutor",
        "CalculatorAgent", "CalculatorAgentExecutor", 
        "WeatherAgent", "WeatherAgentExecutor",
        "ResearchAgent", "ResearchAgentExecutor",
    ]
except ImportError as e:
    # Graceful fallback if some agents can't be imported
    print(f"Warning: Some agents couldn't be imported: {e}")
    __all__ = []
