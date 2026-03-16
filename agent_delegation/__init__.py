"""Agent Delegation System - Production-ready task delegation for custom agents."""

__version__ = "1.0.0"
__author__ = "Todd Nicholas"
__all__ = [
    # Core
    'Coordinator',
    'CoordinatorConfig',
    'Task',
    'TaskStatus',
    'TaskPriority',
    'Agent',
    'AgentCapability',
    'AgentStatus',
    # Examples
    'DataProcessingAgent',
    'APICallAgent',
]

from .core.coordinator import Coordinator, CoordinatorConfig
from .core.task import Task, TaskStatus, TaskPriority
from .core.agent import Agent, AgentCapability, AgentStatus
from .agents.data_processor import DataProcessingAgent
from .agents.api_caller import APICallAgent
