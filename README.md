# Agent Delegation System

A production-ready Python task delegation system for managing custom agents, task queues, and async execution with comprehensive observability.

## Features

✨ **Core Capabilities**
- **Task Queue Management**: Priority-based task queuing with support for retries and timeouts
- **Agent Pool Management**: Register, monitor, and manage multiple agents with capability matching
- **Intelligent Task Routing**: Automatically route tasks to appropriate agents based on capabilities and load
- **Async Execution**: Full async/await support with concurrent task execution
- **Error Handling & Retries**: Automatic retry logic with configurable retry counts and timeouts
- **Webhooks & Callbacks**: Register callbacks for task completion events
- **Comprehensive Logging**: Full observability with structured logging and metrics

## Architecture

### Core Components

#### Task
Represents a unit of work to be executed.

```python
task = Task(
    task_type="data_processing",
    params={"operation": "transform", "data": "input"},
    priority=TaskPriority.HIGH,
    max_retries=3,
    timeout=60
)
```

#### Agent
Base class for custom agents. Agents define capabilities and implement execution logic.

```python
class CustomAgent(Agent):
    def __init__(self, agent_id=None, name=None, **kwargs):
        super().__init__(agent_id, name, **kwargs)
        self.register_capability(AgentCapability("custom_task"))
    
    async def execute(self, task: Task) -> Any:
        # Implement your task execution logic
        return result
```

#### Coordinator
Main orchestrator managing task queue, agent pool, and execution.

```python
coordinator = Coordinator(CoordinatorConfig(worker_count=4))
coordinator.register_agent(agent)
task_id = coordinator.submit_task(task)
await coordinator.start()
```

## Installation

### From Source

```bash
cd agent-delegation
pip install -e .
```

### With Dependencies

```bash
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```python
import asyncio
from agent_delegation import (
    Coordinator,
    CoordinatorConfig,
    Task,
    TaskPriority,
    DataProcessingAgent,
)

async def main():
    # Create coordinator
    config = CoordinatorConfig(worker_count=2)
    coordinator = Coordinator(config)
    
    # Register agent
    agent = DataProcessingAgent(agent_id="processor-1")
    coordinator.register_agent(agent)
    
    # Submit task
    task = Task(
        task_type="data_processing",
        params={
            "operation": "transform",
            "data": "hello world"
        },
        priority=TaskPriority.HIGH
    )
    task_id = coordinator.submit_task(task)
    
    # Start coordinator
    await coordinator.start()
    
    # Wait for task completion
    result = await coordinator.wait_for_task(task_id, timeout=10)
    print(f"Result: {result}")
    
    await coordinator.stop()

asyncio.run(main())
```

## Creating Custom Agents

### Simple Agent Example

```python
from agent_delegation import Agent, AgentCapability
from agent_delegation.core.task import Task

class EmailAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_capability(AgentCapability("send_email"))
    
    async def execute(self, task: Task):
        if task.task_type != "send_email":
            raise ValueError(f"Cannot handle {task.task_type}")
        
        email = task.params.get("email")
        subject = task.params.get("subject")
        body = task.params.get("body")
        
        # Send email...
        
        return {"sent": True, "email": email}
```

### Registering and Using Custom Agent

```python
async def main():
    coordinator = Coordinator()
    
    # Register custom agent
    email_agent = EmailAgent(agent_id="email-agent-1")
    coordinator.register_agent(email_agent)
    
    # Submit email task
    task = Task(
        task_type="send_email",
        params={
            "email": "user@example.com",
            "subject": "Hello",
            "body": "Test message"
        }
    )
    
    task_id = coordinator.submit_task(task)
    await coordinator.start()
    result = await coordinator.wait_for_task(task_id)
    await coordinator.stop()
```

## Advanced Features

### Task Callbacks

Register callbacks to be triggered when tasks complete:

```python
async def on_task_complete(task: Task):
    print(f"Task {task.task_id} completed: {task.result}")

