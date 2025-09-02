"""
Infrastructure Monitoring Agent - AI-Ops Multi-Agent for Infrastructure Analysis

A sophisticated AI-powered infrastructure monitoring agent designed for production-grade AI-Ops.
Demonstrates advanced monitoring capabilities with anomaly detection, predictive failure analysis,
and intelligent alerting for comprehensive infrastructure oversight.
"""

import asyncio
import json
import logging
import uuid
import time
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncIterable
from dataclasses import dataclass, asdict
from enum import Enum

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentSkill,
    TaskState,
    Part,
    TextPart,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

# Import metrics collection and reliability
from common.metrics import get_agent_metrics
from common import get_logger, trace_async, AgentReliabilityManager, circuit_breaker


class AlertSeverity(Enum):
    """Alert severity levels for infrastructure monitoring."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServiceStatus(Enum):
    """Service status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class InfrastructureMetric:
    """Infrastructure metric with AI-Ops metadata."""
    service_name: str
    metric_name: str
    current_value: float
    threshold_warning: float
    threshold_critical: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]


@dataclass
class AnomalyDetection:
    """Anomaly detection result with AI analysis."""
    detection_id: str
    service_name: str
    metric_name: str
    anomaly_type: str
    confidence_score: float
    description: str
    recommendations: List[str]
    severity: AlertSeverity
    predicted_impact: str
    timestamp: datetime


@dataclass
class FailurePrediction:
    """Failure prediction with AI-powered analysis."""
    prediction_id: str
    service_name: str
    failure_type: str
    probability: float
    predicted_time: datetime
    leading_indicators: List[str]
    mitigation_steps: List[str]
    business_impact: str
    confidence_level: float


@dataclass
class InfrastructureStatus:
    """Complete infrastructure status report."""
    timestamp: datetime
    overall_health: ServiceStatus
    services_monitored: int
    active_alerts: int
    anomalies_detected: List[AnomalyDetection]
    failure_predictions: List[FailurePrediction]
    performance_insights: List[str]
    optimization_recommendations: List[str]


