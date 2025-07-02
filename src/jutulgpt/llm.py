from langchain_ollama import ChatOllama

from jutulgpt.config import model_name
from jutulgpt.prompts import code_gen_prompt
from jutulgpt.state import Code

llm = ChatOllama(model=model_name)
structured_llm = llm.with_structured_output(Code, include_raw=True)


def parse_output(solution):
    return solution["parsed"]


code_gen_chain = code_gen_prompt | structured_llm | parse_output
concatenated_content = ""  # Placeholder for documentation
