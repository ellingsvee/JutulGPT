from langchain_core.runnables import RunnableConfig

from jutulgpt.cli import print_to_console
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.rag.retrieval import function_signature_retriever
from jutulgpt.rag.retriever_specs import RETRIEVER_SPECS

if __name__ == "__main__":
    function_names = [
        "reservoir_domain",
        "setup_vertical_well",
        "setup_well",
        "nonexistent_func",
    ]

    my_config = BaseConfiguration()
    config = RunnableConfig(configurable=my_config.from_runnable_config().__dict__)

    # retrieved_signatures = ""

    spec = RETRIEVER_SPECS["jutuldarcy"]["function_signatures"]
    retrieved_signatures = function_signature_retriever(
        function_names=function_names, spec=spec
    )

    # with retrieval.make_retriever(
    #     config=config,
    #     spec=RETRIEVER_SPECS["jutuldarcy"]["function_signatures"],
    #     retrieval_overrides={
    #         "search_type": "similarity",
    #         "search_kwargs": {"k": 1},
    #     },
    # ) as retriever:
    #     for function_name in function_names:
    #         retrieved_signature = retriever.invoke(function_name)[
    #             0
    #         ].page_content.strip()
    #         if retrieved_signature:
    #             retrieved_signatures += (
    #                 f"Function: {function_name}\nSignature: {retrieved_signature}\n\n"
    #             )

    print_to_console(
        text=retrieved_signatures,
        title="Retrieved Function Signatures",
        border_style="white",
        with_markdown=False,
    )
