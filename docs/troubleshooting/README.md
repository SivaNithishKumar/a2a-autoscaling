# Troubleshooting Guide

This comprehensive troubleshooting guide helps diagnose and resolve common issues in the Multi-Agent A2A Autoscaling Platform.

## 🚨 Common Issues & Solutions

### Deployment Issues

#### Pod Startup Failures
**Symptoms**: Pods stuck in `Pending`, `CrashLoopBackOff`, or `Error` states

**Diagnosis**:
```bash
# Check pod status
kubectl get pods -n multi-agent-a2a

# Describe problematic pod
kubectl describe pod <pod-name> -n multi-agent-a2a

# Check logs
kubectl logs <pod-name> -n multi-agent-a2a --previous
```

**Common Causes & Solutions**:

1. **Image Pull Errors**
   ```bash
   # Verify image exists
   docker images | grep a2a-
   
   # Rebuild if missing
   ./docker/build-scripts/build_all_images.sh
   ```

2. **Resource Constraints**
   ```bash
   # Check node resources
   kubectl describe nodes
   
   # Adjust resource requests in deployment YAML
   kubectl edit deployment base-agent -n multi-agent-a2a
   ```

3. **Configuration Issues**
   ```bash
   # Check ConfigMaps and Secrets
   kubectl get configmaps -n multi-agent-a2a
   kubectl get secrets -n multi-agent-a2a
   
   # Verify environment variables
   kubectl exec -it <pod-name> -n multi-agent-a2a -- env | grep -E "AZURE|A2A"
   ```

#### Service Discovery Problems
**Symptoms**: Agents cannot reach each other or external services

**Diagnosis**:
```bash
# Test service connectivity
kubectl exec -it <pod-name> -n multi-agent-a2a -- nslookup base-agent-service

# Check service endpoints
kubectl get endpoints -n multi-agent-a2a

# Test HTTP connectivity
kubectl exec -it <pod-name> -n multi-agent-a2a -- curl http://base-agent-service:8080/health
```

**Solutions**:
1. Verify service definitions match deployment labels
2. Check network policies aren't blocking traffic
3. Ensure DNS resolution is working in cluster

### Agent Communication Issues

#### A2A Protocol Errors
**Symptoms**: Agents fail to communicate, timeout errors, message delivery failures

**Error Examples**:
```
ConnectionError: Failed to connect to agent at http://calculator-agent:8081
TimeoutError: Request timed out after 30 seconds
ProtocolError: Invalid A2A message format
```

**Diagnosis Steps**:
```bash
# Check agent health
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health

# Test A2A message flow
python scripts/testing/test_integration_complete.py

# Monitor agent logs
kubectl logs -f deployment/base-agent -n multi-agent-a2a
```

**Solutions**:
1. **Connection Issues**:
   ```bash
   # Verify service endpoints
   kubectl get svc -n multi-agent-a2a
   
   # Check if agents are responding
   kubectl port-forward svc/base-agent-service 8080:8080
   curl http://localhost:8080/health
   ```

2. **Message Format Issues**:
   ```python
   # Validate message structure
   from a2a.types import Message, TextPart, Part
   
   # Correct format
   message = Message(parts=[Part(root=TextPart(text="Hello"))])
   ```

3. **Timeout Issues**:
   ```yaml
   # Increase timeout in agent configuration
   readinessProbe:
     timeoutSeconds: 10
   livenessProbe:
     timeoutSeconds: 10
   ```

### Performance Issues

#### High Response Latency
**Symptoms**: Slow response times, timeouts, poor user experience

**Diagnosis**:
```bash
# Check resource utilization
kubectl top pods -n multi-agent-a2a
kubectl top nodes

# Monitor metrics
kubectl port-forward svc/prometheus-service 9090:9090
# Visit http://localhost:9090 and query:
# rate(a2a_request_duration_seconds_sum[5m]) / rate(a2a_request_duration_seconds_count[5m])
```

**Solutions**:
1. **Scale Up Resources**:
   ```bash
   # Increase CPU/memory limits
   kubectl patch deployment base-agent -n multi-agent-a2a -p '{"spec":{"template":{"spec":{"containers":[{"name":"base-agent","resources":{"limits":{"cpu":"1000m","memory":"1Gi"}}}]}}}}'
   ```

2. **Horizontal Scaling**:
   ```bash
   # Force scale up
   kubectl scale deployment base-agent --replicas=5 -n multi-agent-a2a
   
   # Check HPA status
   kubectl get hpa -n multi-agent-a2a
   ```

3. **Optimize Agent Code**:
   ```python
   # Add connection pooling
   import aiohttp
   
   connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
   session = aiohttp.ClientSession(connector=connector)
   ```

#### Autoscaling Not Working
**Symptoms**: Pods not scaling up/down despite load changes

**Diagnosis**:
```bash
# Check HPA status
kubectl describe hpa -n multi-agent-a2a

# Verify metrics server
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods

# Check custom metrics
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/multi-agent-a2a/pods/*/a2a_requests_per_second"
```

**Solutions**:
1. **Install Metrics Server**:
   ```bash
   kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
   ```

