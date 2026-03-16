#!/usr/bin/env python
"""Verification script for agent-delegation system."""

from agent_delegation import Coordinator, Task, TaskPriority, DataProcessingAgent
import asyncio


async def verify():
    """Verify the installation and basic functionality."""
    print('=== Agent Delegation System Verification ===\n')
    
    try:
        # Create coordinator
        coordinator = Coordinator()
        print('[OK] Coordinator created')
        
        # Register agent
        agent = DataProcessingAgent(agent_id='test-agent')
        coordinator.register_agent(agent)
        print('[OK] Agent registered with capabilities:', agent.get_capabilities())
        
        # Create task
        task = Task(
            task_type='data_processing',
            params={'operation': 'aggregate', 'data': [10, 20, 30], 'type': 'sum'},
            priority=TaskPriority.HIGH
        )
        print('\n[OK] Task created:', task.task_id)
        
        # Submit and execute
        await coordinator.start()
        task_id = coordinator.submit_task(task)
        print('[OK] Task submitted for execution')
        
        result = await coordinator.wait_for_task(task_id, timeout=5)
        await coordinator.stop()
        
        if result:
            print('[OK] Task completed with result:', result['result'])
            print('\n' + '='*50)
            print('[SUCCESS] SYSTEM VERIFICATION PASSED')
            print('='*50)
            return True
        else:
            print('[FAIL] Task execution timeout')
            return False
            
    except Exception as e:
        print('[FAIL] Error during verification:', str(e))
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = asyncio.run(verify())
    exit(0 if success else 1)
