from jutulgpt.multi_agent_system.agents.coding_agent import CodingAgent
from jutulgpt.prompts import DEFAULT_CODER_PROMPT
from jutulgpt.tools import (
    read_from_file_tool,
    retrieve_fimbul_tool,
    retrieve_jutuldarcy_tool,
    write_to_file_tool,
)

agent = CodingAgent(
    part_of_multi_agent=False,
    prompt=DEFAULT_CODER_PROMPT,
    tools=[
        retrieve_fimbul_tool,
        retrieve_jutuldarcy_tool,
        read_from_file_tool,
        write_to_file_tool,
    ],
)
