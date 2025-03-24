from typing import List, Optional
from pydantic import BaseModel

class Repository(BaseModel):
    """Repository metadata model"""
    name: str
    path: str
    url: str

class CodeSnippet(BaseModel):
    """Code snippet model with metadata"""
    id: str
    code: str
    file_path: str
    line_from: int
    line_to: int
    repo: Repository

class SearchQuery(BaseModel):
    """Search query parameters"""
    query: str
    top_n: int = 10
    allowed_repos: Optional[List[str]] = None
    
class SearchResult(BaseModel):
    """Search results container"""
    snippets: List[CodeSnippet]

class ServiceStatus(BaseModel):
    """Service health/status information"""
    status: str
    error: Optional[str] = None

class IndexStatus(BaseModel):
    """Indexing process status information"""
    status: str
    total_docs: Optional[int] = None
    error: Optional[str] = None

class SystemStatus(BaseModel):
    """Overall system status"""
    status: str
    embedder: ServiceStatus
    qdrant: ServiceStatus
    index: IndexStatus