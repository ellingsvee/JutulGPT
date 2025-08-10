from functools import partial
from typing import Annotated, List

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg, tool
from pydantic import BaseModel, Field

# from jutulgpt import configuration
import jutulgpt.rag.retrieval as retrieval
import jutulgpt.rag.split_examples as split_examples
from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration, cli_mode
from jutulgpt.julia import get_function_documentation_from_list_of_funcs
from jutulgpt.rag.retriever_specs import RETRIEVER_SPECS
from jutulgpt.utils import get_file_source


def make_retrieve_tool(
    name: str,
    doc_key: str,
    doc_label: str,
    input_cls: type,
) -> BaseTool:
    @tool(
        name,
        args_schema=input_cls,
        description=f"""Use this tool to look up full examples from the {doc_label} documentation. Use this tool when answering any Julia code question about {doc_label}.""",
    )
    def retrieve_tool(
        query: str, config: Annotated[RunnableConfig, InjectedToolArg]
    ) -> str:
        configuration = BaseConfiguration.from_runnable_config(config)

        # Human interaction: modify query
        if configuration.human_interaction.rag_query:
            if cli_mode:
                from jutulgpt.human_in_the_loop.cli import modify_rag_query

                query = modify_rag_query(query, doc_label)
            else:
                from jutulgpt.human_in_the_loop.ui import modify_rag_query

                query = modify_rag_query(query, doc_label)
        else:
            print_to_console(
                text=f"**Query:** `{query}`",
                title=f"Retrieving from {doc_label}",
                border_style=colorscheme.message,
            )

        if not query.strip():
            return "The query is empty."

        # Retrieve examples
        with retrieval.make_retriever(
            config=config,
            spec=RETRIEVER_SPECS[doc_key]["examples"],
            retrieval_params=retrieval.RetrievalParams(
                search_type=configuration.examples_search_type,
                search_kwargs=configuration.examples_search_kwargs,
            ),
        ) as retriever:
            retrieved_examples = retriever.invoke(query)

        # Human interaction: filter docs/examples
        if (
            configuration.human_interaction.retrieved_documents
            or configuration.human_interaction.retrieved_examples
        ):
            if cli_mode:
                from jutulgpt.human_in_the_loop.cli import response_on_rag

                if configuration.human_interaction.retrieved_examples:
                    retrieved_examples = response_on_rag(
                        docs=retrieved_examples,
                        get_file_source=get_file_source,
                        get_section_path=split_examples.get_section_path,
                        format_doc=partial(
                            split_examples.format_doc, within_julia_context=False
                        ),
                        action_name=f"Modify retrieved {doc_label} examples",
                        edit_julia_file=True,
                    )
            else:
                from jutulgpt.human_in_the_loop.ui import response_on_rag

                if configuration.human_interaction.retrieved_examples:
                    retrieved_examples = response_on_rag(
                        retrieved_examples,
                        get_file_source=get_file_source,
                        get_section_path=split_examples.get_section_path,
                        format_doc=split_examples.format_doc,
                        action_name=f"Modify retrieved {doc_label} examples",
                    )

        # docs = split_docs.format_docs(retrieved_docs)
        examples = split_examples.format_examples(retrieved_examples)

        format_str = lambda s: s if s != "" else "(empty)"
        out = f"""
# Retrieved from {doc_label} examples
{format_str(examples)}
"""
        return out

    return retrieve_tool


# Input schemas
class RetrieveJutulDarcyToolInput(BaseModel):
    query: str = Field(
        "The query that will be used for document and example retrieval",
    )


class RetrieveFimbulToolInput(BaseModel):
    query: str = Field(
        "The query that will be used for document and example retrieval",
    )


# Create tools
retrieve_jutuldarcy_examples_tool = make_retrieve_tool(
    name="retrieve_jutuldarcy_examples",
    doc_key="jutuldarcy",
    doc_label="JutulDarcy",
    input_cls=RetrieveJutulDarcyToolInput,
)

retrieve_fimbul_tool = make_retrieve_tool(
    name="retrieve_fimbul",
    doc_key="fimbul",
    doc_label="Fimbul",
    input_cls=RetrieveFimbulToolInput,
)


# Tool for retrieving function documentation
class RetrieveFunctionDocumentationToolInput(BaseModel):
    function_names: List[str] = Field(
        description="A list of function names to retrieve the documentation for.",
    )


@tool(
    "retrieve_function_documentation",
    args_schema=RetrieveFunctionDocumentationToolInput,
)
def retrieve_function_documentation_tool(
    function_names: List[str],
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Use this tool to retrieve the documentation for spesific Julia functions."""

    _, retrieved_signatures = get_function_documentation_from_list_of_funcs(
        func_names=function_names
    )

    if retrieved_signatures:
        return retrieved_signatures

    return "No function signatures found for the provided function names."
