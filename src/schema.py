from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from typing import List


class Code(BaseModel):
    prefix: str = Field(description="Description of the problem and approach")
    imports: str = Field(description="Code block import statements")
    code: str = Field(description="Code block not including import statements")


class GraphState(TypedDict):
    error: str
    messages: List
    generation: str
    iterations: int
