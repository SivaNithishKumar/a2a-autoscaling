"""Azure OpenAI integration utilities."""

import os
from typing import Optional, Dict, Any
from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI

from . import get_logger

logger = get_logger(__name__)

# Simple configuration fallback if config module has issues
def get_env_or_default(key: str, default: str = "") -> str:
    """Get environment variable or return default."""
    return os.getenv(key, default)


def create_azure_openai_client() -> AzureOpenAI:
    """Create an Azure OpenAI client."""
    try:
        from ..config import config
        client = AzureOpenAI(
            api_key=config.azure_openai.api_key,
            azure_endpoint=config.azure_openai.endpoint,
            api_version=config.azure_openai.api_version,
        )
    except ImportError:
        # Fallback to environment variables if config module has issues
        client = AzureOpenAI(
            api_key=get_env_or_default("AZURE_OPENAI_API_KEY"),
            azure_endpoint=get_env_or_default("AZURE_OPENAI_ENDPOINT"),
            api_version=get_env_or_default("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        )
    
    return client


def create_azure_chat_openai(
    temperature: float = 0.0,
    max_tokens: Optional[int] = None,
    model_kwargs: Optional[Dict[str, Any]] = None
) -> AzureChatOpenAI:
    """Create a LangChain Azure ChatOpenAI instance."""
    try:
        from ..config import config
        return AzureChatOpenAI(
            azure_deployment=config.azure_openai.model,
            azure_endpoint=config.azure_openai.endpoint,
            api_key=config.azure_openai.api_key,
            api_version=config.azure_openai.api_version,
            temperature=temperature,
            max_tokens=max_tokens,
            model_kwargs=model_kwargs or {},
        )
    except ImportError:
        # Fallback to environment variables if config module has issues
        return AzureChatOpenAI(
            azure_deployment=get_env_or_default("AZURE_OPENAI_MODEL", "gpt-4"),
            azure_endpoint=get_env_or_default("AZURE_OPENAI_ENDPOINT"),
            api_key=get_env_or_default("AZURE_OPENAI_API_KEY"),
            api_version=get_env_or_default("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            temperature=temperature,
            max_tokens=max_tokens,
            model_kwargs=model_kwargs or {},
        )


def setup_langsmith_environment() -> None:
    """Setup LangSmith environment variables."""
    if config.langsmith.tracing:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_PROJECT"] = config.langsmith.project
        
        if config.langsmith.api_key:
            os.environ["LANGSMITH_API_KEY"] = config.langsmith.api_key
            logger.info(f"LangSmith tracing enabled for project: {config.langsmith.project}")
        else:
            logger.warning("LangSmith tracing enabled but no API key provided")
    else:
        os.environ["LANGSMITH_TRACING"] = "false"
        logger.info("LangSmith tracing disabled")


# Initialize LangSmith environment on import
setup_langsmith_environment()