coordinator.register_callback(task_id, on_task_complete)
```

### Priority Queue

Tasks are automatically sorted by priority:

```python
# High priority task
task = Task(
    task_type="urgent_process",
    params={...},
    priority=TaskPriority.CRITICAL
)
```

Priority levels: `CRITICAL` > `HIGH` > `MEDIUM` > `LOW`

### Task Metadata

Attach custom metadata to tasks:

```python
task = Task(
    task_type="process",
    params={...},
    metadata={
        "user_id": 123,
        "source": "webhook",
        "batch_id": "batch-001"
    }
)
```

### Retry Logic

Automatic retry on failure:

```python
task = Task(
    task_type="api_call",
    params={...},
    max_retries=3,
    timeout=60  # 60 second timeout
)
```

### Task Timeout

Set execution timeout (raises asyncio.TimeoutError):

```python
task = Task(
    task_type="long_running",
    params={...},
    timeout=300  # 5 minutes
)
```

Or globally in coordinator:

```python
config = CoordinatorConfig(task_timeout=300)
```

## Monitoring

### Get Coordinator Statistics

```python
stats = coordinator.get_stats()
print(f"Completed tasks: {stats['completed_tasks']}")
print(f"Failed tasks: {stats['failed_tasks']}")
print(f"Queue size: {stats['queue_size']}")
```

### Get Agent Information

```python
for agent in coordinator.get_agents():
    print(f"Agent: {agent.name}")
    print(f"  Status: {agent.status.value}")
    print(f"  Total tasks: {agent.stats.total_tasks}")
    print(f"  Completed: {agent.stats.completed_tasks}")
    print(f"  Failed: {agent.stats.failed_tasks}")
    print(f"  Avg runtime: {agent.stats.avg_runtime:.2f}s")
```

### Get Task Status

```python
status = coordinator.get_task_status(task_id)
if status:
    print(f"Task status: {status['status']}")
    print(f"Result: {status['result']}")
    print(f"Error: {status['error']}")
```

## Example Agents

### DataProcessingAgent

Built-in agent for data transformation and aggregation:

```python
from agent_delegation import DataProcessingAgent, Task

agent = DataProcessingAgent()

# Transform
task = Task(
    task_type="data_processing",
    params={
        "operation": "transform",
        "data": "hello"
    }
)
# Result: "HELLO"

# Aggregate
task = Task(
    task_type="data_processing",
    params={
        "operation": "aggregate",
        "data": [1, 2, 3, 4, 5],
        "type": "sum"  # sum, avg, count, min, max
    }
)
# Result: 15

# Filter
task = Task(
    task_type="data_processing",
    params={
        "operation": "filter",
        "data": [1, 2, 2, 3, 2],
        "criteria": 2
    }
)
# Result: [2, 2, 2]

# Sort
task = Task(
    task_type="data_processing",
    params={
        "operation": "sort",
        "data": [3, 1, 4, 1, 5],
        "reverse": False
    }
)
# Result: [1, 1, 3, 4, 5]
```

### APICallAgent

Built-in agent for making HTTP requests:

```python
from agent_delegation import APICallAgent, Task

agent = APICallAgent()

# GET request
task = Task(
    task_type="api_call",
    params={
        "operation": "get",
        "url": "https://api.example.com/data"
    }
)

# POST request
task = Task(
    task_type="api_call",
    params={
        "operation": "post",
        "url": "https://api.example.com/data",
        "json": {"key": "value"}
    }
)

# Webhook
task = Task(
    task_type="webhook",
    params={
        "operation": "webhook",
        "url": "https://webhook.example.com/events",
        "payload": {"event": "task_completed"}
    }
)
```

### TrumpSpeechFactCheckAgent

Built-in agent for local next-word prediction and rule-based fact-check flags:

```python
from agent_delegation import Task
from agent_delegation.agents import TrumpSpeechFactCheckAgent

agent = TrumpSpeechFactCheckAgent()

# Train on transcript text
train_task = Task(
    task_type="trump_speech_prediction",
    params={"operation": "train", "transcripts": ["We will win and keep winning."]}
)
await agent.execute(train_task)

# Predict likely next words
predict_task = Task(
    task_type="trump_speech_prediction",
    params={"operation": "predict_next_words", "prompt": "we will", "top_k": 5}
)
prediction = await agent.execute(predict_task)

# Flag claim-like statements for fact-checking
check_task = Task(
    task_type="trump_fact_check",
    params={"operation": "fact_check", "text": "The largest inauguration crowd was mine."}
)
checks = await agent.execute(check_task)
```

## Configuration

### CoordinatorConfig

```python
from agent_delegation import CoordinatorConfig

config = CoordinatorConfig(
    max_queue_size=1000,        # None for unlimited
    worker_count=4,              # Number of concurrent workers
    task_timeout=300,            # Default task timeout in seconds
    enable_logging=True,         # Enable structured logging
    log_level="INFO"            # Logging level
)

coordinator = Coordinator(config)
```

## Testing

Run the test suite:

```bash
# All tests
pytest

# Specific test file
pytest tests/test_coordinator.py

# With verbose output
pytest -v

