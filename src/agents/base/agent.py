"""Base agent implementation - A2A Standard General Purpose Agent."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentSkill,
    Message,
    TaskState,
    Part,
    TextPart,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

# Import metrics collection
from ...common.metrics import get_agent_metrics

# Simplified imports to avoid dependency issues
def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

def trace_async(operation: str, component: str):
    """Simple trace decorator."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger = logging.getLogger(f"{component}.{operation}")
            logger.debug(f"Starting {operation}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"Completed {operation}")
                return result
            except Exception as e:
                logger.error(f"Error in {operation}: {e}")
                raise
        return wrapper
    return decorator

# Simple OpenAI client for demonstration
class SimpleAIClient:
    """Simple AI client that returns mock responses."""
    
    async def ainvoke(self, prompt: str) -> Any:
        """Simple mock AI response."""
        class MockResponse:
            def __init__(self, content: str):
                self.content = content
        
        # Simple response logic based on prompt content
        if "general" in prompt.lower() or "hello" in prompt.lower():
            return MockResponse("Hello! I'm a general purpose AI assistant. I can help you with various questions, provide information, engage in conversation, and assist with many different tasks. How can I help you today?")
        elif "yourself" in prompt.lower():
            return MockResponse("I'm the Base Agent, a general purpose AI assistant designed to help with various questions and tasks. I can engage in conversation, provide information, and assist with general queries.")
        elif "help" in prompt.lower():
            return MockResponse("I can help you with:\n• Answering general questions\n• Providing information on various topics\n• Engaging in conversation\n• Assisting with tasks and problem-solving\n• Explaining concepts\n\nWhat would you like assistance with?")
        else:
            return MockResponse(f"I understand you're asking about: {prompt[:100]}{'...' if len(prompt) > 100 else ''}. While I'm running in demo mode with limited capabilities, I'm designed to be a helpful general purpose assistant. How else can I help you?")

def create_azure_chat_openai(temperature: float = 0.7) -> SimpleAIClient:
    """Create a simple AI client for demonstration."""
    return SimpleAIClient()


class BaseAgent:
    """General purpose assistant agent that can handle various queries."""
    
    def __init__(self):
        self.name = "Base Agent"
        self.description = "A general purpose AI assistant"
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.llm = create_azure_chat_openai(temperature=0.7)
        
        # Initialize metrics collection with separate metrics port
        self.metrics = get_agent_metrics("base", metrics_port=9080)
    
    def get_skills(self) -> List[AgentSkill]:
        """Get the skills this agent provides."""
        return [
            AgentSkill(
                id='general_assistance',
                name='General Assistance',
                description='Provide helpful responses to general questions and tasks',
                tags=['general', 'assistance', 'chat', 'help'],
                examples=[
                    'Help me understand a concept',
                    'Answer a question about a topic',
                    'Provide information or advice',
                    'Assist with general tasks'
                ],
            ),
            AgentSkill(
                id='conversation',
                name='Conversation',
                description='Engage in natural conversation and dialogue',
                tags=['conversation', 'chat', 'dialogue'],
                examples=[
                    'Hello, how are you?',
                    'Tell me about yourself',
                    'What can you help me with?',
                    'Have a conversation with me'
                ],
            ),
        ]
    
    @trace_async("process_query", "base_agent")
    async def process_query(self, query: str, context_id: str) -> Dict[str, Any]:
        """Process a query and return a response."""
        async with self.metrics.track_request_duration("general_assistance"):
            try:
                self.logger.info(f"Processing query: {query[:100]}...")
                
                # Create a general prompt for the base agent
                prompt = f"""You are a helpful AI assistant. Please provide a helpful, informative response to the following query:

Query: {query}

Please provide a clear, concise, and helpful response."""

                # Get response from LLM
                response = await self.llm.ainvoke(prompt)
                
                result_text = response.content if hasattr(response, 'content') else str(response)
                
                self.logger.info("Successfully processed query")
                return {
                    "content": result_text,
                    "is_task_complete": True,
                    "require_user_input": False
                }
                
            except Exception as e:
                self.logger.error(f"Error processing query: {e}")
                return {
                    "content": f"I apologize, but I encountered an error while processing your request: {str(e)}",
                    "is_task_complete": True,
                    "require_user_input": False
                }
    
    async def stream(self, query: str, context_id: str):
        """Stream responses for the given query."""
        result = await self.process_query(query, context_id)
        yield result


class BaseAgentExecutor(AgentExecutor):
    """Base Agent Executor following A2A samples patterns."""
    
    def __init__(self):
        self.agent = BaseAgent()
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        # Use shared metrics instance from the agent
        self.metrics = self.agent.metrics
    
    @trace_async("execute_task", "base_agent_executor")
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute a base agent task."""
        try:
            # Get user input
            query = context.get_user_input()
            if not query:
                await event_queue.enqueue_event(
                    new_agent_text_message("No input provided")
                )
                return
            
            # Get or create task
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            updater = TaskUpdater(event_queue, task.id, task.context_id)
            self.logger.info(f"Processing base agent request: {query}")
            
            # Stream responses
            async for item in self.agent.stream(query, task.context_id):
                is_task_complete = item['is_task_complete']
                require_user_input = item['require_user_input']
                content = item['content']

                if not is_task_complete and not require_user_input:
                    # Working status
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                    )
                elif require_user_input:
                    # Input required
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                        final=True,
                    )
                    break
                else:
                    # Task complete - add result as artifact and complete
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))],
                        name='base_agent_result',
                    )
                    await updater.complete()
                    break

        except Exception as e:
            self.logger.error(f'Error occurred while processing request: {e}', exc_info=True)
            
            # Update task with error status
            task = context.current_task
            if task:
                updater = TaskUpdater(event_queue, task.id, task.context_id)
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(
                        f'Request failed: {str(e)}',
                        task.context_id,
                        task.id,
                    ),
                    final=True,
                )
            
            # Raise server error
            from a2a.types import InternalError
            raise ServerError(error=InternalError()) from e
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel a running task."""
        self.logger.info(f"Cancelling task: {context.task_id}")
        await event_queue.enqueue_event(
            new_agent_text_message("Task cancelled by user request")
        )