2. **Fix Custom Metrics**:
   ```bash
   # Verify Prometheus adapter
   kubectl get pods -n monitoring
   kubectl logs -f deployment/prometheus-adapter -n monitoring
   ```

3. **Adjust HPA Configuration**:
   ```yaml
   # Lower thresholds for testing
   spec:
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 50  # Lower from 70
   ```

### Monitoring & Observability Issues

#### Missing Metrics
**Symptoms**: Grafana dashboards show no data, Prometheus targets down

**Diagnosis**:
```bash
# Check Prometheus targets
kubectl port-forward svc/prometheus-service 9090:9090
# Visit http://localhost:9090/targets

# Check ServiceMonitor
kubectl get servicemonitor -n multi-agent-a2a

# Test metrics endpoint
curl http://localhost:8080/metrics
```

**Solutions**:
1. **Fix ServiceMonitor Labels**:
   ```yaml
   spec:
     selector:
       matchLabels:
         app: base-agent  # Must match service labels
   ```

2. **Verify Metrics Port**:
   ```yaml
   # In deployment spec
   ports:
   - containerPort: 8080
     name: metrics  # Name must match ServiceMonitor
   ```

3. **Check Prometheus Configuration**:
   ```bash
   kubectl exec -it prometheus-0 -n monitoring -- cat /etc/prometheus/prometheus.yml
   ```

#### Grafana Dashboard Issues
**Symptoms**: Empty dashboards, connection errors to Prometheus

**Diagnosis**:
```bash
# Check Grafana logs
kubectl logs -f deployment/grafana -n monitoring

# Test Prometheus connection from Grafana
kubectl exec -it deployment/grafana -n monitoring -- wget -O- http://prometheus-service:9090/api/v1/query?query=up
```

**Solutions**:
1. **Configure Data Source**:
   ```yaml
   # Grafana datasource
   url: http://prometheus-service:9090
   access: proxy
   ```

2. **Import Dashboards**:
   ```bash
   # Import from configmap
   kubectl apply -f k8s/monitoring/a2a-agents-dashboard.yaml
   ```

### Streamlit Application Issues

#### Connection Failures
**Symptoms**: Cannot connect to agents, routing errors, UI not responsive

**Diagnosis**:
```bash
# Check Streamlit logs
kubectl logs -f deployment/streamlit-app -n multi-agent-a2a

# Test agent connectivity from Streamlit pod
kubectl exec -it deployment/streamlit-app -n multi-agent-a2a -- curl http://base-agent-service:8080/health
```

**Solutions**:
1. **Fix Service Configuration**:
   ```python
   # In streamlit_a2a_app.py
   AGENT_ENDPOINTS = {
       "base": {
           "url": "http://base-agent-service:8080",  # Use service name
           # ...
       }
   }
   ```

2. **Check Environment Variables**:
   ```bash
   kubectl exec -it deployment/streamlit-app -n multi-agent-a2a -- env | grep AGENT
   ```

#### LLM Routing Issues
**Symptoms**: Poor agent selection, routing to wrong agents

**Diagnosis**:
```python
# Test routing logic
from src.clients.ai_agent_router import AIAgentRouter

router = AIAgentRouter()
result = await router.route_query("Calculate 2+2")
print(f"Selected agent: {result.agent_name}, confidence: {result.confidence}")
```

**Solutions**:
1. **Verify Azure OpenAI Configuration**:
   ```bash
   # Check environment variables
   echo $AZURE_OPENAI_ENDPOINT
   echo $AZURE_OPENAI_API_KEY
   ```

2. **Improve Routing Prompts**:
   ```python
   # Enhance agent descriptions and specialties
   agents = {
       "calculator": {
           "specialties": ["math", "calculations", "equations", "numbers", "arithmetic"]
       }
   }
   ```

## 🔍 Debugging Tools & Techniques

### Log Analysis

#### Structured Log Queries
```bash
# Filter by log level
kubectl logs deployment/base-agent -n multi-agent-a2a | grep ERROR

# Filter by component
kubectl logs deployment/base-agent -n multi-agent-a2a | grep "router"

# Follow logs in real-time
kubectl logs -f deployment/base-agent -n multi-agent-a2a --tail=100
```

#### Log Aggregation (ELK Stack)
```bash
# If using centralized logging
curl -X GET "elasticsearch:9200/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"kubernetes.namespace": "multi-agent-a2a"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}'
```

### Performance Profiling

#### CPU Profiling
```python
# Add to agent code for profiling
import cProfile
import pstats

def profile_agent_execution():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Agent execution code here
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

#### Memory Profiling
```python
# Memory usage monitoring
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")
```

### Network Debugging

#### Packet Capture
```bash
# Capture traffic between agents
kubectl exec -it base-agent-pod -n multi-agent-a2a -- tcpdump -i eth0 host calculator-agent-service

# Analyze with Wireshark
kubectl exec -it base-agent-pod -n multi-agent-a2a -- tcpdump -i eth0 -w /tmp/capture.pcap
kubectl cp multi-agent-a2a/base-agent-pod:/tmp/capture.pcap ./capture.pcap
```

#### Service Mesh Debugging (if using Istio)
```bash
# Check Envoy proxy logs
kubectl logs -f base-agent-pod -c istio-proxy -n multi-agent-a2a

