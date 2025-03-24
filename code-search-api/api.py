from fastapi import FastAPI, HTTPException
from qdrant_client import models
import json
import logging
import asyncio
from typing import List

from .settings import settings
from .models import (
    SearchQuery, SearchResult, SystemStatus,
    ServiceStatus, IndexStatus, Repository,
    CodeSnippet
)
from .services import QuadrantService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Code Search API", description="Search code across repositories using vector embeddings")

# Initialize service
quadrant_service = QuadrantService()

@app.on_event("startup")
async def startup():
    # Initialize collection (will also start indexing if collection is new)
    await quadrant_service.ensure_collection_exists()

@app.get("/status", response_model=SystemStatus)
async def get_status():
    """Get system status including all components"""
    
    # Check embedder
    is_embedder_ready = await quadrant_service.check_embedder_available()
    embedder_status = ServiceStatus(
        status="ready" if is_embedder_ready else "starting",
        error=None if is_embedder_ready else "Waiting for embedder to initialize (this may take a few minutes)"
    )
    
    # Check Qdrant
    try:
        quadrant_service.client.get_collections()
        qdrant_status = ServiceStatus(status="connected")
    except Exception as e:
        qdrant_status = ServiceStatus(status="error", error=str(e))
    
    # Check index
    try:
        collection_info = quadrant_service.get_collection_info()
        indexing_status = quadrant_service.get_indexing_status()
        index_status = IndexStatus(
            status=indexing_status["status"],
            total_docs=indexing_status["total_docs"] or collection_info.points_count,
            error=indexing_status["error"]
        )
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
    """Search for code snippets using vector similarity with filtering"""
    try:
        # Get embedding for the query
        query_embedding = await quadrant_service.get_embedding(f"query: {search_query.query}")
        
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
        search_results = quadrant_service.search(
            query_vector=query_embedding,
            limit=search_query.top_n,
            search_filter=search_filter
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
    """Get list of indexed repositories"""
    try:
        with open(settings.CONFIG_FILE, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load repositories config: {e}")
        raise HTTPException(status_code=500, detail="Failed to load repositories configuration")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}