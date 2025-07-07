from jutulgpt.graph import graph
from jutulgpt.rag import (
    # create_docs_retriever,
    docs_retriever,
    examples_retriever,
    format_docs,
    format_examples,
)
from jutulgpt.state import Code
from jutulgpt.tools import _docs_retriever_tool, _examples_retriever_tool
from jutulgpt.utils import format_code_response, load_lines_from_txt

if __name__ == "__main__":
    # ctx = examples_retriever.invoke(
    #     "How do I discretize the domain using a CartesianMesh?"
    # )
    # print(len(ctx))
    # print(ctx)

    # formatted = format_docs(ctx)
    # print(formatted)
    # chunks = create_docs_retriever()
    # print(chunks)

    qn = "What are the different types of wells?"

    # ctx = docs_retriever.invoke("What are the different types of wells?")
    # # ctx = docs_retriever.invoke("cartesian mesh")
    # formatted = format_docs(ctx)
    # print(formatted)
    ans_1 = _docs_retriever_tool.invoke({"query": qn})
    ans_2 = _examples_retriever_tool.invoke({"query": qn})

    print(ans_1)

    # print(ans_2)
