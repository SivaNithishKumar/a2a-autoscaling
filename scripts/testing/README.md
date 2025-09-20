# Kubernetes Agent Testing Scripts

This directory contains comprehensive test scripts for validating all agents deployed in the multi-agent-a2a Kubernetes system.

## Available Test Scripts

### 1. Quick Bash Test (`quick_test_k8s_agents.sh`)

A fast, lightweight bash script that performs basic validation of all agents.

**Features:**
- ✅ Kubernetes cluster connectivity check
- ✅ Pod status verification for all agents
- ✅ Service availability check
- ✅ Health endpoint testing via port-forward
- ✅ Agent card endpoint validation
- ✅ Recent error log analysis
- ✅ Basic monitoring stack verification

**Usage:**
```bash
# Run the quick test
./scripts/testing/quick_test_k8s_agents.sh

# Make it executable if needed
chmod +x ./scripts/testing/quick_test_k8s_agents.sh
```

**Expected Runtime:** ~30-60 seconds

### 2. Comprehensive Python Test (`test_all_agents_kubernetes.py`)

A detailed, feature-rich Python script with advanced testing capabilities.

**Features:**
- 🔗 Cluster connection validation
- 🚀 Pod status analysis with JSON parsing
- 🌐 Service discovery and validation
- 🏥 Health endpoint testing via port-forward
- 🔄 Direct cluster access via kubectl proxy
- 📊 Monitoring stack verification
- 📜 Log analysis with error pattern detection
- 📈 Detailed reporting and statistics
- 🎯 Configurable test options

**Usage:**
```bash
# Run all tests
python3 ./scripts/testing/test_all_agents_kubernetes.py

# Run with verbose output
python3 ./scripts/testing/test_all_agents_kubernetes.py --verbose

# Skip port-forward tests
python3 ./scripts/testing/test_all_agents_kubernetes.py --no-port-forward

# Skip cluster-direct tests
python3 ./scripts/testing/test_all_agents_kubernetes.py --no-cluster-direct

# Show help
python3 ./scripts/testing/test_all_agents_kubernetes.py --help
```

**Expected Runtime:** ~30-90 seconds (depending on options)

### 3. 🆕 Functional Agent Test (`test_agent_functionality.py`)

A comprehensive test suite that validates each agent's actual capabilities with real functional queries.

**Features:**
- 🧮 **Calculator Agent**: Tests arithmetic operations, mathematical functions, unit conversions, and statistical calculations
- 🌤️ **Weather Agent**: Tests current weather queries, forecasts, location-based requests, and international weather data
- 🔬 **Research Agent**: Tests technology research, scientific inquiries, current events analysis, and industry research
- 🏠 **Move Orchestrator**: Tests move planning, office relocations, international moves, and timeline creation
- 🖥️ **Infrastructure Monitor**: Tests system health checks, performance monitoring, resource utilization, and alert analysis
- 💬 **Base Agent**: Tests general conversation, information processing, and task assistance
- 🎯 Uses real A2A protocol (JSON-RPC 2.0) with actual message passing
- ⚡ Fast response validation with keyword detection
- 📊 Detailed per-agent performance breakdown

**Usage:**
```bash
# Run all functional tests
python3 ./scripts/testing/test_agent_functionality.py

# Run with verbose output to see full responses
python3 ./scripts/testing/test_agent_functionality.py --verbose

# Set custom timeout (default: 30s)
python3 ./scripts/testing/test_agent_functionality.py --timeout=15

# Skip port-forward tests (for cluster-internal testing)
python3 ./scripts/testing/test_agent_functionality.py --no-port-forward

# Show help
python3 ./scripts/testing/test_agent_functionality.py --help
```

**Expected Runtime:** ~20-30 seconds
**Success Rate:** 100% (when all agents are functioning properly)

## Tested Components

### Agents Tested with Functional Queries

| Agent | Service | A2A Port | Metrics Port | Test Categories |
|-------|---------|----------|--------------|-----------------|
| **Base Agent** | `base-agent-service` | 8080 | 8080 | General conversation, information processing, task assistance |
| **Calculator Agent** | `calculator-agent-service` | 8081 | 8081 | Arithmetic operations, mathematical functions, unit conversions, statistics |
| **Weather Agent** | `weather-agent-service` | 8082 | 8082 | Current weather, forecasts, location queries, international data |
| **Research Agent** | `research-agent-service` | 8083 | 8083 | Technology research, scientific inquiry, current events, industry analysis |
| **Move Orchestrator** | `move-orchestrator-service` | 8004 | 8084 | Move planning, office relocations, international moves, timeline creation |
| **Infrastructure Monitor** | `infrastructure-monitor-service` | 8005 | 8085 | System health, performance monitoring, resource utilization, alert analysis |