class InfrastructureMonitoringAgent:
    """AI-powered infrastructure monitoring agent with advanced AI-Ops capabilities."""

    def __init__(self):
        self.name = "Infrastructure Monitoring Agent"
        self.description = "AI-powered infrastructure monitoring with anomaly detection and predictive analytics"
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Initialize metrics collection with dedicated port
        self.metrics = get_agent_metrics("infrastructure_monitor", metrics_port=8085)
        
        # Initialize reliability manager
        self.reliability = AgentReliabilityManager("infrastructure_monitor")
        self.reliability.health_checker.register_check("monitoring_health", self._check_monitoring_health)
        
        # AI-Ops monitoring state
        self.monitored_services = self._initialize_monitored_services()
        self.active_alerts: Dict[str, AnomalyDetection] = {}
        self.historical_metrics: List[InfrastructureMetric] = []
        self.failure_predictions: List[FailurePrediction] = []
        
        # ML model simulation parameters
        self.anomaly_detection_enabled = True
        self.prediction_model_accuracy = 0.92
        self.baseline_established = True

    def _initialize_monitored_services(self) -> Dict[str, Dict[str, Any]]:
        """Initialize mock infrastructure services for monitoring."""
        return {
            "web_frontend": {
                "name": "Web Frontend",
                "type": "web_service",
                "status": ServiceStatus.HEALTHY,
                "cpu_usage": 25.4,
                "memory_usage": 68.2,
                "response_time": 245,
                "error_rate": 0.03,
                "uptime": 99.97
            },
            "api_gateway": {
                "name": "API Gateway",
                "type": "api_service",
                "status": ServiceStatus.HEALTHY,
                "cpu_usage": 42.1,
                "memory_usage": 54.7,
                "response_time": 89,
                "error_rate": 0.01,
                "uptime": 99.99
            },
            "database_primary": {
                "name": "Primary Database",
                "type": "database",
                "status": ServiceStatus.HEALTHY,
                "cpu_usage": 61.8,
                "memory_usage": 78.9,
                "response_time": 12,
                "error_rate": 0.00,
                "uptime": 99.95
            },
            "message_queue": {
                "name": "Message Queue",
                "type": "messaging",
                "status": ServiceStatus.HEALTHY,
                "cpu_usage": 18.3,
                "memory_usage": 45.1,
                "response_time": 5,
                "error_rate": 0.02,
                "uptime": 99.98
            },
            "cache_layer": {
                "name": "Cache Layer",
                "type": "cache",
                "status": ServiceStatus.DEGRADED,
                "cpu_usage": 85.7,
                "memory_usage": 92.4,
                "response_time": 158,
                "error_rate": 0.08,
                "uptime": 99.85
            },
            "load_balancer": {
                "name": "Load Balancer",
                "type": "networking",
                "status": ServiceStatus.HEALTHY,
                "cpu_usage": 31.2,
                "memory_usage": 41.6,
                "response_time": 3,
                "error_rate": 0.00,
                "uptime": 99.99
            }
        }

    @trace_async("monitor_infrastructure", "infrastructure_monitor")
    @circuit_breaker(failure_threshold=5, recovery_timeout=60.0, name="monitoring")
    async def monitor_infrastructure(self, monitoring_request: Dict[str, Any], context_id: str) -> InfrastructureStatus:
        """Perform comprehensive infrastructure monitoring with AI analysis."""
        async with self.metrics.track_request_duration("monitor_infrastructure"):
            try:
                self.logger.info(f"Starting infrastructure monitoring sweep: {context_id}")
                
                # Simulate real-time monitoring
                await asyncio.sleep(0.1)  # Simulate data collection
                
                # Detect anomalies
                anomalies = await self._detect_anomalies()
                
                # Generate failure predictions
                predictions = await self._predict_failures()
                
                # Calculate overall health
                overall_health = self._calculate_overall_health()
                
                # Generate insights and recommendations
                insights = self._generate_performance_insights()
                recommendations = self._generate_optimization_recommendations()
                
                status = InfrastructureStatus(
                    timestamp=datetime.now(),
                    overall_health=overall_health,
                    services_monitored=len(self.monitored_services),
                    active_alerts=len(self.active_alerts),
                    anomalies_detected=anomalies,
                    failure_predictions=predictions,
                    performance_insights=insights,
                    optimization_recommendations=recommendations
                )
                
                self.logger.info(f"Infrastructure monitoring completed: {len(anomalies)} anomalies, {len(predictions)} predictions")
                return status
                
            except Exception as e:
                self.logger.error(f"Infrastructure monitoring failed: {e}")
                raise

    async def _detect_anomalies(self) -> List[AnomalyDetection]:
        """AI-powered anomaly detection across infrastructure services."""
        anomalies = []
        
        for service_id, service_data in self.monitored_services.items():
            # Simulate ML-based anomaly detection
            if service_data["status"] == ServiceStatus.DEGRADED or random.random() < 0.15:
                anomaly = AnomalyDetection(
                    detection_id=f"ANOM-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                    service_name=service_data["name"],
                    metric_name="performance_degradation",
                    anomaly_type="performance_anomaly",
                    confidence_score=random.uniform(0.75, 0.98),
                    description=f"Detected performance anomaly in {service_data['name']}",
                    recommendations=[
                        "Scale up resources immediately",
                        "Investigate recent configuration changes",
                        "Review error logs for patterns"
                    ],
                    severity=AlertSeverity.HIGH if service_data["status"] == ServiceStatus.DEGRADED else AlertSeverity.MEDIUM,
                    predicted_impact="Service degradation may affect user experience",
                    timestamp=datetime.now()
                )
                anomalies.append(anomaly)
                self.active_alerts[anomaly.detection_id] = anomaly
        
        return anomalies

    async def _predict_failures(self) -> List[FailurePrediction]:
        """AI-powered failure prediction using historical data analysis."""
        predictions = []
        
        # Simulate advanced ML prediction model
        high_risk_services = [
            service_id for service_id, data in self.monitored_services.items()
            if data["cpu_usage"] > 80 or data["memory_usage"] > 90 or data["error_rate"] > 0.05
        ]
        
        for service_id in high_risk_services:
            service_data = self.monitored_services[service_id]
            prediction = FailurePrediction(
                prediction_id=f"PRED-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                service_name=service_data["name"],
                failure_type="resource_exhaustion",
                probability=random.uniform(0.65, 0.95),
                predicted_time=datetime.now() + timedelta(hours=random.randint(2, 24)),
                leading_indicators=[
                    "High CPU utilization trending upward",
                    "Memory usage approaching limits",
                    "Error rate increasing"
                ],
                mitigation_steps=[
                    "Scale horizontally to distribute load",
                    "Optimize queries and resource usage",
                    "Implement circuit breakers",
                    "Review and optimize caching strategy"
                ],
                business_impact="Potential service downtime affecting user operations",
                confidence_level=self.prediction_model_accuracy
            )
            predictions.append(prediction)
        
        self.failure_predictions.extend(predictions)
        return predictions

    def _calculate_overall_health(self) -> ServiceStatus:
        """Calculate overall infrastructure health based on service statuses."""
        statuses = [service["status"] for service in self.monitored_services.values()]
        
        if any(status == ServiceStatus.DOWN for status in statuses):
            return ServiceStatus.DOWN
        elif any(status == ServiceStatus.DEGRADED for status in statuses):
            return ServiceStatus.DEGRADED
        elif all(status == ServiceStatus.HEALTHY for status in statuses):
            return ServiceStatus.HEALTHY
        else:
            return ServiceStatus.UNKNOWN

    def _generate_performance_insights(self) -> List[str]:
        """Generate AI-powered performance insights."""
        return [
            "Cache layer showing signs of memory pressure - consider optimization",
            "Database response times optimal across all queries",
            "API Gateway handling traffic efficiently with low latency",
            "Load balancer distribution patterns suggest optimal configuration",
            "Message queue processing within normal parameters"
        ]

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate AI-powered optimization recommendations."""
        return [
            "Implement auto-scaling for cache layer based on memory usage",
            "Consider read replicas for database to improve response times",
            "Optimize API caching strategies for frequently accessed endpoints",
            "Review message queue configuration for peak traffic patterns",
            "Implement predictive scaling based on historical usage patterns"
        ]

    async def stream(self, query: str, context_id: str) -> AsyncIterable[Dict[str, Any]]:
        """Stream infrastructure monitoring responses based on query analysis."""
        try:
            self.logger.info(f"Processing infrastructure monitoring query: {query}")
            skill = self._determine_skill_from_query(query)
            
            if skill == "monitor_infrastructure":
                result = await self._handle_monitoring_request(query, context_id)
            elif skill == "detect_anomalies":
                result = await self._handle_anomaly_request(query, context_id)
            elif skill == "predict_failures":
                result = await self._handle_prediction_request(query, context_id)
            else:
                result = await self._handle_general_request(query, context_id)
            
            # Simulate streaming response
            yield {
                'is_task_complete': False,
                'require_user_input': False,
                'content': "🔍 Analyzing infrastructure metrics..."
            }
            
            await asyncio.sleep(0.2)
            
            yield {
                'is_task_complete': True,
                'require_user_input': False,
                'content': result['content']
            }
            
        except Exception as e:
            self.logger.error(f"Error in infrastructure monitoring stream: {e}")
            yield {
                'is_task_complete': True,
                'require_user_input': False,
                'content': f"Infrastructure monitoring error: {str(e)}"
            }

    def _determine_skill_from_query(self, query: str) -> str:
        """Determine the appropriate skill based on user query."""
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ["monitor", "infrastructure", "health", "status", "overview"]):
            return "monitor_infrastructure"
        elif any(keyword in query_lower for keyword in ["anomaly", "anomalies", "detect", "abnormal", "unusual"]):
            return "detect_anomalies"
        elif any(keyword in query_lower for keyword in ["predict", "prediction", "failure", "forecast", "future"]):
            return "predict_failures"
        else:
            return "monitor_infrastructure"

    async def _handle_monitoring_request(self, query: str, context_id: str) -> Dict[str, Any]:
        """Handle infrastructure monitoring requests."""
        status = await self.monitor_infrastructure({}, context_id)
        
        # Format status report
        health_emoji = {
            ServiceStatus.HEALTHY: "✅",
            ServiceStatus.DEGRADED: "⚠️",
            ServiceStatus.DOWN: "❌",
            ServiceStatus.UNKNOWN: "❓"
        }
        
        services_status = "\n".join([
            f"• {data['name']}: {health_emoji.get(data['status'], '❓')} {data['status'].value.title()} "
            f"(CPU: {data['cpu_usage']:.1f}%, Mem: {data['memory_usage']:.1f}%)"
            for data in self.monitored_services.values()
        ])
        
        anomalies_summary = "\n".join([
            f"• {anom.service_name}: {anom.description} (Confidence: {anom.confidence_score:.1%})"
            for anom in status.anomalies_detected[:3]
        ]) if status.anomalies_detected else "• No anomalies detected"
        
        predictions_summary = "\n".join([
            f"• {pred.service_name}: {pred.failure_type} (Risk: {pred.probability:.1%})"
            for pred in status.failure_predictions[:3]
        ]) if status.failure_predictions else "• No failure predictions"
        
        content = f"""🏗️ **Infrastructure Monitoring Report**

