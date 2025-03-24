from typing import Optional, List, Dict

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.runnables.config import RunnableConfig
import httpx

from .....settings import settings

# Configure the search API URL with a default value
SEARCH_API_URL = getattr(settings, "SEARCH_API_URL", "http://localhost:8000")

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


def format_search_results(snippets: List[Dict]) -> str:
    """Format search results into a readable string"""
    if not snippets:
        return "No matching code found."
        
    result_parts = []
    for snippet in snippets:
        # Format repository information
        repo_info = snippet['repo']
        repo_url = f"{repo_info['url']}/blob/main/{snippet['file_path']}#L{snippet['line_from']}-L{snippet['line_to']}"
        
        # Format the snippet header
        header = f"\nFile: {snippet['file_path']} (Lines {snippet['line_from']}-{snippet['line_to']})"
        header += f"\nRepository: {repo_info['name']}"
        header += f"\nGitHub: {repo_url}\n"
        
        # Format the code with some basic formatting
        code = snippet['code'].strip()
        if code:
            code = "\n".join("    " + line for line in code.split("\n"))
            
        # Combine all parts
        result_parts.append(f"{header}\n{code}\n{'='*80}")
        
    return "\n".join(result_parts)


async def semantic_search(query: str, allowed_repos: Optional[List[str]]) -> str:
    """A tool for searching for a semantic query in the code"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SEARCH_API_URL}/search",
                json={
                    "query": query,
                    "allowed_repos": allowed_repos,
                    "top_n": 10
                }
            )
            
            if response.status_code != 200:
                error_detail = response.json().get('detail', str(response.text))
                raise Exception(f"Search API error (Status {response.status_code}): {error_detail}")
                
            result = response.json()
            return format_search_results(result["snippets"])
            
    except httpx.TimeoutException:
        return "Error: Search API request timed out. Please try again."
    except httpx.RequestError as e:
        return f"Error: Could not connect to Search API ({str(e)})"
    except Exception as e:
        return f"Error performing semantic search: {str(e)}"


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
