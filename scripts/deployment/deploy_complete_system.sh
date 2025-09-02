#!/bin/bash
# Complete Kubernetes A2A Multi-Agent System Deployment Script
# This script deploys the entire system from the consolidated structure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-multi-agent-a2a}"
REGISTRY="${REGISTRY:-}"
VERSION="${VERSION:-latest}"
SKIP_BUILD="${SKIP_BUILD:-false}"
SKIP_MONITORING="${SKIP_MONITORING:-false}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-300}"

echo -e "${BLUE}🚀 Deploying Kubernetes A2A Multi-Agent Autoscaling System${NC}"
echo "Namespace: $NAMESPACE"
echo "Registry: $REGISTRY"
echo "Version: $VERSION"
echo "Skip Build: $SKIP_BUILD"
echo "Skip Monitoring: $SKIP_MONITORING"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for deployment
wait_for_deployment() {
    local deployment=$1
    local namespace=$2
    local timeout=${3:-300}
    
    echo -e "${YELLOW}⏳ Waiting for deployment $deployment to be ready...${NC}"
    kubectl wait --for=condition=available --timeout=${timeout}s deployment/$deployment -n $namespace
}

# Function to wait for pods
wait_for_pods() {
    local label=$1
    local namespace=$2
    local timeout=${3:-300}
    
    echo -e "${YELLOW}⏳ Waiting for pods with label $label to be ready...${NC}"
    kubectl wait --for=condition=ready --timeout=${timeout}s pod -l $label -n $namespace
}

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

if ! command_exists kubectl; then
    echo -e "${RED}❌ kubectl is not installed${NC}"
    exit 1
fi

if ! command_exists docker && [ "$SKIP_BUILD" = "false" ]; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Check if kubectl is connected to a cluster
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo -e "${RED}❌ kubectl is not connected to a Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Step 1: Build Docker images (if not skipped)
if [ "$SKIP_BUILD" = "false" ]; then
    echo -e "${BLUE}🔨 Building Docker images...${NC}"
    if [ -f "docker/build-scripts/build_all_images.sh" ]; then
        chmod +x docker/build-scripts/build_all_images.sh
        REGISTRY="$REGISTRY" VERSION="$VERSION" ./docker/build-scripts/build_all_images.sh
    else
        echo -e "${YELLOW}⚠️ Build script not found, skipping image build${NC}"
    fi
else
    echo -e "${YELLOW}⏭️ Skipping Docker image build${NC}"
fi

# Step 2: Install Prometheus Operator CRDs (if monitoring not skipped)
if [ "$SKIP_MONITORING" = "false" ]; then
    echo -e "${BLUE}📊 Installing Prometheus Operator CRDs...${NC}"
    if ! kubectl get crd servicemonitors.monitoring.coreos.com >/dev/null 2>&1; then
        echo -e "${YELLOW}⏳ Installing Prometheus Operator CRDs...${NC}"
        kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml || true
        sleep 10
    else
        echo -e "${GREEN}✅ Prometheus Operator CRDs already installed${NC}"
    fi
fi

# Step 3: Deploy namespace and RBAC
echo -e "${BLUE}🏗️ Deploying namespace and RBAC...${NC}"
kubectl apply -f k8s/agents/namespace.yaml

# Step 4: Deploy agents
echo -e "${BLUE}🤖 Deploying A2A agents...${NC}"
kubectl apply -f k8s/agents/

# Wait for agent deployments
echo -e "${YELLOW}⏳ Waiting for agent deployments to be ready...${NC}"
for agent in base calculator weather research move-orchestrator infrastructure-monitor; do
    if kubectl get deployment ${agent}-agent -n $NAMESPACE >/dev/null 2>&1; then
        wait_for_deployment "${agent}-agent" "$NAMESPACE" "$WAIT_TIMEOUT"
    fi
done

# Step 5: Deploy monitoring stack (if not skipped)
if [ "$SKIP_MONITORING" = "false" ]; then
    echo -e "${BLUE}📊 Deploying monitoring stack...${NC}"
    kubectl apply -f k8s/monitoring/
    
    # Wait for monitoring components
    echo -e "${YELLOW}⏳ Waiting for monitoring components...${NC}"
    sleep 30  # Give time for monitoring components to start
    
    if kubectl get deployment prometheus -n $NAMESPACE >/dev/null 2>&1; then
        wait_for_deployment "prometheus" "$NAMESPACE" "$WAIT_TIMEOUT"
    fi
    
    if kubectl get deployment grafana -n $NAMESPACE >/dev/null 2>&1; then
        wait_for_deployment "grafana" "$NAMESPACE" "$WAIT_TIMEOUT"
    fi
else
    echo -e "${YELLOW}⏭️ Skipping monitoring stack deployment${NC}"
fi

# Step 6: Deploy autoscaling
echo -e "${BLUE}📈 Deploying autoscaling configurations...${NC}"
kubectl apply -f k8s/autoscaling/

# Step 7: Verify deployment
echo -e "${BLUE}🔍 Verifying deployment...${NC}"

# Check all pods are running
echo -e "${YELLOW}📋 Checking pod status...${NC}"
kubectl get pods -n $NAMESPACE

# Check HPA status
echo -e "${YELLOW}📈 Checking HPA status...${NC}"
kubectl get hpa -n $NAMESPACE

# Check services
echo -e "${YELLOW}🌐 Checking services...${NC}"
kubectl get svc -n $NAMESPACE

# Step 8: Run health checks
echo -e "${BLUE}🏥 Running health checks...${NC}"
if [ -f "scripts/validation/health_check.sh" ]; then
    chmod +x scripts/validation/health_check.sh
    ./scripts/validation/health_check.sh
else
    echo -e "${YELLOW}⚠️ Health check script not found${NC}"
fi

# Step 9: Display access information
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Access Information:${NC}"
echo ""
echo -e "${YELLOW}Agent Endpoints (use kubectl port-forward):${NC}"
echo "  Base Agent:        kubectl port-forward -n $NAMESPACE svc/base-agent-service 8000:8080"
echo "  Calculator Agent:  kubectl port-forward -n $NAMESPACE svc/calculator-agent-service 8002:8080"
echo "  Weather Agent:     kubectl port-forward -n $NAMESPACE svc/weather-agent-service 8001:8080"
echo "  Research Agent:    kubectl port-forward -n $NAMESPACE svc/research-agent-service 8003:8080"
echo ""
if [ "$SKIP_MONITORING" = "false" ]; then
echo -e "${YELLOW}Monitoring Dashboards:${NC}"
echo "  Grafana:           kubectl port-forward -n $NAMESPACE svc/grafana-service 3000:3000"
echo "  Prometheus:        kubectl port-forward -n $NAMESPACE svc/prometheus-service 9090:9090"
echo "  AlertManager:      kubectl port-forward -n $NAMESPACE svc/alertmanager-service 9093:9093"
echo ""
fi
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  Check pods:        kubectl get pods -n $NAMESPACE"
echo "  Check HPA:         kubectl get hpa -n $NAMESPACE"
echo "  Check logs:        kubectl logs -f deployment/base-agent -n $NAMESPACE"
echo "  Scale manually:    kubectl scale deployment base-agent --replicas=5 -n $NAMESPACE"
echo ""
echo -e "${GREEN}✅ System is ready for use!${NC}"
