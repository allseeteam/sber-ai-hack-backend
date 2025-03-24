from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import httpx
import json
import os
import uuid
from typing import List, Dict, Any, Optional
import asyncio
import logging
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
    limit: int = 10
    
class SearchResult(BaseModel):
    snippets: List[CodeSnippet]
    
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
                    size=768,  # Use the actual vector size from the model
                    distance=models.Distance.COSINE
                )
            )
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise

@app.on_event("startup")
async def startup():
    ensure_collection_exists()

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
                    "model": "Salesforce/SFR-Embedding-Code-2B_R"
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                logger.error(f"Embedding API error: {response.text}")
                raise HTTPException(status_code=500, detail="Embedding service error")
                
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

@app.post("/search", response_model=SearchResult)
async def search_code(search_query: SearchQuery):
    """
    Search for code snippets using vector similarity
    """
    try:
        # Get embedding for the query
        query_embedding = await get_embedding(f"query: {search_query.query}")
        
        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=search_query.limit
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