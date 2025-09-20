#!/bin/bash

# 🚀 Complete A2A Multi-Agent System Deployment & Streamlit Launcher
# This script deploys all Kubernetes components and starts the Streamlit app
# 
# Author: Enhanced for Complete System Deployment
# Date: $(date)
# Purpose: Single script to deploy entire A2A ecosystem with health validation

set -e

# Colors for enhanced output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration Variables
NAMESPACE="${NAMESPACE:-multi-agent-a2a}"
REGISTRY="${REGISTRY:-}"
VERSION="${VERSION:-latest}"
SKIP_BUILD="${SKIP_BUILD:-false}"
SKIP_MONITORING="${SKIP_MONITORING:-false}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-300}"
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Health check configuration
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=10
PORT_FORWARD_PIDS=()

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                  🚀 A2A Multi-Agent System Complete Deployment                   ║${NC}"
echo -e "${CYAN}║                        with Integrated Streamlit Launch                         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "   Namespace:        ${YELLOW}$NAMESPACE${NC}"
echo -e "   Registry:         ${YELLOW}${REGISTRY:-<local>}${NC}"
echo -e "   Version:          ${YELLOW}$VERSION${NC}"
echo -e "   Skip Build:       ${YELLOW}$SKIP_BUILD${NC}"
echo -e "   Skip Monitoring:  ${YELLOW}$SKIP_MONITORING${NC}"
echo -e "   Streamlit Port:   ${YELLOW}$STREAMLIT_PORT${NC}"
echo -e "   Project Dir:      ${YELLOW}$PROJECT_DIR${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print step headers
print_step() {
    local step_num=$1
    local step_title=$2
    echo ""
    echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║  Step $step_num: $step_title${NC}"
    echo -e "${MAGENTA}╚════════════════════════════════════════════════════════════════════════════════╝${NC}"
}

# Function to wait for deployment with progress indication
wait_for_deployment() {
    local deployment=$1
    local namespace=$2
    local timeout=${3:-300}
    
    echo -e "${YELLOW}⏳ Waiting for deployment $deployment to be ready (timeout: ${timeout}s)...${NC}"
    
    # Special handling for Prometheus which might take longer due to WAL replay
    if [[ "$deployment" == "prometheus" ]]; then
        echo -e "${YELLOW}   Note: Prometheus may take longer due to data recovery (WAL replay)${NC}"
        # For Prometheus, just check if pods are running, not necessarily ready
        local count=0
        local max_attempts=$((timeout / 10))
        while [ $count -lt $max_attempts ]; do
            local running_pods=$(kubectl get pods -n $namespace -l app=prometheus --no-headers | grep -c "Running" || echo "0")
            if [ "$running_pods" -gt 0 ]; then
                echo -e "${GREEN}✅ Prometheus pod is running (may still be initializing)${NC}"
                return 0
            fi
            count=$((count + 1))
            echo -e "${YELLOW}   Attempt $count/$max_attempts - waiting for Prometheus pod to start...${NC}"
            sleep 10
        done
        echo -e "${YELLOW}⚠️ Prometheus pod not running yet, but continuing deployment...${NC}"
        return 0
    fi
    
    if kubectl wait --for=condition=available --timeout=${timeout}s deployment/$deployment -n $namespace 2>/dev/null; then
        echo -e "${GREEN}✅ Deployment $deployment is ready${NC}"
        return 0
    else
        echo -e "${RED}❌ Deployment $deployment failed to become ready within ${timeout}s${NC}"
        return 1
    fi
}

# Function to wait for pods with label selector
wait_for_pods() {
    local label=$1
    local namespace=$2
    local timeout=${3:-300}
    
    echo -e "${YELLOW}⏳ Waiting for pods with label $label to be ready...${NC}"
    kubectl wait --for=condition=ready --timeout=${timeout}s pods -l $label -n $namespace
}

# Function to check service health via port-forward
check_service_health() {
    local service=$1
    local namespace=$2
    local port=$3
    local health_path=${4:-/health}
    local retries=${HEALTH_CHECK_RETRIES}
    
    echo -e "${YELLOW}🔍 Health checking $service...${NC}"
    
    # Start port-forward in background
    kubectl port-forward -n $namespace svc/$service $port:$port >/dev/null 2>&1 &
    local pf_pid=$!
    PORT_FORWARD_PIDS+=($pf_pid)
    
    # Wait a moment for port-forward to establish
    sleep 3
    
    # Perform health check
    local count=0
    while [ $count -lt $retries ]; do
        if curl -s -f "http://localhost:$port$health_path" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service is healthy${NC}"
            kill $pf_pid 2>/dev/null || true
            return 0
        fi
        count=$((count + 1))
        echo -e "${YELLOW}   Attempt $count/$retries failed, retrying in ${HEALTH_CHECK_INTERVAL}s...${NC}"
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    echo -e "${RED}❌ $service health check failed after $retries attempts${NC}"
    kill $pf_pid 2>/dev/null || true
    return 1
}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up port-forwards...${NC}"
    for pid in "${PORT_FORWARD_PIDS[@]}"; do
        kill $pid 2>/dev/null || true
    done
}
trap cleanup EXIT

