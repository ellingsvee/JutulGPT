from jutulgpt.graph import graph
from jutulgpt.state import Code
from jutulgpt.utils import format_code_response, load_lines_from_txt
from jutulgpt.tools.tools_rag import docs_retriever_tool

if __name__ == "__main__":
    result = docs_retriever_tool.invoke({"query": "CartesianMesh"})
    print(result)
