"""Tests for Agent class."""

import pytest
import asyncio
from datetime import datetime
from agent_delegation.core.agent import Agent, AgentCapability, AgentStatus
from agent_delegation.core.task import Task


class SimpleTestAgent(Agent):
    """Test agent implementation."""
    
    async def execute(self, task: Task):
        """Simple test implementation."""
        await asyncio.sleep(0.01)
        return f"Processed: {task.task_id}"


class TestAgentCapability:
    """Test AgentCapability class."""
    
    def test_capability_creation(self):
        """Test capability creation."""
        cap = AgentCapability("data_processing", version="2.0", max_concurrent=5)
        
        assert cap.name == "data_processing"
        assert cap.version == "2.0"
        assert cap.max_concurrent == 5
    
    def test_capability_defaults(self):
        """Test capability defaults."""
        cap = AgentCapability("test")
        
        assert cap.version == "1.0"
        assert cap.max_concurrent == 1


class TestAgentClass:
    """Test Agent class."""
    
    def test_agent_creation(self):
        """Test agent creation."""
        agent = SimpleTestAgent(agent_id="agent-1", name="TestAgent", max_concurrent_tasks=2)
        
        assert agent.agent_id == "agent-1"
        assert agent.name == "TestAgent"
        assert agent.max_concurrent_tasks == 2
        assert agent.status == AgentStatus.IDLE
    
    def test_agent_auto_id(self):
        """Test agent auto-generates ID."""
        agent = SimpleTestAgent()
        assert agent.agent_id is not None
        assert len(agent.agent_id) > 0
    
    def test_agent_capabilities(self):
        """Test agent capability management."""
        agent = SimpleTestAgent()
        
        cap1 = AgentCapability("data_processing")
        cap2 = AgentCapability("api_call")
        
        agent.register_capability(cap1)
        assert agent.has_capability("data_processing")
        assert not agent.has_capability("api_call")
        
        agent.register_capabilities([cap2])
        assert agent.has_capability("api_call")
        
        capabilities = agent.get_capabilities()
        assert "data_processing" in capabilities
        assert "api_call" in capabilities
    
    def test_can_accept_task(self):
        """Test task acceptance logic."""
        agent = SimpleTestAgent(max_concurrent_tasks=2)
        
        assert agent.can_accept_task() is True
        
        # Add tasks
        agent.current_tasks.add("task-1")
        assert agent.can_accept_task() is True
        
        agent.current_tasks.add("task-2")
        assert agent.can_accept_task() is False
    
    def test_can_handle_task_type(self):
        """Test task type handling."""
        agent = SimpleTestAgent()
        agent.register_capability(AgentCapability("data_processing"))
        
        assert agent.can_handle("data_processing") is True
        assert agent.can_handle("api_call") is False
    
    @pytest.mark.asyncio
    async def test_task_lifecycle(self):
        """Test task lifecycle callbacks."""
        agent = SimpleTestAgent()
        
        # Start task
        task_id = "task-1"
        agent.on_task_start(task_id)
        
        assert task_id in agent.current_tasks
        assert agent.status == AgentStatus.BUSY
        assert agent.stats.total_tasks == 0
        
        # Complete task
        agent.on_task_complete(task_id, runtime=1.5, success=True)
        
        assert task_id not in agent.current_tasks
        assert agent.status == AgentStatus.IDLE
        assert agent.stats.total_tasks == 1
        assert agent.stats.completed_tasks == 1
        assert agent.stats.total_runtime == 1.5
        assert agent.stats.avg_runtime == 1.5
    
    def test_task_failure_tracking(self):
        """Test failure tracking."""
        agent = SimpleTestAgent()
        
        # Failed task
        agent.stats.total_tasks = 1
        agent.on_task_complete("task-1", runtime=0.5, success=False)
        
        assert agent.stats.failed_tasks == 1
        assert agent.stats.total_tasks == 2
        assert agent.stats.completed_tasks == 0
    
    def test_agent_to_dict(self):
        """Test agent serialization."""
        agent = SimpleTestAgent(agent_id="agent-1", name="TestAgent")
        agent.register_capability(AgentCapability("test_cap"))
        
        agent_dict = agent.to_dict()
        
        assert agent_dict['agent_id'] == "agent-1"
        assert agent_dict['name'] == "TestAgent"
        assert agent_dict['status'] == AgentStatus.IDLE.value
        assert 'test_cap' in agent_dict['capabilities']
        assert agent_dict['stats']['total_tasks'] == 0
    
    @pytest.mark.asyncio
    async def test_execute_task(self):
        """Test task execution."""
        agent = SimpleTestAgent()
        agent.register_capability(AgentCapability("test"))
        
        task = Task(task_type="test", params={})
        result = await agent.execute(task)
        
        assert "Processed" in result
        assert task.task_id in result
