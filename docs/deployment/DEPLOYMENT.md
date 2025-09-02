# 🚀 Kubernetes A2A Multi-Agent System Deployment Guide

## **Prerequisites**

### **System Requirements**
- **Kubernetes**: v1.24+ (k3s, minikube, EKS, GKE, AKS)
- **Docker**: v20.10+ for building images
- **kubectl**: Configured and connected to your cluster
- **Python**: 3.8+ (for development and testing)
- **Resources**: Minimum 4 CPU cores, 8GB RAM

### **Required Tools**
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install k3s (optional - for local development)
curl -sfL https://get.k3s.io | sh -
```

## **🔧 Configuration**

### **1. Environment Setup**
```bash
# Clone the repository
git clone <repository-url>
cd kubernetes-a2a-autoscaling

# Copy and configure environment
cp configs/.env.template .env
```

### **2. Edit Configuration**
Edit `.env` file with your specific values:
```bash
# Required: Azure OpenAI (for AI routing)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_MODEL=gpt-4

# Optional: Customize agent ports and settings
BASE_AGENT_PORT=8000
CALCULATOR_AGENT_PORT=8002
# ... other configurations
```

## **🐳 Docker Image Building**

### **Build All Images**
```bash
# Build all 6 agent images
./docker/build-scripts/build_all_images.sh

# Verify images
docker images | grep a2a
```

### **Individual Agent Builds**
```bash
# Build specific agent
docker build -t a2a-base-agent:latest -f src/agents/base/Dockerfile .
docker build -t a2a-calculator-agent:latest -f src/agents/calculator/Dockerfile .
# ... repeat for other agents
```

### **Push to Registry (Production)**
```bash
# Tag for your registry
docker tag a2a-base-agent:latest your-registry.com/a2a-base-agent:latest

# Push to registry
docker push your-registry.com/a2a-base-agent:latest
```

## **☸️ Kubernetes Deployment**

### **Step 1: Deploy Namespace and Agents**
```bash
# Create namespace and deploy agents
kubectl apply -f k8s/agents/namespace.yaml
kubectl apply -f k8s/agents/

# Verify agent deployment
kubectl get pods -n multi-agent-a2a
```

### **Step 2: Deploy Monitoring Stack**
```bash
# Install Prometheus Operator CRDs (if not already installed)
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

# Deploy monitoring components
kubectl apply -f k8s/monitoring/

# Verify monitoring deployment
kubectl get pods -n multi-agent-a2a | grep -E "(prometheus|grafana|alertmanager)"
```

### **Step 3: Deploy Autoscaling**
```bash
# Deploy HPA configurations
kubectl apply -f k8s/autoscaling/

# Verify HPA status
kubectl get hpa -n multi-agent-a2a
```

### **Step 4: Verification**
```bash
# Run comprehensive validation
./scripts/validation/validate_kubernetes_deployment.sh

# Check all components
kubectl get all -n multi-agent-a2a
```

## **🔍 Verification & Testing**

### **Health Checks**
```bash
# Test agent health endpoints
kubectl port-forward -n multi-agent-a2a svc/base-agent-service 8000:8080 &
curl http://localhost:8000/health

# Test A2A protocol compliance
curl http://localhost:8000/.well-known/agent-card.json
```

### **Load Testing**
```bash
# Run autoscaling load test
python scripts/testing/load_test_autoscaling.py --duration 300 --rps 20

# Monitor scaling behavior
watch kubectl get hpa -n multi-agent-a2a
```

### **Integration Testing**
```bash
# Run complete integration tests
python scripts/testing/test_integration_complete.py

# Test individual agents
python scripts/testing/test_calculator_agent.py
python scripts/testing/test_weather_agent.py
```

## **📊 Monitoring Access**

### **Dashboard Access**
```bash
# Grafana Dashboard
kubectl port-forward -n multi-agent-a2a svc/grafana-service 3000:3000
# Access: http://localhost:3000 (admin/admin123)

# Prometheus Metrics
kubectl port-forward -n multi-agent-a2a svc/prometheus-service 9090:9090
# Access: http://localhost:9090

