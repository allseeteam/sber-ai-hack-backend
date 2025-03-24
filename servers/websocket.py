import argparse
import asyncio
import json
import websockets

from pydantic_core import ValidationError

from agentic.demo_graph import demo_graph
from common.models import UserRequest


async def conversation(websocket):
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
            async for event in demo_graph.astream(
                input=inputs, config=config, stream_mode="values"
            ):
                messages = event["messages"]
                message = messages[-1]
                if isinstance(message, tuple):
                    print(message)
                else:
                    message.pretty_print()
                    print("\n")

                await websocket.send(
                    json.dumps(
                        {
                            "message": "Я умный бот, а ты мешок с костями.",
                            "id": user_message_json["id"],
                        },
                        ensure_ascii=False,
                    )
                )
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
