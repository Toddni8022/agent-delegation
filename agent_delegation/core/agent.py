"""Base Agent class for task execution."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import uuid


class AgentStatus(Enum):
    """Agent operational status."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentCapability:
    """
    Represents a capability/skill of an agent.
    
    Attributes:
        name: Capability name (e.g., 'data_processing')
        version: Capability version (e.g., '1.0')
        max_concurrent: Max concurrent tasks for this capability
    """
    name: str
    version: str = "1.0"
    max_concurrent: int = 1


@dataclass
class AgentStats:
    """Statistics about agent performance."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_runtime: float = 0.0  # seconds
    avg_runtime: float = 0.0    # seconds
    last_task_at: Optional[datetime] = None
    uptime_pct: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'total_runtime': self.total_runtime,
            'avg_runtime': self.avg_runtime,
            'last_task_at': self.last_task_at.isoformat() if self.last_task_at else None,
            'uptime_pct': self.uptime_pct,
        }


class Agent(ABC):
    """
    Abstract base class for agents that execute tasks.
    
    Agents define their capabilities and implement task execution logic.
    The coordinator uses agent capabilities to route tasks appropriately.
    """
    
    def __init__(self, agent_id: Optional[str] = None, 
                 name: Optional[str] = None,
                 max_concurrent_tasks: int = 1):
        """
        Initialize an agent.
        
        Args:
            agent_id: Unique identifier for the agent (auto-generated if not provided)
            name: Human-readable agent name
            max_concurrent_tasks: Maximum concurrent tasks this agent can handle
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.capabilities: Dict[str, AgentCapability] = {}
        self.status = AgentStatus.IDLE
        self.current_tasks: Set[str] = set()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.stats = AgentStats()
        self._last_error: Optional[str] = None
        self._registered_at = datetime.utcnow()
    
    def register_capability(self, capability: AgentCapability) -> None:
        """
        Register a capability for this agent.
        
        Args:
            capability: AgentCapability object
        """
        self.capabilities[capability.name] = capability
    
    def register_capabilities(self, capabilities: List[AgentCapability]) -> None:
        """
        Register multiple capabilities.
        
        Args:
            capabilities: List of AgentCapability objects
        """
        for cap in capabilities:
            self.register_capability(cap)
    
    def has_capability(self, capability_name: str) -> bool:
        """Check if agent has a specific capability."""
        return capability_name in self.capabilities
    
    def get_capabilities(self) -> List[str]:
        """Get list of capability names."""
        return list(self.capabilities.keys())
    
    def can_accept_task(self) -> bool:
        """Check if agent can accept more tasks."""
        return len(self.current_tasks) < self.max_concurrent_tasks and \
               self.status != AgentStatus.ERROR and \
               self.status != AgentStatus.OFFLINE
    
    def can_handle(self, task_type: str) -> bool:
        """
        Check if agent can handle a specific task type.
        
        Args:
            task_type: Type of task to check
            
        Returns:
            True if agent can handle this task type
        """
        return self.has_capability(task_type)
    
    async def execute(self, task: 'Task') -> Any:
        """
        Execute a task. Must be implemented by subclasses.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
            
        Raises:
            NotImplementedError: If not implemented by subclass
            Exception: If task execution fails
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def on_task_start(self, task_id: str) -> None:
        """Called when task execution starts."""
        self.current_tasks.add(task_id)
        if len(self.current_tasks) > 0:
            self.status = AgentStatus.BUSY
    
    def on_task_complete(self, task_id: str, runtime: float, success: bool = True) -> None:
        """Called when task execution completes."""
        self.current_tasks.discard(task_id)
        
        self.stats.total_tasks += 1
        self.stats.total_runtime += runtime
        self.stats.avg_runtime = self.stats.total_runtime / self.stats.total_tasks
        self.stats.last_task_at = datetime.utcnow()
        
        if success:
            self.stats.completed_tasks += 1
        else:
            self.stats.failed_tasks += 1
        
        if len(self.current_tasks) == 0:
            self.status = AgentStatus.IDLE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary."""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'status': self.status.value,
            'capabilities': self.get_capabilities(),
            'current_tasks': len(self.current_tasks),
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'stats': self.stats.to_dict(),
            'registered_at': self._registered_at.isoformat(),
        }
