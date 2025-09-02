"""
Test Helpers

Common classes and utilities for A2A testing framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import json


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_name: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None
    
    def __post_init__(self):
        """Calculate duration when end_time is set."""
        if self.end_time and not self.duration:
            self.duration = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "test_name": self.test_name,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "message": self.message,
            "details": self.details,
            "error": str(self.error) if self.error else None
        }


@dataclass
class TestCase:
    """Definition of a single test case."""
    name: str
    description: str
    agent_endpoint: str
    test_data: Dict[str, Any]
    expected_response: Optional[Dict[str, Any]] = None
    timeout: int = 30
    retries: int = 3
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "agent_endpoint": self.agent_endpoint,
            "test_data": self.test_data,
            "expected_response": self.expected_response,
            "timeout": self.timeout,
            "retries": self.retries,
            "tags": self.tags
        }


@dataclass
class TestSuite:
    """Collection of test cases and execution results."""
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    results: List[TestResult] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Total execution duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def summary(self) -> Dict[str, int]:
        """Summary of test results."""
        summary = {status.value: 0 for status in TestStatus}
        for result in self.results:
            summary[result.status.value] += 1
        return summary
    
    def add_test_case(self, test_case: TestCase):
        """Add a test case to the suite."""
        self.test_cases.append(test_case)
    
    def add_result(self, result: TestResult):
        """Add a test result to the suite."""
        self.results.append(result)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "results": [r.to_dict() for r in self.results],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "summary": self.summary
        }
    
    def save_to_file(self, filepath: str):
        """Save test suite results to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


def create_test_message(text: str, message_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a standard A2A message for testing."""
    import uuid
    
    return {
        "role": "user",
        "parts": [
            {
                "kind": "text",
                "text": text
            }
        ],
        "messageId": message_id or str(uuid.uuid4())
    }


def create_jsonrpc_request(method: str, params: Dict[str, Any], request_id: Union[str, int] = 1) -> Dict[str, Any]:
    """Create a JSON-RPC 2.0 request."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params
    }


def validate_jsonrpc_response(response: Dict[str, Any]) -> bool:
    """Validate JSON-RPC 2.0 response format."""
    required_fields = ["jsonrpc", "id"]
    if not all(field in response for field in required_fields):
        return False
    
    if response["jsonrpc"] != "2.0":
        return False
    
    # Must have either result or error, but not both
    has_result = "result" in response
    has_error = "error" in response
    
    return has_result != has_error  # XOR - exactly one should be true
