"""Agent implementations package - A2A Standard."""

# Export all available agents and executors
__all__ = []
available_agents = []

# Import Base Agent
try:
    from .base import BaseAgent, BaseAgentExecutor
    __all__.extend(["BaseAgent", "BaseAgentExecutor"])
    available_agents.append("Base")
except ImportError:
    pass

# Import Calculator Agent
try:
    from .calculator import CalculatorAgent, CalculatorAgentExecutor
    __all__.extend(["CalculatorAgent", "CalculatorAgentExecutor"])
    available_agents.append("Calculator")
except ImportError:
    pass

# Import Weather Agent (may not have executor)
try:
    from .weather import WeatherAgent
    __all__.append("WeatherAgent")
    available_agents.append("Weather")
    try:
        from .weather import WeatherAgentExecutor
        __all__.append("WeatherAgentExecutor")
    except ImportError:
        pass  # Weather agent may not have executor
except ImportError:
    pass

# Import Research Agent
try:
    from .research import ResearchAgent, ResearchAgentExecutor
    __all__.extend(["ResearchAgent", "ResearchAgentExecutor"])
    available_agents.append("Research")
except ImportError:
    pass
