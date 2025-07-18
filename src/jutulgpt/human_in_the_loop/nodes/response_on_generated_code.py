from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import interrupt

from jutulgpt.configuration import Configuration, interactive_environment
from jutulgpt.state import State
from jutulgpt.utils import get_last_code_response


def response_on_generated_code(state: State, config: RunnableConfig):
    if interactive_environment:
        configuration = Configuration.from_runnable_config(config)

        messages = state.messages
        code_block = get_last_code_response(state)

        description = "The RAG provided you with the following documents. You can modify the content of any of these documents by editing the text in the input boxes below. If you do not want to modify a document, leave the input box empty."
        request = HumanInterrupt(
            action_request=ActionRequest(
                action="Modify the generated code",
                args={"imports": code_block.imports, "code": code_block.code},
            ),
            config=HumanInterruptConfig(
                allow_ignore=True,
                allow_accept=False,
                allow_respond=False,
                allow_edit=True,
            ),
            description=description,
        )

        human_response: HumanResponse = interrupt([request])[0]
        response_type = human_response.get("type")
        if response_type == "edit":
            args_dics = human_response.get("args", {}).get("args", {})

            # Get the updated imports and code
            imports = args_dics.get("imports", code_block.imports)
            code = args_dics.get("code", code_block.code)

            # Add a new message to the state
            human_message_content = f"""The code was updated by the user. The followng is what will be run and checked:
```julia
{imports}

{code}
```
"""

            # Return the updated message.
            return {"messages": [AIMessage(content=human_message_content)]}

        elif response_type == "ignore":
            pass
        else:
            raise TypeError(
                f"Interrupt value of type {response_type} is not supported."
            )

    # Return the unmodified state. This is always called if not in an interactive environment.
    return {}
