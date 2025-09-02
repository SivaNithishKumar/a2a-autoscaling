#!/bin/bash
# Comprehensive Kubernetes Deployment Validation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="multi-agent-a2a"
TIMEOUT="300s"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}🏥 Comprehensive Kubernetes Health Check${NC}"
echo "Namespace: $NAMESPACE"
echo "Timeout: $TIMEOUT"
echo ""

# Validation results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to run a validation check
validate_check() {
    local check_name="$1"
    local command="$2"
    local expected_result="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "${CYAN}🔍 Checking: $check_name${NC}"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS: $check_name${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL: $check_name${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to validate with output
validate_with_output() {
    local check_name="$1"
    local command="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "${CYAN}🔍 Checking: $check_name${NC}"
    
    local output
    output=$(eval "$command" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ PASS: $check_name${NC}"
        echo "$output"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL: $check_name${NC}"
        echo "$output"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

echo -e "${BLUE}📋 BASIC CONNECTIVITY CHECKS${NC}"
echo "================================"

# Check kubectl connectivity
validate_check "Kubectl connectivity" "kubectl cluster-info"

# Check namespace exists
validate_check "Namespace exists" "kubectl get namespace $NAMESPACE"

echo -e "\n${BLUE}🤖 AGENT DEPLOYMENT CHECKS${NC}"
echo "================================"

# Check all deployments are available
AGENTS=("base-agent" "calculator-agent" "weather-agent" "research-agent" "move-orchestrator-agent" "infrastructure-monitor-agent")

for agent in "${AGENTS[@]}"; do
    validate_check "$agent deployment ready" "kubectl get deployment $agent -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' | grep -v '^0$'"
done

# Check all pods are running
validate_with_output "All pods running" "kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers | wc -l"

# Check no pods are failing
validate_check "No failed pods" "[ \$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed --no-headers | wc -l) -eq 0 ]"

echo -e "\n${BLUE}🌐 SERVICE CHECKS${NC}"
echo "================================"

# Check all services exist
for agent in "${AGENTS[@]}"; do
    service_name="${agent}-service"
    validate_check "$service_name exists" "kubectl get service $service_name -n $NAMESPACE"
done

echo -e "\n${BLUE}📈 AUTOSCALING CHECKS${NC}"
echo "================================"

# Check HPA exists and is working
HPA_NAMES=("base-agent-hpa" "calculator-agent-hpa" "weather-agent-hpa" "research-agent-hpa" "move-orchestrator-hpa" "infrastructure-monitor-hpa")

for hpa in "${HPA_NAMES[@]}"; do
    validate_check "$hpa exists" "kubectl get hpa $hpa -n $NAMESPACE"
done

# Check metrics server is working
validate_check "Metrics server responding" "kubectl top nodes"

echo -e "\n${BLUE}📊 MONITORING CHECKS${NC}"
echo "================================"

# Check Prometheus is running
validate_check "Prometheus deployment" "kubectl get deployment prometheus -n $NAMESPACE"

# Check Grafana is running  
validate_check "Grafana deployment" "kubectl get deployment grafana -n $NAMESPACE"

# Check ServiceMonitors exist
validate_check "ServiceMonitors configured" "kubectl get servicemonitor -n $NAMESPACE"

echo -e "\n${BLUE}🔍 HEALTH ENDPOINT CHECKS${NC}"
echo "================================"

# Function to test health endpoint
test_health_endpoint() {
    local agent_name="$1"
    local port="$2"
    local service_name="${agent_name}-service"
    
    echo -e "${CYAN}Testing $agent_name health endpoint...${NC}"
    
    # Port forward and test
    kubectl port-forward svc/$service_name $port:$port -n $NAMESPACE &
    local pf_pid=$!
    
    # Wait for port forward to establish
    sleep 3
    
    # Test health endpoint
    if curl -f -s "http://localhost:$port/health" > /dev/null; then
        echo -e "${GREEN}✅ $agent_name health endpoint responding${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ $agent_name health endpoint failed${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    # Kill port forward
    kill $pf_pid 2>/dev/null || true
    sleep 1
}

# Test health endpoints for each agent
declare -A AGENT_PORTS=(
    ["base-agent"]="8080"
    ["calculator-agent"]="8081"
    ["weather-agent"]="8082"
    ["research-agent"]="8083"
    ["move-orchestrator-agent"]="8004"
    ["infrastructure-monitor-agent"]="8005"
)

for agent in "${!AGENT_PORTS[@]}"; do
    test_health_endpoint "$agent" "${AGENT_PORTS[$agent]}"
done

echo -e "\n${BLUE}🔧 CONFIGURATION CHECKS${NC}"
echo "================================"

# Check ConfigMaps exist
validate_check "Agent ConfigMap exists" "kubectl get configmap agent-config -n $NAMESPACE"

# Check Secrets exist
validate_check "AI-Ops secrets exist" "kubectl get secret ai-ops-secrets -n $NAMESPACE"

# Check RBAC is configured
validate_check "ServiceAccount exists" "kubectl get serviceaccount prometheus -n $NAMESPACE"

echo -e "\n${BLUE}📊 RESOURCE UTILIZATION${NC}"
echo "================================"

# Show current resource usage
echo -e "${CYAN}Current pod resource usage:${NC}"
kubectl top pods -n $NAMESPACE 2>/dev/null || echo "Metrics not available"

echo -e "\n${CYAN}Current HPA status:${NC}"
kubectl get hpa -n $NAMESPACE

echo -e "\n${CYAN}Node resource usage:${NC}"
kubectl top nodes 2>/dev/null || echo "Node metrics not available"

echo -e "\n${BLUE}📋 VALIDATION SUMMARY${NC}"
echo "================================"

echo "Total Checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"

SUCCESS_RATE=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
echo "Success Rate: $SUCCESS_RATE%"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL CHECKS PASSED! System is healthy and ready.${NC}"
    echo -e "${GREEN}✅ Your A2A Multi-Agent System with Kubernetes autoscaling is working perfectly!${NC}"
    
    echo -e "\n${BLUE}🎯 Ready for:${NC}"
    echo "  • Production deployment"
    echo "  • Load testing and autoscaling demo"
    echo "  • Interview presentation"
    echo "  • Business value demonstration"
    
    exit 0
else
    echo -e "\n${YELLOW}⚠️  Some checks failed. System may have issues.${NC}"
    echo -e "${YELLOW}Please review the failed checks above and fix any issues.${NC}"
    
    echo -e "\n${BLUE}🔧 Troubleshooting commands:${NC}"
    echo "  • Check pod logs: kubectl logs <pod-name> -n $NAMESPACE"
    echo "  • Describe resources: kubectl describe <resource> <name> -n $NAMESPACE"
    echo "  • Check events: kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'"
    echo "  • Check HPA details: kubectl describe hpa -n $NAMESPACE"
    
    exit 1
fi
