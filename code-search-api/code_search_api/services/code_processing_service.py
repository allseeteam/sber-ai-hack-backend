import os
import glob
import logging
import uuid
from typing import List, Dict, Any

# Setup logging
logger = logging.getLogger(__name__)

class CodeProcessingService:
    def __init__(self):
        """Initialize CodeProcessingService with supported file extensions"""
        self.code_extensions = [
            '.py', '.js', '.ts', '.java', '.cpp', 
            '.hpp', '.h', '.c', '.cs', '.go', 
            '.rs', '.php', '.rb'
        ]
        self.excluded_dirs = ['__pycache__', 'node_modules', '.git']

    def extract_code_snippets(self, repo_path: str, repo_name: str) -> List[Dict[str, Any]]:
        """
        Extract code snippets from a repository

        Args:
            repo_path (str): Path to the repository
            repo_name (str): Name of the repository

        Returns:
            List[Dict[str, Any]]: List of code snippets with metadata
        """
        snippets = []
        
        for ext in self.code_extensions:
            files = glob.glob(f"{repo_path}/**/*{ext}", recursive=True)
            
            for file_path in files:
                rel_path = os.path.relpath(file_path, repo_path)
                
                if any(d in rel_path.split(os.sep) for d in self.excluded_dirs):
                    continue
                    
                try:
                    snippets.extend(self._process_file(file_path, rel_path, repo_path, repo_name))
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
        
        return snippets

    def _process_file(self, file_path: str, rel_path: str, repo_path: str, repo_name: str) -> List[Dict[str, Any]]:
        """
        Process a single file and extract code snippets

        Args:
            file_path (str): Path to the file
            rel_path (str): Relative path in the repository
            repo_path (str): Path to the repository
            repo_name (str): Name of the repository

        Returns:
            List[Dict[str, Any]]: List of code snippets from the file
        """
        snippets = []
        chunk_size = 100  # Number of lines per chunk

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
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
            logger.error(f"Error reading file {file_path}: {e}")
            
        return snippets

    def process_batch(self, snippets: List[Dict[str, Any]], batch_size: int = 50) -> List[List[Dict[str, Any]]]:
        """
        Split snippets into batches for processing

        Args:
            snippets (List[Dict[str, Any]]): List of code snippets
            batch_size (int, optional): Size of each batch. Defaults to 50.

        Returns:
            List[List[Dict[str, Any]]]: List of batches of snippets
        """
        return [snippets[i:i + batch_size] for i in range(0, len(snippets), batch_size)]