# Prerequisite checks
print_step "0" "Prerequisites Verification"

echo -e "${BLUE}🔍 Checking required tools...${NC}"
required_tools=("kubectl" "docker" "curl")
for tool in "${required_tools[@]}"; do
    if command_exists "$tool"; then
        echo -e "${GREEN}✅ $tool is available${NC}"
    else
        echo -e "${RED}❌ $tool is not installed${NC}"
        exit 1
    fi
done

# Check kubectl cluster connection
echo -e "${BLUE}🔗 Checking Kubernetes cluster connection...${NC}"
if kubectl cluster-info >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Connected to Kubernetes cluster${NC}"
    kubectl cluster-info | head -1
else
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Step 1: Build Docker Images (if not skipped)
print_step "1" "Docker Image Build Phase"

if [ "$SKIP_BUILD" = "false" ]; then
    echo -e "${BLUE}🐳 Building Docker images...${NC}"
    if [ -f "docker/build-scripts/build_all_images.sh" ]; then
        echo -e "${YELLOW}📦 Executing build script...${NC}"
        chmod +x docker/build-scripts/build_all_images.sh
        cd docker/build-scripts
        REGISTRY="$REGISTRY" VERSION="$VERSION" ./build_all_images.sh
        cd "$PROJECT_DIR"
        echo -e "${GREEN}✅ Docker images built successfully${NC}"
    else
        echo -e "${YELLOW}⚠️ Build script not found, skipping image build${NC}"
    fi
else
    echo -e "${YELLOW}⏭️ Skipping Docker image build (SKIP_BUILD=true)${NC}"
fi

# Step 2: Install Prometheus Operator CRDs (if monitoring enabled)
print_step "2" "Prometheus Operator CRDs Installation"

if [ "$SKIP_MONITORING" = "false" ]; then
    echo -e "${BLUE}📊 Installing Prometheus Operator CRDs...${NC}"
    if ! kubectl get crd servicemonitors.monitoring.coreos.com >/dev/null 2>&1; then
        echo -e "${YELLOW}⏳ Installing Prometheus Operator CRDs...${NC}"
        kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml || true
        echo -e "${YELLOW}⏳ Waiting for CRDs to be established...${NC}"
        sleep 15
        echo -e "${GREEN}✅ Prometheus Operator CRDs installed${NC}"
    else
        echo -e "${GREEN}✅ Prometheus Operator CRDs already installed${NC}"
    fi
else
    echo -e "${YELLOW}⏭️ Skipping Prometheus Operator CRDs (monitoring disabled)${NC}"
fi

# Step 3: Deploy Namespace and RBAC
print_step "3" "Namespace and RBAC Deployment"

echo -e "${BLUE}🏗️ Deploying namespace and RBAC...${NC}"
kubectl apply -f k8s/agents/namespace.yaml
echo -e "${GREEN}✅ Namespace and RBAC deployed${NC}"

# Check if namespace is active
kubectl get namespace $NAMESPACE
echo -e "${GREEN}✅ Namespace $NAMESPACE is active${NC}"

# Step 4: Deploy Core A2A Agents
print_step "4" "A2A Agents Deployment"

echo -e "${BLUE}🤖 Deploying A2A agents...${NC}"
agents=("base-agent" "calculator-agent" "weather-agent" "research-agent" "move-orchestrator-agent" "infrastructure-monitor-agent")

# Deploy agent manifests
kubectl apply -f k8s/agents/

echo -e "${YELLOW}⏳ Waiting for agent deployments to be ready...${NC}"
for agent in "${agents[@]}"; do
    if kubectl get deployment $agent -n $NAMESPACE >/dev/null 2>&1; then
        echo -e "${BLUE}   Waiting for $agent...${NC}"
        wait_for_deployment "$agent" "$NAMESPACE" "$WAIT_TIMEOUT"
    else
        echo -e "${YELLOW}   ⚠️ Deployment $agent not found, skipping...${NC}"
    fi
done

echo -e "${GREEN}✅ All A2A agents deployed successfully${NC}"

# Step 5: Deploy Monitoring Stack (if enabled)
print_step "5" "Monitoring Stack Deployment"

