#!/bin/bash

# Simple health check script for A2A services
# This checks services directly using kubectl exec instead of port-forwarding

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

NAMESPACE="multi-agent-a2a"

echo -e "${BLUE}🔍 A2A System Health Check${NC}"
echo "=============================="

# Function to check service health directly
check_service_health_direct() {
    local service_name=$1
    local deployment_name=$2
    local port=$3
    local health_endpoint=${4:-/health}
    
    echo -e "${YELLOW}🔍 Checking $service_name...${NC}"
    
    # Check if deployment exists and has ready pods
    if ! kubectl get deployment $deployment_name -n $NAMESPACE >/dev/null 2>&1; then
        echo -e "${RED}❌ Deployment $deployment_name not found${NC}"
        return 1
    fi
    
    # Get ready pods count
    local ready_pods=$(kubectl get deployment $deployment_name -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    local desired_pods=$(kubectl get deployment $deployment_name -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    
    if [ "$ready_pods" != "$desired_pods" ]; then
        echo -e "${YELLOW}⚠️  $service_name: $ready_pods/$desired_pods pods ready${NC}"
    fi
    
    # Try to exec into a pod and check health endpoint
    local pod_name=$(kubectl get pods -n $NAMESPACE -l app=${deployment_name} -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -n "$pod_name" ]; then
        if kubectl exec -n $NAMESPACE $pod_name -- curl -s -f http://localhost:$port$health_endpoint >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is healthy${NC}"
            return 0
        else
            echo -e "${RED}❌ $service_name health check failed${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ No pods found for $service_name${NC}"
        return 1
    fi
}

# Function to check monitoring service health
check_monitoring_health() {
    local service_name=$1
    local deployment_name=$2
    local port=$3
    local health_endpoint=${4:-/}
    
    echo -e "${YELLOW}🔍 Checking $service_name...${NC}"
    
    # Check if deployment exists and has ready pods
    if ! kubectl get deployment $deployment_name -n $NAMESPACE >/dev/null 2>&1; then
        echo -e "${RED}❌ Deployment $deployment_name not found${NC}"
        return 1
    fi
    
    # Get ready pods count
    local ready_pods=$(kubectl get deployment $deployment_name -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    local desired_pods=$(kubectl get deployment $deployment_name -n $NAMESPACE -o jsonpath='{.spec.replicas}')
    
    if [ "$ready_pods" = "$desired_pods" ] && [ "$ready_pods" -gt "0" ]; then
        echo -e "${GREEN}✅ $service_name is healthy ($ready_pods/$desired_pods pods ready)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $service_name: $ready_pods/$desired_pods pods ready${NC}"
        return 1
    fi
}

echo -e "\n${BLUE}🤖 Checking Agent Services${NC}"
echo "=========================="

# Check A2A agent services
check_service_health_direct "Base Agent" "base-agent" "8080" "/health"
check_service_health_direct "Calculator Agent" "calculator-agent" "8081" "/health"
check_service_health_direct "Weather Agent" "weather-agent" "8082" "/health"
check_service_health_direct "Research Agent" "research-agent" "8083" "/health"
check_service_health_direct "Move Orchestrator" "move-orchestrator-agent" "8004" "/health"
check_service_health_direct "Infrastructure Monitor" "infrastructure-monitor-agent" "8005" "/health"

echo -e "\n${BLUE}📊 Checking Monitoring Services${NC}"
echo "=============================="

# Check monitoring services
check_monitoring_health "Prometheus" "prometheus" "9090"
check_monitoring_health "Grafana" "grafana" "3000"
check_monitoring_health "AlertManager" "alertmanager" "9093"

echo -e "\n${BLUE}🎨 Checking Streamlit App${NC}"
echo "========================"

check_monitoring_health "Streamlit A2A App" "streamlit-a2a-app" "8501"

echo -e "\n${BLUE}📊 System Summary${NC}"
echo "================="

# Get overall system status
kubectl get deployments -n $NAMESPACE -o wide

echo -e "\n${GREEN}🎉 Health check completed!${NC}"
echo -e "${BLUE}🌐 Access URLs (use kubectl port-forward):${NC}"
echo -e "   📊 Grafana:    ${YELLOW}kubectl port-forward -n $NAMESPACE svc/grafana-service 3000:3000${NC}"
echo -e "   🔍 Prometheus: ${YELLOW}kubectl port-forward -n $NAMESPACE svc/prometheus-service 9090:9090${NC}"
echo -e "   🚨 AlertManager: ${YELLOW}kubectl port-forward -n $NAMESPACE svc/alertmanager-service 9093:9093${NC}"
echo -e "   🎨 Streamlit:  ${YELLOW}kubectl port-forward -n $NAMESPACE svc/streamlit-a2a-service 8501:8501${NC}"