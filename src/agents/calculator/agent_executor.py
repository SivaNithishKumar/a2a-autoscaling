"""
Calculator Agent Executor - A2A Standard Implementation

AgentExecutor implementation for the Calculator Agent following A2A samples patterns.
"""

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError

from .agent import CalculatorAgent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalculatorAgentExecutor(AgentExecutor):
    """Calculator Agent Executor following A2A samples patterns."""

    def __init__(self):
        """Initialize the Calculator Agent Executor."""
        self.agent = CalculatorAgent()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Execute calculator requests following A2A patterns.
        
        Args:
            context: Request context containing user input and task info
            event_queue: Event queue for task status updates
        """
        # Validate the request
        error = self._validate_request(context)
        if error:
            self.logger.error("Invalid request parameters")
            raise ServerError(error=InvalidParamsError())

        # Get user input and task information
        query = context.get_user_input()
        task = context.current_task
        
        # Create new task if none exists
        if not task:
            task = new_task(context.message)  # type: ignore
            await event_queue.enqueue_event(task)
        
        # Create task updater for progress updates
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        
        try:
            self.logger.info(f"Processing calculator request: {query}")
            
            # Stream calculation results
            async for item in self.agent.stream(query, task.context_id):
                is_task_complete = item['is_task_complete']
                require_user_input = item['require_user_input']
                content = item['content']

                if not is_task_complete and not require_user_input:
                    # Working status - calculation in progress
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                    )
                elif require_user_input:
                    # Input required - need more information from user
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
                        name='calculation_result',
                    )
                    await updater.complete()
                    break

        except Exception as e:
            self.logger.error(f'Error occurred while processing calculation: {e}', exc_info=True)
            
            # Update task with error status
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f'Calculation failed: {str(e)}',
                    task.context_id,
                    task.id,
                ),
                final=True,
            )
            
            # Raise server error
            raise ServerError(error=InternalError()) from e

    def _validate_request(self, context: RequestContext) -> bool:
        """
        Validate the incoming request.
        
        Args:
            context: Request context to validate
            
        Returns:
            True if there's an error, False if valid
        """
        try:
            # Check if we have a message
            if not context.message:
                self.logger.error("No message provided in request")
                return True
            
            # Check if we can get user input
            user_input = context.get_user_input()
            if not user_input or not user_input.strip():
                self.logger.error("No user input provided")
                return True
            
            # Request is valid
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating request: {e}")
            return True

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """
        Cancel the current calculation task.
        
        Args:
            context: Request context
            event_queue: Event queue for updates
            
        Raises:
            ServerError: Always raises UnsupportedOperationError as cancellation
                        is not supported for calculator operations
        """
        self.logger.warning("Cancel operation requested - not supported for calculator")
        raise ServerError(error=UnsupportedOperationError())
