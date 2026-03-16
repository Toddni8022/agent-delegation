"""Basic usage example of the agent delegation system."""

import asyncio
import logging
from agent_delegation import (
    Coordinator,
    CoordinatorConfig,
    Task,
    TaskPriority,
    DataProcessingAgent,
    APICallAgent,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_basic_delegation():
    """Basic example of task delegation."""
    logger.info("=== Basic Task Delegation Example ===\n")
    
    # Create coordinator with configuration
    config = CoordinatorConfig(
        worker_count=2,
        task_timeout=30,
        enable_logging=True,
        log_level="INFO"
    )
    coordinator = Coordinator(config)
    
    # Create and register agents
    data_agent = DataProcessingAgent(agent_id="data-processor-1")
    coordinator.register_agent(data_agent)
    
    logger.info(f"Registered agent: {data_agent.name}")
    logger.info(f"Agent capabilities: {data_agent.get_capabilities()}\n")
    
    # Create tasks
    tasks = [
        Task(
            task_type="data_processing",
            params={
                "operation": "transform",
                "data": "hello world"
            },
            priority=TaskPriority.HIGH
        ),
        Task(
            task_type="data_processing",
            params={
                "operation": "aggregate",
                "data": [1, 2, 3, 4, 5],
                "type": "sum"
            },
            priority=TaskPriority.MEDIUM
        ),
        Task(
            task_type="data_processing",
            params={
                "operation": "sort",
                "data": [5, 2, 8, 1, 9, 3]
            },
            priority=TaskPriority.LOW
        ),
    ]
    
    # Submit tasks
    task_ids = []
    for task in tasks:
        task_id = coordinator.submit_task(task)
        task_ids.append(task_id)
        logger.info(f"Submitted task {task_id}: {task.task_type} (priority: {task.priority.name})")
    
    # Start coordinator
    await coordinator.start()
    logger.info("\nCoordinator started\n")
    
    # Wait for all tasks to complete
    results = []
    for task_id in task_ids:
        result = await coordinator.wait_for_task(task_id, timeout=10)
        if result:
            results.append(result)
            logger.info(f"Task {task_id} completed: {result['result']}")
        else:
            logger.error(f"Task {task_id} timeout or failed")
    
    # Get and display statistics
    stats = coordinator.get_stats()
    logger.info(f"\n=== Coordinator Statistics ===")
    logger.info(f"Completed tasks: {stats['completed_tasks']}")
    logger.info(f"Failed tasks: {stats['failed_tasks']}")
    logger.info(f"Queue size: {stats['queue_size']}")
    logger.info(f"Uptime: {stats['uptime_seconds']:.2f}s")
    
    # Display agent statistics
    logger.info(f"\n=== Agent Statistics ===")
    for agent in coordinator.get_agents():
        logger.info(f"Agent: {agent.name}")
        logger.info(f"  Status: {agent.status.value}")
        logger.info(f"  Total tasks: {agent.stats.total_tasks}")
        logger.info(f"  Completed: {agent.stats.completed_tasks}")
        logger.info(f"  Failed: {agent.stats.failed_tasks}")
        logger.info(f"  Avg runtime: {agent.stats.avg_runtime:.2f}s")
    
    # Stop coordinator
    await coordinator.stop()
    logger.info("\nCoordinator stopped")


async def example_with_callbacks():
    """Example with task completion callbacks."""
    logger.info("\n=== Task Completion Callbacks Example ===\n")
    
    coordinator = Coordinator(CoordinatorConfig(worker_count=1))
    agent = DataProcessingAgent(agent_id="data-agent-2")
    coordinator.register_agent(agent)
    
    # Callback functions
    async def on_task_complete(task):
        logger.info(f"Callback: Task {task.task_id} completed with result: {task.result}")
    
    def sync_callback(task):
        logger.info(f"Sync callback: Task {task.task_id} status: {task.status.value}")
    
    # Create and submit task with callbacks
    task = Task(
        task_type="data_processing",
        params={"operation": "aggregate", "data": [10, 20, 30], "type": "avg"}
    )
    task_id = coordinator.submit_task(task)
    
    # Register callbacks
    coordinator.register_callback(task_id, on_task_complete)
    coordinator.register_callback(task_id, sync_callback)
    
    # Start and run
    await coordinator.start()
    await coordinator.wait_for_task(task_id, timeout=5)
    await coordinator.stop()


async def example_multiple_agents():
    """Example with multiple agents and task routing."""
    logger.info("\n=== Multiple Agents with Task Routing Example ===\n")
    
    coordinator = Coordinator(CoordinatorConfig(worker_count=3))
    
    # Register multiple agents
    data_agent = DataProcessingAgent(agent_id="data-1", max_concurrent_tasks=3)
    api_agent = APICallAgent(agent_id="api-1", max_concurrent_tasks=2)
    
    coordinator.register_agent(data_agent)
    coordinator.register_agent(api_agent)
    
    logger.info(f"Registered {len(coordinator.get_agents())} agents")
    
    # Create mixed workload
    tasks = []
    
    # Data processing tasks
    for i in range(3):
        tasks.append(Task(
            task_type="data_processing",
            params={"operation": "sort", "data": [5, 2, 8, 1, 9]},
            metadata={"batch": i}
        ))
    
    # Submit tasks
    task_ids = []
    for task in tasks:
        task_id = coordinator.submit_task(task)
        task_ids.append(task_id)
    
    logger.info(f"Submitted {len(task_ids)} tasks\n")
    
    # Start and monitor
    await coordinator.start()
    
    # Track completion
    completed = 0
    for task_id in task_ids:
        result = await coordinator.wait_for_task(task_id, timeout=10)
        if result:
            completed += 1
            logger.info(f"Task completed: {result['status']}")
    
    logger.info(f"\nCompleted: {completed}/{len(task_ids)} tasks")
    
    # Show agent utilization
    logger.info(f"\n=== Agent Utilization ===")
    for agent in coordinator.get_agents():
        logger.info(f"{agent.name}: {agent.stats.total_tasks} tasks, "
                   f"avg runtime: {agent.stats.avg_runtime:.2f}s")
    
    await coordinator.stop()


async def example_priority_queue():
    """Example showing priority queue behavior."""
    logger.info("\n=== Priority Queue Example ===\n")
    
    coordinator = Coordinator(CoordinatorConfig(worker_count=1))
    agent = DataProcessingAgent()
    coordinator.register_agent(agent)
    
    # Submit tasks with different priorities
    task_ids = []
    
    for priority, name in [
        (TaskPriority.LOW, "Low Priority"),
        (TaskPriority.CRITICAL, "Critical"),
        (TaskPriority.MEDIUM, "Medium Priority"),
    ]:
        task = Task(
            task_type="data_processing",
            params={"operation": "transform", "data": name},
            priority=priority,
            metadata={"name": name}
        )
        task_id = coordinator.submit_task(task)
        task_ids.append((task_id, name))
        logger.info(f"Submitted {name}: {priority.name}")
    
    logger.info("\nExecuting tasks (should process CRITICAL first)...\n")
    
    await coordinator.start()
    await asyncio.sleep(2)  # Let tasks process
    await coordinator.stop()
    
    # Display results in completion order
    logger.info("\nTask completion order:")
    for task_id, name in task_ids:
        result = coordinator.task_results.get(task_id)
        if result:
            logger.info(f"  {name}: {result.get('result')}")


async def main():
    """Run all examples."""
    try:
        await example_basic_delegation()
        await example_with_callbacks()
        await example_multiple_agents()
        await example_priority_queue()
        
        logger.info("\n=== All Examples Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
