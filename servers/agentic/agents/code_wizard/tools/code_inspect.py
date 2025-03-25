from typing import Optional, Dict, List, Union
import httpx
import base64
import re

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.runnables.config import RunnableConfig


class InspectQuery(BaseModel):
    """Pydantic model for the code inspection query"""
    repo_url: str = Field(description="Полная ссылка на репозиторий на Github (к примеру, 'https://github.com/владелец/название_репозитория')")
    path: str = Field(description="Относительный путь внутри репозитория к папке или файлу (к примеру, 'папка/имя_файла.расширение_файла')", default="")


async def get_github_content(repo_url: str, path: str = "") -> Union[str, List[Dict], None]:
    """
    Asynchronously fetches the content of a file or folder from a GitHub repository.
    
    Args:
        repo_url: Full GitHub repository URL (e.g., "https://github.com/owner/repo")
        path: Relative path within the repository (e.g., "folder/file.txt")
        
    Returns:
        - For files: The raw file content as a string
        - For directories: A list of dictionaries with file/directory information
        - None: If the resource doesn't exist or there's an error
    """
    # Extract owner and repo from URL
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        return None
    
    owner, repo = match.groups()
    # Remove .git extension if present
    repo = repo.replace(".git", "")
    
    # Normalize path (remove leading and trailing slashes)
    path = path.strip("/")
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    
    async with httpx.AsyncClient() as client:
        try:
            # Set Accept header for raw content for files
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            response = await client.get(api_url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle directory case (list of files/folders)
            if isinstance(data, list):
                return data
            
            # Handle file case
            elif isinstance(data, dict) and data.get("type") == "file":
                # Extract and decode content if it's base64 encoded
                if data.get("encoding") == "base64" and "content" in data:
                    content = base64.b64decode(data["content"]).decode("utf-8")
                    return content
                
                # If raw content is not included, fetch it directly using download_url
                elif "download_url" in data:
                    raw_response = await client.get(data["download_url"], follow_redirects=True)
                    raw_response.raise_for_status()
                    return raw_response.text
                
                return None
            
            # Handle symlink case
            elif isinstance(data, dict) and data.get("type") == "symlink":
                # Follow the symlink target
                if "target" in data:
                    return await get_github_content(repo_url, data["target"])
                return None
            
            # Handle submodule case (limited support)
            elif isinstance(data, dict) and data.get("type") == "submodule":
                return f"Submodule: {data.get('submodule_git_url', 'Unknown submodule URL')}"
            
            return None
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Try alternate methods - maybe it's a README
                if not path or path == "":
                    try:
                        readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
                        readme_response = await client.get(readme_url, headers=headers)
                        readme_response.raise_for_status()
                        
                        readme_data = readme_response.json()
                        if readme_data.get("encoding") == "base64" and "content" in readme_data:
                            return base64.b64decode(readme_data["content"]).decode("utf-8")
                    except:
                        pass
            return None
            
        except (httpx.RequestError, ValueError, KeyError) as e:
            return None


def format_content_result(content: Union[str, List[Dict], None], repo_url: str, path: str) -> str:
    """Format the content result into a readable string"""
    if content is None:
        return f"Error: Could not fetch content from {repo_url}/{path}"
    
    # Handle directory listing
    if isinstance(content, list):
        result_parts = [f"Contents of {repo_url}/{path}:"]
        for item in content:
            item_type = item.get('type', 'unknown')
            item_name = item.get('name', 'unnamed')
            
            # Add type-specific formatting
            if item_type == 'file':
                result_parts.append(f"📄 {item_name}")
            elif item_type == 'dir':
                result_parts.append(f"📁 {item_name}/")
            elif item_type == 'symlink':
                result_parts.append(f"🔗 {item_name} -> {item.get('target', 'unknown')}")
            else:
                result_parts.append(f"❓ {item_name}")
        
        return "\n".join(result_parts)
    
    # Handle file content
    if isinstance(content, str):
        if path.endswith(('.md', '.txt')):
            # For markdown and text files, return as is
            return content
        else:
            # For code files, add some basic formatting
            lines = content.split('\n')
            formatted_lines = [f"{i+1:4d} | {line}" for i, line in enumerate(lines)]
            return '\n'.join(formatted_lines)
    
    return str(content)


async def inspect_code(repo_url: str, path: str = "") -> str:
    """
    A tool for inspecting code in GitHub repositories
    
    Args:
        repo_url: Full GitHub repository URL
        path: Relative path within the repository
        
    Returns:
        Formatted string containing the inspection results
    """
    try:
        content = await get_github_content(repo_url, path)
        return format_content_result(content, repo_url, path)
    except Exception as e:
        return f"Error inspecting code: {str(e)}"


# Creating a structured tool for code inspection
inspect_tool = StructuredTool.from_function(
    coroutine=inspect_code,
    name="InspectCode",
    description=(
"""
Просмотр содержимого файлов или папок в репозиториях на GitHub.
"""
    ),
    args_schema=InspectQuery,
)
