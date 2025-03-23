from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# read more:
# - https://langchain-ai.github.io/langgraph/tutorials/introduction/

# Define the state structure
class State(TypedDict):
    messages: Annotated[list, add_messages] # This would make our state value not overrite but uppend new values

# Create the graph builder
graph_builder = StateGraph(State)

# Define the first node
def node1(state: State) -> State:
    return {"messages": ("assistant", "Node 1 executed!")}

# Add the first node to the graph
graph_builder.add_node("node1", node1)

# Define the second node
def node2(state: State) -> State:
    return {"messages": ("assistant", "Node 2 executed!")}

# Add the second node to the graph
graph_builder.add_node("node2", node2)

# Define the third node
def node3(state: State) -> State:
    return {"messages": ("assistant", "Node 3 executed!")}

# Add the third node to the graph
graph_builder.add_node("node3", node3)

# Define the graph's flow (edges)
graph_builder.add_edge(START, "node1")  # Start with `node1`
graph_builder.add_edge("node1", "node2")  # Then to `node2`
graph_builder.add_edge("node2", "node3")  # Then to `node3`
graph_builder.add_edge("node3", END)  # End the graph at `node3`

# Compile the graph
demo_graph = graph_builder.compile()