# AlertManager
kubectl port-forward -n multi-agent-a2a svc/alertmanager-service 9093:9093
# Access: http://localhost:9093
```

### **Key Metrics to Monitor**
- **Agent Health**: All pods running and healthy
- **Request Rate**: `a2a_requests_per_second`
- **Response Time**: `a2a_response_time_seconds`
- **Error Rate**: `a2a_error_rate`
- **Scaling Events**: HPA scaling activities

## **🔧 Production Deployment**

### **Production Checklist**
- [ ] **Security**: Update default passwords and secrets
- [ ] **Resources**: Set appropriate resource limits
- [ ] **Monitoring**: Configure alerting webhooks
- [ ] **Backup**: Set up configuration backups
- [ ] **DNS**: Configure proper DNS entries
- [ ] **TLS**: Enable TLS for all endpoints
- [ ] **RBAC**: Implement proper access controls

### **Production Configuration Updates**
```bash
# Update image references for production registry
sed -i 's|a2a-base-agent:latest|your-registry.com/a2a-base-agent:v1.0.0|g' k8s/agents/*.yaml

# Update resource limits for production
# Edit k8s/agents/*.yaml files to set appropriate limits

# Configure production secrets
kubectl create secret generic grafana-secrets \
  --from-literal=admin-password=your-secure-password \
  -n multi-agent-a2a
```

### **High Availability Setup**
```bash
# Enable multi-replica deployments
kubectl scale deployment base-agent --replicas=3 -n multi-agent-a2a
kubectl scale deployment calculator-agent --replicas=2 -n multi-agent-a2a

# Configure pod disruption budgets
kubectl apply -f k8s/production/pod-disruption-budgets.yaml
```

## **🔄 Updates and Maintenance**

### **Rolling Updates**
```bash
# Update agent image
kubectl set image deployment/base-agent base-agent=a2a-base-agent:v1.1.0 -n multi-agent-a2a

# Monitor rollout
kubectl rollout status deployment/base-agent -n multi-agent-a2a

# Rollback if needed
kubectl rollout undo deployment/base-agent -n multi-agent-a2a
```

### **Configuration Updates**
```bash
# Update ConfigMaps
kubectl apply -f k8s/agents/

# Restart deployments to pick up changes
kubectl rollout restart deployment -n multi-agent-a2a
```

## **🚨 Troubleshooting**

### **Common Issues**

**Pods Not Starting**
```bash
# Check pod status
kubectl describe pod <pod-name> -n multi-agent-a2a

# Check logs
kubectl logs <pod-name> -n multi-agent-a2a

# Common fixes:
# - Verify image availability
# - Check resource limits
# - Validate configuration
```

**HPA Not Scaling**
```bash
# Check HPA status
kubectl describe hpa <hpa-name> -n multi-agent-a2a

# Verify metrics server
kubectl get apiservice v1beta1.metrics.k8s.io

# Check custom metrics
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1"
```

**Monitoring Issues**
```bash
# Check Prometheus targets
kubectl port-forward svc/prometheus-service 9090:9090 -n multi-agent-a2a
# Visit: http://localhost:9090/targets

# Verify ServiceMonitors
kubectl get servicemonitor -n multi-agent-a2a
```

### **Debug Commands**
```bash
# Get all resources
kubectl get all -n multi-agent-a2a

# Check events
kubectl get events -n multi-agent-a2a --sort-by='.lastTimestamp'

# Exec into pod for debugging
kubectl exec -it <pod-name> -n multi-agent-a2a -- /bin/bash
```

## **📋 Deployment Checklist**

- [ ] Prerequisites installed and configured
- [ ] Environment variables configured
- [ ] Docker images built successfully
- [ ] Kubernetes cluster accessible
- [ ] Namespace created
- [ ] Agents deployed and healthy
- [ ] Monitoring stack deployed
- [ ] Autoscaling configured
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Documentation reviewed
- [ ] Production security configured

---

**🎉 Congratulations! Your Kubernetes A2A Multi-Agent Autoscaling System is now deployed and ready for production use.**
