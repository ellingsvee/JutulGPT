from jutulgpt.multi_agent_system.agents.coding_agent import CodingAgent
from jutulgpt.nodes._tools import agent_tools
from jutulgpt.prompts import DEFAULT_CODER_PROMPT

agent = CodingAgent(
    part_of_multi_agent=False, prompt=DEFAULT_CODER_PROMPT, tools=agent_tools
)
