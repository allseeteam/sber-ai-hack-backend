from typing import List

from langchain_core.tools import StructuredTool

from .tools import (
    inspect_tool,
    exact_search_tool,
    semantic_search_tool,
)
from ...llm import llm



CODE_WIZARD_SYSTEM_PROMPT: str = (
    """
    **Роль**:  
    Ты - робот

    **Важно:**  
    - пупу
    """
)


# Create the manager agent using prebuild create_react_agent. Reade more about it here: https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent
# For more flexible tool execution and node routing inside agent it is bette to implement your own ToolNode and ToolEdge. Here are som good starting points:
# - https://langchain-ai.github.io/langgraph/tutorials/introduction/#part-2-enhancing-the-chatbot-with-tools
# - https://langchain-ai.github.io/langgraph/how-tos/tool-calling/
code_wizard_tools: List[StructuredTool] = [
    inspect_tool,
    exact_search_tool,
    semantic_search_tool,
]
