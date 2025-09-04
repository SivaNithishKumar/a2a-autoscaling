"""Common utilities and shared components."""

import logging
import asyncio
import functools
from typing import Any, Callable, TypeVar, Optional
from langsmith import traceable
from config import get_config

# Import reliability components
from .reliability import (
    AgentReliabilityManager,
    CircuitBreaker,
    HealthChecker,
    HealthStatus,
    CircuitState,
    circuit_breaker,
    create_circuit_breaker
)

# Set up logging with safe defaults
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

T = TypeVar('T')


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def setup_logging(log_level: Optional[str] = None) -> None:
    """Set up logging configuration."""
    try:
        config = get_config()
        level = log_level or config.system.log_level
    except Exception:
        level = log_level or "INFO"
    
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True  # Force reconfiguration if already configured
    )


def trace_async(name: Optional[str] = None, run_type: str = "tool") -> Callable:
    """Decorator for tracing async functions with LangSmith."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                config = get_config()
                if config.langsmith.tracing:
                    traced_func = traceable(
                        name=name or func.__name__,
                        run_type=run_type,
                        project_name=config.langsmith.project
                    )(func)
                    return await traced_func(*args, **kwargs)
            except Exception:
                # Fallback to non-traced execution if config fails
                pass
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def trace_sync(name: Optional[str] = None, run_type: str = "tool") -> Callable:
    """Decorator for tracing sync functions with LangSmith."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                config = get_config()
                if config.langsmith.tracing:
                    traced_func = traceable(
                        name=name or func.__name__,
                        run_type=run_type,
                        project_name=config.langsmith.project
                    )(func)
                    return traced_func(*args, **kwargs)
            except Exception:
                # Fallback to non-traced execution if config fails
                pass
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    delay: float = 1.0,
    **kwargs: Any
) -> Any:
    """Retry an async function with exponential backoff."""
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = delay * (2 ** attempt)
                get_logger(__name__).warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                get_logger(__name__).error(f"All {max_retries + 1} attempts failed")
    
    raise last_exception


class AsyncTaskManager:
    """Manages background async tasks."""
    
    def __init__(self):
        self.tasks: set[asyncio.Task] = set()
    
    def create_task(self, coro: Any, name: Optional[str] = None) -> asyncio.Task:
        """Create and track an async task."""
        task = asyncio.create_task(coro, name=name)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task
    
    async def shutdown(self) -> None:
        """Cancel all running tasks."""
        if self.tasks:
            get_logger(__name__).info(f"Cancelling {len(self.tasks)} running tasks...")
            for task in self.tasks:
                task.cancel()
            
            await asyncio.gather(*self.tasks, return_exceptions=True)
            self.tasks.clear()


# Global task manager instance
task_manager = AsyncTaskManager()
