from langchain_core.messages import convert_to_messages
from langchain_core.runnables.config import RunnableConfig

# from jutulgpt.agents import agent_config
from jutulgpt.graph import graph

# from jutulgpt.state import InputState
from jutulgpt.utils import get_tool_message


def main():
    print("Welcome to JutulGPT! Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        # Build initial state from user input
        # state = make_initial_state(user_input)
        # state = InputState(
        #     messages=convert_to_messages([{"role": "user", "content": user_input}]),
        # )

        # Stream the graph's response
        print("JutulGPT:")
        prev_message = None
        for chunk in graph.stream({"messages": [("user", user_input.strip())]}):
            for node, update in chunk.items():
                # Print only the latest message from the assistant
                # tool_message = get_tool_message(update["messages"], print=True)
                try:
                    msg = update["messages"][-1]
                    # Only print AI messages (not user echo)
                    if getattr(msg, "type", None) == "ai":
                        if prev_message is None or msg.content != prev_message.content:
                            print(msg.content)
                        prev_message = msg
                except Exception as e:
                    pass


if __name__ == "__main__":
    main()
