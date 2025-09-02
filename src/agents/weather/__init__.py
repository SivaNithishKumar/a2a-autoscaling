"""Weather agent implementation - A2A Standard."""

try:
    from .agent import WeatherAgent
    from .agent_executor import WeatherAgentExecutor
    __all__ = ["WeatherAgent", "WeatherAgentExecutor"]
except ImportError:
    # If weather agent can't be imported, just make the module empty
    __all__ = []
