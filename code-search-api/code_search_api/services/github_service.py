import os
import logging
from git import Repo
from code_search_api.settings import settings

# Setup logging
logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self):
        """Initialize GitHub service and ensure repos directory exists"""
        os.makedirs(settings.REPOS_DIR, exist_ok=True)
    
    async def clone_repository(self, repo_name: str) -> str:
        """
        Clone a GitHub repository if it doesn't exist

        Args:
            repo_name (str): GitHub repository name in format "owner/repo"

        Returns:
            str: Path to the cloned repository
        """
        repo_url = f"https://github.com/{repo_name}.git"
        repo_path = os.path.join(settings.REPOS_DIR, repo_name.replace("/", "_"))
        
        if os.path.exists(repo_path):
            logger.info(f"Repository {repo_name} already exists at {repo_path}")
            return repo_path
        
        logger.info(f"Cloning {repo_name} to {repo_path}")
        os.makedirs(os.path.dirname(repo_path), exist_ok=True)
        Repo.clone_from(repo_url, repo_path)
        return repo_path

    def get_repo_url(self, repo_name: str) -> str:
        """
        Get GitHub repository URL

        Args:
            repo_name (str): GitHub repository name in format "owner/repo"

        Returns:
            str: GitHub repository URL
        """
        return f"https://github.com/{repo_name}"