import logging
import httpx
import json
from typing import List, Optional
from fastapi import HTTPException
from qdrant_client import QdrantClient, models
import asyncio

from ..settings import settings
from .github_service import GitHubService
from .code_processing_service import CodeProcessingService

# Setup logging
logger = logging.getLogger(__name__)

class QuadrantService:
    def __init__(self):
        """Initialize QuadrantService with Qdrant client and required services"""
        self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        self._collection_initialized = False
        self.github_service = GitHubService()
        self.code_processing = CodeProcessingService()
        self.indexing_status = {"status": "not_started", "total_docs": 0, "error": None}
        
    async def check_embedder_available(self) -> bool:
        """Check if embedder service is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.EMBEDDER_URL,
                    json={
                        "input": "test",
                        "model": settings.EMBEDDER_MODEL
                    },
                    timeout=5.0
                )
                return response.status_code == 200 and "data" in response.json()
        except Exception:
            return False

    async def wait_for_embedder(self):
        """Wait for embedder service to become available"""
        while True:
            if await self.check_embedder_available():
                logger.info("Embedder service is available")
                break
            logger.info("Waiting for embedder service...")
            await asyncio.sleep(5)

    async def ensure_collection_exists(self):
        """Initialize collection if it doesn't exist, waiting for embedder first"""
        if self._collection_initialized:
            return

        # Wait for embedder before creating collection
        await self.wait_for_embedder()

        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if settings.COLLECTION_NAME not in collection_names:
                logger.info(f"Creating collection {settings.COLLECTION_NAME}")
                self.client.create_collection(
                    collection_name=settings.COLLECTION_NAME,
                    vectors_config=models.VectorParams(
                        size=1536,  # Update this to match the embedder's output size
                        distance=models.Distance.COSINE
                    )
                )
                # Start indexing process only when collection is newly created
                await self.process_repositories()
            self._collection_initialized = True
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    async def process_repositories(self):
        """Process and index repositories from config"""
        try:
            self.indexing_status["status"] = "indexing"
            
            # Load config
            with open(settings.CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            # Process each repository
            for repo_config in config['repos']:
                if repo_config['type'] == 'github':
                    for repo_name in repo_config['repos']:
                        try:
                            # Clone repository
                            repo_path = await self.github_service.clone_repository(repo_name)
                            
                            # Extract code snippets
                            logger.info(f"Extracting code from {repo_name}")
                            snippets = self.code_processing.extract_code_snippets(repo_path, repo_name)
                            logger.info(f"Found {len(snippets)} code snippets in {repo_name}")
                            
                            # Index snippets in batches
                            for batch in self.code_processing.process_batch(snippets):
                                points = []
                                for snippet in batch:
                                    try:
                                        # Get embedding
                                        embedding = await self.get_embedding(snippet["code"])
                                        
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
                                    self.upsert_points(points)
                                    self.indexing_status["total_docs"] += len(points)
                                    
                        except Exception as e:
                            logger.error(f"Error processing repository {repo_name}: {e}")
            
            self.indexing_status["status"] = "completed"
            
        except Exception as e:
            logger.error(f"Indexing error: {e}")
            self.indexing_status["status"] = "error"
            self.indexing_status["error"] = str(e)

    async def get_embedding(self, text: str) -> List[float]:
        """Get embeddings from embedder service"""
        instruction = "Instruct: Given Code or Text, retrieval relevant content\nQuery: "
        prompt = f"{instruction}{text}" if "query" in text else text
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.EMBEDDER_URL,
                    json={
                        "input": prompt,
                        "model": settings.EMBEDDER_MODEL
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

    def search(self, query_vector: List[float], limit: int, search_filter: Optional[models.Filter] = None) -> List[models.ScoredPoint]:
        """Search for similar vectors in the collection"""
        return self.client.search(
            collection_name=settings.COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            query_filter=search_filter
        )

    def upsert_points(self, points: List[models.PointStruct], wait: bool = True):
        """Insert or update points in the collection"""
        return self.client.upsert(
            collection_name=settings.COLLECTION_NAME,
            points=points,
            wait=wait
        )

    def get_collection_info(self):
        """Get information about the collection"""
        return self.client.get_collection(settings.COLLECTION_NAME)

    def get_indexing_status(self):
        """Get current indexing status"""
        return self.indexing_status