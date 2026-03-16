"""Main Coordinator class for task delegation."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Coroutine
from datetime import datetime
from dataclasses import dataclass
import time

from .task import Task, TaskStatus, TaskPriority
from .agent import Agent, AgentStatus


logger = logging.getLogger(__name__)


@dataclass
class CoordinatorConfig:
    """Configuration for the Coordinator."""
    max_queue_size: Optional[int] = None
    worker_count: int = 4
    task_timeout: Optional[int] = 300  # 5 minutes default
    enable_logging: bool = True
    log_level: str = "INFO"


class TaskQueue:
    """Priority-based task queue."""
    
    def __init__(self, max_size: Optional[int] = None):
        """
        Initialize task queue.
        
        Args:
            max_size: Maximum queue size (None for unlimited)
        """
        self.max_size = max_size
        self.queue: List[Task] = []
    
    def add(self, task: Task) -> None:
        """
        Add task to queue.
        
        Args:
            task: Task to add
            
        Raises:
            RuntimeError: If queue is full
        """
        if self.max_size and len(self.queue) >= self.max_size:
            raise RuntimeError(f"Queue is full (max size: {self.max_size})")
        
        task.status = TaskStatus.QUEUED
        self.queue.append(task)
        self._sort()
    
    def get_next(self) -> Optional[Task]:
        """Get next task from queue."""
        if not self.queue:
            return None
        return self.queue.pop(0)
    
    def _sort(self) -> None:
        """Sort queue by priority."""
        self.queue.sort(key=lambda t: (t.priority.value, t.created_at))
    
    def size(self) -> int:
        """Get queue size."""
        return len(self.queue)
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self.queue) == 0
    
    def get_tasks(self) -> List[Task]:
        """Get all tasks in queue."""
        return self.queue.copy()


class AgentPool:
    """Manages a pool of agents."""
    
    def __init__(self):
        """Initialize agent pool."""
        self.agents: Dict[str, Agent] = {}
    
    def register(self, agent: Agent) -> None:
        """
        Register an agent.
        
        Args:
            agent: Agent to register
            
        Raises:
            ValueError: If agent ID already exists
        """
        if agent.agent_id in self.agents:
            raise ValueError(f"Agent {agent.agent_id} already registered")
        
        self.agents[agent.agent_id] = agent
        logger.info(f"Agent registered: {agent.agent_id} ({agent.name})")
    
    def unregister(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent unregistered: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[Agent]:
        """Get all agents."""
        return list(self.agents.values())
    
    def get_agents_by_capability(self, capability: str) -> List[Agent]:
        """Get all agents with specific capability."""
        return [a for a in self.agents.values() if a.has_capability(capability)]
    
    def get_available_agents(self, capability: str) -> List[Agent]:
        """Get available agents with specific capability."""
        candidates = self.get_agents_by_capability(capability)
        return [a for a in candidates if a.can_accept_task()]
    
    def size(self) -> int:
        """Get number of registered agents."""
        return len(self.agents)


class Coordinator:
    """
    Main coordinator for task delegation.
    
    Manages task queue, agent pool, routing, and execution.
    """
    
    def __init__(self, config: Optional[CoordinatorConfig] = None):
        """
        Initialize coordinator.
        
        Args:
            config: Coordinator configuration (uses defaults if not provided)
        """
        self.config = config or CoordinatorConfig()
        
        # Setup logging
        if self.config.enable_logging:
            logging.basicConfig(
                level=getattr(logging, self.config.log_level),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        self.queue = TaskQueue(self.config.max_queue_size)
        self.agent_pool = AgentPool()
        self.task_results: Dict[str, Any] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self._running = False
        self._start_time = datetime.utcnow()
        self._workers: List[asyncio.Task] = []
    
    # ========== Task Management ==========
    
    def submit_task(self, task: Task) -> str:
        """
        Submit a task for execution.
        
        Args:
            task: Task to submit
            
        Returns:
            Task ID
            
        Raises:
            ValueError: If no agents can handle this task
        """
        if not self.agent_pool.get_available_agents(task.task_type):
            # Log warning but still queue the task
            logger.warning(f"No available agents for task type '{task.task_type}'")
        
        self.queue.add(task)
        logger.info(f"Task submitted: {task.task_id} (type: {task.task_type}, priority: {task.priority.name})")
        return task.task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        # Check if task completed and in results
        if task_id in self.task_results:
            return self.task_results[task_id]
        
        # Check queue
        for task in self.queue.get_tasks():
            if task.task_id == task_id:
                return task.to_dict()
        
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: ID of task to cancel
            
        Returns:
            True if task was cancelled
        """
        for task in self.queue.get_tasks():
            if task.task_id == task_id:
                task.status = TaskStatus.CANCELLED
                self.queue.queue.remove(task)
                logger.info(f"Task cancelled: {task_id}")
                return True
        
        return False
    
    # ========== Agent Management ==========
    
    def register_agent(self, agent: Agent) -> str:
        """
        Register an agent.
        
        Args:
            agent: Agent to register
            
        Returns:
            Agent ID
        """
        self.agent_pool.register(agent)
        return agent.agent_id
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent.
        
        Args:
            agent_id: Agent ID to unregister
            
        Returns:
            True if agent was unregistered
        """
        agent = self.agent_pool.get_agent(agent_id)
        if agent and len(agent.current_tasks) == 0:
            self.agent_pool.unregister(agent_id)
            logger.info(f"Agent unregistered: {agent_id}")
            return True
        
        return False
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self.agent_pool.get_agent(agent_id)
    
    def get_agents(self) -> List[Agent]:
        """Get all agents."""
        return self.agent_pool.get_all_agents()
    
    # ========== Callback Management ==========
    
    def register_callback(self, task_id: str, callback: Callable) -> None:
        """
        Register a callback for task completion.
        
        Args:
            task_id: Task ID
            callback: Async function to call when task completes
        """
        if task_id not in self.callbacks:
            self.callbacks[task_id] = []
        self.callbacks[task_id].append(callback)
    
    async def _trigger_callbacks(self, task: Task) -> None:
        """Trigger callbacks for a completed task."""
        callbacks = self.callbacks.get(task.task_id, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task)
                else:
                    callback(task)
            except Exception as e:
                logger.error(f"Error in callback for task {task.task_id}: {e}")
    
    # ========== Task Routing & Execution ==========
    
    def _find_agent_for_task(self, task: Task) -> Optional[Agent]:
        """
        Find best agent for task using capability matching.
        
        Prioritizes agents by:
        1. Capability match
        2. Available capacity
        3. Load (fewest current tasks)
        """
        available = self.agent_pool.get_available_agents(task.task_type)
        
        if not available:
            return None
        
        # Sort by current task load (least busy first)
        available.sort(key=lambda a: len(a.current_tasks))
        return available[0]
    
    async def _execute_task(self, task: Task, agent: Agent) -> None:
        """Execute a task on an agent."""
        task.agent_id = agent.agent_id
        task.status = TaskStatus.ASSIGNED
        
        agent.on_task_start(task.task_id)
        start_time = time.time()
        
        try:
            logger.info(f"Executing task {task.task_id} on agent {agent.agent_id}")
            task.mark_started()
            
            # Execute with timeout if configured
            timeout = task.timeout or self.config.task_timeout
            if timeout:
                result = await asyncio.wait_for(
                    agent.execute(task),
                    timeout=timeout
                )
            else:
                result = await agent.execute(task)
            
            task.mark_completed(result)
            runtime = time.time() - start_time
            agent.on_task_complete(task.task_id, runtime, success=True)
            
            logger.info(f"Task completed: {task.task_id} (runtime: {runtime:.2f}s)")
            self.task_results[task.task_id] = task.to_dict()
            
            # Trigger callbacks
            await self._trigger_callbacks(task)
            
        except asyncio.TimeoutError:
            error_msg = f"Task execution timeout after {task.timeout or self.config.task_timeout}s"
            task.mark_failed(error_msg)
            runtime = time.time() - start_time
            agent.on_task_complete(task.task_id, runtime, success=False)
            agent.status = AgentStatus.ERROR
            
            logger.error(f"Task timeout: {task.task_id}")
            self.task_results[task.task_id] = task.to_dict()
            await self._trigger_callbacks(task)
            
        except Exception as e:
            error_msg = f"Task execution failed: {str(e)}"
            task.mark_failed(error_msg)
            runtime = time.time() - start_time
            agent.on_task_complete(task.task_id, runtime, success=False)
            agent.status = AgentStatus.ERROR
            
            logger.error(f"Task failed: {task.task_id} - {error_msg}")
            self.task_results[task.task_id] = task.to_dict()
            await self._trigger_callbacks(task)
    
    async def _worker(self) -> None:
        """Worker coroutine that processes tasks from queue."""
        while self._running:
            try:
                task = self.queue.get_next()
                
                if not task:
                    await asyncio.sleep(0.1)
                    continue
                
                # Find agent for task
                agent = self._find_agent_for_task(task)
                
                if not agent:
                    # No agent available, put task back in queue
                    logger.warning(f"No agent available for task {task.task_id}, requeuing")
                    self.queue.add(task)
                    await asyncio.sleep(0.5)
                    continue
                
                # Execute task
                await self._execute_task(task, agent)
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)
    
    async def start(self) -> None:
        """Start the coordinator."""
        if self._running:
            logger.warning("Coordinator already running")
            return
        
        self._running = True
        self._start_time = datetime.utcnow()
        
        # Start worker coroutines
        self._workers = [
            asyncio.create_task(self._worker())
            for _ in range(self.config.worker_count)
        ]
        
        logger.info(f"Coordinator started with {self.config.worker_count} workers")
    
    async def stop(self) -> None:
        """Stop the coordinator."""
        self._running = False
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        logger.info("Coordinator stopped")
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[Task]:
        """
        Wait for a task to complete.
        
        Args:
            task_id: Task ID to wait for
            timeout: Maximum wait time in seconds
            
        Returns:
            Completed task or None if timeout
        """
        start = time.time()
        
        while self._running:
            if task_id in self.task_results:
                return self.task_results[task_id]
            
            if timeout and (time.time() - start) > timeout:
                return None
            
            await asyncio.sleep(0.1)
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get coordinator statistics."""
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        total_completed = len(self.task_results)
        failed_tasks = sum(
            1 for result in self.task_results.values()
            if result.get('status') == 'failed'
        )
        
        return {
            'uptime_seconds': uptime,
            'running': self._running,
            'queue_size': self.queue.size(),
            'agent_count': self.agent_pool.size(),
            'total_tasks_submitted': total_completed + self.queue.size(),
            'completed_tasks': total_completed,
            'failed_tasks': failed_tasks,
            'workers': self.config.worker_count,
        }
