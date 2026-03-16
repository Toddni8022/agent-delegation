"""Advanced workflow example with custom agents and monitoring."""

import asyncio
import logging
from datetime import datetime
from agent_delegation import (
    Coordinator,
    CoordinatorConfig,
    Task,
    TaskPriority,
    Agent,
    AgentCapability,
)
from agent_delegation.core.task import Task

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationAgent(Agent):
    """Custom agent that validates data."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_capability(AgentCapability("validate_data"))
    
    async def execute(self, task: Task):
        """Validate input data."""
        data = task.params.get("data")
        rules = task.params.get("rules", {})
        
        logger.info(f"Validating data: {data}")
        
        # Simulate validation
        await asyncio.sleep(0.1)
        
        errors = []
        if rules.get("required") and not data:
            errors.append("Data is required")
        if rules.get("min_length") and len(str(data)) < rules["min_length"]:
            errors.append(f"Data too short (min: {rules['min_length']})")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "data": data
        }


class EnrichmentAgent(Agent):
    """Custom agent that enriches data."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_capability(AgentCapability("enrich_data"))
    
    async def execute(self, task: Task):
        """Enrich data with additional information."""
        data = task.params.get("data")
        enrichment_type = task.params.get("type", "default")
        
        logger.info(f"Enriching data: {data} with type: {enrichment_type}")
        
        # Simulate enrichment
        await asyncio.sleep(0.2)
        
        enrichments = {
            "default": {"timestamp": datetime.utcnow().isoformat(), "source": "system"},
            "geo": {"latitude": 40.7128, "longitude": -74.0060, "country": "US"},
            "metadata": {"version": "1.0", "schema": "v2"},
        }
        
        return {
            "original": data,
            "enriched": {**enrichments.get(enrichment_type, {}), "data": data}
        }


class StorageAgent(Agent):
    """Custom agent that stores processed data."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_capability(AgentCapability("store_data"))
        self.storage = {}
    
    async def execute(self, task: Task):
        """Store data in simulated database."""
        data = task.params.get("data")
        collection = task.params.get("collection", "default")
        
        logger.info(f"Storing data in '{collection}' collection")
        
        # Simulate storage
        await asyncio.sleep(0.15)
        
        if collection not in self.storage:
            self.storage[collection] = []
        
        doc_id = len(self.storage[collection])
        self.storage[collection].append({"id": doc_id, "data": data})
        
        return {
            "collection": collection,
            "doc_id": doc_id,
            "status": "stored"
        }


class NotificationAgent(Agent):
    """Custom agent that sends notifications."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_capability(AgentCapability("notify"))
    
    async def execute(self, task: Task):
        """Send notification."""
        recipient = task.params.get("recipient")
        message = task.params.get("message")
        
        logger.info(f"Sending notification to {recipient}: {message}")
        
        # Simulate sending notification
        await asyncio.sleep(0.05)
        
        return {
            "recipient": recipient,
            "message": message,
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat()
        }


