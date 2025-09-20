# 🚀 A2A Multi-Agent System - Complete Deployment Guide

This document provides comprehensive instructions for deploying the entire A2A Multi-Agent system and starting the Streamlit application.

## 📋 Overview

The deployment consists of two main scripts:

1. **`deploy_complete_a2a_system.sh`** - Complete system deployment script
2. **`start_streamlit_app.sh`** - Streamlit application startup helper

## 🎯 Quick Start

### One-Command Deployment

```bash
# Deploy everything and start Streamlit
./deploy_complete_a2a_system.sh
```

### Manual Step-by-Step

```bash
# 1. Deploy Kubernetes components only
SKIP_STREAMLIT=true ./deploy_complete_a2a_system.sh

# 2. Start Streamlit separately
./start_streamlit_app.sh
```

## 📚 Detailed Usage

### 🔧 Script 1: `deploy_complete_a2a_system.sh`

Complete system deployment with health checks and validation.

#### Features:
- ✅ Prerequisite verification (kubectl, docker, curl)
- 🐳 Docker image building (optional)
- 📊 Prometheus Operator CRDs installation
- 🏗️ Namespace and RBAC setup
- 🤖 A2A agents deployment (6 agents)
- 📈 Monitoring stack deployment (Prometheus, Grafana)
- 📊 Autoscaling configuration (HPA)
- 🏥 Comprehensive health checks
- 🎨 Streamlit application integration

#### Environment Variables:

```bash
# Kubernetes Configuration
export NAMESPACE="multi-agent-a2a"        # Target namespace
export REGISTRY=""                        # Docker registry (optional)
export VERSION="latest"                   # Image version

# Deployment Options
export SKIP_BUILD="false"                # Skip Docker image build
export SKIP_MONITORING="false"           # Skip monitoring stack
export WAIT_TIMEOUT="300"                # Deployment timeout (seconds)

# Streamlit Configuration
export STREAMLIT_PORT="8501"             # Streamlit port
```

#### Usage Examples:

```bash
# Standard deployment
./deploy_complete_a2a_system.sh

# Skip Docker build (use existing images)
SKIP_BUILD=true ./deploy_complete_a2a_system.sh

# Deploy without monitoring
SKIP_MONITORING=true ./deploy_complete_a2a_system.sh

# Custom namespace and port
NAMESPACE=my-a2a STREAMLIT_PORT=8502 ./deploy_complete_a2a_system.sh

# Production deployment with registry
REGISTRY=my-registry.com VERSION=v1.0.0 ./deploy_complete_a2a_system.sh
```

### 🎨 Script 2: `start_streamlit_app.sh`

Streamlit application startup helper with agent connectivity verification.

#### Features:
- 🔗 Automatic port-forward setup for all agents
- 🔍 Agent connectivity verification
- ⚙️ Streamlit configuration generation
- 🌍 Environment variables setup
- 📦 Python dependencies installation
- 🚀 Smart port selection
- 🧹 Automatic cleanup on exit

#### Agent Port Mappings:

| Agent | Local Port | Service |
|-------|------------|---------|
| Base Agent | 8000 | base-agent-service:8080 |
| Weather Agent | 8001 | weather-agent-service:8080 |
| Calculator Agent | 8002 | calculator-agent-service:8080 |
| Research Agent | 8003 | research-agent-service:8080 |
| Move Orchestrator | 8004 | move-orchestrator-agent-service:8080 |
| Infrastructure Monitor | 8005 | infrastructure-monitor-agent-service:8080 |

#### Usage Examples:

```bash
# Standard startup
./start_streamlit_app.sh

# Custom port
STREAMLIT_PORT=8502 ./start_streamlit_app.sh

# Custom namespace
NAMESPACE=my-a2a ./start_streamlit_app.sh
```

## 📊 System Components

### 🤖 A2A Agents (6 Total)

1. **Base Agent** (Port 8080)
   - General purpose conversational agent
   - LLM-powered query routing
   - 2-10 replicas with HPA

2. **Calculator Agent** (Port 8081)
   - Mathematical computations
   - Scientific calculations
   - 1-8 replicas with HPA

3. **Weather Agent** (Port 8082)
   - Weather information and forecasts
   - Location-based services
   - 1-5 replicas with HPA

4. **Research Agent** (Port 8083)
   - Information research and analysis
   - Web search capabilities
   - 2-12 replicas with HPA

5. **Move Orchestrator Agent** (Port 8084)
   - Complex task orchestration
   - Multi-step workflow management
   - 3-20 replicas with HPA

6. **Infrastructure Monitor Agent** (Port 8085)
   - System health monitoring
   - Performance metrics collection
   - 2-8 replicas with HPA

### 📊 Monitoring Stack

- **Prometheus** (Port 9090) - Metrics collection
- **Grafana** (Port 3000) - Visualization dashboards
- **AlertManager** (Port 9093) - Alert management
- **Node Exporter** - Node metrics
- **Kube State Metrics** - Kubernetes metrics

### 📈 Autoscaling

- **HPA v2** with custom metrics
- **CPU and Memory** based scaling
- **A2A Protocol** specific metrics
- **Request rate** and **latency** based scaling

