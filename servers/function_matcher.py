from langchain_core.messages import AIMessage
from mcp.server.fastmcp import FastMCP, Context

from agentic.graph_manager import AsyncGraphManager
from common import models


mcp = FastMCP("Function Matcher")


@mcp.tool()
async def search_similar_code(request: models.UserRequest, ctx: Context) -> str:
    """Поиск функционально похожего кода в репозиториях."""

    async with AsyncGraphManager() as graph_manager:
        try:
            config = {"configurable": {"thread_id": request.id}}
            inputs = {"messages": [("user", request.message)]}
            async for event in graph_manager.graph.astream(
                input=inputs, config=config, stream_mode="values"
            ):
                messages = event["messages"]
                message = messages[-1]
                if isinstance(message, tuple):
                    print(message)
                else:
                    message.pretty_print()
                    print("\n")

                # Проверяем тип сообщения
                if isinstance(message, AIMessage):
                    # Проверяем, содержит ли AIMessage вызовы инструментов
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        # У AIMessage есть вызовы инструментов, отправляем состояние
                        state = ""
                        for tool_call in message.tool_calls:
                            tool_name = tool_call.name
                            if tool_name == "InspectCode":
                                state = "проверяю файлы"
                                break  # Берем первый инструмент, если их несколько
                            elif tool_name == "SemanticSearch":
                                state = "использую семантический поиск"
                                break
                            elif tool_name == "ExactSearch":
                                state = "ищу файлы по индексу"
                                break

                        # Отправляем сообщение о состоянии
                        ctx.info(state)
                    else:
                        # У AIMessage нет вызовов инструментов, отправляем только содержимое сообщения
                        return message.content
                else:
                    # Если сообщение не AIMessage (например, ToolMessage),
                    # просто игнорируем его или обрабатываем по-другому, если нужно
                    pass
        except Exception as e:
            return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
