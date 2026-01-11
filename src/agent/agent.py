from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, AgentType
from agent.tools import (
    job_post_tool,
    resume_parse_tool,
    match_profiles_tool
)

from langchain.prompts import SystemMessagePromptTemplate

SYSTEM_PROMPT = """
You are an HR assistant agent.
You MUST always respond using this format:

Thought:
Action:
Action Input:

Never refuse. If the task is not allowed, explain it using the Action 'Final Answer'.
"""

llm = Ollama(
    model="llama3",
    temperature=0
)

tools = [
    job_post_tool,
    resume_parse_tool,
    match_profiles_tool
]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,  # ⭐ IMPORTANT
)

def run_agent(user_input, memory):
    try:
        response = agent.run(user_input)
        return response
    except ValueError as e:
        response = "⚠️ I couldn’t process that request. Please rephrase."
        return response