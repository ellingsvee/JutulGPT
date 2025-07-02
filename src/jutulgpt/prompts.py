from langchain_core.prompts import ChatPromptTemplate

code_gen_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                You are a coding assistant with expertise in the Julia programming language. \n 
                Answer the user question based on your expertise and the documentation provided above. 
                Ensure any code you provide can be executed with all required imports and variables defined. 
                Structure your answer with a description of the code solution. \n
                Then list the imports of the packages. And finally list the functioning code block. Here is the user question:
            """,
        ),
        ("placeholder", "{messages}"),
    ]
)
# code_gen_prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             """
#                 You are a coding assistant with expertise. \n
#                 Here is some context is relevant to the question:
#                 \n ------- \n
#                 {context}
#                 \n ------- \n
#                 Answer the user question based on your expertise and the documentation provided above.
#                 Ensure any code you provide can be executed with all required imports and variables defined.
#                 Structure your answer with a description of the code solution. \n
#                 Then list the imports. And finally list the functioning code block. Here is the user question:
#             """,
#         ),
#         ("placeholder", "{messages}"),
#     ]
# )
