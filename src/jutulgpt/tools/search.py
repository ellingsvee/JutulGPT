# """It includes a basic Tavily search function."""

# from typing import Annotated, Any, Optional, cast

# from dotenv import find_dotenv, load_dotenv
# from langchain_community.tools.tavily_search import TavilySearchResults
# from langchain_core.runnables import RunnableConfig
# from langchain_core.tools import InjectedToolArg, tool

# from jutulgpt.configuration import Configuration

# _: bool = load_dotenv(find_dotenv())


# @tool(parse_docstring=True)
# async def search(
#     query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
# ) -> Optional[list[dict[str, Any]]]:
#     """Search for general web results.

#     Args:
#       query: The query to search for.

#     This function performs a search using the Tavily search engine, which is designed
#     to provide comprehensive, accurate, and trusted results. It's particularly useful
#     for finding information on a wide range of topics.
#     """
#     configuration = Configuration.from_runnable_config(config)
#     wrapped = TavilySearchResults(max_results=configuration.max_search_results)
#     result = await wrapped.ainvoke({"query": query})
#     return cast(list[dict[str, Any]], result)