### A2A Protocol Testing

All functional tests use the proper A2A (Agent-to-Agent) protocol:
- **Protocol**: JSON-RPC 2.0
- **Endpoint**: `POST /` (root endpoint)
- **Method**: `message/send`
- **Format**: 
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "Your query here"}],
      "messageId": "unique-message-id"
    }
  }
}
```

### Sample Functional Tests

**Calculator Agent Examples:**
- "What is 25 + 17 * 3?" → Expects: 76
- "Calculate the square root of 144" → Expects: 12
- "Convert 100 degrees Fahrenheit to Celsius" → Expects: 37.78°C
- "Calculate the average of 10, 20, 30, 40, 50" → Expects: 30

**Weather Agent Examples:**
- "What's the current weather in New York City?"
- "Can you give me a 3-day weather forecast for London?"
- "Is it raining in Seattle today?"
- "What's the temperature in Tokyo right now?"

**Research Agent Examples:**
- "Research the latest developments in quantum computing"
- "Tell me about machine learning algorithms and their applications"
- "What are the latest trends in artificial intelligence?"
- "Research the impact of blockchain technology on finance"

**Move Orchestrator Examples:**
- "I need to plan a move from London to Manchester next month"
- "Help me organize an office relocation for 50 employees"
- "I'm moving from New York to Paris. What steps should I take?"
- "Create a timeline for a household move happening in 6 weeks"

**Infrastructure Monitor Examples:**
- "Check the health status of the web frontend and database services"
- "Monitor the performance metrics for our production environment"
- "What's the current CPU and memory utilization of our services?"
- "Analyze current system alerts and provide recommendations"

### Monitoring Stack
| Service | Port | Health Check |
|---------|------|--------------|
| Prometheus | 9090 | `/api/v1/query` |
| Grafana | 3000 | `/api/health` |
| Alertmanager | 9093 | `/api/v1/status` |

## Prerequisites

### For Bash Script
- `kubectl` configured and connected to cluster
- `curl` available in PATH
- `grep` and basic shell utilities

### For Python Script
- Python 3.7+
- Required packages: `httpx`, `pyyaml`
- `kubectl` configured and connected to cluster

**Auto-install dependencies:**
The Python script will automatically install missing packages using pip.

## Understanding Test Results

### Exit Codes
- `0`: All tests passed
- `1`: Some tests failed
- `130`: Interrupted by user (Ctrl+C)

### Test Categories

1. **Connectivity Tests**: Verify kubectl can reach the cluster
2. **Pod Status Tests**: Check if agent pods are running and ready
3. **Service Tests**: Verify services are properly configured
4. **Health Endpoint Tests**: Test actual agent health via HTTP
5. **Agent Card Tests**: Validate A2A protocol endpoints
6. **Monitoring Tests**: Check observability stack
7. **Log Analysis**: Scan for recent errors

### Sample Output

```
🧪 QUICK KUBERNETES AGENT TEST
===============================

🔗 Test 1: Kubernetes Connection
Testing kubectl cluster connection... PASSED
Testing multi-agent-a2a namespace... PASSED

🚀 Test 2: Pod Status
Testing base-agent pods... PASSED
Testing calculator-agent pods... PASSED
...

📊 TEST SUMMARY
===============
Total Tests: 34
✅ Passed: 34
❌ Failed: 0

🎉 All tests passed!
```

## Troubleshooting

### Common Issues

**Port-forward failures:**
- Ensure no other processes are using the test ports (9000-9005)
- Check if kubectl has proper permissions

**Service connection timeouts:**
- Verify pods are in Running state: `kubectl get pods -n multi-agent-a2a`
- Check service endpoints: `kubectl get endpoints -n multi-agent-a2a`

**Permission errors:**
- Ensure kubectl context has proper RBAC permissions
- Verify namespace access: `kubectl auth can-i get pods -n multi-agent-a2a`

### Debug Mode

For the Python script, use `--verbose` flag to see detailed HTTP request/response information and debug logs.

## Integration with CI/CD

These scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Test Kubernetes Agents
  run: |
    ./scripts/testing/quick_test_k8s_agents.sh
```

```yaml
# Example with Python script
- name: Comprehensive Agent Testing
  run: |
    python3 ./scripts/testing/test_all_agents_kubernetes.py --no-cluster-direct
```

## Contributing

When adding new agents:
1. Update the agent configurations in both scripts
2. Ensure new agents follow the standard health endpoint pattern
3. Test the scripts against the updated deployment
4. Update this documentation

## Related Scripts

- `test_integration_complete.py`: End-to-end integration testing
- `quick_test.sh`: File structure validation
- `load_test_autoscaling.py`: Performance and scaling tests