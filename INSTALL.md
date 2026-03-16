# Installation Guide

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation Methods

### Method 1: Development Installation (Recommended)

Development installation allows you to modify code and test immediately.

```bash
# Navigate to project directory
cd agent-delegation

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### Method 2: Standard Installation

```bash
cd agent-delegation
pip install -e .
```

### Method 3: Install from Requirements

```bash
cd agent-delegation
pip install -r requirements.txt
```

For development tools:
```bash
pip install -r requirements-dev.txt
```

## Verify Installation

### Test Import

```bash
python -c "from agent_delegation import Coordinator, Task; print('Success!')"
```

### Run Test Suite

```bash
# Install test dependencies if not already done
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_task.py -v
```

### Try the Basic Example

```bash
python examples/basic_usage.py
```

## Virtual Environment Setup (Optional but Recommended)

### Using venv

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install package
pip install -e .

# Deactivate when done
deactivate
```

### Using conda

```bash
# Create environment
conda create -n agent-delegation python=3.10

# Activate
conda activate agent-delegation

# Install
pip install -e .

# Deactivate
conda deactivate
```

## Troubleshooting

### Import Error: "No module named 'agent_delegation'"

**Solution:** Make sure you're in the project directory and have installed in development mode:
```bash
cd agent-delegation
pip install -e .
```

### Test Failures: "No module named 'pytest'"

**Solution:** Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

Or install pytest directly:
```bash
pip install pytest pytest-asyncio
```

### Import Error: "No module named 'aiohttp'"

**Solution:** Install runtime dependencies:
```bash
pip install aiohttp>=3.8.0
```

## Quick Start After Installation

### 1. Create a Script

Create `my_task.py`:

```python
import asyncio
from agent_delegation import Coordinator, Task, DataProcessingAgent

async def main():
    # Create coordinator
    coordinator = Coordinator()
    
    # Register agent
    agent = DataProcessingAgent()
    coordinator.register_agent(agent)
    
    # Create task
    task = Task(
        task_type="data_processing",
        params={"operation": "aggregate", "data": [1, 2, 3, 4, 5], "type": "sum"}
    )
    
    # Submit and execute
    task_id = coordinator.submit_task(task)
    await coordinator.start()
    result = await coordinator.wait_for_task(task_id, timeout=10)
    await coordinator.stop()
    
    print(f"Sum result: {result['result']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Run It

```bash
python my_task.py
```

## Uninstall

```bash
pip uninstall agent-delegation
```

## Next Steps

1. **Read the README**: `README.md` for comprehensive documentation
2. **Review Examples**: Check `examples/basic_usage.py` and `examples/advanced_workflow.py`
3. **Create Custom Agents**: Extend the Agent base class for your use cases
4. **Run Tests**: `pytest tests/ -v` to verify everything works

## Support

- Check README.md for API reference
- Review test files for usage examples
- See examples/ directory for working code

---

**Version:** 1.0.0  
**Python:** 3.10+  
**Status:** Production Ready
