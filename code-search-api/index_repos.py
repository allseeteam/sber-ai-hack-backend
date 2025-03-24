import os
import json
import asyncio
import httpx
import uuid
import glob
from git import Repo
import logging
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_URL = "http://localhost:8000"
REPOS_DIR = "./repos"
CONFIG_FILE = "repos_config.json"

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
    
    # File extensions to consider
    code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.hpp', '.h', '.c', '.cs', '.go', '.rs', '.php', '.rb']
    
    for ext in code_extensions:
        files = glob.glob(f"{repo_path}/**/*{ext}", recursive=True)
        
        for file_path in files:
            rel_path = os.path.relpath(file_path, repo_path)
            
            # Skip files in common directories to avoid
            if any(d in rel_path.split(os.sep) for d in ['__pycache__', 'node_modules', '.git']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split into functions or methods (simplified approach)
                # For a production system, you'd want to use a proper parser
                lines = content.split('\n')
                
                # Simple chunking approach - divide into sections of 100 lines
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
                            "url": f"https://github.com/{repo_name}"
                        }
                    })
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
    
    return snippets

async def index_snippets(snippets: List[Dict[str, Any]]):
    """Send snippets to the API for indexing"""
    async with httpx.AsyncClient() as client:
        # Process in batches to avoid overwhelming the API
        batch_size = 50
        for i in range(0, len(snippets), batch_size):
            batch = snippets[i:i+batch_size]
            logger.info(f"Indexing batch {i//batch_size+1}/{(len(snippets)-1)//batch_size+1}")
            
            try:
                response = await client.post(
                    f"{API_URL}/index",
                    json=batch,
                    timeout=300.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to index batch: {response.text}")
                else:
                    logger.info(f"Successfully indexed {len(batch)} snippets")
            
            except Exception as e:
                logger.error(f"Error indexing batch: {e}")

async def main():
    # Create repos directory if it doesn't exist
    os.makedirs(REPOS_DIR, exist_ok=True)
    
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
                    
                    # Index snippets
                    await index_snippets(snippets)
                    
                except Exception as e:
                    logger.error(f"Error processing repository {repo_name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())