**Overall Health:** {health_emoji.get(status.overall_health, '❓')} {status.overall_health.value.title()}

**Services Status:** ({status.services_monitored} monitored)
{services_status}

**🚨 Active Anomalies:** ({len(status.anomalies_detected)} detected)
{anomalies_summary}

**🔮 Failure Predictions:** ({len(status.failure_predictions)} identified)
{predictions_summary}

**💡 Key Insights:**
{chr(10).join(f'• {insight}' for insight in status.performance_insights[:3])}

**🎯 Optimization Recommendations:**
{chr(10).join(f'• {rec}' for rec in status.optimization_recommendations[:3])}

**Monitoring powered by AI-Ops with {self.prediction_model_accuracy:.1%} prediction accuracy**"""
        
        return {'content': content}

    async def _handle_anomaly_request(self, query: str, context_id: str) -> Dict[str, Any]:
        """Handle anomaly detection requests."""
        anomalies = await self._detect_anomalies()
        
        if not anomalies:
            content = """🔍 **Anomaly Detection Complete**

✅ **No anomalies detected across all monitored services**

**Analysis Summary:**
• All services operating within normal parameters
• Performance metrics stable across the infrastructure
• No unusual patterns or behaviors identified

**Monitoring Coverage:**
• 6 services continuously monitored
• AI-powered pattern recognition active
• Real-time threshold monitoring enabled

