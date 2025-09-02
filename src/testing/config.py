"""
A2A Testing Framework Configuration

Configuration settings for the A2A testing framework.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

# Default agent configurations
DEFAULT_AGENTS = {
    "base": {
        "name": "Base Agent",
        "endpoint": "http://localhost:8000",
        "port": 8000,
        "skills": ["base_functionality", "agent_coordination"]
    },
    "weather": {
        "name": "Weather Agent",
        "endpoint": "http://localhost:8001",
        "port": 8001,
        "skills": ["current_weather", "weather_forecast"]
    },
    "calculator": {
        "name": "Calculator Agent", 
        "endpoint": "http://localhost:8002",
        "port": 8002,
        "skills": ["basic_math", "advanced_calculations"]
    },
    "research": {
        "name": "Research Agent",
        "endpoint": "http://localhost:8003", 
        "port": 8003,
        "skills": ["web_search", "fact_checking"]
    }
}

# Test configuration
TEST_CONFIG = {
    "default_timeout": 30,
    "discovery_timeout": 10,
    "streaming_timeout": 60,
    "max_retries": 3,
    "retry_delay": 1.0,
    "concurrent_limit": 5
}

# Protocol configuration
PROTOCOL_CONFIG = {
    "jsonrpc_version": "2.0",
    "content_type": "application/json",
    "user_agent": "A2A-Test-Framework/1.0.0",
    "max_message_size": 10 * 1024 * 1024,  # 10MB
}

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "test_results"
LOGS_DIR = OUTPUT_DIR / "logs"
REPORTS_DIR = OUTPUT_DIR / "reports"

# Ensure output directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard"
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "a2a_testing.log"),
            "formatter": "detailed"
        }
    },
    "loggers": {
        "a2a_testing": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}
