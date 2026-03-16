"""Tests for example agents."""

import pytest
from agent_delegation.agents import DataProcessingAgent, APICallAgent
from agent_delegation.core.task import Task


class TestDataProcessingAgent:
    """Test DataProcessingAgent."""
    
    @pytest.mark.asyncio
    async def test_transform_operation(self):
        """Test data transformation."""
        agent = DataProcessingAgent()
        
        task = Task(
            task_type="data_processing",
            params={
                "operation": "transform",
                "data": "hello"
            }
        )
        
        result = await agent.execute(task)
        assert result == "HELLO"
    
    @pytest.mark.asyncio
    async def test_aggregate_sum(self):
        """Test sum aggregation."""
        agent = DataProcessingAgent()
        
        task = Task(
            task_type="data_processing",
            params={
                "operation": "aggregate",
                "data": [1, 2, 3, 4, 5],
                "type": "sum"
            }
        )
        
        result = await agent.execute(task)
        assert result == 15
    
    @pytest.mark.asyncio
    async def test_aggregate_avg(self):
        """Test average aggregation."""
        agent = DataProcessingAgent()
        
        task = Task(
            task_type="data_processing",
            params={
                "operation": "aggregate",
                "data": [10, 20, 30],
                "type": "avg"
            }
        )
        
        result = await agent.execute(task)
        assert result == 20
    
    @pytest.mark.asyncio
    async def test_aggregate_count(self):
        """Test count aggregation."""
        agent = DataProcessingAgent()
        
        task = Task(
            task_type="data_processing",
            params={
                "operation": "aggregate",
                "data": [1, 2, 3, 4],
                "type": "count"
            }
        )
        
        result = await agent.execute(task)
        assert result == 4
    
    @pytest.mark.asyncio
    async def test_aggregate_max(self):
        """Test max aggregation."""
        agent = DataProcessingAgent()
        
        task = Task(
            task_type="data_processing",
            params={
                "operation": "aggregate",
                "data": [10, 50, 30, 20],
                "type": "max"
            }
        )
        
        result = await agent.execute(task)
        assert result == 50
    
    @pytest.mark.asyncio
    async def test_aggregate_min(self):
        """Test min aggregation."""
        agent = DataProcessingAgent()
        
        task = Task(
            task_type="data_processing",
            params={
                "operation": "aggregate",
                "data": [10, 50, 30, 5],
                "type": "min"
            }
        )
        
        result = await agent.execute(task)
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_filter_operation(self):
        """Test filtering."""
        agent = DataProcessingAgent()
        
        task = Task(
            task_type="data_processing",
            params={
                "operation": "filter",
                "data": [1, 2, 2, 3, 2, 4],
                "criteria": 2
            }
        )
        
        result = await agent.execute(task)
        assert result == [2, 2, 2]
    
    @pytest.mark.asyncio
    async def test_sort_operation(self):
        """Test sorting."""
        agent = DataProcessingAgent()
        
        task = Task(
            task_type="data_processing",
            params={
                "operation": "sort",
                "data": [3, 1, 4, 1, 5, 9, 2, 6]
            }
        )
        
        result = await agent.execute(task)
        assert result == [1, 1, 2, 3, 4, 5, 6, 9]
    
    @pytest.mark.asyncio
    async def test_sort_reverse(self):
        """Test reverse sorting."""
        agent = DataProcessingAgent()
        
        task = Task(
            task_type="data_processing",
            params={
                "operation": "sort",
                "data": [3, 1, 4, 1, 5],
                "reverse": True
            }
        )
        
        result = await agent.execute(task)
        assert result == [5, 4, 3, 1, 1]
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test invalid operation raises error."""
        agent = DataProcessingAgent()
        
        task = Task(
            task_type="data_processing",
            params={
                "operation": "invalid_op",
                "data": []
            }
        )
        
        with pytest.raises(ValueError):
            await agent.execute(task)


class TestAPICallAgent:
    """Test APICallAgent."""
    
    def test_api_agent_capabilities(self):
        """Test API agent has correct capabilities."""
        agent = APICallAgent()
        
        assert agent.has_capability("api_call")
        assert agent.has_capability("webhook")
        assert not agent.has_capability("data_processing")
    
    @pytest.mark.asyncio
    async def test_api_call_missing_url(self):
        """Test API call without URL raises error."""
        agent = APICallAgent()
        
        task = Task(
            task_type="api_call",
            params={"operation": "get"}
        )
        
        with pytest.raises(ValueError):
            await agent.execute(task)
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_webhook_missing_url(self):
        """Test webhook without URL raises error."""
        agent = APICallAgent()
        
        task = Task(
            task_type="webhook",
            params={"operation": "webhook"}
        )
        
        with pytest.raises(ValueError):
            await agent.execute(task)
        
        await agent.close()
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test invalid operation raises error."""
        agent = APICallAgent()
        
        task = Task(
            task_type="api_call",
            params={"operation": "invalid"}
        )
        
        with pytest.raises(ValueError):
            await agent.execute(task)
        
        await agent.close()