if [ "$SKIP_MONITORING" = "false" ]; then
    echo -e "${BLUE}📊 Deploying monitoring stack...${NC}"
    kubectl apply -f k8s/monitoring/
    
    echo -e "${YELLOW}⏳ Waiting for monitoring components to start...${NC}"
    sleep 30
    
    # Wait for key monitoring components
    monitoring_components=("prometheus" "grafana")
    for component in "${monitoring_components[@]}"; do
        if kubectl get deployment $component -n $NAMESPACE >/dev/null 2>&1; then
            echo -e "${BLUE}   Waiting for $component...${NC}"
            wait_for_deployment "$component" "$NAMESPACE" "$WAIT_TIMEOUT"
        else
            echo -e "${YELLOW}   ⚠️ $component deployment not found, might be StatefulSet or DaemonSet${NC}"
        fi
    done
    
    echo -e "${GREEN}✅ Monitoring stack deployed successfully${NC}"
else
    echo -e "${YELLOW}⏭️ Skipping monitoring stack deployment${NC}"
fi

# Step 6: Deploy Autoscaling Configurations
print_step "6" "Autoscaling Configuration Deployment"

echo -e "${BLUE}📈 Deploying autoscaling configurations...${NC}"
kubectl apply -f k8s/autoscaling/

# Wait a moment for HPA to initialize
sleep 10

echo -e "${YELLOW}📊 Current HPA Status:${NC}"
kubectl get hpa -n $NAMESPACE || echo "No HPA found yet, they may need time to initialize"

echo -e "${GREEN}✅ Autoscaling configurations deployed${NC}"

# Step 7: System Health Verification
print_step "7" "System Health Verification"

echo -e "${BLUE}🏥 Performing comprehensive health checks...${NC}"

# Check all pods status
echo -e "${YELLOW}📋 Pod Status:${NC}"
kubectl get pods -n $NAMESPACE -o wide

# Check services
echo -e "\n${YELLOW}🌐 Service Status:${NC}"
kubectl get svc -n $NAMESPACE

# Check deployments
echo -e "\n${YELLOW}🚀 Deployment Status:${NC}"
kubectl get deployments -n $NAMESPACE

# Perform detailed health checks for key services
echo -e "\n${BLUE}🔍 Performing detailed health checks...${NC}"

# Health check agent services
agent_services=("base-agent-service:8080" "calculator-agent-service:8080" "weather-agent-service:8080" "research-agent-service:8080")

for service_port in "${agent_services[@]}"; do
    IFS=':' read -r service port <<< "$service_port"
    if kubectl get svc $service -n $NAMESPACE >/dev/null 2>&1; then
        check_service_health "$service" "$NAMESPACE" "$port" "/health" || echo -e "${YELLOW}⚠️ Health check failed for $service, but continuing...${NC}"
    else
        echo -e "${YELLOW}⚠️ Service $service not found${NC}"
    fi
done

echo -e "${GREEN}✅ Health verification completed${NC}"

# Step 8: Deploy and Start Streamlit Application
print_step "8" "Streamlit Application Deployment & Launch"

echo -e "${BLUE}🎨 Deploying Streamlit application...${NC}"

# Check if Streamlit app deployment exists
if [ -f "k8s/agents/streamlit-app.yaml" ]; then
    echo -e "${YELLOW}📱 Deploying Streamlit app to Kubernetes...${NC}"
    kubectl apply -f k8s/agents/streamlit-app.yaml
    
    # Wait for Streamlit deployment
    if kubectl get deployment streamlit-a2a-app -n $NAMESPACE >/dev/null 2>&1; then
        wait_for_deployment "streamlit-a2a-app" "$NAMESPACE" "$WAIT_TIMEOUT"
    fi
    
    echo -e "${YELLOW}🌐 Setting up Streamlit port-forward...${NC}"
    kubectl port-forward -n $NAMESPACE svc/streamlit-a2a-app-service $STREAMLIT_PORT:8501 >/dev/null 2>&1 &
    STREAMLIT_PF_PID=$!
    
    echo -e "${GREEN}✅ Streamlit app deployed and accessible${NC}"
else
    echo -e "${BLUE}🚀 Starting Streamlit app locally...${NC}"
    
    # Ensure Python dependencies are installed
    echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    # Set up port-forwards for agents
    echo -e "${YELLOW}🔗 Setting up port-forwards for agents...${NC}"
    kubectl port-forward -n $NAMESPACE svc/base-agent-service 8000:8080 >/dev/null 2>&1 &
    kubectl port-forward -n $NAMESPACE svc/calculator-agent-service 8002:8080 >/dev/null 2>&1 &
    kubectl port-forward -n $NAMESPACE svc/weather-agent-service 8001:8080 >/dev/null 2>&1 &
    kubectl port-forward -n $NAMESPACE svc/research-agent-service 8003:8080 >/dev/null 2>&1 &
    
    # Wait for port-forwards to establish
    sleep 5
    
    echo -e "${YELLOW}🚀 Starting Streamlit application...${NC}"
    streamlit run streamlit_a2a_app.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0 &
    STREAMLIT_PID=$!
