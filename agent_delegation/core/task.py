"""Task class and related enums for the delegation system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
import uuid


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 3
    MEDIUM = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class Task:
    """
    Represents a task to be executed by an agent.
    
    Attributes:
        task_type: Type/category of the task (e.g., 'data_processing', 'api_call')
        params: Task parameters passed to the agent
        priority: Task priority level (default: MEDIUM)
        task_id: Unique identifier (auto-generated if not provided)
        status: Current task status
        agent_id: ID of assigned agent (None if not yet assigned)
        result: Task result/output (populated after execution)
        error: Error message if task failed
        created_at: Task creation timestamp
        started_at: When task execution started
        completed_at: When task execution completed
        retry_count: Number of retry attempts
        max_retries: Maximum allowed retries (default: 3)
        timeout: Execution timeout in seconds (None for no timeout)
        metadata: Additional metadata about the task
        callbacks: Webhook URLs to call on task completion
    """
    
    task_type: str
    params: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    task_id: Optional[str] = None
    status: TaskStatus = field(default=TaskStatus.PENDING)
    agent_id: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    callbacks: list = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize task_id if not provided."""
        if self.task_id is None:
            self.task_id = str(uuid.uuid4())
    
    def mark_started(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
    
    def mark_completed(self, result: Any) -> None:
        """Mark task as completed with result."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
        self.error = None
    
    def mark_failed(self, error: str) -> None:
        """Mark task as failed with error message."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error
        self.result = None
    
    def mark_retrying(self) -> None:
        """Mark task as being retried."""
        self.status = TaskStatus.RETRYING
        self.retry_count += 1
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries and self.status == TaskStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'status': self.status.value,
            'priority': self.priority.name,
            'agent_id': self.agent_id,
            'result': self.result,
            'error': self.error,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'params': self.params,
            'metadata': self.metadata,
        }
