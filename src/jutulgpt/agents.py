from langchain_core.vectorstores import in_memory
from langgraph.prebuilt import create_react_agent

from jutulgpt.config import model_name
from jutulgpt.prompts import code_gen_prompt
from jutulgpt.state import Code
from jutulgpt.tools import tools
from jutulgpt.config import llm


agent = create_react_agent(
    llm,
    tools=tools,
    response_format=Code,
)


def get_structured_response(response) -> Code:
    """Extract structured response from the agent output."""
    structured_response = response.get("structured_response", None)
    if structured_response is None:
        raise ValueError("Structured response is missing from the agent output.")
    return structured_response


# code_gen_chain = code_gen_prompt | structured_llm
code_gen_chain = code_gen_prompt | agent | get_structured_response
concatenated_content = ""  # Placeholder for documentation