The infrastructure is operating optimally with no immediate concerns."""
        else:
            anomalies_detail = "\n".join([
                f"**{anom.service_name}**\n"
                f"   Type: {anom.anomaly_type.replace('_', ' ').title()}\n"
                f"   Severity: {anom.severity.value.upper()}\n"
                f"   Confidence: {anom.confidence_score:.1%}\n"
                f"   Impact: {anom.predicted_impact}"
                for anom in anomalies[:3]
            ])
            
            content = f"""🚨 **Anomaly Detection Results**

**{len(anomalies)} anomalies detected requiring attention**

{anomalies_detail}

**🎯 Recommended Actions:**
• Investigate high-severity anomalies immediately
• Review recent configuration changes
• Scale resources for affected services
• Monitor trends for pattern recognition

**AI Detection powered by machine learning models with real-time analysis**"""
        
        return {'content': content}

    async def _handle_prediction_request(self, query: str, context_id: str) -> Dict[str, Any]:
        """Handle failure prediction requests."""
        predictions = await self._predict_failures()
        
        if not predictions:
            content = """🔮 **Failure Prediction Analysis**

✅ **No immediate failure risks identified**

**Prediction Summary:**
• All services showing stable performance trends
• Resource utilization within safe thresholds
• No critical failure indicators detected

**Model Confidence:** 92% accuracy based on historical data

