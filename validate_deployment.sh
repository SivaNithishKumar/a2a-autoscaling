#!/bin/bash

# 🧪 A2A Multi-Agent System - Deployment Test & Validation
# This script performs validation tests for the deployment scripts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🧪 A2A Multi-Agent System - Deployment Validation${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""

# Test variables
NAMESPACE="multi-agent-a2a-test"
TEST_PASSED=0
TEST_FAILED=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${BLUE}🔍 Testing: $test_name${NC}"
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS: $test_name${NC}"
        TEST_PASSED=$((TEST_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL: $test_name${NC}"
        TEST_FAILED=$((TEST_FAILED + 1))
        return 1
    fi
}

# Function to run test with output
run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${BLUE}🔍 Testing: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASS: $test_name${NC}"
        TEST_PASSED=$((TEST_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL: $test_name${NC}"
        TEST_FAILED=$((TEST_FAILED + 1))
        return 1
    fi
}

echo -e "${BLUE}📋 Pre-deployment Validation${NC}"
echo "================================"

# Test 1: Check if scripts exist
run_test "Deploy script exists" "[ -f 'deploy_complete_a2a_system.sh' ]"
run_test "Streamlit script exists" "[ -f 'start_streamlit_app.sh' ]"
run_test "Deploy script is executable" "[ -x 'deploy_complete_a2a_system.sh' ]"
run_test "Streamlit script is executable" "[ -x 'start_streamlit_app.sh' ]"

# Test 2: Check required tools
run_test "kubectl available" "command -v kubectl"
run_test "docker available" "command -v docker"
run_test "curl available" "command -v curl"

# Test 3: Check Kubernetes connection
run_test "Kubernetes cluster accessible" "kubectl cluster-info"

# Test 4: Check required files exist
run_test "Streamlit app exists" "[ -f 'streamlit_a2a_app.py' ]"
run_test "Requirements file exists" "[ -f 'requirements.txt' ]"
run_test "Namespace YAML exists" "[ -f 'k8s/agents/namespace.yaml' ]"

# Test 5: Check K8s manifests
run_test "Agent manifests exist" "[ -d 'k8s/agents' ] && [ \$(ls k8s/agents/*.yaml | wc -l) -gt 0 ]"
run_test "Monitoring manifests exist" "[ -d 'k8s/monitoring' ] && [ \$(ls k8s/monitoring/*.yaml | wc -l) -gt 0 ]"
run_test "Autoscaling manifests exist" "[ -d 'k8s/autoscaling' ] && [ \$(ls k8s/autoscaling/*.yaml | wc -l) -gt 0 ]"

# Test 6: Validate YAML syntax
echo -e "${BLUE}🔍 Testing: YAML syntax validation${NC}"
if find k8s -name "*.yaml" -exec kubectl apply --dry-run=client -f {} \; >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS: YAML syntax validation${NC}"
    TEST_PASSED=$((TEST_PASSED + 1))
else
    echo -e "${RED}❌ FAIL: YAML syntax validation${NC}"
    TEST_FAILED=$((TEST_FAILED + 1))
fi

# Test 7: Python dependencies check
echo -e "${BLUE}🔍 Testing: Python dependencies check${NC}"
if python3 -c "import streamlit, httpx, dotenv" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS: Core Python dependencies available${NC}"
    TEST_PASSED=$((TEST_PASSED + 1))
else
    echo -e "${YELLOW}⚠️ WARN: Some Python dependencies not installed (will be installed during deployment)${NC}"
    TEST_PASSED=$((TEST_PASSED + 1))
fi

# Test 8: Script syntax validation
run_test "Deploy script syntax" "bash -n deploy_complete_a2a_system.sh"
run_test "Streamlit script syntax" "bash -n start_streamlit_app.sh"

echo ""
echo -e "${CYAN}📊 Test Results Summary${NC}"
echo "======================"
echo -e "Tests Passed: ${GREEN}$TEST_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TEST_FAILED${NC}"
echo -e "Total Tests:  $((TEST_PASSED + TEST_FAILED))"

if [ $TEST_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All validation tests passed! The deployment is ready to run.${NC}"
    echo ""
    echo -e "${BLUE}🚀 To deploy the system, run:${NC}"
    echo -e "${YELLOW}   ./deploy_complete_a2a_system.sh${NC}"
    echo ""
    echo -e "${BLUE}🎨 To start just the Streamlit app (after K8s deployment), run:${NC}"
    echo -e "${YELLOW}   ./start_streamlit_app.sh${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some validation tests failed. Please address the issues before deployment.${NC}"
    exit 1
fi