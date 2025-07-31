from typing import Annotated, List

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from pydantic import BaseModel, Field

# from jutulgpt import configuration
import jutulgpt.rag.retrieval as retrieval
import jutulgpt.rag.split_docs as split_docs
import jutulgpt.rag.split_examples as split_examples
from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration, cli_mode
from jutulgpt.human_in_the_loop import modify_rag_query, response_on_rag
from jutulgpt.rag.retriever_specs import RETRIEVER_SPECS
from jutulgpt.utils import get_file_source


class RetrieveJutulDarcyToolInput(BaseModel):
    query: str = Field(
        "The query that will be used for document and example retrieval",
    )


@tool("retrieve_jutuldarcy", args_schema=RetrieveJutulDarcyToolInput)
def retrieve_jutuldarcy_tool(
    query: str, config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Use this tool to look up any information, usage, or examples from the JutulDarcy documentation. ALWAYS use this tool before answering any Julia code question about JutulDarcy."""
    configuration = BaseConfiguration.from_runnable_config(config)

    if configuration.human_interaction:
        if cli_mode:
            # CLI mode: use interactive CLI query modification
            from jutulgpt.cli.cli_human_interaction import cli_modify_rag_query

            query = cli_modify_rag_query(query, "JutulDarcy")
        else:
            from jutulgpt.human_in_the_loop import modify_rag_query

            # UI mode: use the original UI-based interaction
            query = modify_rag_query(query, "JutulDarcy")

    if not query.strip():  # If the query is empty, return an informative message
        retrieved_content = "The retrieval was skipped by the user. It is not relevant to the current question."

    with retrieval.make_retriever(
        config=config, spec=RETRIEVER_SPECS["jutuldarcy"]["docs"]
    ) as retriever:
        retrieved_docs = retriever.invoke(query)
    with retrieval.make_retriever(
        config=config, spec=RETRIEVER_SPECS["jutuldarcy"]["examples"]
    ) as retriever:
        retrieved_examples = retriever.invoke(query)

    if configuration.human_interaction:
        if cli_mode:
            from jutulgpt.cli.cli_human_interaction import cli_response_on_rag

            # console.print("\n[bold blue]Retrieved JutulDarcy Documents[/bold blue]")

            retrieved_docs = cli_response_on_rag(
                docs=retrieved_docs,
                get_file_source=get_file_source,
                get_section_path=split_docs.get_section_path,
                format_doc=split_docs.format_doc,
                action_name="Modify retrieved JutulDarcy documentation",
            )

            # console.print("\n[bold blue]Retrieved JutulDarcy Examples[/bold blue]")
            retrieved_examples = cli_response_on_rag(
                docs=retrieved_examples,
                get_file_source=get_file_source,
                get_section_path=split_examples.get_section_path,
                format_doc=split_examples.format_doc,
                action_name="Modify retrieved JutulDarcy examples",
            )
        else:
            # UI mode: use the original UI-based interaction
            retrieved_docs = response_on_rag(
                retrieved_docs,
                get_file_source=get_file_source,
                get_section_path=split_docs.get_section_path,
                format_doc=split_docs.format_doc,
                action_name="Modify retrieved JutulDarcy documentation",
            )
            retrieved_examples = response_on_rag(
                retrieved_examples,
                get_file_source=get_file_source,
                get_section_path=split_examples.get_section_path,
                format_doc=split_examples.format_doc,
                action_name="Modify retrieved JutulDarcy examples",
            )

    docs = split_docs.format_docs(retrieved_docs)
    examples = split_examples.format_examples(retrieved_examples)

    format_str = lambda s: s if s != "" else "(empty)"
    out = f"""
# Retrieved from JutulDarcy documentation 
{format_str(docs)}

# Retrieved from JutulDarcy examples
{format_str(examples)}
"""
    return out


class RetrieveFimbulToolInput(BaseModel):
    query: str = Field(
        "The query that will be used for document and example retrieval",
    )


@tool("retrieve_fimbul", args_schema=RetrieveFimbulToolInput)
def retrieve_fimbul_tool(
    query: str, config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Use this tool to look up any information, usage, or examples from the Fimbul documentation. ALWAYS use this tool before answering any Julia code question about Fimbul."""
    configuration = BaseConfiguration.from_runnable_config(config)

    # Modify the query if human interaction is enabled
    if configuration.human_interaction:
        if cli_mode:
            # CLI mode: use interactive CLI query modification

            from jutulgpt.cli.cli_human_interaction import cli_modify_rag_query

            query = cli_modify_rag_query(query, "Fimbul")
        else:
            # UI mode: use the original UI-based interaction
            query = modify_rag_query(query, "Fimbul")

    with retrieval.make_retriever(
        config=config, spec=RETRIEVER_SPECS["fimbul"]["docs"]
    ) as retriever:
        retrieved_docs = retriever.invoke(query)
    with retrieval.make_retriever(
        config=config, spec=RETRIEVER_SPECS["fimbul"]["examples"]
    ) as retriever:
        retrieved_examples = retriever.invoke(query)

    if configuration.human_interaction:
        if cli_mode:
            from jutulgpt.cli.cli_human_interaction import cli_response_on_rag

            retrieved_docs = cli_response_on_rag(
                docs=retrieved_docs,
                get_file_source=get_file_source,
                get_section_path=split_docs.get_section_path,
                format_doc=split_docs.format_doc,
                action_name="Modify retrieved Fimbul documentation",
            )

            # console.print("\n[bold blue] Retrieved Fimbul Examples[/bold blue]")
            retrieved_examples = cli_response_on_rag(
                docs=retrieved_examples,
                get_file_source=get_file_source,
                get_section_path=split_examples.get_section_path,
                format_doc=split_examples.format_doc,
                action_name="Modify retrieved Fimbul examples",
            )
        else:
            # UI mode: use the original UI-based interaction
            retrieved_docs = response_on_rag(
                retrieved_docs,
                get_file_source=get_file_source,
                get_section_path=split_docs.get_section_path,
                format_doc=split_docs.format_doc,
                action_name="Modify retrieved Fimbul documentation",
            )
            retrieved_examples = response_on_rag(
                retrieved_examples,
                get_file_source=get_file_source,
                get_section_path=split_examples.get_section_path,
                format_doc=split_examples.format_doc,
                action_name="Modify retrieved Fimbul examples",
            )

    docs = split_docs.format_docs(retrieved_docs)
    examples = split_examples.format_examples(retrieved_examples)

    format_str = lambda s: s if s != "" else "(empty)"
    out = f""" 
# Retrieved from Fimbul documentation
{format_str(docs)}

# Retrieved from Fimbul examples
{format_str(examples)}
"""
    return out


class RetrieveFunctionSignatureToolInput(BaseModel):
    function_names: List[str] = Field(
        description="A list of function names to retrieve the function signature for.",
    )


@tool("retrieve_function_signature", args_schema=RetrieveFunctionSignatureToolInput)
def retrieve_function_signature_tool(
    function_names: List[str],
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Use this tool to retrieve the function signature of a specific function from the JutulDarcy documentation. This is useful for understanding how to use a function, its parameters, and return types."""
    retrieved_signatures = retrieval.function_signature_retriever(
        function_names=function_names,
        spec=RETRIEVER_SPECS["jutuldarcy"]["function_signatures"],
    )

    print_to_console(
        text=retrieved_signatures,
        title="Retrieved Function Signatures",
        border_style=colorscheme.message,
    )

    return retrieved_signatures
