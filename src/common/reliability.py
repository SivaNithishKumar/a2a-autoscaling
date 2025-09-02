"""
Production reliability components for A2A agents.

Provides circuit breakers, health checks, and resilience patterns
for production-grade agent deployments.
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from contextlib import asynccontextmanager
import structlog

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    expected_exception_types: tuple = (Exception,)
    name: str = "default"


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: float
    check_duration_ms: float


class CircuitBreaker:
    """Production-grade circuit breaker implementation."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.logger = structlog.get_logger(f"circuit_breaker.{config.name}")
        
    def __call__(self, func: Callable):
        """Decorator to wrap functions with circuit breaker."""
        async def wrapper(*args, **kwargs):
            async with self.call():
                return await func(*args, **kwargs)
        return wrapper
    
    @asynccontextmanager
    async def call(self):
        """Context manager for circuit breaker calls."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                self.logger.warning("Circuit breaker is OPEN - call rejected")
                raise CircuitBreakerOpenException(f"Circuit breaker {self.config.name} is OPEN")
        
        try:
            yield
            self._on_success()
        except self.config.expected_exception_types as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.logger.info("Circuit breaker reset to CLOSED after successful call")
        
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.error(
                f"Circuit breaker opened after {self.failure_count} failures",
                failure_threshold=self.config.failure_threshold
            )
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.config.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "recovery_timeout": self.config.recovery_timeout
        }


class HealthChecker:
    """Comprehensive health checking for A2A agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = structlog.get_logger(f"health_checker.{agent_name}")
        self.checks: Dict[str, Callable] = {}
        self.last_health_result: Optional[HealthCheckResult] = None
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check function."""
        self.checks[name] = check_func
        self.logger.info(f"Registered health check: {name}")
    
    async def check_health(self, include_details: bool = True) -> HealthCheckResult:
        """Perform comprehensive health check."""
        start_time = time.time()
        
        try:
            check_results = {}
            overall_status = HealthStatus.HEALTHY
            
            for check_name, check_func in self.checks.items():
                try:
                    result = await self._run_check(check_name, check_func)
                    check_results[check_name] = result
                    
                    # Determine overall status based on worst individual result
                    if result.get('status') == 'unhealthy':
                        overall_status = HealthStatus.UNHEALTHY
                    elif result.get('status') == 'degraded' and overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED
                        
                except Exception as e:
                    check_results[check_name] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
                    overall_status = HealthStatus.UNHEALTHY
                    self.logger.error(f"Health check {check_name} failed", error=str(e))
            
            duration_ms = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                status=overall_status,
                message=f"Agent {self.agent_name} health check completed",
                details=check_results if include_details else {},
                timestamp=time.time(),
                check_duration_ms=duration_ms
            )
            
            self.last_health_result = result
            self.logger.info(
                f"Health check completed: {overall_status.value}",
                duration_ms=duration_ms,
                checks_performed=len(check_results)
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Health check system failure", error=str(e))
            
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Health check system failure: {str(e)}",
                details={},
                timestamp=time.time(),
                check_duration_ms=duration_ms
            )
    
    async def _run_check(self, name: str, check_func: Callable) -> Dict[str, Any]:
        """Run individual health check with timeout."""
        try:
            # Add timeout to health checks
            result = await asyncio.wait_for(check_func(), timeout=10.0)
            return result if isinstance(result, dict) else {'status': 'healthy'}
        except asyncio.TimeoutError:
            return {'status': 'unhealthy', 'error': 'Health check timeout'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def get_last_health_status(self) -> Optional[HealthStatus]:
        """Get the last known health status."""
        return self.last_health_result.status if self.last_health_result else None


class AgentReliabilityManager:
    """Manages reliability components for A2A agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = structlog.get_logger(f"reliability.{agent_name}")
        
        # Initialize circuit breakers
        self.circuit_breakers = {
            'default': CircuitBreaker(CircuitBreakerConfig(name=f"{agent_name}_default")),
            'llm_calls': CircuitBreaker(CircuitBreakerConfig(
                name=f"{agent_name}_llm",
                failure_threshold=3,
                recovery_timeout=30.0
            )),
            'external_api': CircuitBreaker(CircuitBreakerConfig(
                name=f"{agent_name}_external",
                failure_threshold=5,
                recovery_timeout=60.0
            ))
        }
        
        # Initialize health checker
        self.health_checker = HealthChecker(agent_name)
        self._register_default_health_checks()
        
        self.logger.info("Agent reliability manager initialized")
    
    def _register_default_health_checks(self):
        """Register default health checks for agents."""
        self.health_checker.register_check("memory_usage", self._check_memory_usage)
        self.health_checker.register_check("circuit_breakers", self._check_circuit_breakers)
        self.health_checker.register_check("basic_functionality", self._check_basic_functionality)
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            if memory_percent > 90:
                return {'status': 'unhealthy', 'memory_percent': memory_percent}
            elif memory_percent > 75:
                return {'status': 'degraded', 'memory_percent': memory_percent}
            else:
                return {
                    'status': 'healthy',
                    'memory_percent': memory_percent,
                    'memory_mb': memory_info.rss / 1024 / 1024
                }
        except ImportError:
            return {'status': 'healthy', 'note': 'psutil not available'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def _check_circuit_breakers(self) -> Dict[str, Any]:
        """Check circuit breaker states."""
        breaker_states = {}
        unhealthy_count = 0
        
        for name, breaker in self.circuit_breakers.items():
            state = breaker.get_state()
            breaker_states[name] = state
            if state['state'] == 'open':
                unhealthy_count += 1
        
        if unhealthy_count > 0:
            return {
                'status': 'degraded' if unhealthy_count < len(self.circuit_breakers) else 'unhealthy',
                'circuit_breakers': breaker_states,
                'open_breakers': unhealthy_count
            }
        else:
            return {
                'status': 'healthy',
                'circuit_breakers': breaker_states
            }
    
    async def _check_basic_functionality(self) -> Dict[str, Any]:
        """Check basic agent functionality."""
        try:
            # Basic functionality test - this can be overridden by specific agents
            start_time = time.time()
            # Simulate basic operation
            await asyncio.sleep(0.001)
            response_time = (time.time() - start_time) * 1000
            
            if response_time > 1000:  # 1 second
                return {'status': 'degraded', 'response_time_ms': response_time}
            else:
                return {'status': 'healthy', 'response_time_ms': response_time}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def get_circuit_breaker(self, name: str = 'default') -> CircuitBreaker:
        """Get circuit breaker by name."""
        return self.circuit_breakers.get(name, self.circuit_breakers['default'])
    
    async def get_health_status(self, include_details: bool = True) -> HealthCheckResult:
        """Get current health status."""
        return await self.health_checker.check_health(include_details)
    
    def get_reliability_status(self) -> Dict[str, Any]:
        """Get comprehensive reliability status."""
        return {
            'agent_name': self.agent_name,
            'circuit_breakers': {
                name: breaker.get_state() 
                for name, breaker in self.circuit_breakers.items()
            },
            'last_health_check': (
                {
                    'status': self.health_checker.last_health_result.status.value,
                    'timestamp': self.health_checker.last_health_result.timestamp,
                    'duration_ms': self.health_checker.last_health_result.check_duration_ms
                } 
                if self.health_checker.last_health_result 
                else None
            )
        }


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# Utility functions for easy integration
def create_circuit_breaker(name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0) -> CircuitBreaker:
    """Create a circuit breaker with custom configuration."""
    config = CircuitBreakerConfig(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout
    )
    return CircuitBreaker(config)


def circuit_breaker(failure_threshold: int = 5, recovery_timeout: float = 60.0, name: str = "default"):
    """Decorator for adding circuit breaker to functions."""
    def decorator(func: Callable):
        breaker = create_circuit_breaker(
            name=f"{func.__name__}_{name}",
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
        return breaker(func)
    return decorator