## 🔍 Verification Commands

### Check Deployment Status

```bash
# Check all pods
kubectl get pods -n multi-agent-a2a

# Check services
kubectl get svc -n multi-agent-a2a

# Check deployments
kubectl get deployments -n multi-agent-a2a

# Check HPA status
kubectl get hpa -n multi-agent-a2a
```

### Health Checks

```bash
# System health check
./scripts/validation/health_check.sh

# Kubernetes validation
./scripts/validation/validate_kubernetes_deployment.sh

# Verify metrics
./scripts/validation/verify_metrics.py
```

### Manual Port Forwards

```bash
# Agents
kubectl port-forward -n multi-agent-a2a svc/base-agent-service 8000:8080
kubectl port-forward -n multi-agent-a2a svc/calculator-agent-service 8002:8080
kubectl port-forward -n multi-agent-a2a svc/weather-agent-service 8001:8080
kubectl port-forward -n multi-agent-a2a svc/research-agent-service 8003:8080

# Monitoring
kubectl port-forward -n multi-agent-a2a svc/grafana-service 3000:3000
kubectl port-forward -n multi-agent-a2a svc/prometheus-service 9090:9090
```

## 🏥 Health Endpoints

All agents expose health endpoints:

```bash
# Agent health checks
curl http://localhost:8000/health  # Base Agent
curl http://localhost:8001/health  # Weather Agent
curl http://localhost:8002/health  # Calculator Agent
curl http://localhost:8003/health  # Research Agent
curl http://localhost:8004/health  # Move Orchestrator
curl http://localhost:8005/health  # Infrastructure Monitor
```

## 🚨 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using a port
   lsof -i :8501
   
   # Use different port
   STREAMLIT_PORT=8502 ./start_streamlit_app.sh
   ```

2. **Agent Not Responding**
   ```bash
   # Check pod logs
   kubectl logs -f deployment/base-agent -n multi-agent-a2a
   
   # Restart deployment
   kubectl rollout restart deployment/base-agent -n multi-agent-a2a
   ```

3. **Image Pull Errors**
   ```bash
   # Build images locally
   SKIP_BUILD=false ./deploy_complete_a2a_system.sh
   ```

4. **HPA Not Scaling**
   ```bash
   # Check HPA status
   kubectl describe hpa -n multi-agent-a2a
   
   # Check metrics server
   kubectl top pods -n multi-agent-a2a
   ```

### Cleanup Commands

```bash
# Remove all resources
kubectl delete namespace multi-agent-a2a

# Clean up port-forwards
pkill -f "kubectl port-forward"

# Stop Streamlit
pkill -f "streamlit run"
```

## 📈 Scaling Operations

### Manual Scaling

```bash
# Scale specific agent
kubectl scale deployment base-agent --replicas=5 -n multi-agent-a2a

# Scale all agents
for agent in base calculator weather research move-orchestrator infrastructure-monitor; do
  kubectl scale deployment ${agent}-agent --replicas=3 -n multi-agent-a2a
done
```

### Load Testing

```bash
# CPU stress test
python scripts/testing/cpu_stress_test.py

# Load test autoscaling
python scripts/testing/load_test_autoscaling.py

# Dashboard load test
python scripts/testing/dashboard_load_test.py
```

## 🔐 Security Considerations

1. **Secrets Management**
   - Store OpenAI API keys in Kubernetes secrets
   - Use RBAC for service account permissions
   - Enable network policies for pod communication

2. **Container Security**
   - Non-root container execution
   - Minimal base images
   - Security context restrictions

3. **Network Security**
   - Service mesh integration (optional)
   - TLS encryption for internal communication
   - Ingress security policies

## 🎯 Performance Optimization

1. **Resource Limits**
   - Set appropriate CPU/memory limits
   - Use resource quotas per namespace
   - Monitor resource utilization

2. **HPA Tuning**
   - Adjust scaling thresholds
   - Configure scale-up/down policies
   - Use multiple metrics for scaling

3. **Monitoring**
   - Set up alerting rules
   - Monitor SLA metrics
   - Track business metrics

## 📊 Metrics and Monitoring

### Key Metrics

- **Request Rate**: Requests per second per agent
- **Response Time**: Average response latency
- **Error Rate**: Error percentage per agent
- **Resource Usage**: CPU/Memory utilization
- **Scaling Events**: HPA scaling activities

### Grafana Dashboards

1. **A2A Agents Overview** - System-wide metrics
2. **Individual Agent Performance** - Per-agent metrics
3. **Kubernetes Cluster** - Infrastructure metrics
4. **Business Metrics** - Application-specific KPIs

## 🎉 Success Indicators

The system is successfully deployed when:

1. ✅ All 6 agents are running and responding to health checks
2. ✅ Streamlit app is accessible at http://localhost:8501
3. ✅ HPA is configured and responsive
4. ✅ Monitoring stack is collecting metrics
5. ✅ All port-forwards are established
6. ✅ Agent routing is working through Streamlit interface

Enjoy your A2A Multi-Agent System! 🚀