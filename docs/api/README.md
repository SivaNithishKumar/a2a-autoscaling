# API Documentation

This directory contains comprehensive API documentation for the Multi-Agent A2A Autoscaling Platform.

## 📁 Documentation Structure

### Core API Documentation
- [**A2A Protocol API**](a2a-protocol-api.md) - Complete A2A protocol implementation
- [**Agent APIs**](agent-apis.md) - Individual agent API specifications
- [**Routing API**](routing-api.md) - Intelligent agent routing and selection
- [**Monitoring API**](monitoring-api.md) - Metrics and observability endpoints

### Integration Guides
- [**Client Integration**](client-integration.md) - How to integrate with the A2A system
- [**Webhook Integration**](webhook-integration.md) - Event-driven integration patterns
- [**External APIs**](external-apis.md) - Third-party API integrations

### Protocol Specifications
- [**Message Formats**](message-formats.md) - A2A message structure and schemas
- [**Event Specifications**](event-specifications.md) - Event types and handling
- [**Error Handling**](error-handling.md) - Error codes and recovery patterns

## 🚀 Quick Start

### Basic A2A Client Usage
```python
from a2a.client import A2AClient

# Initialize client
client = A2AClient(base_url="http://localhost:8080")

# Send message to agent
response = await client.send_message(
    agent_url="http://base-agent:8080",
    message="Hello, how can you help me?"
)
```

### Agent Discovery
```python
# Discover available agents
agents = await client.discover_agents()
print(f"Available agents: {[agent.name for agent in agents]}")
```

### Intelligent Routing
```python
from src.clients.ai_agent_router import AIAgentRouter

# Use intelligent routing
router = AIAgentRouter()
best_agent = await router.route_query("Calculate 2+2")
print(f"Best agent for query: {best_agent.name}")
```

## 📊 API Endpoints Overview

### Core Endpoints
- `GET /health` - Agent health check
- `POST /skills` - Get agent skills and capabilities
- `POST /messages` - Send message to agent
- `GET /metrics` - Prometheus metrics

### Agent-Specific Endpoints
- **Base Agent**: General conversation and coordination
- **Calculator**: Mathematical operations and unit conversions
- **Weather**: Weather data and forecasting
- **Research**: Information gathering and fact-checking
- **Move Orchestrator**: Complex logistics coordination
- **Infrastructure Monitor**: System monitoring and alerts

## 🔧 Authentication & Security

### API Authentication
Currently, the system supports:
- **Development**: No authentication required
- **Production**: Kubernetes service account tokens
- **Future**: OAuth 2.0 and API key authentication

### Security Headers
All API responses include appropriate security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

## 📈 Rate Limiting

### Default Limits
- **Requests per minute**: 1000 per IP
- **Burst capacity**: 100 requests
- **Agent-specific limits**: Vary by agent type

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 🔍 Monitoring & Observability

### Metrics Endpoints
- `/metrics` - Prometheus metrics
- `/health` - Health check
- `/ready` - Readiness probe

### Custom Metrics
- `a2a_requests_total` - Total requests by agent and skill
- `a2a_request_duration_seconds` - Request processing time
- `a2a_active_tasks` - Currently active tasks

## 📝 Request/Response Examples

### Send Message Request
```json
{
  "message": {
    "parts": [
      {
        "text": "What's the weather like in London?"
      }
    ]
  },
  "context_id": "conversation-123"
}
```

### Send Message Response
```json
{
  "task_id": "task-456",
  "status": "completed",
  "result": {
    "parts": [
      {
        "text": "The weather in London is currently 15°C with light rain..."
      }
    ]
  },
  "metadata": {
    "agent": "weather-agent",
    "processing_time_ms": 150
  }
}
```

## 🐛 Error Handling

### Standard Error Format
```json
{
  "error": {
    "code": "AGENT_UNAVAILABLE",
    "message": "The requested agent is currently unavailable",
    "details": {
      "agent": "weather-agent",
      "retry_after": 30
    }
  }
}
```

### Common Error Codes
- `AGENT_UNAVAILABLE` - Agent is down or unreachable
- `INVALID_REQUEST` - Malformed request
- `RATE_LIMITED` - Too many requests
- `INTERNAL_ERROR` - Server error

## 🔄 Versioning

### API Versioning Strategy
- **Current Version**: v1
- **Versioning Method**: URL path (`/api/v1/...`)
- **Backward Compatibility**: Maintained for 2 versions

### Version Headers
```
API-Version: v1
Supported-Versions: v1
```

## 📚 Additional Resources

- [OpenAPI Specification](openapi.yaml) - Complete API schema
- [Postman Collection](postman-collection.json) - Ready-to-use API tests
- [SDK Documentation](../sdk/) - Client SDK documentation
- [Integration Examples](../examples/) - Real-world integration examples

For detailed implementation examples and advanced usage patterns, see the individual API documentation files in this directory.