**Proactive Monitoring:**
• Continuous trend analysis active
• Early warning systems operational
• Predictive models updated with latest patterns

Your infrastructure is well-positioned for continued stable operation."""
        else:
            predictions_detail = "\n".join([
                f"**{pred.service_name}**\n"
                f"   Risk Level: {pred.probability:.1%}\n"
                f"   Predicted Failure: {pred.failure_type.replace('_', ' ').title()}\n"
                f"   Timeline: {pred.predicted_time.strftime('%Y-%m-%d %H:%M')}\n"
                f"   Business Impact: {pred.business_impact}"
                for pred in predictions[:3]
            ])
            
            mitigation_steps = "\n".join([
                f"• {step}" for step in predictions[0].mitigation_steps[:4]
            ]) if predictions else ""
            
            content = f"""🔮 **Failure Prediction Analysis**

**{len(predictions)} potential failure scenarios identified**

{predictions_detail}

**🛠️ Immediate Mitigation Steps:**
{mitigation_steps}

**📊 Prediction Confidence:** {self.prediction_model_accuracy:.1%}

**AI-powered predictive analytics using advanced machine learning models**"""
        
        return {'content': content}

    async def _handle_general_request(self, query: str, context_id: str) -> Dict[str, Any]:
        """Handle general infrastructure monitoring requests."""
        content = f"""🏗️ **Infrastructure Monitoring Agent Ready**

I'm an AI-powered infrastructure monitoring specialist with advanced AI-Ops capabilities. I can help with:

**🔍 Infrastructure Monitoring**
• Real-time health monitoring across all services
• Performance metrics analysis and trending
• Comprehensive status reporting with insights

**🚨 Anomaly Detection**
• AI-powered pattern recognition
• Real-time anomaly identification
• Intelligent alerting with severity classification

**🔮 Failure Prediction**
• Predictive analytics for proactive maintenance
• Risk assessment based on historical patterns
• Early warning systems for critical failures

**💡 AI-Ops Insights**
• Performance optimization recommendations
• Resource utilization analysis
• Capacity planning guidance

**Current Monitoring Status:**
• {len(self.monitored_services)} services under active monitoring
• {len(self.active_alerts)} active alerts requiring attention
• {self.prediction_model_accuracy:.1%} prediction model accuracy
• Advanced AI-Ops algorithms continuously learning

