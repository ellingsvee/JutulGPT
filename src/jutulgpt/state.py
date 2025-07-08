from dataclasses import dataclass
from typing import Annotated

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Code(BaseModel):
    prefix: str = Field(
        default="",
        description="The part of the answer that is not code. Provides a description of the coding problem, and your reasoning and approach for solving it. When not having to produce code, the full answer is in this field.",
    )
    imports: str = Field(default="", description="Code block import statements")
    code: str = Field(
        default="", description="Code block not including import statements"
    )


@dataclass(kw_only=False, frozen=True)
class GraphState:
    # messages: Annotated[list[AnyMessage], add_messages]
    messages: Annotated[list, add_messages]
    structured_response: Code
    error: bool
    iterations: int
    docs_context: str
    examples_context: str


def make_initial_state(user_question: str) -> GraphState:
    return GraphState(
        messages=[HumanMessage(content=user_question)],
        structured_response=Code(prefix="", imports="", code=""),
        error=False,
        iterations=0,
        docs_context="",
        examples_context="",
    )
