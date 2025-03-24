from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import httpx
import json
import os
import uuid
import time
from typing import List, Dict, Any, Optional
import asyncio
import logging
import glob
from git import Repo
from qdrant_client import QdrantClient, models

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Code Search API", description="Search code across repositories using vector embeddings")

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
EMBEDDER_URL = os.getenv("EMBEDDER_URL", "http://embedder:8000/v1/embeddings")
COLLECTION_NAME = "code-search"
REPOS_DIR = "./data/semantic_search/repos"
CONFIG_FILE = os.getenv("CONFIG_PATH", "repos_config.json")

# Create necessary directories
os.makedirs(REPOS_DIR, exist_ok=True)

# Background indexing state
indexing_status = {"status": "not_started", "total_docs": 0, "error": None}

async def clone_repository(repo_name: str) -> str:
    """Clone a GitHub repository"""
    repo_url = f"https://github.com/{repo_name}.git"
    repo_path = os.path.join(REPOS_DIR, repo_name.replace("/", "_"))
    
    if os.path.exists(repo_path):
        logger.info(f"Repository {repo_name} already exists at {repo_path}")
        return repo_path
    
    logger.info(f"Cloning {repo_name} to {repo_path}")
    os.makedirs(os.path.dirname(repo_path), exist_ok=True)
    Repo.clone_from(repo_url, repo_path)
    return repo_path

def extract_code_snippets(repo_path: str, repo_name: str) -> List[Dict[str, Any]]:
    """Extract code snippets from a repository"""
    snippets = []
    
    code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.hpp', '.h', '.c', '.cs', '.go', '.rs', '.php', '.rb']
    
    for ext in code_extensions:
        files = glob.glob(f"{repo_path}/**/*{ext}", recursive=True)
        
        for file_path in files:
            rel_path = os.path.relpath(file_path, repo_path)
            
            if any(d in rel_path.split(os.sep) for d in ['__pycache__', 'node_modules', '.git']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                chunk_size = 100
                for i in range(0, len(lines), chunk_size):
                    chunk = '\n'.join(lines[i:i+chunk_size])
                    if not chunk.strip():
                        continue
                        
                    snippets.append({
                        "id": str(uuid.uuid4()),
                        "code": chunk,
                        "file_path": rel_path,
                        "line_from": i + 1,
                        "line_to": min(i + chunk_size, len(lines)),
                        "repo": {
                            "name": repo_name,
                            "path": repo_path,
                            "url": f"github.com/{repo_name}"
                        }
                    })
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
    
    return snippets

async def process_repositories():
    """Background task to process and index repositories"""
    global indexing_status

    # Check if collection already has data
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        if collection_info.points_count > 0:
            logger.info(f"Collection already contains {collection_info.points_count} points. Skipping indexing.")
            indexing_status["status"] = "completed"
            indexing_status["total_docs"] = collection_info.points_count
            return
    except Exception as e:
        logger.error(f"Error checking collection: {e}")
    
    try:
        # Wait for embedder to be ready (no timeout)
        indexing_status["status"] = "waiting_for_embedder"
        while True:
            try:
                if await check_embedder_available():
                    logger.info("Embedder service is available")
                    break
            except Exception as e:
                logger.info("Waiting for embedder service...")
            await asyncio.sleep(5)

        indexing_status["status"] = "indexing"
        
        # Load config
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Process each repository
        for repo_config in config['repos']:
            if repo_config['type'] == 'github':
                for repo_name in repo_config['repos']:
                    try:
                        # Clone repository
                        repo_path = await clone_repository(repo_name)
                        
                        # Extract code snippets
                        logger.info(f"Extracting code from {repo_name}")
                        snippets = extract_code_snippets(repo_path, repo_name)
                        logger.info(f"Found {len(snippets)} code snippets in {repo_name}")
                        
                        # Index snippets in batches
                        batch_size = 50
                        for i in range(0, len(snippets), batch_size):
                            batch = snippets[i:i+batch_size]
                            
                            points = []
                            for snippet in batch:
                                try:
                                    # Get embedding
                                    embedding = await get_embedding(snippet["code"])
                                    
                                    # Create point
                                    point = models.PointStruct(
                                        id=snippet["id"],
                                        vector=embedding,
                                        payload=snippet
                                    )
                                    points.append(point)
                                    
                                except Exception as e:
                                    logger.error(f"Error processing snippet: {e}")
                            
                            if points:
                                qdrant_client.upsert(
                                    collection_name=COLLECTION_NAME,
                                    points=points,
                                    wait=True
                                )
                                indexing_status["total_docs"] += len(points)
                                
                    except Exception as e:
                        logger.error(f"Error processing repository {repo_name}: {e}")
        
        indexing_status["status"] = "completed"
        
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        indexing_status["status"] = "error"
        indexing_status["error"] = str(e)

# Data models
class Repository(BaseModel):
    name: str
    path: str
    url: str

class CodeSnippet(BaseModel):
    id: str
    code: str
    file_path: str
    line_from: int
    line_to: int
    repo: Repository

class SearchQuery(BaseModel):
    query: str
    top_n: int = 10
    allowed_repos: Optional[List[str]] = None
    
class SearchResult(BaseModel):
    snippets: List[CodeSnippet]

class ServiceStatus(BaseModel):
    status: str
    error: Optional[str] = None

class IndexStatus(BaseModel):
    status: str
    total_docs: Optional[int] = None
    error: Optional[str] = None

class SystemStatus(BaseModel):
    status: str
    embedder: ServiceStatus
    qdrant: ServiceStatus
    index: IndexStatus
    
# Global client
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Initialize collection
def ensure_collection_exists():
    try:
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if COLLECTION_NAME not in collection_names:
            logger.info(f"Creating collection {COLLECTION_NAME}")
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=1536,  # Update this to match the embedder's output size
                    distance=models.Distance.COSINE
                )
            )
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise

