# A2A Protocol API Reference

## Overview

This document provides comprehensive documentation for the Google A2A (Agent-to-Agent) protocol implementation in the Multi-Agent Autoscaling Platform.

## 🚀 A2A Protocol Implementation

### Core Components

#### AgentExecutor Pattern
The foundation of A2A agent implementation:

```python
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue

class MyAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Agent-specific execution logic
        pass
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Cancellation handling
        pass
```

#### RequestContext Management
Context object for maintaining conversation state:

```python
# Access user input
user_input = context.get_user_input()

# Get current task
task = context.current_task

# Access conversation history
messages = context.conversation_history
```

#### EventQueue Communication
Real-time event streaming:

```python
from a2a.utils import new_agent_text_message

# Send message to user
await event_queue.enqueue_event(
    new_agent_text_message("Processing your request...")
)
```

### Agent Skill Registration

#### Skill Definition
```python
from a2a.types import AgentSkill

skill = AgentSkill(
    id='calculation',
    name='Mathematical Calculation',
    description='Perform mathematical operations and calculations',
    tags=['math', 'calculation', 'arithmetic'],
    examples=[
        'Calculate 2 + 2',
        'What is the square root of 16?',
        'Convert 100°F to Celsius'
    ]
)
```

#### Skills Endpoint
**GET** `/skills`

Returns available agent skills and capabilities:

```json
{
  "skills": [
    {
      "id": "calculation",
      "name": "Mathematical Calculation",
      "description": "Perform mathematical operations and calculations",
      "tags": ["math", "calculation", "arithmetic"],
      "examples": [
        "Calculate 2 + 2",
        "What is the square root of 16?",
        "Convert 100°F to Celsius"
      ]
    }
  ]
}
```

## 📨 Message API

### Send Message
**POST** `/messages`

Send a message to the agent for processing.

#### Request Format
```json
{
  "message": {
    "parts": [
      {
        "text": "Calculate the square root of 144"
      }
    ]
  },
  "context_id": "conv-12345",
  "task_id": "task-67890"
}
```

#### Response Format
```json
{
  "task": {
    "id": "task-67890",
    "context_id": "conv-12345",
    "state": "completed",
    "created_at": "2025-09-04T10:30:00Z",
    "updated_at": "2025-09-04T10:30:02Z"
  },
  "messages": [
    {
      "id": "msg-001",
      "parts": [
        {
          "text": "The square root of 144 is 12."
        }
      ],
      "timestamp": "2025-09-04T10:30:02Z",
      "source": "agent"
    }
  ],
  "artifacts": [
    {
      "name": "calculation_result",
      "parts": [
        {
          "text": "√144 = 12"
        }
      ]
    }
  ]
}
```

### Message Parts Types

#### Text Part
```json
{
  "text": "Hello, how can I help you?"
}
```

#### Image Part (Future)
```json
{
  "image": {
    "url": "https://example.com/image.jpg",
    "alt_text": "Weather map showing current conditions"
  }
}
```

#### Data Part (Future)
```json
{
  "data": {
    "type": "application/json",
    "content": {
      "temperature": 22,
      "humidity": 65,
      "pressure": 1013.25
    }
  }
}
```

## 🔄 Task Lifecycle

### Task States
- `created` - Task has been created
- `working` - Agent is processing the task
- `input_required` - Agent needs user input
- `completed` - Task completed successfully
- `failed` - Task failed with error
- `cancelled` - Task was cancelled

### Task State Transitions
```
created → working → completed
       ↘ input_required → working
       ↘ failed
       ↘ cancelled
```

### TaskUpdater API
```python
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState

updater = TaskUpdater(event_queue, task_id, context_id)

# Update task status
await updater.update_status(
    TaskState.working,
    new_agent_text_message("Processing your request...")
)

# Add artifact
await updater.add_artifact(
    [Part(root=TextPart(text="Result data"))],
    name='calculation_result'
)

# Complete task
await updater.complete()
```

## 🎯 Agent-Specific APIs

### Base Agent API
**Endpoint**: `http://base-agent:8080`

**Capabilities**:
- General conversation
- Task coordination
- Help and assistance

**Example Request**:
```json
{
  "message": {
    "parts": [{"text": "Hello, what can you help me with?"}]
  }
}
```

### Calculator Agent API
**Endpoint**: `http://calculator-agent:8081`

**Capabilities**:
- Arithmetic operations
- Unit conversions
- Statistical calculations

**Example Request**:
```json
{
  "message": {
    "parts": [{"text": "Calculate sin(π/2) + cos(0)"}]
  }
}
```

### Weather Agent API
**Endpoint**: `http://weather-agent:8082`

**Capabilities**:
- Current weather conditions
- Weather forecasts
- Location-based weather data

**Example Request**:
```json
{
  "message": {
    "parts": [{"text": "What's the weather like in London today?"}]
  }
}
```

### Research Agent API
**Endpoint**: `http://research-agent:8083`

**Capabilities**:
- Web search and research
- Fact verification
- Content analysis

