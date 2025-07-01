from langchain_ollama import ChatOllama
from schema import Code
from config import model_name
from prompts import code_gen_prompt

llm = ChatOllama(model=model_name)
structured_llm = llm.with_structured_output(Code, include_raw=True)


def parse_output(solution):
    return solution["parsed"]


code_gen_chain = code_gen_prompt | structured_llm | parse_output
concatenated_content = ""  # Placeholder for documentation
