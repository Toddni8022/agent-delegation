"""Example DataProcessingAgent implementation."""

import asyncio
from typing import Any, Dict
from ..core.agent import Agent, AgentCapability
from ..core.task import Task


class DataProcessingAgent(Agent):
    """
    Example agent that processes data.
    
    Capabilities:
    - data_processing: Process, transform, and analyze data
    - data_aggregation: Aggregate data from multiple sources
    """
    
    def __init__(self, agent_id: str = None, name: str = "DataProcessor", **kwargs):
        """Initialize data processing agent."""
        super().__init__(agent_id, name, **kwargs)
        
        self.register_capabilities([
            AgentCapability("data_processing", version="1.0"),
            AgentCapability("data_aggregation", version="1.0"),
        ])
    
    async def execute(self, task: Task) -> Any:
        """
        Execute a data processing task.
        
        Supported operations:
        - transform: Apply transformation to data
        - aggregate: Aggregate data
        - filter: Filter data by criteria
        - sort: Sort data
        """
        if task.task_type not in self.get_capabilities():
            raise ValueError(f"Agent cannot handle task type: {task.task_type}")
        
        operation = task.params.get('operation')
        data = task.params.get('data')
        
        if operation == 'transform':
            return await self._transform(data, task.params)
        elif operation == 'aggregate':
            return await self._aggregate(data, task.params)
        elif operation == 'filter':
            return await self._filter(data, task.params)
        elif operation == 'sort':
            return await self._sort(data, task.params)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    async def _transform(self, data: Any, params: Dict[str, Any]) -> Any:
        """Transform data."""
        # Simulate processing
        await asyncio.sleep(0.1)
        
        transformation_fn = params.get('fn')
        if callable(transformation_fn):
            return transformation_fn(data)
        
        # Default: uppercase strings
        if isinstance(data, str):
            return data.upper()
        elif isinstance(data, list):
            return [str(x).upper() if isinstance(x, str) else x for x in data]
        
        return data
    
    async def _aggregate(self, data: Any, params: Dict[str, Any]) -> Any:
        """Aggregate data."""
        await asyncio.sleep(0.1)
        
        if not isinstance(data, list):
            return data
        
        agg_type = params.get('type', 'sum')
        
        if agg_type == 'sum':
            return sum(x for x in data if isinstance(x, (int, float)))
        elif agg_type == 'count':
            return len(data)
        elif agg_type == 'avg':
            nums = [x for x in data if isinstance(x, (int, float))]
            return sum(nums) / len(nums) if nums else 0
        elif agg_type == 'max':
            nums = [x for x in data if isinstance(x, (int, float))]
            return max(nums) if nums else None
        elif agg_type == 'min':
            nums = [x for x in data if isinstance(x, (int, float))]
            return min(nums) if nums else None
        
        return data
    
    async def _filter(self, data: Any, params: Dict[str, Any]) -> Any:
        """Filter data by criteria."""
        await asyncio.sleep(0.1)
        
        if not isinstance(data, list):
            return data
        
        criteria = params.get('criteria')
        filter_fn = params.get('fn')
        
        if callable(filter_fn):
            return [x for x in data if filter_fn(x)]
        
        # Default filter by value
        if criteria is not None:
            return [x for x in data if x == criteria]
        
        return data
    
    async def _sort(self, data: Any, params: Dict[str, Any]) -> Any:
        """Sort data."""
        await asyncio.sleep(0.1)
        
        if not isinstance(data, list):
            return data
        
        reverse = params.get('reverse', False)
        return sorted(data, reverse=reverse)