**Example Request**:
```json
{
  "message": {
    "parts": [{"text": "Research the latest developments in quantum computing"}]
  }
}
```

### Move Orchestrator API
**Endpoint**: `http://move-orchestrator:8004`

**Capabilities**:
- Moving logistics coordination
- Timeline optimization
- Service provider management

**Example Request**:
```json
{
  "message": {
    "parts": [{"text": "Help me plan a move from New York to San Francisco"}]
  }
}
```

### Infrastructure Monitor API
**Endpoint**: `http://infrastructure-monitor:8005`

**Capabilities**:
- Infrastructure health monitoring
- Anomaly detection
- Performance analysis

**Example Request**:
```json
{
  "message": {
    "parts": [{"text": "Check the current system health status"}]
  }
}
```

## 🔍 Health and Status APIs

### Health Check
**GET** `/health`

Returns agent health status:

```json
{
  "status": "healthy",
  "timestamp": "2025-09-04T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "metrics": {
    "requests_processed": 1250,
    "average_response_time_ms": 145,
    "error_rate": 0.02
  }
}
```

### Readiness Check
**GET** `/ready`

Returns agent readiness status:

```json
{
  "ready": true,
  "timestamp": "2025-09-04T10:30:00Z",
  "dependencies": {
    "llm_service": "connected",
    "metrics_server": "connected",
    "event_queue": "ready"
  }
}
```

## 📊 Metrics API

### Prometheus Metrics
**GET** `/metrics`

Returns Prometheus-format metrics:

```
# HELP a2a_requests_total Total A2A requests processed
# TYPE a2a_requests_total counter
a2a_requests_total{agent_name="base",skill="general_assistance",status="success"} 1250

# HELP a2a_request_duration_seconds A2A request processing duration
# TYPE a2a_request_duration_seconds histogram
a2a_request_duration_seconds_bucket{agent_name="base",skill="general_assistance",le="0.1"} 950
a2a_request_duration_seconds_bucket{agent_name="base",skill="general_assistance",le="0.2"} 1200
a2a_request_duration_seconds_bucket{agent_name="base",skill="general_assistance",le="+Inf"} 1250

# HELP a2a_active_tasks Currently active tasks
# TYPE a2a_active_tasks gauge
a2a_active_tasks{agent_name="base"} 5
```

## ⚡ Event Streaming

### Server-Sent Events (SSE)
**GET** `/events/{context_id}`

Stream real-time events for a conversation:

```
data: {"type": "task_created", "task_id": "task-123", "timestamp": "2025-09-04T10:30:00Z"}

data: {"type": "message", "content": "Processing your request...", "timestamp": "2025-09-04T10:30:01Z"}

data: {"type": "task_completed", "task_id": "task-123", "timestamp": "2025-09-04T10:30:02Z"}
```

### WebSocket Events (Future)
**WS** `/ws/{context_id}`

Real-time bidirectional communication for enhanced interactivity.

## 🔐 Security and Authentication

### Authentication Headers
```
Authorization: Bearer <jwt_token>
X-API-Key: <api_key>
```

### CORS Configuration
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-API-Key
```

### Rate Limiting
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 🐛 Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request message is malformed",
    "details": {
      "field": "message.parts",
      "reason": "Missing required field"
    },
    "timestamp": "2025-09-04T10:30:00Z",
    "request_id": "req-12345"
  }
}
```

### Error Codes
- `INVALID_REQUEST` (400) - Malformed request
- `UNAUTHORIZED` (401) - Authentication required
- `FORBIDDEN` (403) - Access denied
- `NOT_FOUND` (404) - Resource not found
- `RATE_LIMITED` (429) - Too many requests
- `INTERNAL_ERROR` (500) - Server error
- `SERVICE_UNAVAILABLE` (503) - Service temporarily unavailable

## 📚 SDK Examples

### Python SDK Usage
```python
from a2a.client import A2AClient
from a2a.types import Message, TextPart, Part

# Initialize client
client = A2AClient("http://base-agent:8080")

# Send message
message = Message(parts=[Part(root=TextPart(text="Hello!"))])
response = await client.send_message(message)

print(f"Response: {response.messages[-1].parts[0].text}")
```

### JavaScript SDK Usage (Future)
```javascript
import { A2AClient } from '@a2a/client';

const client = new A2AClient('http://base-agent:8080');

const response = await client.sendMessage({
  parts: [{ text: 'Hello!' }]
});

console.log('Response:', response.messages[0].parts[0].text);
```

## 🔄 Protocol Versioning

### Version Headers
```
A2A-Protocol-Version: 0.3.3
A2A-API-Version: v1
```

### Backward Compatibility
The API maintains backward compatibility for:
- Message formats
- Response structures
- Error codes
- Endpoint paths

### Version Migration
When upgrading to new protocol versions:
1. Review breaking changes documentation
2. Update client SDKs
3. Test against new endpoints
4. Deploy with feature flags
5. Monitor for issues

This A2A Protocol API provides a robust foundation for building scalable, interoperable AI agent systems with standardized communication patterns and enterprise-grade reliability.
