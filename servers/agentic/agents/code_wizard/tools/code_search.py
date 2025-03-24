from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.runnables.config import RunnableConfig
import httpx

from .....settings import settings
from servers.sourcebot.sourcebot_client import SourcebotClient, SourcebotApiError

# Configure API URLs with default values
SEARCH_API_URL = getattr(settings, "SEARCH_API_URL", "http://localhost:8000")
SOURCEBOT_URL = getattr(settings, "SOURCEBOT_URL", "http://localhost:3000")

class ExactSearchQuery(BaseModel):
    """Pydantic model for the exact search query"""
    query: str = Field(description="Query to search in the code")
    allowed_repos: Optional[List[str]] = Field(description="List of allowed repositories to search in", default=None)


class SemanticSearchQuery(BaseModel):
    """Pydantic model for the semantic search query"""
    query: str = Field(description="Query to search in the code")
    allowed_repos: Optional[List[str]] = Field(description="List of allowed repositories to search in", default=None)


def format_sourcebot_results(result: Dict[str, Any]) -> str:
    """Format Sourcebot search results into a readable string"""
    if not result or not result.get('matches'):
        return "No matching code found."
        
    result_parts = []
    for match in result['matches']:
        # Extract repository and file information
        repo = match['repository']
        file_name = match['filePath']
        
        # Format the file information
        header = f"\nFile: {file_name}"
        if 'lines' in match:
            line_start = match['lines']['from']
            line_end = match['lines']['to']
            header += f" (Lines {line_start}-{line_end})"
            
        header += f"\nRepository: {repo}"
        
        # Add GitHub link if repository format matches owner/repo
        if '/' in repo:
            github_url = f"https://github.com/{repo}/blob/main/{file_name}"
            if 'lines' in match:
                github_url += f"#L{match['lines']['from']}-L{match['lines']['to']}"
            header += f"\nGitHub: {github_url}"
        
        # Format the code with basic formatting
        code = match.get('content', '').strip()
        if code:
            code = "\n".join("    " + line for line in code.split("\n"))
            
        # Combine all parts
        result_parts.append(f"{header}\n\n{code}\n{'='*80}")
        
    return "\n".join(result_parts)


async def exact_search(query: str, allowed_repos: Optional[List[str]]) -> str:
    """A tool for searching for an exact query in the code using Sourcebot"""
    try:
        async with SourcebotClient(base_url=SOURCEBOT_URL) as client:
            # Perform the search with up to 10 matches
            result = await client.search(
                query=query,
                max_match_display_count=10,
                whole=True  # Get complete file contents for better context
            )
            
            # If allowed_repos is specified, filter the results
            if allowed_repos:
                filtered_matches = [
                    match for match in result.get('matches', [])
                    if match['repository'] in allowed_repos
                ]
                result['matches'] = filtered_matches
                
            return format_sourcebot_results(result)
            
    except SourcebotApiError as e:
        return f"Error: Sourcebot search failed - {str(e)}"
    except Exception as e:
        return f"Error performing exact search: {str(e)}"


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
