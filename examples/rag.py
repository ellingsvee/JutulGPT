from langchain_core.runnables import RunnableConfig

import jutulgpt.rag.retrieval as retrieval
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.rag.retriever_specs import RETRIEVER_SPECS

if __name__ == "__main__":
    query = "geothermal_doublet function"

    my_config = BaseConfiguration()
    config = RunnableConfig(configurable=my_config.from_runnable_config().__dict__)

    with retrieval.make_retriever(
        config=config, spec=RETRIEVER_SPECS["fimbul"]["docs"]
    ) as retriever:
        retrieved_docs = retriever.invoke(query)
        for doc in retrieved_docs:
            print(f"Source: {doc.metadata['source']}")
            print(f"- {doc.page_content[:100]}...\n")