async def check_embedder_available() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                EMBEDDER_URL,
                json={
                    "input": "test",
                    "model": "Qodo/Qodo-Embed-1-1.5B"
                },
                timeout=5.0
            )
            if response.status_code == 200 and "data" in response.json():
                return True
            return False
    except Exception:
        return False

@app.on_event("startup")
async def startup():
    # Initialize collection
    ensure_collection_exists()
    
    # Check if collection is already populated
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        if collection_info.points_count > 0:
            logger.info(f"Collection {COLLECTION_NAME} already contains {collection_info.points_count} points. Skipping indexing.")
            global indexing_status
            indexing_status["status"] = "completed"
            indexing_status["total_docs"] = collection_info.points_count
            return
    except Exception as e:
        logger.error(f"Error checking collection: {e}")
    
    # Start background indexing task only if collection is empty
    asyncio.create_task(process_repositories())


# Get embeddings from vllm service
async def get_embedding(text: str) -> List[float]:
    instruction = "Instruct: Given Code or Text, retrieval relevant content\nQuery: "
    prompt = f"{instruction}{text}" if "query" in text else text
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                EMBEDDER_URL,
                json={
                    "input": prompt,
                    "model": "Qodo/Qodo-Embed-1-1.5B"
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                logger.error(f"Embedding API error: Status={response.status_code}, Response={response.text}")
                raise HTTPException(status_code=500, detail=f"Embedding service error: {response.text}")
                
            result = response.json()
            return result["data"][0]["embedding"]
            
    except Exception as e:
        logger.error(f"Failed to get embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")

# API endpoints
@app.post("/index")
async def index_code(snippets: List[CodeSnippet]):
    """
    Index code snippets from repositories
    """
    points = []
    
    for snippet in snippets:
        try:
            # Get embedding for the code
            embedding = await get_embedding(snippet.code)
            
            # Create point
            point = models.PointStruct(
                id=snippet.id,
                vector=embedding,
                payload={
                    "code": snippet.code,
                    "file_path": snippet.file_path,
                    "line_from": snippet.line_from,
                    "line_to": snippet.line_to,
                    "repo": {
                        "name": snippet.repo.name,
                        "path": snippet.repo.path,
                        "url": snippet.repo.url
                    }
                }
            )
            points.append(point)
            
        except Exception as e:
            logger.error(f"Error processing snippet {snippet.id}: {e}")
    
    if points:
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True
        )
    
    return {"indexed": len(points)}

@app.get("/status", response_model=SystemStatus)
async def get_status():
    """Get system status including all components"""
    
    # Check embedder
    is_embedder_ready = await check_embedder_available()
    embedder_status = ServiceStatus(
        status="ready" if is_embedder_ready else "starting",
        error=None if is_embedder_ready else "Waiting for embedder to initialize (this may take a few minutes)"
    )
    
    # Check Qdrant
    try:
        collections = qdrant_client.get_collections()
        qdrant_status = ServiceStatus(status="connected")
    except Exception as e:
        qdrant_status = ServiceStatus(status="error", error=str(e))
    
    # Check index
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        # Use global indexing status with more detailed states
        index_status = IndexStatus(
            status=indexing_status["status"],
            total_docs=indexing_status["total_docs"] or collection_info.points_count,
            error=indexing_status["error"]
        )
        if index_status.status == "waiting_for_embedder":
            index_status.error = "Waiting for embedder service to be ready"
    except Exception as e:
        index_status = IndexStatus(status="error", error=str(e))
    
    # Determine overall status
    overall_status = "healthy"
    if embedder_status.status != "ready" or qdrant_status.status != "connected":
        overall_status = "error"
    
    return SystemStatus(
        status=overall_status,
        embedder=embedder_status,
        qdrant=qdrant_status,
        index=index_status
    )

@app.post("/search", response_model=SearchResult)
async def search_code(search_query: SearchQuery):
    """
    Search for code snippets using vector similarity with filtering
    """
    try:
        # Get embedding for the query
        query_embedding = await get_embedding(f"query: {search_query.query}")
        
        # Prepare filter if allowed_repos specified
        search_filter = None
        if search_query.allowed_repos:
            search_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="repo.name",
                        match=models.MatchAny(any=search_query.allowed_repos)
                    )
                ]
            )
        
        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=search_query.top_n,
            query_filter=search_filter
        )
        
        # Format results
        snippets = []
        for result in search_results:
            payload = result.payload
            snippet = CodeSnippet(
                id=str(result.id),
                code=payload["code"],
                file_path=payload["file_path"],
                line_from=payload["line_from"],
                line_to=payload["line_to"],
                repo=Repository(**payload["repo"])
            )
            snippets.append(snippet)
        
        return SearchResult(snippets=snippets)
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/repositories")
async def get_repositories():
    """
    Get list of indexed repositories
    """
    config_path = os.getenv("CONFIG_PATH", "repos_config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load repositories config: {e}")
        raise HTTPException(status_code=500, detail="Failed to load repositories configuration")

# CLI tool for indexing repos (this would be a separate script)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}