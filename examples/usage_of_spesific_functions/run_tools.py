from jutulgpt.tools import grep_search_tool, semantic_search_tool

# query = "geothermal doublet"
query = "MRST"

if __name__ == "__main__":
    out = semantic_search_tool.invoke(query)
    print("Output from semantic search:\n" + out)

    # out = grep_search_tool.invoke({"query": query, "isRegexp": False})
    out = grep_search_tool.invoke({"query": query})
    print("Output from grep search:\n" + out)
