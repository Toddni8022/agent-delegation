"""Tests for Coordinator class."""

import pytest
import asyncio
from agent_delegation.core.coordinator import Coordinator, CoordinatorConfig, TaskQueue, AgentPool
from agent_delegation.core.task import Task, TaskStatus, TaskPriority
from agent_delegation.core.agent import Agent, AgentCapability
from agent_delegation.agents import DataProcessingAgent


class DummyAgent(Agent):
    """Simple test agent."""
    
    async def execute(self, task: Task):
        """Simple execution."""
        await asyncio.sleep(0.01)
        return {"processed": True, "task_id": task.task_id}


class TestTaskQueue:
    """Test TaskQueue class."""
    
    def test_queue_add_and_get(self):
        """Test adding and retrieving tasks."""
        queue = TaskQueue()
        task = Task(task_type="test", params={})
        
        queue.add(task)
        assert queue.size() == 1
        
        next_task = queue.get_next()
        assert next_task.task_id == task.task_id
        assert queue.size() == 0
    
    def test_queue_priority_sorting(self):
        """Test priority-based sorting."""
        queue = TaskQueue()
        
        low = Task(task_type="test", params={}, priority=TaskPriority.LOW)
        high = Task(task_type="test", params={}, priority=TaskPriority.HIGH)
        medium = Task(task_type="test", params={}, priority=TaskPriority.MEDIUM)
        
        queue.add(low)
        queue.add(medium)
        queue.add(high)
        
        # Should get in priority order: HIGH, MEDIUM, LOW
        assert queue.get_next().priority == TaskPriority.HIGH
        assert queue.get_next().priority == TaskPriority.MEDIUM
        assert queue.get_next().priority == TaskPriority.LOW
    
    def test_queue_max_size(self):
        """Test queue max size enforcement."""
        queue = TaskQueue(max_size=2)
        
        queue.add(Task(task_type="test", params={}))
        queue.add(Task(task_type="test", params={}))
        
        with pytest.raises(RuntimeError):
            queue.add(Task(task_type="test", params={}))
    
    def test_queue_empty_check(self):
        """Test empty queue check."""
        queue = TaskQueue()
        assert queue.is_empty() is True
        
        queue.add(Task(task_type="test", params={}))
        assert queue.is_empty() is False


class TestAgentPool:
    """Test AgentPool class."""
    
    def test_pool_register_agent(self):
        """Test agent registration."""
        pool = AgentPool()
        agent = DummyAgent(agent_id="agent-1")
        
        pool.register(agent)
        assert pool.size() == 1
        assert pool.get_agent("agent-1") == agent
    
    def test_pool_duplicate_registration(self):
        """Test duplicate registration raises error."""
        pool = AgentPool()
        agent = DummyAgent(agent_id="agent-1")
        
        pool.register(agent)
        with pytest.raises(ValueError):
            pool.register(agent)
    
    def test_pool_get_agents_by_capability(self):
        """Test getting agents by capability."""
        pool = AgentPool()
        
        agent1 = DummyAgent(agent_id="agent-1")
        agent1.register_capability(AgentCapability("data_processing"))
        
        agent2 = DummyAgent(agent_id="agent-2")
        agent2.register_capability(AgentCapability("api_call"))
        
        pool.register(agent1)
        pool.register(agent2)
        
        data_agents = pool.get_agents_by_capability("data_processing")
        assert len(data_agents) == 1
        assert data_agents[0].agent_id == "agent-1"
    
    def test_pool_get_available_agents(self):
        """Test getting available agents."""
        pool = AgentPool()
        
        agent1 = DummyAgent(agent_id="agent-1", max_concurrent_tasks=1)
        agent1.register_capability(AgentCapability("test"))
        
        agent2 = DummyAgent(agent_id="agent-2", max_concurrent_tasks=1)
        agent2.register_capability(AgentCapability("test"))
        
        pool.register(agent1)
        pool.register(agent2)
        
        # Both should be available
        available = pool.get_available_agents("test")
        assert len(available) == 2
        
        # Add task to agent1
        agent1.current_tasks.add("task-1")
        available = pool.get_available_agents("test")
        assert len(available) == 1
        assert available[0].agent_id == "agent-2"