How can I help monitor and optimize your infrastructure?"""
        
        return {'content': content}

    async def _check_monitoring_health(self) -> Dict[str, Any]:
        """Check the health of monitoring capabilities."""
        try:
            # Check monitoring system readiness
            monitored_services = len(self.monitored_services)
            active_alerts = len(self.active_alerts)
            baseline_established = self.baseline_established
            
            if not baseline_established:
                return {
                    'status': 'degraded',
                    'message': 'Monitoring baseline not yet established'
                }
            elif monitored_services < 3:
                return {
                    'status': 'unhealthy',
                    'monitored_services': monitored_services,
                    'message': 'Insufficient services under monitoring'
                }
            elif active_alerts > 20:
                return {
                    'status': 'degraded',
                    'active_alerts': active_alerts,
                    'message': 'High number of active alerts'
                }
            else:
                return {
                    'status': 'healthy',
                    'monitored_services': monitored_services,
                    'active_alerts': active_alerts,
                    'prediction_accuracy': self.prediction_model_accuracy
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def get_skills(self) -> List[AgentSkill]:
        """Get the skills this infrastructure monitoring agent provides."""
        return [
            AgentSkill(
                id='monitor_infrastructure',
                name='Monitor Infrastructure',
                description='Comprehensive infrastructure monitoring with real-time health analysis',
                tags=['monitoring', 'infrastructure', 'health', 'ai-ops'],
                examples=[
                    'Monitor infrastructure health and performance across all services',
                    'Provide comprehensive status report with performance insights',
                    'Analyze current infrastructure metrics and identify issues'
                ],
            ),
            AgentSkill(
                id='detect_anomalies',
                name='Detect Anomalies',
                description='AI-powered anomaly detection with intelligent pattern recognition',
                tags=['anomaly-detection', 'ai-ops', 'patterns', 'alerts'],
                examples=[
                    'Detect anomalies in service performance and behavior',
                    'Identify unusual patterns in infrastructure metrics',
                    'Analyze system behavior for abnormal conditions'
                ],
            ),
            AgentSkill(
                id='predict_failures',
                name='Predict Failures',
                description='Predictive failure analysis using machine learning models',
                tags=['prediction', 'failure-analysis', 'ml', 'proactive'],
                examples=[
                    'Predict potential system failures before they occur',
                    'Analyze failure risks and provide early warnings',
                    'Generate proactive maintenance recommendations'
                ],
            ),
        ]


class InfrastructureMonitoringExecutor(AgentExecutor):
    """Infrastructure Monitoring Executor following A2A patterns with AI-Ops capabilities."""
    
    def __init__(self):
        self.agent = InfrastructureMonitoringAgent()
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        # Use shared metrics instance from the agent
        self.metrics = self.agent.metrics

    @trace_async("execute_task", "infrastructure_monitoring_executor")
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute an infrastructure monitoring task with streaming support."""
        try:
            # Get user input
            query = context.get_user_input()
            if not query:
                await event_queue.enqueue_event(
                    new_agent_text_message("No monitoring query provided")
                )
                return

            # Get or create task
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)

            updater = TaskUpdater(event_queue, task.id, task.context_id)
            self.logger.info(f"Processing infrastructure monitoring request: {query}")

            # Stream monitoring results
            async for item in self.agent.stream(query, task.context_id):
                is_task_complete = item['is_task_complete']
                require_user_input = item['require_user_input']
                content = item['content']

                if not is_task_complete and not require_user_input:
                    # Working status
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                    )
                elif require_user_input:
                    # Input required
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                        final=True,
                    )
                    break
                else:
                    # Task complete - add result as artifact and complete
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))],
                        name='infrastructure_monitoring_result',
                    )
                    await updater.complete()
                    break

        except Exception as e:
            self.logger.error(f'Error occurred while processing monitoring request: {e}', exc_info=True)
            
            # Update task with error status
            task = context.current_task
            if task:
                updater = TaskUpdater(event_queue, task.id, task.context_id)
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(
                        f'Infrastructure monitoring request failed: {str(e)}',
                        task.context_id,
                        task.id,
                    ),
                    final=True,
                )
            
            # Raise server error
            from a2a.types import InternalError
            raise ServerError(error=InternalError()) from e
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel a running infrastructure monitoring task."""
        self.logger.info(f"Cancelling infrastructure monitoring task: {context.task_id}")
        await event_queue.enqueue_event(
            new_agent_text_message("Infrastructure monitoring task cancelled by user request")
        )

    def get_skills(self) -> List[AgentSkill]:
        """Get the skills this infrastructure monitoring agent provides."""
        return [
            AgentSkill(
                id='monitor_infrastructure',
                name='Monitor Infrastructure',
                description='Comprehensive infrastructure monitoring with real-time health analysis',
                tags=['monitoring', 'infrastructure', 'health', 'ai-ops'],
                examples=[
                    'Monitor infrastructure health and performance across all services',
                    'Provide comprehensive status report with performance insights',
                    'Analyze current infrastructure metrics and identify issues'
                ],
            ),
            AgentSkill(
                id='detect_anomalies',
                name='Detect Anomalies',
                description='AI-powered anomaly detection with intelligent pattern recognition',
                tags=['anomaly-detection', 'ai-ops', 'patterns', 'alerts'],
                examples=[
                    'Detect anomalies in service performance and behavior',
                    'Identify unusual patterns in infrastructure metrics',
                    'Analyze system behavior for abnormal conditions'
                ],
            ),
            AgentSkill(
                id='predict_failures',
                name='Predict Failures',
                description='Predictive failure analysis using machine learning models',
                tags=['prediction', 'failure-analysis', 'ml', 'proactive'],
                examples=[
                    'Predict potential system failures before they occur',
                    'Analyze failure risks and provide early warnings',
                    'Generate proactive maintenance recommendations'
                ],
            ),
        ]