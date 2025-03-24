from typing import List

from langchain_core.tools import StructuredTool

from .tools import (
    inspect_tool,
    exact_search_tool,
    semantic_search_tool,
)

CODE_WIZARD_SYSTEM_PROMPT: str = (
    """
    **Роль**:
    Ты - AI-агент, с доступом к функциям поиска и просмотра кода. Твоя задача: находить функционально похожий код по запросу пользователя и предоставить ему информацию о твоих результатах с указанием источников.

    **Важно**:
    - Не уточняй ограничения по репозиториям для поиска, если пользователь не уточнил их сам.
    - Используй доступные инструменты (tools) для выполнения задач.
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
