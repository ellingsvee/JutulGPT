from functools import partial
from typing import Annotated, List

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg, tool
from pydantic import BaseModel, Field

# from jutulgpt import configuration
import jutulgpt.rag.retrieval as retrieval
import jutulgpt.rag.split_docs as split_docs
import jutulgpt.rag.split_examples as split_examples
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
        description=f"""Use this tool to look up any information, usage, or examples from the {doc_label} documentation. ALWAYS use this tool before answering any Julia code question about {doc_label}.""",
    )
    def retrieve_tool(
        query: str, config: Annotated[RunnableConfig, InjectedToolArg]
    ) -> str:
        configuration = BaseConfiguration.from_runnable_config(config)

        # Human interaction: modify query
        if configuration.human_interaction.rag_query:
            if cli_mode:
                from jutulgpt.cli.cli_human_interaction import cli_modify_rag_query

                query = cli_modify_rag_query(query, doc_label)
            else:
                from jutulgpt.human_in_the_loop import modify_rag_query

                query = modify_rag_query(query, doc_label)

        if not query.strip():
            return "The retrieval was skipped by the user. It is not relevant to the current question."

        # Retrieve docs/examples
        with retrieval.make_retriever(
            config=config,
            spec=RETRIEVER_SPECS[doc_key]["docs"],
            retrieval_params=retrieval.RetrievalParams(
                search_type=configuration.documents_search_type,
                search_kwargs=configuration.documents_search_kwargs,
            ),
        ) as retriever:
            retrieved_docs = retriever.invoke(query)
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
                from jutulgpt.cli.cli_human_interaction import cli_response_on_rag

                if configuration.human_interaction.retrieved_documents:
                    retrieved_docs = cli_response_on_rag(
                        docs=retrieved_docs,
                        get_file_source=get_file_source,
                        get_section_path=split_docs.get_section_path,
                        format_doc=split_docs.format_doc,
                        action_name=f"Modify retrieved {doc_label} documentation",
                    )
                if configuration.human_interaction.retrieved_examples:
                    retrieved_examples = cli_response_on_rag(
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
                from jutulgpt.human_in_the_loop import response_on_rag

                if configuration.human_interaction.retrieved_documents:
                    retrieved_docs = response_on_rag(
                        retrieved_docs,
                        get_file_source=get_file_source,
                        get_section_path=split_docs.get_section_path,
                        format_doc=split_docs.format_doc,
                        action_name=f"Modify retrieved {doc_label} documentation",
                    )
                if configuration.human_interaction.retrieved_examples:
                    retrieved_examples = response_on_rag(
                        retrieved_examples,
                        get_file_source=get_file_source,
                        get_section_path=split_examples.get_section_path,
                        format_doc=split_examples.format_doc,
                        action_name=f"Modify retrieved {doc_label} examples",
                    )

        docs = split_docs.format_docs(retrieved_docs)
        examples = split_examples.format_examples(retrieved_examples)

        format_str = lambda s: s if s != "" else "(empty)"
        out = f"""
# Retrieved from {doc_label} documentation
{format_str(docs)}

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
retrieve_jutuldarcy_tool = make_retrieve_tool(
    name="retrieve_jutuldarcy",
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

    _, retrieved_signatures = get_function_documentation_from_list_of_funcs(
        func_names=function_names
    )

    if retrieved_signatures:
        return retrieved_signatures

    return "No function signatures found for the provided function names."
