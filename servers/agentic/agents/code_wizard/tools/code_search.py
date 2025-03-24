from typing import Optional, List

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.runnables.config import RunnableConfig

from .....settings import settings


class ExactSearchQuery(BaseModel):
    """Pydantic model for the exact search query"""
    query: str = Field(description="Query to search in the code")
    allowed_repos: Optional[List[str]] = Field(description="List of allowed repositories to search in", default=None)


class SemanticSearchQuery(BaseModel):
    """Pydantic model for the semantic search query"""
    query: str = Field(description="Query to search in the code")
    allowed_repos: Optional[List[str]] = Field(description="List of allowed repositories to search in", default=None)


async def exact_search(query: str, allowed_repos: Optional[List[str]]) -> str:
    """A tool for searching for an exact query in the code"""
    # Getting the search result
    search_result = "Mockup search result"

    # Returning the search result
    return search_result


async def semantic_search(query: str, allowed_repos: Optional[List[str]]) -> str:
    """A tool for searching for a semantic query in the code"""
    # Getting the search result
    search_result = "Mockup search result"

    # Returning the search result
    return search_result


# Creating a structured tool for searching for an exact query in the code
exact_search_tool = StructuredTool.from_function(
    coroutine=exact_search,
    name="ExactSearch",
    description="Поиск точного запроса в коде",
    args_schema=ExactSearchQuery,
)


# Creating a structured tool for searching for a semantic query in the code
semantic_search_tool = StructuredTool.from_function(
    coroutine=semantic_search,
    name="SemanticSearch",
    description="Поиск семантического запроса в коде",
    args_schema=SemanticSearchQuery,
)
