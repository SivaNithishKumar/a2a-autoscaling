"""Prometheus metrics collection for A2A agents."""

import time
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

logger = structlog.get_logger(__name__)

# Global metrics for all agents
REQUEST_COUNT = Counter(
    'a2a_requests_total', 
    'Total A2A requests processed',
    ['agent_name', 'skill', 'status']
)

REQUEST_DURATION = Histogram(
    'a2a_request_duration_seconds',
    'A2A request processing duration',
    ['agent_name', 'skill']
)

ACTIVE_TASKS = Gauge(
    'a2a_active_tasks',
    'Currently active tasks',
    ['agent_name']
)

ERROR_COUNT = Counter(
    'a2a_errors_total',
    'Total errors in A2A processing',
    ['agent_name', 'error_type']
)

AGENT_UPTIME = Gauge(
    'a2a_agent_uptime_seconds',
    'Agent uptime in seconds',
    ['agent_name']
)

class AgentMetrics:
    """Metrics collector for individual agents."""
    
    def __init__(self, agent_name: str, metrics_port: Optional[int] = None):
        self.agent_name = agent_name
        self.metrics_port = metrics_port
        self.start_time = time.time()
        self.logger = structlog.get_logger(f"metrics.{agent_name}")
        
        # Initialize agent uptime
        AGENT_UPTIME.labels(agent_name=self.agent_name).set_function(
            lambda: time.time() - self.start_time
        )
        
        if metrics_port:
            try:
                start_http_server(metrics_port)
                self.logger.info(f"Metrics server started on port {metrics_port}")
            except Exception as e:
                self.logger.warning(f"Failed to start metrics server: {e}")
    
    def increment_request_count(self, skill: str, status: str = "success"):
        """Increment the request counter."""
        REQUEST_COUNT.labels(
            agent_name=self.agent_name,
            skill=skill,
            status=status
        ).inc()
    
    def increment_error_count(self, error_type: str):
        """Increment the error counter."""
        ERROR_COUNT.labels(
            agent_name=self.agent_name,
            error_type=error_type
        ).inc()
    
    def set_active_tasks(self, count: int):
        """Set the number of active tasks."""
        ACTIVE_TASKS.labels(agent_name=self.agent_name).set(count)
    
    @asynccontextmanager
    async def track_request_duration(self, skill: str):
        """Context manager to track request duration."""
        start_time = time.time()
        self.set_active_tasks(1)  # Simplified - in real implementation track actual count
        
        try:
            yield
            # Success
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                agent_name=self.agent_name,
                skill=skill
            ).observe(duration)
            self.increment_request_count(skill, "success")
            
        except Exception as e:
            # Error
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                agent_name=self.agent_name,
                skill=skill
            ).observe(duration)
            self.increment_request_count(skill, "error")
            self.increment_error_count(type(e).__name__)
            raise
        finally:
            self.set_active_tasks(0)
    
    def track_simple_operation(self, operation: str):
        """Track a simple operation without timing."""
        self.increment_request_count(operation, "success")
        self.logger.debug(f"Tracked operation: {operation}")

# Agent-specific metrics instances
_agent_metrics: Dict[str, AgentMetrics] = {}

def get_agent_metrics(agent_name: str, metrics_port: Optional[int] = None) -> AgentMetrics:
    """Get or create metrics instance for an agent."""
    if agent_name not in _agent_metrics:
        _agent_metrics[agent_name] = AgentMetrics(agent_name, metrics_port)
    return _agent_metrics[agent_name]

def cleanup_metrics():
    """Cleanup metrics instances."""
    global _agent_metrics
    _agent_metrics.clear()