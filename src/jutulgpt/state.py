"""
State structures for the agent, including:
- InputState: initial and ongoing message state for the agent's execution.
- State: main agent state, tracks errors, iterations, and step control.
- CodeBlock: container for code and imports, with formatting helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep, RemainingSteps
from pydantic import BaseModel, Field
from typing_extensions import Annotated, Sequence


class CodeBlock(BaseModel):
    """
    Container for a code block, split into imports and main code.

    - imports: Any import statements needed for the code to run.
    - code: The main code body (excluding imports).

    """

    imports: str = Field(default="", description="Code block import statements")
    code: str = Field(
        default="", description="Code block not including import statements"
    )

    def is_empty(self) -> bool:
        if not self.imports and not self.code:
            return True
        return False

    def get_full_code(
        self, within_julia_context: bool = False, return_empty_if_no_code: bool = False
    ) -> str:
        """
        Returns the full code block, optionally wrapped as a Julia markdown code block.
        If within_julia_context is True, wraps the code in triple backticks and 'julia' for syntax highlighting.
        """

        # WARNING: This might be unneccessary
        if return_empty_if_no_code and not self.imports and not self.code:
            return ""

        full_code = "```julia" if within_julia_context else ""
        if self.imports:
            full_code += "\n" if within_julia_context else ""
            full_code += f"{self.imports}"
        if self.code:
            full_code += "\n" if within_julia_context or self.imports else ""
            full_code += f"{self.code}"
        full_code += "\n```" if within_julia_context else ""
        return full_code


@dataclass
class InputState:
    """
    Base input state for the agent, representing the evolving conversation and tool interaction history.

    - messages: List of all messages exchanged so far (user, AI, tool, etc.).
      The `add_messages` annotation ensures new messages are merged by ID, so the state is append-only unless a message is replaced.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
        default_factory=list
    )
    is_last_step: IsLastStep = field(default=False)
    remaining_steps: RemainingSteps = field(default=50)


@dataclass
class State(InputState):
    """
    Main agent state, extends InputState with error tracking, step control, and iteration count.

    - is_last_step: True if the next step will hit the recursion limit (managed by the graph, not user code).
    - error: True if the agent encountered an error in the last step.
    - error_message: Details of the last error, if any.
    - iterations: Number of steps/turns taken so far (useful for limiting recursion or debugging).
    - regenerate_code: True if the human has asked the agent to regenerate code before executing it.
    - retrieved_context: Context retrieved from RAG agent, available to subsequent agents.
    - code_block: The current code block being worked on, including imports and main code.
    - retrieved_function_definitions: Retrieved function definitions. Used by the code-agent.
    """

    error: bool = field(default=False)
    error_message: str = field(default="")
    iterations: int = field(default=0)
    regenerate_code: bool = field(default=False)
    retrieved_context: str = field(default="")
    code_block: CodeBlock = field(default_factory=CodeBlock)
    original_user_query: str = field(default="")
