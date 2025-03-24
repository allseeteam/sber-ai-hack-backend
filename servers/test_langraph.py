"""
LangGraph Demo Script

This script demonstrates the usage of LangGraph with Postgres state management.

Setup:
1. Copy .env.example to .env and configure your environment variables
2. Start Postgres using docker-compose:
   $ docker-compose up -d postgres
3. Run this script:
   $ python servers/test_langraph.py
"""

import asyncio
import os

from .agentic.graph_manager import AsyncGraphManager

async def demo_langraph():
    """Demo function to showcase the graph functionality."""
    try:
        async with AsyncGraphManager() as manager:
            demo_query = "hello"
            inputs = {"messages": [("user", demo_query)]}
            config = {"configurable": {"thread_id": str(1)}}

            print(f"\nProcessing query: '{demo_query}'\n")
            # values mode returns whole state at each step
            # https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.graph.CompiledGraph.astream
            async for event in manager.graph.astream(inputs, config=config, stream_mode="values"):
                messages = event["messages"]
                message = messages[-1]
                if isinstance(message, tuple):
                    print(message)
                else:
                    message.pretty_print()
                    print("\n")
    except Exception as e:
        print(f"Error during graph execution: {e}")

async def main():
    """Main entry point for the script."""
    await demo_langraph()

if __name__ == "__main__":
    asyncio.run(main())
