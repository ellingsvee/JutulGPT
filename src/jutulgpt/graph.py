"""This module defines the state graph for the react agent."""

from typing import Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.vectorstores import in_memory
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import Command, interrupt

from jutulgpt.configuration import Configuration, static_config
from jutulgpt.julia_interface import get_last_code_response
from jutulgpt.nodes import check_code, generate_response, tools_node
from jutulgpt.state import State


def decide_to_finish(state: State):
    """
    Determines whether to finish.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """
    error = state.error
    iterations = state.iterations

    if not error or iterations == static_config.max_iterations:
        return END
    else:
        return "generate_response"


def human_decide_check_code(
    state: State, config: RunnableConfig
) -> Command[Literal["check_code", "__end__"]]:
    """
    Ask human whether to check code or proceed to end.
    """
    configuration = Configuration.from_runnable_config(config)

    # Only give the option is there are any code to check.
    code_block = get_last_code_response(state)
    if (
        code_block.imports != "" or code_block.code != ""
    ) and configuration.check_code_bool:
        interrupt_message = f"""Do you want to check the code before proceeding?

    If you accept, the agent will run the code and try to fix potential errors. If you ignore, the agent will finish. 

    Alternatively, respond 'yes' to check the code, or 'no' to finish.
        """

        description = (
            "Review the generated code and decide if it should be checked."
            + "If you accept, the agent will run the code and try to fix potential errors. "
            + "If you ignore, the agent will finish."
        )

        request = HumanInterrupt(
            action_request=ActionRequest(
                action="Check code?",
                args={"code": interrupt_message},
            ),
            config=HumanInterruptConfig(
                allow_ignore=True,
                allow_accept=True,
                allow_respond=True,
                allow_edit=False,
            ),
            description=description,
        )

        human_response: HumanResponse = interrupt([request])[0]
        response_type = human_response.get("type")

        if response_type == "response":
            resp = human_response.get("args").strip().lower()
            if resp in {"yes", "y"}:
                return Command(goto="check_code")
            else:
                return Command(goto=Send(END, arg={}))
        elif response_type == "accept":
            return Command(goto="check_code")
        elif human_response.get("type") == "ignore":
            return Command(
                goto=Send(
                    END,
                    arg={},
                )
            )
        else:
            raise TypeError(
                f"Interrupt value of type {type(human_response)} is not supported."
            )
    else:
        # Go to end if no code has been generated.
        return Command(
            goto=Send(
                END,
                arg={},
            )
        )


builder = StateGraph(State, config_schema=Configuration)

builder.add_node("generate_response", generate_response)
builder.add_node("tools", tools_node)
builder.add_node("check_code", check_code)
builder.add_node("human_decide_check_code", human_decide_check_code)

builder.add_edge(START, "generate_response")
builder.add_conditional_edges(
    "generate_response",
    tools_condition,
    {END: "human_decide_check_code", "tools": "tools"},
)
builder.add_edge("tools", "generate_response")

builder.add_conditional_edges(
    "check_code",
    decide_to_finish,
    {
        END: END,
        "generate_response": "generate_response",
    },
)

builder.add_edge("human_decide_check_code", END)

graph = builder.compile(name="agent")

graph.get_graph().draw_mermaid_png(output_file_path="./graph.png")
