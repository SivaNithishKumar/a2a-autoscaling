#!/bin/bash
# Quick Kubernetes Agent Test Script
# Tests all agents in the multi-agent-a2a namespace

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

# Counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "Testing $test_name... "
    
    if output=$(eval "$test_command" 2>&1); then
        if [[ -z "$expected_pattern" ]] || echo "$output" | grep -q "$expected_pattern"; then
            echo -e "${GREEN}PASSED${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            echo -e "${RED}FAILED${NC} (unexpected output)"
            echo "  Expected pattern: $expected_pattern"
            echo "  Got: $output"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        echo -e "${RED}FAILED${NC} (command failed)"
        echo "  Error: $output"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to test agent endpoint with timeout
test_agent_endpoint() {
    local agent_name="$1"
    local service_name="$2"
    local port="$3"
    local endpoint="$4"
    local local_port="$5"
    
    echo "  Setting up port-forward for $agent_name..."
    
    # Start port-forward in background
    kubectl port-forward -n multi-agent-a2a "svc/$service_name" "$local_port:$port" > /dev/null 2>&1 &
    local pf_pid=$!
    
    # Wait a moment for port-forward to establish
    sleep 3
    
    # Test the endpoint
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "  Testing $agent_name $endpoint... "
    
    if curl -s --max-time 5 "http://localhost:$local_port$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        success=true
    else
        echo -e "${RED}FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        success=false
    fi
    
    # Clean up port-forward
    kill $pf_pid 2>/dev/null || true
    wait $pf_pid 2>/dev/null || true
    
    return $([[ $success == true ]] && echo 0 || echo 1)
}

echo -e "${BOLD}${BLUE}🧪 QUICK KUBERNETES AGENT TEST${NC}"
echo -e "${BOLD}================================${NC}"
echo ""

# Test 1: Check kubectl connection
echo -e "${BLUE}🔗 Test 1: Kubernetes Connection${NC}"
run_test "kubectl cluster connection" "kubectl cluster-info" "Kubernetes.*running"
run_test "multi-agent-a2a namespace" "kubectl get namespace multi-agent-a2a" "multi-agent-a2a.*Active"
echo ""

# Test 2: Check pod status
echo -e "${BLUE}🚀 Test 2: Pod Status${NC}"
agents=("base-agent" "calculator-agent" "weather-agent" "research-agent" "move-orchestrator-agent" "infrastructure-monitor-agent")

for agent in "${agents[@]}"; do
    run_test "$agent pods" "kubectl get pods -n multi-agent-a2a -l app=$agent" "Running"
done
echo ""

# Test 3: Check services
echo -e "${BLUE}🌐 Test 3: Services${NC}"
services=("base-agent-service" "calculator-agent-service" "weather-agent-service" "research-agent-service" "move-orchestrator-service" "infrastructure-monitor-service")

for service in "${services[@]}"; do
    run_test "$service" "kubectl get svc -n multi-agent-a2a $service" "ClusterIP"
done
echo ""

# Test 4: Health endpoints (with port-forward)
echo -e "${BLUE}🏥 Test 4: Agent Health Endpoints${NC}"
echo "Note: This will set up temporary port-forwards to test endpoints"

# Agent configurations: name:service:port:local_port
declare -A agent_configs=(
    ["Base Agent"]="base-agent-service:8080:9000"
    ["Calculator Agent"]="calculator-agent-service:8081:9001" 
    ["Weather Agent"]="weather-agent-service:8082:9002"
    ["Research Agent"]="research-agent-service:8083:9003"
    ["Move Orchestrator"]="move-orchestrator-service:8084:9004"
    ["Infrastructure Monitor"]="infrastructure-monitor-service:8085:9005"
)

for agent_name in "${!agent_configs[@]}"; do
    IFS=':' read -r service port local_port <<< "${agent_configs[$agent_name]}"
    
    echo "Testing $agent_name:"
    test_agent_endpoint "$agent_name" "$service" "$port" "/health" "$local_port"
    test_agent_endpoint "$agent_name" "$service" "$port" "/.well-known/agent-card.json" "$local_port"
done
echo ""

# Test 5: Check for recent errors in logs
echo -e "${BLUE}📜 Test 5: Recent Error Check${NC}"
for agent in "${agents[@]}"; do
    echo -n "Checking $agent logs... "
    
    # Get the first pod for this agent
    pod_name=$(kubectl get pods -n multi-agent-a2a -l "app=$agent" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -n "$pod_name" ]]; then
        # Check last 10 log lines for errors
        if kubectl logs -n multi-agent-a2a "$pod_name" --tail=10 2>/dev/null | grep -i -E "(error|fatal|exception|failed)" > /dev/null; then
            echo -e "${YELLOW}WARNINGS FOUND${NC}"
            TESTS_RUN=$((TESTS_RUN + 1))
            # Don't count as failure, just warning
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${GREEN}CLEAN${NC}"
            TESTS_RUN=$((TESTS_RUN + 1))
            TESTS_PASSED=$((TESTS_PASSED + 1))
        fi
    else
        echo -e "${RED}NO POD FOUND${NC}"
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
done
echo ""

# Test 6: Quick monitoring check
echo -e "${BLUE}📊 Test 6: Monitoring Stack${NC}"
monitoring_services=("prometheus-service" "grafana-service")

for service in "${monitoring_services[@]}"; do
    run_test "$service" "kubectl get svc -n multi-agent-a2a $service" "ClusterIP"
done
echo ""

# Summary
echo -e "${BOLD}📊 TEST SUMMARY${NC}"
echo "==============="
echo "Total Tests: $TESTS_RUN"
echo -e "✅ Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "❌ Failed: ${RED}$TESTS_FAILED${NC}"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    success_rate=$(( (TESTS_PASSED * 100) / TESTS_RUN ))
    echo -e "\nSuccess Rate: ${success_rate}%"
    echo -e "${RED}🚨 Some tests failed${NC}"
    exit 1
fi