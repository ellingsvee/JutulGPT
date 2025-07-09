from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# from jutulgpt.tools.tools_rag import docs_retriever_tool
from jutulgpt.config import avoid_tools, llm

# from jutulgpt.config import model_name
from jutulgpt.prompts import code_gen_prompt
from jutulgpt.state import Code
from jutulgpt.tools import tools

memory = MemorySaver()
# agent_config = {"configurable": {"thread_id": "1"}}
agent_config = RunnableConfig(
    configurable={"thread_id": "1"},
)


def make_agent(avoid_tools: bool = False):
    """Create the agent with the given configuration."""
    if avoid_tools:
        return create_react_agent(
            llm,
            tools=[],
            response_format=Code,
            # checkpointer=memory,
        )
    else:
        return create_react_agent(
            llm,
            tools=tools,
            response_format=Code,
            # checkpointer=memory,
        )


agent = make_agent(avoid_tools=avoid_tools)


def get_structured_response(response) -> Code:
    """Extract structured response from the agent output."""
    structured_response = response.get("structured_response", None)
    if structured_response is None:
        raise ValueError("Structured response is missing from the agent output.")
    return structured_response


code_gen_chain = code_gen_prompt | agent
