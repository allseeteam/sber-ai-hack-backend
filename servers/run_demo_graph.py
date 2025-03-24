import asyncio
from agentic.demo_graph import demo_graph


async def run_demo_graph_and_print_events():
    global demo_graph

    demo_query = "buy me a coffee"
    inputs = {"messages": [("user", demo_query)]}

    # values mode retun whole state at each step
    # https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.graph.CompiledGraph.astream
    async for event in demo_graph.astream(inputs, stream_mode="values"):
        messages = event["messages"]
        message = messages[-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()
            print("\n")


if __name__ == "__main__":
    asyncio.run(run_demo_graph_and_print_events())