async def example_data_pipeline():
    """
    Example: Multi-stage data processing pipeline.
    
    Flow:
    1. Validate input data
    2. Enrich with metadata
    3. Store in database
    4. Send notification
    """
    logger.info("\n=== Data Processing Pipeline Example ===\n")
    
    # Create coordinator with multiple workers
    config = CoordinatorConfig(
        worker_count=4,
        task_timeout=30,
        enable_logging=True
    )
    coordinator = Coordinator(config)
    
    # Register agents
    agents = [
        ValidationAgent(agent_id="validator-1", max_concurrent_tasks=2),
        EnrichmentAgent(agent_id="enricher-1", max_concurrent_tasks=2),
        StorageAgent(agent_id="storage-1"),
        NotificationAgent(agent_id="notifier-1", max_concurrent_tasks=3),
    ]
    
    for agent in agents:
        coordinator.register_agent(agent)
        logger.info(f"Registered: {agent.name} - Capabilities: {agent.get_capabilities()}")
    
    logger.info("")
    
    # Start coordinator
    await coordinator.start()
    
    # Pipeline configuration
    test_data = [
        {"value": "user-123", "type": "user"},
        {"value": "product-456", "type": "product"},
        {"value": "order-789", "type": "order"},
    ]
    
    # Stage 1: Validation
    logger.info("Stage 1: Validating data...\n")
    validation_tasks = {}
    
    for item in test_data:
        task = Task(
            task_type="validate_data",
            params={
                "data": item["value"],
                "rules": {"required": True, "min_length": 5}
            },
            priority=TaskPriority.HIGH,
            metadata={"item_type": item["type"]}
        )
        task_id = coordinator.submit_task(task)
        validation_tasks[task_id] = item
        logger.info(f"Validation task submitted: {task_id}")
    
    logger.info("")
    
    # Wait for validation to complete
    validated_data = {}
    for task_id, item in validation_tasks.items():
        result = await coordinator.wait_for_task(task_id, timeout=10)
        if result:
            validated_data[task_id] = result
            logger.info(f"Validation result: {result['result']['valid']} - {item}")
    
    logger.info("\n" + "="*50 + "\n")
    
    # Stage 2: Enrichment
    logger.info("Stage 2: Enriching data...\n")
    enrichment_tasks = {}
    
    for task_id, result in validated_data.items():
        if result['result']['valid']:
            task = Task(
                task_type="enrich_data",
                params={
                    "data": result['result']['data'],
                    "type": "geo"
                },
                priority=TaskPriority.MEDIUM,
                metadata={"source_task": task_id}
            )
            enrich_id = coordinator.submit_task(task)
            enrichment_tasks[enrich_id] = task_id
            logger.info(f"Enrichment task submitted: {enrich_id}")
    
    logger.info("")
    
    # Wait for enrichment
    enriched_data = {}
    for task_id, source_id in enrichment_tasks.items():
        result = await coordinator.wait_for_task(task_id, timeout=10)
        if result:
            enriched_data[task_id] = result
            logger.info(f"Enriched: {result['result']}")
    
    logger.info("\n" + "="*50 + "\n")
    
    # Stage 3: Storage
    logger.info("Stage 3: Storing data...\n")
    storage_tasks = {}
    
    for task_id, result in enriched_data.items():
        task = Task(
            task_type="store_data",
            params={
                "data": result['result'],
                "collection": "processed_items"
            },
            priority=TaskPriority.MEDIUM,
            metadata={"source_task": task_id}
        )
        storage_id = coordinator.submit_task(task)
        storage_tasks[storage_id] = task_id
        logger.info(f"Storage task submitted: {storage_id}")
    
    logger.info("")
    
    # Wait for storage
    stored_data = {}
    for task_id, source_id in storage_tasks.items():
        result = await coordinator.wait_for_task(task_id, timeout=10)
        if result:
            stored_data[task_id] = result
            logger.info(f"Stored: Collection={result['result']['collection']}, DocID={result['result']['doc_id']}")
    
    logger.info("\n" + "="*50 + "\n")
    
    # Stage 4: Notification
    logger.info("Stage 4: Sending notifications...\n")
    notification_tasks = {}
    
    for task_id, result in stored_data.items():
        task = Task(
            task_type="notify",
            params={
                "recipient": "admin@example.com",
                "message": f"Processed and stored item in collection {result['result']['collection']}"
            },
            priority=TaskPriority.LOW,
            metadata={"source_task": task_id}
        )
        notify_id = coordinator.submit_task(task)
        notification_tasks[notify_id] = task_id
        logger.info(f"Notification task submitted: {notify_id}")
    
    logger.info("")
    
    # Wait for notifications
    for task_id in notification_tasks.keys():
        result = await coordinator.wait_for_task(task_id, timeout=10)
        if result:
            logger.info(f"Notification sent: {result['result']['message']}")
    
    logger.info("\n" + "="*50 + "\n")
    
    # Stop coordinator
    await coordinator.stop()
    
    # Show final statistics
    logger.info("=== Pipeline Complete ===\n")
    stats = coordinator.get_stats()
    logger.info(f"Total tasks processed: {stats['completed_tasks']}")
    logger.info(f"Failed tasks: {stats['failed_tasks']}")
    logger.info(f"Total runtime: {stats['uptime_seconds']:.2f}s\n")
    
    logger.info("=== Agent Performance ===\n")
    for agent in coordinator.get_agents():
        logger.info(f"{agent.name}:")
        logger.info(f"  Tasks: {agent.stats.total_tasks}")
        logger.info(f"  Success rate: {(agent.stats.completed_tasks / max(agent.stats.total_tasks, 1) * 100):.1f}%")
        logger.info(f"  Avg runtime: {agent.stats.avg_runtime:.3f}s")


async def main():
    """Run advanced examples."""
    try:
        await example_data_pipeline()
        logger.info("\n✓ Advanced workflow example completed successfully!")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