# Verify mTLS
istioctl authn tls-check base-agent-service.multi-agent-a2a.svc.cluster.local
```

## 🧪 Testing & Validation

### Health Check Scripts
```bash
# Comprehensive health check
./scripts/validation/health_check.sh

# Individual component checks
./scripts/validation/validate_kubernetes_deployment.sh
python scripts/validation/verify_metrics.py
```

### Load Testing
```bash
# Stress test autoscaling
python scripts/testing/load_test_autoscaling.py --duration 300 --rps 50

# CPU stress test
python scripts/testing/cpu_stress_test.py --target-agent base --duration 180
```

### Integration Testing
```bash
# Full integration test suite
python scripts/testing/test_integration_complete.py

# Test specific agent
python scripts/testing/test_infrastructure_monitor.py
```

## 📊 Monitoring & Alerting

### Key Metrics to Monitor

#### System Health Metrics
- Pod restart count
- Memory and CPU utilization
- Network errors and latency
- Disk I/O and storage

#### Application Metrics
- Request rate and latency
- Error rate by agent and skill
- Task completion rate
- Queue depth and processing time

#### Business Metrics
- User engagement rate
- Conversation completion rate
- Agent utilization efficiency
- Response quality scores

### Alert Rules
```yaml
# Prometheus alert rules
groups:
- name: a2a-agents
  rules:
  - alert: HighErrorRate
    expr: rate(a2a_errors_total[5m]) / rate(a2a_requests_total[5m]) > 0.05
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate in A2A agents"
      
  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(a2a_request_duration_seconds_bucket[5m])) > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High request latency"
```

## 🔐 Security Troubleshooting

### Authentication Issues
```bash
# Check service account tokens
kubectl get serviceaccount -n multi-agent-a2a
kubectl describe serviceaccount default -n multi-agent-a2a

# Verify RBAC
kubectl auth can-i create pods --as=system:serviceaccount:multi-agent-a2a:default
```

### Network Policy Issues
```bash
# Test network connectivity
kubectl exec -it test-pod -n multi-agent-a2a -- nc -zv base-agent-service 8080

# Check network policies
kubectl get networkpolicies -n multi-agent-a2a
kubectl describe networkpolicy allow-agent-communication -n multi-agent-a2a
```

## 🆘 Emergency Procedures

### System Recovery

#### Complete System Reset
```bash
# Delete all resources
kubectl delete namespace multi-agent-a2a

# Redeploy from scratch
kubectl apply -f k8s/agents/namespace.yaml
kubectl apply -f k8s/agents/
kubectl apply -f k8s/monitoring/
kubectl apply -f k8s/autoscaling/
```

#### Rollback Deployment
```bash
# Check rollout history
kubectl rollout history deployment/base-agent -n multi-agent-a2a

# Rollback to previous version
kubectl rollout undo deployment/base-agent -n multi-agent-a2a

# Rollback to specific revision
kubectl rollout undo deployment/base-agent --to-revision=2 -n multi-agent-a2a
```

#### Data Recovery
```bash
# Backup conversation data (if persistent)
kubectl exec -it postgres-pod -n multi-agent-a2a -- pg_dump conversations > backup.sql

# Restore from backup
kubectl exec -i postgres-pod -n multi-agent-a2a -- psql < backup.sql
```

### Incident Response

#### High Severity Incident (P1)
1. **Immediate Assessment** (0-5 minutes)
   - Check overall system status
   - Identify affected components
   - Assess user impact

2. **Initial Response** (5-15 minutes)
   - Scale up resources if needed
   - Enable circuit breakers
   - Notify stakeholders

3. **Investigation** (15-60 minutes)
   - Analyze logs and metrics
   - Identify root cause
   - Implement fix or workaround

4. **Recovery** (60+ minutes)
   - Deploy fix
   - Verify system stability
   - Monitor for regression

#### Communication Template
```
INCIDENT: A2A Multi-Agent System Degradation
STATUS: Investigating/Identified/Resolved
IMPACT: [Description of user impact]
TIMELINE: 
- 10:30 UTC: Issue detected
- 10:35 UTC: Team notified
- 10:45 UTC: Root cause identified
NEXT UPDATE: 15 minutes
```

## 📞 Getting Help

### Internal Resources
- **Documentation**: Complete system documentation in `/docs`
- **Scripts**: Automated troubleshooting in `/scripts`
- **Monitoring**: Grafana dashboards for real-time insights

### External Resources
- **A2A Protocol**: [Google A2A Documentation](https://github.com/google/a2a)
- **Kubernetes**: [Kubernetes Troubleshooting Guide](https://kubernetes.io/docs/tasks/debug-application-cluster/)
- **Prometheus**: [Prometheus Troubleshooting](https://prometheus.io/docs/prometheus/latest/troubleshooting/)

### Community Support
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Community discussions and Q&A
- **Stack Overflow**: Tag questions with `a2a-protocol` and `kubernetes`

Remember: Always check logs first, verify configuration second, and test fixes in a development environment before applying to production.
