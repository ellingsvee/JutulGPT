from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import interrupt


def modify_rag_query(query: str, retriever_name: str) -> str:
    """
    The code is shortened before the test run. This interaction allows the user to previev the shoretned code to make sure nothing breaking has happened.
    """
    interrupt_message = f"Trying to retrieve documents from {retriever_name}. Modify the query if needed."

    # Create the human interrupt request
    request = HumanInterrupt(
        action_request=ActionRequest(
            action=f"Modify {retriever_name} query", args={"Query": query}
        ),
        config=HumanInterruptConfig(
            allow_ignore=False,
            allow_accept=True,
            allow_respond=False,
            allow_edit=True,
        ),
    )

    # Wait for the user's response
    human_response: HumanResponse = interrupt([request])[0]
    response_type = human_response.get("type")

    if response_type == "edit":
        args_dics = human_response.get("args", {}).get("args", {})
        new_query = args_dics.get("Query", query)
        if new_query.strip() != "":
            query = new_query
    elif human_response.get("type") == "ignore":
        query = ""
    elif human_response.get("type") == "accept":
        pass
    else:
        raise TypeError(
            f"Interrupt value of type {type(human_response)} is not supported."
        )
    return query
