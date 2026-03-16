"""Example APICallAgent implementation."""

import asyncio
import aiohttp
from typing import Any, Dict, Optional
from ..core.agent import Agent, AgentCapability
from ..core.task import Task


class APICallAgent(Agent):
    """
    Example agent that makes API calls.
    
    Capabilities:
    - api_call: Make HTTP API requests
    - webhook: Post data to webhooks
    """
    
    def __init__(self, agent_id: str = None, name: str = "APICaller", **kwargs):
        """Initialize API call agent."""
        super().__init__(agent_id, name, **kwargs)
        
        self.register_capabilities([
            AgentCapability("api_call", version="1.0"),
            AgentCapability("webhook", version="1.0"),
        ])
        
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def execute(self, task: Task) -> Any:
        """
        Execute an API call task.
        
        Supported operations:
        - get: HTTP GET request
        - post: HTTP POST request
        - put: HTTP PUT request
        - webhook: POST to webhook URL
        """
        if task.task_type not in self.get_capabilities():
            raise ValueError(f"Agent cannot handle task type: {task.task_type}")
        
        operation = task.params.get('operation')
        
        if operation in ['get', 'post', 'put', 'delete']:
            return await self._make_request(operation, task.params)
        elif operation == 'webhook':
            return await self._post_webhook(task.params)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _make_request(self, method: str, params: Dict[str, Any]) -> Any:
        """Make HTTP request."""
        url = params.get('url')
        headers = params.get('headers', {})
        data = params.get('data')
        json_data = params.get('json')
        
        if not url:
            raise ValueError("'url' parameter required")
        
        session = await self._get_session()
        
        try:
            async with session.request(
                method.upper(),
                url,
                headers=headers,
                data=data,
                json=json_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = {
                    'status': response.status,
                    'headers': dict(response.headers),
                }
                
                # Try to parse JSON, fallback to text
                try:
                    result['body'] = await response.json()
                except:
                    result['body'] = await response.text()
                
                return result
                
        except Exception as e:
            raise RuntimeError(f"API request failed: {str(e)}")
    
    async def _post_webhook(self, params: Dict[str, Any]) -> Any:
        """Post data to webhook."""
        webhook_url = params.get('url')
        payload = params.get('payload', {})
        
        if not webhook_url:
            raise ValueError("'url' parameter required for webhook")
        
        return await self._make_request('post', {
            'url': webhook_url,
            'json': payload,
            'headers': params.get('headers', {'Content-Type': 'application/json'})
        })
    
    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
