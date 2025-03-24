import argparse
import asyncio
import json
import websockets

from pydantic_core import ValidationError

from agentic.graph_manager import AsyncGraphManager
from common.models import UserRequest
from langchain_core.messages import AIMessage, ToolMessage


async def conversation(websocket):
    async with AsyncGraphManager() as graph_manager:
        async for user_message in websocket:
            try:
                print(f"Получено сообщение: {user_message}")
                try:
                    UserRequest.model_validate_json(user_message)
                except ValidationError as e:
                    await websocket.send(
                        json.dumps(
                            {
                                "Error": f"Ошибка сериализации json строки: {e}"
                            },
                            ensure_ascii=False,
                        )
                    )
                    continue

                user_message_json = json.loads(user_message)
                config = {"configurable": {"thread_id": user_message_json["id"]}}
                inputs = {"messages": [("user", user_message)]}
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
                        if hasattr(message, 'tool_calls') and message.tool_calls:
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
                            await websocket.send(
                                json.dumps(
                                    {
                                        "state": state,
                                        "id": user_message_json["id"],
                                    },
                                    ensure_ascii=False,
                                )
                            )
                        else:
                            # У AIMessage нет вызовов инструментов, отправляем только содержимое сообщения
                            await websocket.send(
                                json.dumps(
                                    {
                                        "message": message.content,
                                        "id": user_message_json["id"],
                                    },
                                    ensure_ascii=False,
                                )
                            )
                    else:
                        # Если сообщение не AIMessage (например, ToolMessage),
                        # просто игнорируем его или обрабатываем по-другому, если нужно
                        pass
            except Exception as e:
                await websocket.send(
                    json.dumps(
                        {
                            "Error": str(e)
                        }
                    )
                )


async def main(host: str, port: int):
    async with websockets.serve(conversation, host, port) as server:
        print(f"Сервер запущен на ws://{host}:{port}")
        await server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8765)

    args = parser.parse_args()

    host = args.host
    port = args.port

    asyncio.run(main(host, port))