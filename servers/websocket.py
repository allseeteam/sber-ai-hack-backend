import argparse
import asyncio
import json
import logging
import websockets

from pydantic_core import ValidationError

from agentic.graph_manager import AsyncGraphManager
from common.models import UserRequest
from langchain_core.messages import AIMessage, ToolMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def conversation(websocket):
    async with AsyncGraphManager() as graph_manager:
        async for user_message in websocket:
            try:
                logger.info(f"Received message: {user_message}")
                try:
                    UserRequest.model_validate_json(user_message)
                except ValidationError as e:
                    error_msg = f"JSON serialization error: {e}"
                    logger.error(error_msg)
                    await websocket.send(
                        json.dumps(
                            {
                                "Error": error_msg
                            },
                            ensure_ascii=False,
                        )
                    )
                    continue

                user_message_json = json.loads(user_message)
                config = {"configurable": {"thread_id": user_message_json["id"]}}
                inputs = {"messages": [("user", user_message)]}
                logger.debug(f"Processing input with config: {config}")
                
                async for event in graph_manager.graph.astream(
                    input=inputs, config=config, stream_mode="values"
                ):
                    messages = event["messages"]
                    message = messages[-1]
                    logger.info(f"message: {message}")
                    if isinstance(message, tuple):
                        logger.debug(f"Received tuple message: {message}")
                    else:
                        logger.debug(f"Received message of type {type(message).__name__}")

                    # Проверяем тип сообщения
                    if isinstance(message, AIMessage):
                        # Проверяем, содержит ли AIMessage вызовы инструментов
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            # У AIMessage есть вызовы инструментов, отправляем состояние
                            state = ""
                            for tool_call in message.tool_calls:
                                tool_name = tool_call["name"]
                                if tool_name == "InspectCode":
                                    state = "Проверяю файлы"
                                    break  # Берем первый инструмент, если их несколько
                                elif tool_name == "SemanticSearch":
                                    state = "Использую семантический поиск"
                                    break
                                elif tool_name == "ExactSearch":
                                    state = "Ищу файлы по индексу"
                                    break
                            
                            logger.info(f"Sending state: {state} for message ID: {user_message_json['id']}")
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
                            logger.info(f"Sending AI message content for message ID: {user_message_json['id']}")
                            await websocket.send(
                                json.dumps(
                                    {
                                        "message": message.content,
                                        "id": user_message_json["id"],
                                    },
                                    ensure_ascii=False,
                                )
                            )
                    elif isinstance(message, ToolMessage):
                        # Handle ToolMessage and its artifact data
                        logger.info(f"Processing ToolMessage for message ID: {user_message_json['id']}")
                        
                        # Get data from artifact
                        artifact = message.artifact if message.artifact else {}
                        result_type = artifact.get("result_type", "unknown")
                        
                        # Prepare result based on the result type
                        result = None
                        if result_type == "inspect":
                            watched_type = artifact.get("watched_type")
                            details = artifact.get("details", {})
                            
                            if watched_type == "directory":
                                # For directories, return list of files
                                result = [f["url"] for f in details.get("files", [])]
                            else:
                                # For files or errors, return the formatted content
                                result = message.content
                                
                        elif result_type == "search":
                            # For search results, collect matches
                            matches = artifact.get("matches", [])
                            if matches:
                                # Return formatted content for search results
                                result = message.content
                            else:
                                # If no matches or error occurred
                                result = artifact.get("error", "No matches found")
                        else:
                            # For unknown types, return the raw content
                            result = message.content
                            logger.warning(f"Unknown result type: {result_type}")
                        
                        response_data = {
                            "id": user_message_json["id"],
                            "result_type": result_type,
                            "result": result
                        }
                        
                        logger.debug(f"Sending response: {response_data}")
                        await websocket.send(
                            json.dumps(
                                response_data,
                                ensure_ascii=False
                            )
                        )
                    else:
                        # Log other message types but don't process them
                        logger.debug(f"Skipping message of type: {type(message).__name__}")
                        pass
            except Exception as e:
                logger.exception(f"Error processing message: {e}")
                await websocket.send(
                    json.dumps(
                        {
                            "Error": str(e)
                        }
                    )
                )


async def main(host: str, port: int):
    logger.info(f"Starting server on ws://{host}:{port}")
    async with websockets.serve(conversation, host, port) as server:
        logger.info(f"Server running on ws://{host}:{port}")
        await server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

    args = parser.parse_args()

    host = args.host
    port = args.port
    
    # Set log level from command line argument
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    logger.info(f"Starting application with log level: {args.log_level}")
    asyncio.run(main(host, port))