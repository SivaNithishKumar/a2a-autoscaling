"""Configuration management for the multi-agent A2A system."""

import os
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class AzureOpenAIConfig(BaseSettings):
    """Azure OpenAI configuration."""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2024-12-01-preview"
    azure_openai_model: str = "gpt-4.1"
    
    @property
    def api_key(self) -> Optional[str]:
        """Get the API key."""
        return self.azure_openai_api_key
    
    @property
    def endpoint(self) -> Optional[str]:
        """Get the endpoint."""
        return self.azure_openai_endpoint
    
    @property
    def api_version(self) -> str:
        """Get the API version."""
        return self.azure_openai_api_version
    
    @property
    def model(self) -> str:
        """Get the model."""
        return self.azure_openai_model
    
    @property
    def is_configured(self) -> bool:
        """Check if Azure OpenAI is properly configured."""
        return bool(self.azure_openai_api_key and self.azure_openai_endpoint)


class LangSmithConfig(BaseSettings):
    """LangSmith configuration."""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    langsmith_tracing: bool = True
    langsmith_project: str = "multi-agent-a2a"
    langsmith_api_key: Optional[str] = None
    
    @property
    def tracing(self) -> bool:
        """Get tracing setting."""
        return self.langsmith_tracing
    
    @property
    def project(self) -> str:
        """Get project name."""
        return self.langsmith_project
    
    @property
    def api_key(self) -> Optional[str]:
        """Get API key."""
        return self.langsmith_api_key


class SystemConfig(BaseSettings):
    """System configuration."""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    log_level: str = "INFO"
    environment: str = "development"
    debug: bool = False


class AgentPortsConfig(BaseSettings):
    """Agent ports configuration."""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    weather_agent_port: int = 8001
    calculator_agent_port: int = 8002
    research_agent_port: int = 8003


class EngineConfig(BaseSettings):
    """Engine configuration."""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    agent_engine_host: str = "0.0.0.0"
    agent_engine_port: int = 8000
    
    @property
    def host(self) -> str:
        """Get the host."""
        return self.agent_engine_host
    
    @property
    def port(self) -> int:
        """Get the port."""
        return self.agent_engine_port


class Config:
    """Main configuration class."""
    
    def __init__(self):
        self.azure_openai = AzureOpenAIConfig()
        self.langsmith = LangSmithConfig()
        self.system = SystemConfig()
        self.agent_ports = AgentPortsConfig()
        self.engine = EngineConfig()
    
    @property
    def weather_agent_url(self) -> str:
        """Get the weather agent URL."""
        return f"http://localhost:{self.agent_ports.weather_agent_port}"
    
    @property
    def calculator_agent_url(self) -> str:
        """Get the calculator agent URL."""
        return f"http://localhost:{self.agent_ports.calculator_agent_port}"
    
    @property
    def research_agent_url(self) -> str:
        """Get the research agent URL."""
        return f"http://localhost:{self.agent_ports.research_agent_port}"


# Global configuration instance - lazy loaded
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance with lazy loading."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
