from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver, AsyncConnectionPool
from langgraph.prebuilt import create_react_agent
from langgraph.graph.state import CompiledGraph

from settings import settings
from agentic.agents.code_wizard.code_wizard import (
    code_wizard_tools,
    CODE_WIZARD_SYSTEM_PROMPT,
)
from agentic.llm import llm


# State manager for langgraph graph
class AsyncGraphManager:
    def __init__(self):
        self._graph = None
        self._postgres_saver = None
        self._postgres_connection_pool = None

    async def __aenter__(self) -> 'AsyncGraphManager':
        # AsyncPostgresSaver is responsible for saving the graph state to the PostgreSQL database for ecah user.
        self._postgres_connection_pool = await AsyncConnectionPool(conninfo=settings.checkpointer.POSGRES_CONNECTION_STRING, kwargs={"autocommit": True}).__aenter__()
        self._postgres_saver = AsyncPostgresSaver(self._postgres_connection_pool)
        await self._postgres_saver.setup()
        self._graph: CompiledGraph = create_react_agent(
            model=llm,
            tools=code_wizard_tools,
            prompt=CODE_WIZARD_SYSTEM_PROMPT,
            checkpointer=self._postgres_saver,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._postgres_saver and self._postgres_connection_pool:
            await self._postgres_connection_pool.__aexit__(exc_type, exc_val, exc_tb)
            self._postgres_connection_pool = None
            self._postgres_saver = None

    @property
    def graph(self) -> CompiledGraph:
        if not self._graph:
            raise RuntimeError("Graph not initialized. Use 'async with' context manager.")
        return self._graph
            