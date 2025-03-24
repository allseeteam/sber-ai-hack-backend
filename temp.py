import httpx
import base64
import asyncio
from typing import Union, Dict, List, Optional, Any
import re

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

# Example usage:
async def main():
    # Get file content
    file_content = await get_github_content(
        "https://github.com/octokit/octokit.rb", 
        "README.md"
    )
    if file_content:
        print(f"File content (first 100 chars): {file_content[:100]}...")
    
    # Get directory structure
    dir_structure = await get_github_content(
        "https://github.com/octokit/octokit.rb", 
        "lib"
    )
    if dir_structure:
        print(f"Directory has {len(dir_structure)} items")
        for item in dir_structure[:3]:  # Show first 3 items
            print(f"- {item.get('name')} ({item.get('type')})")

# Run the example
if __name__ == "__main__":
    asyncio.run(main())