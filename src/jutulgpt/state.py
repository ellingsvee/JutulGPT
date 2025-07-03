from typing import Annotated, List, Union

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Code(BaseModel):
    prefix: str = Field(description="Description of the problem and approach")
    imports: str = Field(description="Code block import statements")
    code: str = Field(description="Code block not including import statements")


class CodeState(TypedDict):
    messages: Annotated[list, add_messages]
    code: str
    error: str
    iterations: int


# class RunCodeState(TypedDict):
# out: Union[str, None]
# error: bool
# error_message: Union[str, None]
# error_stacktrace: Union[str, None]
