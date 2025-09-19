# Deployment & Operations Guide

*AI Ops Interview Preparation - Document 8/10*

## Overview

This guide covers **operational excellence** for the AI Ops multi-agent system, including deployment strategies, operational runbooks, troubleshooting procedures, and production management practices.

## Table of Contents

1. [Deployment Strategies](#deployment-strategies)
2. [Production Operations](#production-operations)
3. [Monitoring & Alerting](#monitoring--alerting)
4. [Troubleshooting Runbooks](#troubleshooting-runbooks)
5. [Capacity Planning](#capacity-planning)
6. [Disaster Recovery](#disaster-recovery)
7. [Performance Optimization](#performance-optimization)
8. [Security Operations](#security-operations)

---

## Deployment Strategies

### Blue-Green Deployment

**Implementation for A2A Agents**:
```bash
#!/bin/bash
# Blue-Green deployment script for A2A agents

NAMESPACE="multi-agent-a2a"
SERVICE_NAME="calculator-agent"
NEW_VERSION="v1.2.0"
OLD_VERSION="v1.1.0"

echo "Starting Blue-Green deployment for ${SERVICE_NAME}"

# Step 1: Deploy new version (Green) alongside existing (Blue)
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${SERVICE_NAME}-green
  namespace: ${NAMESPACE}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ${SERVICE_NAME}
      version: green
  template:
    metadata:
      labels:
        app: ${SERVICE_NAME}
        version: green
        app.kubernetes.io/version: ${NEW_VERSION}
    spec:
      containers:
      - name: ${SERVICE_NAME}
        image: a2a-agents/${SERVICE_NAME}:${NEW_VERSION}
        ports:
        - containerPort: 8080
        env:
        - name: DEPLOYMENT_COLOR
          value: "green"
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 20
EOF

# Step 2: Wait for green deployment to be ready
echo "Waiting for green deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/${SERVICE_NAME}-green -n ${NAMESPACE}

# Step 3: Run health checks on green deployment
echo "Running health checks on green deployment..."
GREEN_POD=$(kubectl get pods -n ${NAMESPACE} -l app=${SERVICE_NAME},version=green -o jsonpath='{.items[0].metadata.name}')

# A2A Protocol health check
kubectl exec -n ${NAMESPACE} ${GREEN_POD} -- curl -f http://localhost:8080/health || {
    echo "Health check failed, rolling back"
    kubectl delete deployment ${SERVICE_NAME}-green -n ${NAMESPACE}
    exit 1
}

# A2A Agent discovery check
kubectl exec -n ${NAMESPACE} ${GREEN_POD} -- curl -f http://localhost:8080/a2a/discover || {
    echo "A2A discovery failed, rolling back"
    kubectl delete deployment ${SERVICE_NAME}-green -n ${NAMESPACE}
    exit 1
}

# Step 4: Switch traffic to green (update service selector)
echo "Switching traffic to green deployment..."
kubectl patch service ${SERVICE_NAME} -n ${NAMESPACE} -p '{"spec":{"selector":{"version":"green"}}}'

# Step 5: Monitor for 5 minutes before cleanup
echo "Monitoring green deployment for 5 minutes..."
sleep 300

# Check error rates and response times
ERROR_RATE=$(kubectl exec -n monitoring prometheus-0 -- \
    promtool query instant 'rate(http_requests_total{job="'${SERVICE_NAME}'",status=~"5.."}[5m])' | \
    grep -oE '[0-9]+\.[0-9]+' | head -1)

if (( $(echo "${ERROR_RATE} > 0.01" | bc -l) )); then
    echo "Error rate too high (${ERROR_RATE}), rolling back"
    kubectl patch service ${SERVICE_NAME} -n ${NAMESPACE} -p '{"spec":{"selector":{"version":"blue"}}}'
    kubectl delete deployment ${SERVICE_NAME}-green -n ${NAMESPACE}
    exit 1
fi

# Step 6: Cleanup old blue deployment
echo "Deployment successful, cleaning up blue deployment"
kubectl delete deployment ${SERVICE_NAME}-blue -n ${NAMESPACE}

# Rename green to blue for next deployment
kubectl patch deployment ${SERVICE_NAME}-green -n ${NAMESPACE} -p '{"metadata":{"name":"'${SERVICE_NAME}'-blue"}}'

echo "Blue-Green deployment completed successfully"
```

### Canary Deployment with A2A Metrics

**Istio-based Canary Deployment**:
```yaml
# Canary deployment with traffic splitting
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: calculator-agent-canary
  namespace: multi-agent-a2a
spec:
  hosts:
  - calculator-agent
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: calculator-agent
        subset: canary
      weight: 100
  - route:
    - destination:
        host: calculator-agent
        subset: stable
      weight: 90  # 90% to stable
    - destination:
        host: calculator-agent
        subset: canary
      weight: 10  # 10% to canary
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: calculator-agent-canary
  namespace: multi-agent-a2a
spec:
  host: calculator-agent
  subsets:
  - name: stable
    labels:
      version: stable
  - name: canary
    labels:
      version: canary
```

**Automated Canary Analysis**:
```python
class CanaryAnalyzer:
    def __init__(self):
        self.prometheus_client = PrometheusClient()
        self.alertmanager_client = AlertManagerClient()
        
    async def analyze_canary_metrics(self, service_name: str, 
                                   canary_version: str) -> CanaryAnalysis:
        """Analyze canary deployment metrics."""
        
        # Key metrics to analyze
        metrics = await self._collect_canary_metrics(service_name, canary_version)
        
        analysis = CanaryAnalysis(
            service_name=service_name,
            canary_version=canary_version,
            start_time=metrics.start_time,
            current_time=datetime.utcnow()
        )
        
        # 1. Error Rate Analysis
        stable_error_rate = await self._get_error_rate(service_name, "stable")
        canary_error_rate = await self._get_error_rate(service_name, "canary")
        
        if canary_error_rate > stable_error_rate * 1.5:  # 50% increase threshold
            analysis.add_failure("error_rate", {
                "stable_rate": stable_error_rate,
                "canary_rate": canary_error_rate,
                "threshold_exceeded": True
            })
        
        # 2. Latency Analysis
        stable_p99 = await self._get_latency_percentile(service_name, "stable", 99)
        canary_p99 = await self._get_latency_percentile(service_name, "canary", 99)
        
        if canary_p99 > stable_p99 * 1.2:  # 20% increase threshold
            analysis.add_failure("latency", {
                "stable_p99": stable_p99,
                "canary_p99": canary_p99,
                "threshold_exceeded": True
            })
        
        # 3. A2A Protocol Specific Metrics
        a2a_metrics = await self._analyze_a2a_metrics(service_name, canary_version)
        if a2a_metrics.has_failures():
            analysis.add_failure("a2a_protocol", a2a_metrics.failures)
        
        # 4. Business Metrics (if applicable)
        business_metrics = await self._analyze_business_metrics(service_name, canary_version)
        if business_metrics.has_failures():
            analysis.add_failure("business_metrics", business_metrics.failures)
        
        return analysis
    
    async def _analyze_a2a_metrics(self, service_name: str, 
                                 version: str) -> A2AMetricsAnalysis:
        """Analyze A2A protocol specific metrics for canary."""
        
        # Query A2A message success rate
        a2a_success_rate = await self.prometheus_client.query(
            f'rate(a2a_messages_total{{service="{service_name}",version="{version}",status="success"}}[5m]) / '
            f'rate(a2a_messages_total{{service="{service_name}",version="{version}"}}[5m])'
        )
        
        # Query A2A discovery success rate
        discovery_success_rate = await self.prometheus_client.query(
            f'rate(a2a_discovery_requests_total{{service="{service_name}",version="{version}",status="success"}}[5m]) / '
            f'rate(a2a_discovery_requests_total{{service="{service_name}",version="{version}"}}[5m])'
        )
        
        # Query agent task completion rate
        task_completion_rate = await self.prometheus_client.query(
            f'rate(agent_tasks_completed_total{{service="{service_name}",version="{version}"}}[5m]) / '
            f'rate(agent_tasks_received_total{{service="{service_name}",version="{version}"}}[5m])'
        )
        
        analysis = A2AMetricsAnalysis()
        
        if a2a_success_rate < 0.95:  # 95% threshold
            analysis.add_failure("a2a_message_failure_rate_high", {
                "current_rate": a2a_success_rate,
                "threshold": 0.95
            })
        
        if discovery_success_rate < 0.98:  # 98% threshold
            analysis.add_failure("discovery_failure_rate_high", {
                "current_rate": discovery_success_rate,
                "threshold": 0.98
            })
        
        if task_completion_rate < 0.90:  # 90% threshold
            analysis.add_failure("task_completion_rate_low", {
                "current_rate": task_completion_rate,
                "threshold": 0.90
            })
        
        return analysis

    async def make_canary_decision(self, analysis: CanaryAnalysis) -> CanaryDecision:
        """Make automated canary promotion or rollback decision."""
        
        if analysis.has_failures():
            return CanaryDecision(
                action="rollback",
                reason=f"Canary failed: {analysis.get_failure_summary()}",
                automated=True
            )
        
        # Check if canary has run long enough
        runtime = analysis.current_time - analysis.start_time
        if runtime < timedelta(minutes=10):
            return CanaryDecision(
                action="continue",
                reason="Canary needs more runtime for analysis",
                automated=True
            )
        
        # All checks passed, promote canary
        return CanaryDecision(
            action="promote",
            reason="All canary metrics within acceptable thresholds",
            automated=True
        )
```

---

## Production Operations

### Operational Runbooks

**Agent Health Monitoring**:
```python
class AgentHealthMonitor:
    def __init__(self):
        self.k8s_client = KubernetesClient()
        self.prometheus_client = PrometheusClient()
        self.alert_manager = AlertManager()
        
    async def check_agent_health(self, agent_name: str) -> AgentHealthStatus:
        """Comprehensive agent health check."""
        
        health_status = AgentHealthStatus(agent_name=agent_name)
        
        # 1. Kubernetes Pod Health
        pods = await self.k8s_client.get_pods(
            namespace="multi-agent-a2a",
            label_selector=f"app={agent_name}"
        )
        
        healthy_pods = [p for p in pods if p.status.phase == "Running"]
        health_status.pod_health = {
            "total_pods": len(pods),
            "healthy_pods": len(healthy_pods),
            "ready_pods": len([p for p in healthy_pods if p.status.ready]),
            "health_percentage": len(healthy_pods) / max(len(pods), 1) * 100
        }
        
        # 2. A2A Protocol Health
        a2a_health = await self._check_a2a_health(agent_name)
        health_status.a2a_health = a2a_health
        
        # 3. Resource Utilization
        resource_usage = await self._check_resource_usage(agent_name)
        health_status.resource_usage = resource_usage
        
        # 4. Error Rates
        error_rates = await self._check_error_rates(agent_name)
        health_status.error_rates = error_rates
        
        # 5. Performance Metrics
        performance = await self._check_performance_metrics(agent_name)
        health_status.performance = performance
        
        # Calculate overall health score
        health_status.overall_score = self._calculate_health_score(health_status)
        
        # Generate alerts if needed
        if health_status.overall_score < 80:
            await self._generate_health_alert(health_status)
        
        return health_status
    
    async def _check_a2a_health(self, agent_name: str) -> Dict[str, Any]:
        """Check A2A protocol specific health."""
        
        # Check if agent is discoverable
        discovery_query = f'up{{job="{agent_name}-discovery"}}'
        discovery_up = await self.prometheus_client.query(discovery_query)
        
        # Check A2A message processing rate
        message_rate_query = f'rate(a2a_messages_processed_total{{service="{agent_name}"}}[5m])'
        message_rate = await self.prometheus_client.query(message_rate_query)
        
        # Check agent capabilities registration
        capabilities_query = f'a2a_agent_capabilities_count{{service="{agent_name}"}}'
        capabilities_count = await self.prometheus_client.query(capabilities_query)
        
        return {
            "discoverable": discovery_up > 0,
            "message_processing_rate": message_rate,
            "registered_capabilities": capabilities_count,
            "last_heartbeat": await self._get_last_heartbeat(agent_name)
        }
    
    async def auto_remediate_agent_issues(self, health_status: AgentHealthStatus):
        """Automatic remediation for common agent issues."""
        
        agent_name = health_status.agent_name
        
        # 1. Restart unhealthy pods
        if health_status.pod_health["health_percentage"] < 50:
            await self._restart_unhealthy_pods(agent_name)
        
        # 2. Scale up if resource constrained
        if health_status.resource_usage.get("cpu_utilization", 0) > 90:
            await self._scale_up_agent(agent_name)
        
        # 3. Clear stuck message queues
        if health_status.performance.get("queue_depth", 0) > 1000:
            await self._clear_message_queues(agent_name)
        
        # 4. Re-register with discovery service
        if not health_status.a2a_health.get("discoverable", True):
            await self._re_register_agent(agent_name)

class SystemHealthDashboard:
    def __init__(self):
        self.health_monitor = AgentHealthMonitor()
        
    async def generate_health_report(self) -> SystemHealthReport:
        """Generate comprehensive system health report."""
        
        agents = ["base-agent", "calculator-agent", "weather-agent", 
                 "research-agent", "move-orchestrator", "infrastructure-monitor"]
        
        report = SystemHealthReport(timestamp=datetime.utcnow())
        
        # Check each agent
        for agent in agents:
            agent_health = await self.health_monitor.check_agent_health(agent)
            report.add_agent_health(agent_health)
        
        # System-wide metrics
        report.system_metrics = await self._collect_system_metrics()
        
        # Infrastructure health
        report.infrastructure_health = await self._check_infrastructure_health()
        
        # Generate recommendations
        report.recommendations = await self._generate_recommendations(report)
        
        return report
    
    async def _check_infrastructure_health(self) -> Dict[str, Any]:
        """Check underlying infrastructure health."""
        
        return {
            "kubernetes_cluster": await self._check_k8s_cluster_health(),
            "prometheus_stack": await self._check_monitoring_health(),
            "network_connectivity": await self._check_network_health(),
            "storage_systems": await self._check_storage_health()
        }
```

### Incident Response Procedures

**Automated Incident Detection and Response**:
```python
class IncidentResponseManager:
    def __init__(self):
        self.alert_manager = AlertManager()
        self.notification_service = NotificationService()
        self.runbook_executor = RunbookExecutor()
        
    async def handle_alert(self, alert: Alert) -> IncidentResponse:
        """Handle incoming alert and trigger appropriate response."""
        
        # Classify incident severity
        severity = self._classify_incident_severity(alert)
        
        # Create incident record
        incident = Incident(
            id=str(uuid.uuid4()),
            alert=alert,
            severity=severity,
            created_at=datetime.utcnow(),
            status="open"
        )
        
        # Execute automated remediation if available
        remediation_result = await self._execute_automated_remediation(incident)
        
        if remediation_result.success:
            incident.status = "auto_resolved"
            incident.resolution = remediation_result.description
        else:
            # Escalate to on-call engineer
            await self._escalate_incident(incident)
        
        # Log incident
        await self._log_incident(incident)
        
        return IncidentResponse(incident=incident, remediation=remediation_result)
    
    async def _execute_automated_remediation(self, incident: Incident) -> RemediationResult:
        """Execute automated remediation based on incident type."""
        
        alert_name = incident.alert.name
        
        remediation_playbooks = {
            "AgentHighErrorRate": self._remediate_high_error_rate,
            "AgentHighLatency": self._remediate_high_latency,
            "AgentPodCrashLooping": self._remediate_pod_crashes,
            "A2ADiscoveryFailure": self._remediate_discovery_failure,
            "HighMemoryUsage": self._remediate_memory_pressure,
            "DiskSpaceRunningLow": self._remediate_disk_space
        }
        
        if alert_name in remediation_playbooks:
            return await remediation_playbooks[alert_name](incident)
        
        return RemediationResult(
            success=False,
            description=f"No automated remediation available for {alert_name}"
        )
    
    async def _remediate_high_error_rate(self, incident: Incident) -> RemediationResult:
        """Remediate high error rate incident."""
        
        agent_name = incident.alert.labels.get("service")
        
        steps_executed = []
        
        try:
            # 1. Check recent deployments
            recent_deployment = await self._check_recent_deployments(agent_name)
            if recent_deployment:
                # Rollback recent deployment
                await self._rollback_deployment(agent_name, recent_deployment)
                steps_executed.append(f"Rolled back deployment {recent_deployment}")
            
            # 2. Restart unhealthy pods
            restarted_pods = await self._restart_unhealthy_pods(agent_name)
            steps_executed.append(f"Restarted {len(restarted_pods)} pods")
            
            # 3. Clear error-causing message queues
            cleared_queues = await self._clear_error_queues(agent_name)
            steps_executed.append(f"Cleared {len(cleared_queues)} error queues")
            
            # 4. Wait and verify error rate reduction
            await asyncio.sleep(120)  # Wait 2 minutes
            
            current_error_rate = await self._get_current_error_rate(agent_name)
            if current_error_rate < 0.05:  # Below 5% error rate
                return RemediationResult(
                    success=True,
                    description=f"Successfully reduced error rate to {current_error_rate:.2%}. "
                               f"Steps: {'; '.join(steps_executed)}"
                )
            else:
                return RemediationResult(
                    success=False,
                    description=f"Error rate still high ({current_error_rate:.2%}) after remediation. "
                               f"Steps attempted: {'; '.join(steps_executed)}"
                )
                
        except Exception as e:
            return RemediationResult(
                success=False,
                description=f"Remediation failed with error: {e}. "
                           f"Steps completed: {'; '.join(steps_executed)}"
            )
```

---

## Troubleshooting Runbooks

### A2A Protocol Issues

**Agent Discovery Failures**:
```bash
#!/bin/bash
# Runbook: A2A Agent Discovery Troubleshooting

AGENT_NAME=$1
NAMESPACE="multi-agent-a2a"

echo "=== A2A Agent Discovery Troubleshooting for $AGENT_NAME ==="

# Step 1: Check if agent pods are running
echo "1. Checking agent pod status..."
kubectl get pods -n $NAMESPACE -l app=$AGENT_NAME

POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=$AGENT_NAME -o jsonpath='{.items[0].metadata.name}')

if [ -z "$POD_NAME" ]; then
    echo "ERROR: No pods found for agent $AGENT_NAME"
    exit 1
fi

# Step 2: Check agent health endpoint
echo "2. Checking agent health endpoint..."
kubectl exec -n $NAMESPACE $POD_NAME -- curl -f http://localhost:8080/health
if [ $? -ne 0 ]; then
    echo "ERROR: Health endpoint not responding"
fi

# Step 3: Check A2A discovery endpoint
echo "3. Checking A2A discovery endpoint..."
kubectl exec -n $NAMESPACE $POD_NAME -- curl -f http://localhost:8080/a2a/discover
if [ $? -ne 0 ]; then
    echo "ERROR: A2A discovery endpoint not responding"
fi

# Step 4: Check service registration in etcd/consul
echo "4. Checking service registration..."
kubectl exec -n $NAMESPACE $POD_NAME -- nslookup $AGENT_NAME

# Step 5: Check network connectivity to other agents
echo "5. Testing inter-agent connectivity..."
OTHER_AGENTS=("base-agent" "calculator-agent" "weather-agent")
for other_agent in "${OTHER_AGENTS[@]}"; do
    if [ "$other_agent" != "$AGENT_NAME" ]; then
        echo "Testing connectivity to $other_agent..."
        kubectl exec -n $NAMESPACE $POD_NAME -- curl -f http://$other_agent:8080/health
    fi
done

# Step 6: Check agent logs for discovery errors
echo "6. Checking agent logs for discovery errors..."
kubectl logs -n $NAMESPACE $POD_NAME --tail=100 | grep -i "discovery\|register\|error"

# Step 7: Check Prometheus metrics
echo "7. Checking discovery metrics..."
PROMETHEUS_POD=$(kubectl get pods -n monitoring -l app=prometheus -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n monitoring $PROMETHEUS_POD -- promtool query instant \
    "a2a_discovery_requests_total{service=\"$AGENT_NAME\"}"

# Step 8: Remediation suggestions
echo "8. Remediation suggestions:"
echo "   - If health check fails: kubectl delete pod -n $NAMESPACE $POD_NAME"
echo "   - If discovery endpoint fails: Check agent configuration"
echo "   - If network connectivity fails: Check network policies"
echo "   - If metrics show discovery failures: Check service mesh configuration"
```

**Message Processing Issues**:
```python
class A2AMessageDiagnostics:
    def __init__(self):
        self.k8s_client = KubernetesClient()
        self.prometheus_client = PrometheusClient()
        
    async def diagnose_message_processing_issues(self, agent_name: str) -> DiagnosisReport:
        """Diagnose A2A message processing issues."""
        
        report = DiagnosisReport(agent_name=agent_name)
        
        # 1. Check message queue depths
        queue_metrics = await self._check_message_queues(agent_name)
        report.add_finding("message_queues", queue_metrics)
        
        # 2. Check message processing rates
        processing_rates = await self._check_processing_rates(agent_name)
        report.add_finding("processing_rates", processing_rates)
        
        # 3. Check for stuck messages
        stuck_messages = await self._find_stuck_messages(agent_name)
        report.add_finding("stuck_messages", stuck_messages)
        
        # 4. Check memory and CPU usage during processing
        resource_usage = await self._check_processing_resources(agent_name)
        report.add_finding("resource_usage", resource_usage)
        
        # 5. Check for serialization/deserialization errors
        serialization_errors = await self._check_serialization_errors(agent_name)
        report.add_finding("serialization_errors", serialization_errors)
        
        # Generate remediation recommendations
        report.recommendations = self._generate_remediation_recommendations(report)
        
        return report
    
    async def _check_message_queues(self, agent_name: str) -> Dict[str, Any]:
        """Check message queue status and depths."""
        
        # Query Prometheus for queue depth metrics
        queue_depth = await self.prometheus_client.query(
            f'a2a_message_queue_depth{{service="{agent_name}"}}'
        )
        
        # Query for queue processing latency
        queue_latency = await self.prometheus_client.query(
            f'histogram_quantile(0.95, '
            f'rate(a2a_message_queue_duration_seconds_bucket{{service="{agent_name}"}}[5m]))'
        )
        
        # Check for dead letter queues
        dlq_count = await self.prometheus_client.query(
            f'a2a_dead_letter_queue_size{{service="{agent_name}"}}'
        )
        
        return {
            "current_depth": queue_depth,
            "p95_latency": queue_latency,
            "dead_letter_count": dlq_count,
            "queue_status": "healthy" if queue_depth < 100 else "congested"
        }
    
    async def _find_stuck_messages(self, agent_name: str) -> List[Dict[str, Any]]:
        """Find messages that have been processing for too long."""
        
        # Get pod logs to find long-running message processing
        pods = await self.k8s_client.get_pods(
            namespace="multi-agent-a2a",
            label_selector=f"app={agent_name}"
        )
        
        stuck_messages = []
        
        for pod in pods:
            logs = await self.k8s_client.get_pod_logs(
                pod.metadata.name,
                namespace="multi-agent-a2a",
                tail_lines=1000
            )
            
            # Parse logs for message processing start times
            import re
            message_pattern = r'Processing message (\w+) started at ([\d\-T:\.Z]+)'
            
            for line in logs.split('\n'):
                match = re.search(message_pattern, line)
                if match:
                    message_id = match.group(1)
                    start_time = datetime.fromisoformat(match.group(2).replace('Z', '+00:00'))
                    
                    # Check if message has been processing for more than 5 minutes
                    if (datetime.utcnow().replace(tzinfo=timezone.utc) - start_time).seconds > 300:
                        stuck_messages.append({
                            "message_id": message_id,
                            "start_time": start_time.isoformat(),
                            "processing_duration": (datetime.utcnow().replace(tzinfo=timezone.utc) - start_time).seconds,
                            "pod_name": pod.metadata.name
                        })
        
        return stuck_messages
    
    def _generate_remediation_recommendations(self, report: DiagnosisReport) -> List[str]:
        """Generate remediation recommendations based on diagnosis."""
        
        recommendations = []
        
        # Queue depth issues
        queue_metrics = report.findings.get("message_queues", {})
        if queue_metrics.get("current_depth", 0) > 100:
            recommendations.append(
                "HIGH: Message queue congested. Consider scaling up agent replicas."
            )
        
        # Stuck messages
        stuck_messages = report.findings.get("stuck_messages", [])
        if len(stuck_messages) > 0:
            recommendations.append(
                f"HIGH: {len(stuck_messages)} stuck messages found. "
                "Consider restarting pods or implementing message timeout."
            )
        
        # High processing latency
        processing_rates = report.findings.get("processing_rates", {})
        if processing_rates.get("p95_latency", 0) > 5.0:  # 5 seconds
            recommendations.append(
                "MEDIUM: High message processing latency detected. "
                "Check resource allocation and message complexity."
            )
        
        # Resource constraints
        resource_usage = report.findings.get("resource_usage", {})
        if resource_usage.get("cpu_utilization", 0) > 90:
            recommendations.append(
                "MEDIUM: High CPU utilization during message processing. "
                "Consider vertical scaling or optimizing message handlers."
            )
        
        return recommendations
```

This deployment and operations guide provides practical tools for managing the AI Ops system in production. Let me create the final document to complete your interview preparation package.