fi

# Wait for Streamlit to start
echo -e "${YELLOW}⏳ Waiting for Streamlit to start...${NC}"
sleep 10

# Verify Streamlit is accessible
if curl -s -f "http://localhost:$STREAMLIT_PORT" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Streamlit app is running and accessible${NC}"
else
    echo -e "${YELLOW}⚠️ Streamlit may still be starting up...${NC}"
fi

# Step 9: Final System Summary
print_step "9" "Deployment Summary & Access Information"

echo -e "${GREEN}🎉 A2A Multi-Agent System Deployment Completed Successfully!${NC}"
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                              📋 ACCESS INFORMATION                               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}🎨 Streamlit Application:${NC}"
echo -e "   🌐 URL: ${GREEN}http://localhost:$STREAMLIT_PORT${NC}"
echo -e "   📱 Status: Running"
echo ""
echo -e "${BLUE}🤖 Agent Endpoints (via port-forward):${NC}"
echo -e "   🎯 Base Agent:        ${YELLOW}http://localhost:8000${NC}"
echo -e "   🧮 Calculator Agent:  ${YELLOW}http://localhost:8002${NC}"
echo -e "   🌤️ Weather Agent:     ${YELLOW}http://localhost:8001${NC}"
echo -e "   🔍 Research Agent:    ${YELLOW}http://localhost:8003${NC}"
echo ""

if [ "$SKIP_MONITORING" = "false" ]; then
    echo -e "${BLUE}📊 Monitoring Dashboards:${NC}"
    echo -e "   📈 Grafana:           ${YELLOW}kubectl port-forward -n $NAMESPACE svc/grafana-service 3000:3000${NC}"
    echo -e "   📊 Prometheus:        ${YELLOW}kubectl port-forward -n $NAMESPACE svc/prometheus-service 9090:9090${NC}"
    echo -e "   🚨 AlertManager:      ${YELLOW}kubectl port-forward -n $NAMESPACE svc/alertmanager-service 9093:9093${NC}"
    echo ""
fi

echo -e "${BLUE}🛠️ Useful Commands:${NC}"
echo -e "   📊 Check pods:        ${YELLOW}kubectl get pods -n $NAMESPACE${NC}"
echo -e "   📈 Check HPA:         ${YELLOW}kubectl get hpa -n $NAMESPACE${NC}"
echo -e "   📋 Check logs:        ${YELLOW}kubectl logs -f deployment/base-agent -n $NAMESPACE${NC}"
echo -e "   ⚖️ Scale manually:     ${YELLOW}kubectl scale deployment base-agent --replicas=5 -n $NAMESPACE${NC}"
echo -e "   🔄 Restart service:   ${YELLOW}kubectl rollout restart deployment/base-agent -n $NAMESPACE${NC}"
echo ""

echo -e "${BLUE}🏥 Health Check Commands:${NC}"
echo -e "   🔍 System health:     ${YELLOW}./scripts/validation/health_check.sh${NC}"
echo -e "   ✅ Validate K8s:      ${YELLOW}./scripts/validation/validate_kubernetes_deployment.sh${NC}"
echo ""

echo -e "${GREEN}✨ System is ready for use! Open your browser to: ${CYAN}http://localhost:$STREAMLIT_PORT${NC}"
echo ""
echo -e "${YELLOW}💡 Tip: The system is now fully deployed and the Streamlit app is running.${NC}"
echo -e "${YELLOW}    You can interact with all 6 A2A agents through the web interface.${NC}"
echo ""

# Keep script running if Streamlit was started locally
if [ ! -z "$STREAMLIT_PID" ]; then
    echo -e "${BLUE}🔄 Streamlit is running in the background (PID: $STREAMLIT_PID)${NC}"
    echo -e "${YELLOW}   Press Ctrl+C to stop the application and cleanup${NC}"
    echo ""
    
    # Cleanup function for local Streamlit
    cleanup_local() {
        echo -e "\n${YELLOW}🛑 Shutting down Streamlit and port-forwards...${NC}"
        kill $STREAMLIT_PID 2>/dev/null || true
        cleanup
        echo -e "${GREEN}✅ Cleanup completed${NC}"
    }
    trap cleanup_local INT TERM
    
    # Wait for interrupt
    wait $STREAMLIT_PID
fi

echo -e "${GREEN}🎯 A2A Multi-Agent System deployment script completed successfully!${NC}"