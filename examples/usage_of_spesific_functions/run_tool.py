from jutulgpt.tools import grep_search

query = "MPI"

if __name__ == "__main__":
    out = grep_search.invoke({"query": query})
