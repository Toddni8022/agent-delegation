"""Tests for Task class."""

import pytest
from datetime import datetime
from agent_delegation.core.task import Task, TaskStatus, TaskPriority


class TestTask:
    """Test Task class."""
    
    def test_task_creation_with_defaults(self):
        """Test creating task with default values."""
        task = Task(
            task_type="data_processing",
            params={"operation": "transform"}
        )
        
        assert task.task_type == "data_processing"
        assert task.params == {"operation": "transform"}
        assert task.priority == TaskPriority.MEDIUM
        assert task.status == TaskStatus.PENDING
        assert task.task_id is not None
        assert task.agent_id is None
        assert task.retry_count == 0
        assert task.max_retries == 3
    
    def test_task_creation_with_custom_values(self):
        """Test creating task with custom values."""
        task = Task(
            task_type="api_call",
            params={"url": "https://example.com"},
            priority=TaskPriority.HIGH,
            task_id="custom-id",
            max_retries=5,
            timeout=60
        )
        
        assert task.task_id == "custom-id"
        assert task.priority == TaskPriority.HIGH
        assert task.max_retries == 5
        assert task.timeout == 60
    
    def test_task_status_transitions(self):
        """Test task status transitions."""
        task = Task(task_type="test", params={})
        
        assert task.status == TaskStatus.PENDING
        
        task.mark_started()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None
        
        task.mark_completed("result")
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert task.result == "result"
        assert task.error is None
    
    def test_task_failure(self):
        """Test task failure."""
        task = Task(task_type="test", params={})
        
        task.mark_failed("Test error")
        assert task.status == TaskStatus.FAILED
        assert task.error == "Test error"
        assert task.result is None
        assert task.completed_at is not None
    
    def test_task_retry(self):
        """Test task retry logic."""
        task = Task(task_type="test", params={}, max_retries=3)
        
        assert task.can_retry() is False  # Not failed yet
        
        task.mark_failed("Error")
        assert task.can_retry() is True
        assert task.status == TaskStatus.FAILED
        
        task.mark_retrying()
        assert task.retry_count == 1
        assert task.status == TaskStatus.RETRYING
        
        # Retry multiple times
        for i in range(2, 3):
            task.mark_failed("Error")
            task.mark_retrying()
            assert task.retry_count == i
        
        # Max retries reached (retry_count=2, max_retries=3, can retry once more)
        task.mark_failed("Error")
        task.mark_retrying()
        assert task.retry_count == 3
        
        # Now max retries reached
        task.mark_failed("Error")
        assert task.can_retry() is False
    
    def test_task_to_dict(self):
        """Test task serialization."""
        task = Task(
            task_type="test",
            params={"key": "value"},
            priority=TaskPriority.HIGH
        )
        
        task_dict = task.to_dict()
        
        assert task_dict['task_id'] == task.task_id
        assert task_dict['task_type'] == "test"
        assert task_dict['status'] == TaskStatus.PENDING.value
        assert task_dict['priority'] == TaskPriority.HIGH.name
        assert task_dict['params'] == {"key": "value"}
    
    def test_task_metadata(self):
        """Test task metadata."""
        metadata = {"user_id": 123, "source": "webhook"}
        task = Task(
            task_type="test",
            params={},
            metadata=metadata
        )
        
        assert task.metadata == metadata
        assert task.to_dict()['metadata'] == metadata
    
    def test_task_callbacks(self):
        """Test task callbacks."""
        callbacks = ["http://example.com/callback1", "http://example.com/callback2"]
        task = Task(
            task_type="test",
            params={},
            callbacks=callbacks
        )
        
        assert task.callbacks == callbacks