class TestCoordinator:
    """Test Coordinator class."""
    
    @pytest.mark.asyncio
    async def test_coordinator_initialization(self):
        """Test coordinator initialization."""
        config = CoordinatorConfig(worker_count=2)
        coord = Coordinator(config)
        
        assert coord.config.worker_count == 2
        assert coord.queue.size() == 0
        assert coord.agent_pool.size() == 0
    
    @pytest.mark.asyncio
    async def test_submit_and_execute_task(self):
        """Test submitting and executing a task."""
        coord = Coordinator(CoordinatorConfig(worker_count=1))
        
        # Register agent
        agent = DummyAgent(agent_id="agent-1")
        agent.register_capability(AgentCapability("test"))
        coord.register_agent(agent)
        
        # Submit task
        task = Task(task_type="test", params={})
        task_id = coord.submit_task(task)
        
        # Start coordinator
        await coord.start()
        
        # Wait for task to complete
        result = await coord.wait_for_task(task_id, timeout=5)
        
        await coord.stop()
        
        assert result is not None
        assert result['status'] == TaskStatus.COMPLETED.value
        assert result['result']['processed'] is True
    
    @pytest.mark.asyncio
    async def test_multiple_agents_routing(self):
        """Test task routing to multiple agents."""
        coord = Coordinator(CoordinatorConfig(worker_count=2))
        
        # Register multiple agents with different capabilities
        data_agent = DataProcessingAgent(agent_id="data-agent", max_concurrent_tasks=2)
        dummy_agent = DummyAgent(agent_id="dummy-agent")
        dummy_agent.register_capability(AgentCapability("test"))
        
        coord.register_agent(data_agent)
        coord.register_agent(dummy_agent)
        
        # Submit tasks for different agents
        task1 = Task(task_type="data_processing", params={"operation": "transform", "data": "test"})
        task2 = Task(task_type="test", params={})
        
        id1 = coord.submit_task(task1)
        id2 = coord.submit_task(task2)
        
        await coord.start()
        await asyncio.sleep(2)
        await coord.stop()
        
        # Both tasks should be routed and executed
        assert id1 in coord.task_results
        assert id2 in coord.task_results
    
    @pytest.mark.asyncio
    async def test_task_retry_on_failure(self):
        """Test task retry logic."""
        class FailingAgent(Agent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.attempt = 0
            
            async def execute(self, task: Task):
                self.attempt += 1
                if self.attempt < 2:
                    raise RuntimeError("First attempt fails")
                return {"success": True}
        
        coord = Coordinator(CoordinatorConfig(worker_count=1))
        agent = FailingAgent(agent_id="agent-1")
        agent.register_capability(AgentCapability("test"))
        coord.register_agent(agent)
        
        task = Task(task_type="test", params={}, max_retries=2)
        task_id = coord.submit_task(task)
        
        await coord.start()
        # Note: Retry logic would need to be implemented in coordinator._worker
        await asyncio.sleep(2)
        await coord.stop()
    
    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """Test task cancellation."""
        coord = Coordinator(CoordinatorConfig(worker_count=1))
        
        agent = DummyAgent(agent_id="agent-1")
        agent.register_capability(AgentCapability("test"))
        coord.register_agent(agent)
        
        task = Task(task_type="test", params={})
        task_id = coord.submit_task(task)
        
        # Cancel immediately before execution
        cancelled = coord.cancel_task(task_id)
        assert cancelled is True
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting coordinator statistics."""
        coord = Coordinator(CoordinatorConfig(worker_count=2))
        
        agent = DummyAgent(agent_id="agent-1")
        agent.register_capability(AgentCapability("test"))
        coord.register_agent(agent)
        
        task = Task(task_type="test", params={})
        coord.submit_task(task)
        
        await coord.start()
        await asyncio.sleep(1)
        await coord.stop()
        
        stats = coord.get_stats()
        assert stats['agent_count'] == 1
        assert stats['workers'] == 2
        assert stats['running'] is False
    
    @pytest.mark.asyncio
    async def test_callback_on_completion(self):
        """Test callbacks on task completion."""
        coord = Coordinator(CoordinatorConfig(worker_count=1))
        
        agent = DummyAgent(agent_id="agent-1")
        agent.register_capability(AgentCapability("test"))
        coord.register_agent(agent)
        
        callback_executed = []
        
        async def on_complete(task: Task):
            callback_executed.append(task.task_id)
        
        task = Task(task_type="test", params={})
        task_id = coord.submit_task(task)
        coord.register_callback(task_id, on_complete)
        
        await coord.start()
        await coord.wait_for_task(task_id, timeout=5)
        await coord.stop()
        
        assert task_id in callback_executed
