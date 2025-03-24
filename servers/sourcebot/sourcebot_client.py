from typing import Dict, Any
import httpx
import base64

class SourcebotApiError(Exception):
    """Base exception for Sourcebot API errors"""
    def __init__(self, message: str):
        super().__init__(message)

class SourcebotClient:
    def __init__(self, base_url: str = "http://localhost:3000"):
        """
        Initialize the Sourcebot API client.
        
        Args:
            base_url: Base URL of the Sourcebot API (default: http://localhost:3000)
        """
        self._base_url = base_url.rstrip('/')
        self._client = None

    async def __aenter__(self) -> 'SourcebotClient':
        self._client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._client

    def _build_url(self, endpoint: str) -> str:
        return f"{self._base_url}/api{endpoint}"

    async def search(self, query: str, max_match_display_count: int, whole: bool = None) -> Dict[str, Any]:
        """
        Search through repositories.
        
        Args:
            query: Search query string
            max_match_display_count: Maximum number of matches to display
            whole: Optional flag to return whole file content
            
        Returns:
            JSON response containing search results
        
        Raises:
            SourcebotApiError: If the API request fails
        """
        data = {
            "query": query,
            "maxMatchDisplayCount": max_match_display_count
        }
        if whole is not None:
            data["whole"] = whole

        response = await self.client.post(
            self._build_url("/search"),
            json=data
        )
        
        if response.status_code != 200:
            raise SourcebotApiError(f"Search failed: {response.text}")
            
        try:
            return response.json()
        except Exception as e:
            print(f"Raw response: {response.text}")  # Debug the raw response
            raise SourcebotApiError(f"Failed to parse search response: {str(e)}")

    async def get_file_source(self, file_name: str, repository: str, branch: str = None) -> Dict[str, Any]:
        """
        Fetch source code for a specific file.
        
        Args:
            file_name: Name/path of the file
            repository: Repository identifier
            branch: Optional branch name
            
        Returns:
            JSON response containing the file source and language
            
        Raises:
            SourcebotApiError: If the API request fails
        """
        data = {
            "fileName": file_name,
            "repository": repository
        }
        if branch:
            data["branch"] = branch

        response = await self.client.post(
            self._build_url("/source"),
            json=data
        )
        
        if response.status_code != 200:
            raise SourcebotApiError(f"Get file source failed: {response.text}")
            
        try:
            return response.json()
        except Exception as e:
            print(f"Raw response: {response.text}")  # Debug the raw response
            raise SourcebotApiError(f"Failed to parse file source response: {str(e)}")

    async def get_repos(self) -> Dict[str, Any]:
        """
        Get list of repositories.
        
        Returns:
            JSON response containing repository information
            
        Raises:
            SourcebotApiError: If the API request fails
        """
        response = await self.client.get(self._build_url("/repos"))
        
        if response.status_code != 200:
            raise SourcebotApiError(f"Get repos failed: {response.text}")
            
        try:
            return response.json()
        except Exception as e:
            print(f"Raw response: {response.text}")  # Debug the raw response
            raise SourcebotApiError(f"Failed to parse repos response: {str(e)}")

    async def get_version(self) -> Dict[str, Any]:
        """
        Get sourcebot version.
        
        Returns:
            JSON response containing version information
            
        Raises:
            SourcebotApiError: If the API request fails
        """
        response = await self.client.get(self._build_url("/version"))
        
        if response.status_code != 200:
            raise SourcebotApiError(f"Get version failed: {response.text}")
            
        try:
            return response.json()
        except Exception as e:
            raise SourcebotApiError(f"Failed to parse version response: {str(e)}")
