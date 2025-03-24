from typing import Optional, List

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.runnables.config import RunnableConfig

from .....settings import settings


class InspectQuery(BaseModel):
    """Pydantic model for the inspect params"""
    link: str = Field(description="Ссылка на файл или папку в github-репозитории")


async def inspect(link: str) -> str:
    """A tool for getting file or folder content"""
    # Getting the search result
    inspect_result = "Mockup inspect result"

    # Returning the search result
    return inspect_result


inspect_tool = StructuredTool.from_function(
    coroutine=inspect,
    name="Inspect",
    description="A tool for getting file or folder content",
    args_schema=InspectQuery,
)
