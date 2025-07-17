from typing import Annotated, Any, Optional, cast

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import Command, interrupt

from jutulgpt.configuration import Configuration
from jutulgpt.rag.retrievers import format_docs, format_examples, retrievers

_: bool = load_dotenv(find_dotenv())


@tool(parse_docstring=True)
def retrieve_jutuldarcy(
    query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Use this tool to look up any information, usage, or examples from the JutulDarcy documentation. ALWAYS use this tool before answering any Julia code question about JutulDarcy.

    Args:
        query: The string sent into the vectorstore retriever.

    Returns:
        String containing the formatted output from the retriever
    """

    configuration = Configuration.from_runnable_config(config)  # Temp

    print("TOOL INVOKED: retrieve_jutuldarcy")

    retrieved_docs = retrievers["jutuldarcy"]["docs"].invoke(input=query)
    retrieved_examples = retrievers["jutuldarcy"]["examples"].invoke(input=query)
    # retrieved = retrieved_docs + retrieved_examples

    docs = format_docs(retrieved_docs)
    examples = format_examples(retrieved_examples)

    #     out = f"""
    # # Retrieved from the JutulDarcy documentation:
    # {docs}

    # # Retrieved from the JutulDarcy examples:
    # {examples}
    # """

    interrupt_message = f"Modify the retrieved documentation and examples!"

    description = "Modify the retrieved documentation and examples"
    request = HumanInterrupt(
        action_request=ActionRequest(
            action="Modify docs and examples",
            args={"docs": docs, "examples": examples},
        ),
        config=HumanInterruptConfig(
            allow_ignore=True,
            allow_accept=False,
            allow_respond=False,
            allow_edit=True,
        ),
        description=description,
    )

    human_response: HumanResponse = interrupt([request])[0]
    response_type = human_response.get("type")

    print(f"Response type: {response_type}")  # WARNING: DELETE LATER
    print(f"Human response: {human_response}")  # WARNING: DELETE LATER

    if response_type == "edit":
        print("Inside response type")  # WARNING: DELETE LATER
        args_dics = human_response.get("args", {}).get("args", {})
        print(f"Args dicts: {args_dics}")  # WARNING: DELETE LATER
        docs: str = cast(str, args_dics.get("docs", ""))
        examples: str = cast(str, args_dics.get("examples", ""))

    elif response_type == "ignore":
        pass
    else:
        print("Invalid response type, using original docs")

    # elif human_response.get("type") == "ignore":
    #     return Command(
    #         goto=Send(
    #             END,
    #             arg={},
    #         )
    #     )
    print("Creating output")  # WARNING: DELETE LATER
    out = f"""
    # Retrieved from the JutulDarcy documentation
    <details>
    <summary>Show documentation</summary>

    {docs}

    </details>

    # Retrieved from the JutulDarcy examples
    <details>
    <summary>Show examples</summary>

    {examples}

    </details>
    """

    print(out)  # WARNING: DELETE LATER

    return out


@tool(parse_docstring=True)
def retrieve_fimbul(
    query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Use this tool to look up any information, usage, or examples from the Fimbul documentation. ALWAYS use this tool before answering any Julia code question about Fimbul.

    Args:
        query: The string sent into the vectorstore retriever.

    Returns:
        String containing the formatted output from the retriever
    """

    configuration = Configuration.from_runnable_config(config)  # Temp

    print("TOOL INVOKED: retrieve_fimbul")

    retrieved_docs = retrievers["fimbul"]["docs"].invoke(input=query)
    retrieved_examples = retrievers["fimbul"]["examples"].invoke(input=query)

    docs = format_docs(retrieved_docs)
    examples = format_examples(retrieved_examples)

    #     out = f"""
    # # Retrieved from the Fimbul documentation:
    # {docs}

    # # Retrieved from the Fimbul examples:
    # {examples}
    # """
    out = f"""
    # Retrieved from the Fimbul documentation
    <details>
    <summary>Show documentation</summary>

    {docs}

    </details>

    # Retrieved from the Fimbul examples
    <details>
    <summary>Show examples</summary>

    {examples}

    </details>
    """
    print(out)  # WARNING: DELETE LATER

    return out