# With coverage
pytest --cov=agent_delegation
```

## Examples

See the `examples/` directory for complete working examples:

- `basic_usage.py` - Basic task delegation
- More examples demonstrating callbacks, multiple agents, priority queue, etc.
- `trump_fact_checker.py` - Interactive next-word prediction + fact-check flags
- `fact_check_transcript.py` - One-command transcript fact-check report (.txt or .pdf)
- `fact_check_gui.py` - Desktop GUI (browse transcript .txt/.pdf, analyze, save report)
- `build_gui_exe.py` - Build a Windows .exe for the GUI with PyInstaller

Run examples:

```bash
python examples/basic_usage.py
python examples/trump_fact_checker.py
python examples/fact_check_transcript.py --transcript examples/data/trump_sample_transcript.txt
python examples/fact_check_gui.py
python examples/build_gui_exe.py
```

### Build Windows .exe for GUI

```bash
# Install builder dependency once
python -m pip install pyinstaller
python -m pip install pypdf

# Build dist/TrumpFactCheckerGUI.exe
python examples/build_gui_exe.py
```

Optional flags:

```bash
python examples/build_gui_exe.py --name MyFactChecker
python examples/build_gui_exe.py --name MyFactChecker --icon path/to/icon.ico
python examples/build_gui_exe.py --no-onefile
```

## Architecture Details

### Task Lifecycle

1. **PENDING** → Task created
2. **QUEUED** → Task added to queue
3. **ASSIGNED** → Agent assigned to task
4. **IN_PROGRESS** → Task execution started
5. **COMPLETED** → Task execution successful
6. **FAILED** → Task execution failed
7. **RETRYING** → Task queued for retry

### Agent Lifecycle

1. **IDLE** → No active tasks
2. **BUSY** → Processing tasks
3. **ERROR** → Error occurred, needs recovery
4. **OFFLINE** → Agent unavailable

### Coordinator Worker Loop

1. Get next task from queue (sorted by priority)
2. Find available agent with matching capability
3. Assign task to agent
4. Execute task asynchronously
5. Handle completion/failure/timeout
6. Trigger callbacks
7. Repeat

## Performance Considerations

- **Worker Count**: Adjust `worker_count` based on system resources. Default is 4.
- **Max Queue Size**: Set `max_queue_size` to prevent memory issues. None (default) is unlimited.
- **Timeouts**: Set reasonable `task_timeout` values to prevent resource exhaustion.
- **Agent Concurrency**: Configure `max_concurrent_tasks` per agent to manage load.

## Error Handling

### Task Execution Errors

```python
# Tasks track errors
result = coordinator.get_task_status(task_id)
if result['status'] == 'failed':
    print(f"Error: {result['error']}")
```

### Coordinator Errors

```python
try:
    await coordinator.start()
    # ... do work ...
except Exception as e:
    logger.error(f"Coordinator error: {e}")
finally:
    await coordinator.stop()
```

## Logging

The system includes comprehensive logging:

```python
import logging

logging.basicConfig(level=logging.INFO)

# Logs include:
# - Task submission and completion
# - Agent registration and status
# - Worker activity
# - Errors and retries
```

## API Reference

### Task

- `task_type: str` - Type of task
- `params: Dict` - Task parameters
- `priority: TaskPriority` - Task priority
- `task_id: str` - Unique ID (auto-generated)
- `status: TaskStatus` - Current status
- `max_retries: int` - Max retry attempts
- `timeout: int` - Execution timeout in seconds
- `metadata: Dict` - Custom metadata
- `callbacks: List` - Webhook URLs
- `mark_started()` - Mark task as started
- `mark_completed(result)` - Mark task as completed
- `mark_failed(error)` - Mark task as failed
- `can_retry()` - Check if task can be retried
- `to_dict()` - Serialize to dictionary

### Agent

- `agent_id: str` - Unique ID
- `name: str` - Agent name
- `capabilities: Dict` - Registered capabilities
- `status: AgentStatus` - Current status
- `stats: AgentStats` - Performance statistics
- `register_capability(cap)` - Add capability
- `has_capability(name)` - Check capability
- `can_accept_task()` - Check if can accept tasks
- `execute(task)` - Execute task (override in subclass)
- `to_dict()` - Serialize to dictionary

### Coordinator

- `submit_task(task)` - Submit task for execution
- `get_task_status(task_id)` - Get task status
- `cancel_task(task_id)` - Cancel queued task
- `register_agent(agent)` - Register agent
- `unregister_agent(agent_id)` - Unregister agent
- `get_agent(agent_id)` - Get agent by ID
- `get_agents()` - Get all agents
- `register_callback(task_id, callback)` - Register completion callback
- `start()` - Start coordinator workers
- `stop()` - Stop coordinator
- `wait_for_task(task_id, timeout)` - Wait for task completion
- `get_stats()` - Get coordinator statistics

## License

MIT License

## Contributing

Contributions welcome! Please follow these guidelines:

1. Write tests for new features
2. Follow PEP 8 style guide
3. Update documentation
4. Ensure all tests pass

## Support

For issues, questions, or contributions, please reach out.

---

**Version**: 1.0.0  
**Author**: Todd Nicholas  
**Created**: 2024
