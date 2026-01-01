"""
Repository Loader - Git clone and update

Handles cloning Git repositories and keeping them updated.
"""

from git import Repo, GitCommandError
import os
import shutil
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RepositoryLoader:
    """Clone and manage Git repositories"""
    
    def __init__(self, clone_path: str = "./data/repositories"):
        """
        Initialize repository loader
        
        Args:
            clone_path: Base directory for cloning repositories
        """
        self.clone_path = Path(clone_path)
        self.clone_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Repository loader initialized at {clone_path}")
    
    async def clone_or_update(
        self, 
        repo_url: str,
        repo_id: str,
        branch: str = "main"
    ) -> str:
        """
        Clone repository or update if already exists
        
        Args:
            repo_url: Git repository URL
            repo_id: Identifier for the repository
            branch: Branch to checkout
        
        Returns:
            Path to the cloned repository
        """
        repo_path = self.clone_path / repo_id
        
        try:
            if repo_path.exists():
                logger.info(f"Repository {repo_id} already exists, updating...")
                return await self._update_repository(repo_path, branch)
            else:
                logger.info(f"Cloning repository {repo_url}...")
                return await self._clone_repository(repo_url, repo_path, branch)
        
        except GitCommandError as e:
            logger.error(f"Git error: {e}")
            raise ValueError(f"Failed to clone/update repository: {e}")
    
    async def _clone_repository(
        self, 
        repo_url: str, 
        repo_path: Path,
        branch: str
    ) -> str:
        """Clone a repository"""
        try:
            repo = Repo.clone_from(
                repo_url,
                str(repo_path),
                branch=branch,
                depth=1  # Shallow clone for faster cloning
            )
            logger.info(f"Successfully cloned {repo_url} to {repo_path}")
            return str(repo_path)
        
        except Exception as e:
            # Cleanup on failure
            if repo_path.exists():
                shutil.rmtree(repo_path)
            raise
    
    async def _update_repository(
        self, 
        repo_path: Path,
        branch: str
    ) -> str:
        """Update an existing repository"""
        try:
            repo = Repo(str(repo_path))
            
            # Checkout the branch
            repo.git.checkout(branch)
            
            # Pull latest changes
            origin = repo.remotes.origin
            origin.pull()
            
            logger.info(f"Successfully updated repository at {repo_path}")
            return str(repo_path)
        
        except Exception as e:
            logger.warning(f"Failed to update repository: {e}")
            # If update fails, return the existing path
            return str(repo_path)
    
    def delete_repository(self, repo_id: str) -> bool:
        """
        Delete a cloned repository
        
        Args:
            repo_id: Repository identifier
        
        Returns:
            True if deleted, False if not found
        """
        repo_path = self.clone_path / repo_id
        
        if repo_path.exists():
            shutil.rmtree(repo_path)
            logger.info(f"Deleted repository {repo_id}")
            return True
        
        return False
    
    def get_repository_path(self, repo_id: str) -> Optional[str]:
        """Get path to cloned repository"""
        repo_path = self.clone_path / repo_id
        return str(repo_path) if repo_path.exists() else None
    
    def list_files(
        self, 
        repo_id: str,
        extensions: Optional[list] = None
    ) -> list:
        """
        List all files in repository
        
        Args:
            repo_id: Repository identifier
            extensions: File extensions to filter (e.g., ['.py', '.js'])
        
        Returns:
            List of file paths relative to repository root
        """
        repo_path = self.clone_path / repo_id
        
        if not repo_path.exists():
            return []
        
        files = []
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                # Skip hidden files and directories
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                
                # Filter by extension if specified
                if extensions and file_path.suffix not in extensions:
                    continue
                
                # Get relative path
                rel_path = file_path.relative_to(repo_path)
                files.append(str(rel_path))
        
        return files
    
    def read_file(self, repo_id: str, file_path: str) -> Optional[str]:
        """
        Read file content
        
        Args:
            repo_id: Repository identifier
            file_path: Relative path to file
        
        Returns:
            File content or None if not found
        """
        full_path = self.clone_path / repo_id / file_path
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
