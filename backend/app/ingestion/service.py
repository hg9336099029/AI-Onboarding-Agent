"""
Ingestion Service - Orchestrates repository ingestion

Coordinates repo loading, parsing, chunking, embedding, and storage.
"""

from typing import Dict, Any, List
import logging
import time

from .repo_loader import RepositoryLoader
from .py_ast import PythonASTParser
from .chunker import CodeChunker

logger = logging.getLogger(__name__)


class IngestionService:
    """Orchestrate code repository ingestion"""
    
    def __init__(
        self,
        repo_loader: RepositoryLoader,
        embedder,
        vector_store,
        storage_service,
        clone_path: str = "./data/repositories"
    ):
        """
        Initialize ingestion service
        
        Args:
            repo_loader: Repository loader instance
            embedder: Code embedder instance
            vector_store: Vector store instance
            storage_service: Storage service instance
            clone_path: Path for cloning repositories
        """
        self.repo_loader = repo_loader
        self.embedder = embedder
        self.vector_store = vector_store
        self.storage = storage_service
        
        # Initialize parsers
        self.py_parser = PythonASTParser()
        # TODO: Add JS parser when implemented
        
        # Initialize chunker
        self.chunker = CodeChunker()
        
        logger.info("Ingestion service initialized")
    
    async def ingest(
        self,
        repo_url: str,
        repo_id: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Ingest a repository
        
        Args:
            repo_url: Git repository URL
            repo_id: Repository identifier
            branch: Branch to process
        
        Returns:
            Ingestion statistics
        """
        start_time = time.time()
        logger.info(f"Starting ingestion for {repo_url}")
        
        try:
            # 1. Clone repository
            repo_path = await self.repo_loader.clone_or_update(repo_url, repo_id, branch)
            
            # 2. Get all supported files
            py_files = self.repo_loader.list_files(repo_id, extensions=['.py'])
            # TODO: Add .js, .ts files when JS parser is ready
            
            all_chunks = []
            all_calls = []
            all_files = []
            
            # 3. Process each file
            for file_path in py_files:
                content = self.repo_loader.read_file(repo_id, file_path)
                if not content:
                    continue
                
                # Parse file
                parsed = self.py_parser.parse_file(file_path, content)
                if 'error' in parsed:
                    logger.warning(f"Skipping {file_path} due to parse error")
                    continue
                
                # Create chunks
                chunks = self.chunker.chunk_file(parsed, content, repo_id)
                all_chunks.extend(chunks)
                
                # Extract call graph
                for call in parsed.get('calls', []):
                    all_calls.append({
                        'repo_id': repo_id,
                        'caller_identifier': call['caller'],
                        'caller_file': file_path,
                        'callee_identifier': call['callee'],
                        'call_type': 'direct'
                    })
                
                # Store file metadata
                all_files.append({
                    'repo_id': repo_id,
                    'file_path': file_path,
                    'language': 'python',
                    'content': content,
                    'size_bytes': len(content.encode('utf-8')),
                    'line_count': len(content.split('\n')),
                    'imports': parsed.get('imports', [])
                })
            
            # 4. Generate embeddings
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
            embeddings = await self.embedder.embed_code_chunks(all_chunks)
            
            # 5. Store in vector database
            logger.info("Storing vectors...")
            vector_metadata = [
                {
                    'chunk_id': chunk['id'],
                    'repo_id': chunk['repo_id'],
                    'file_path': chunk['file_path'],
                    'identifier': chunk['identifier']
                }
                for chunk in all_chunks
            ]
            self.vector_store.add(embeddings, vector_metadata)
            
            # 6. Store in relational database
            logger.info("Storing metadata...")
            await self.storage.save_code_chunks(all_chunks)
            await self.storage.save_call_graph(all_calls)
            await self.storage.save_files(all_files)
            
            # 7. Save vector store
            self.vector_store.save()
            
            elapsed = time.time() - start_time
            
            result = {
                'files_processed': len(all_files),
                'functions_extracted': len(all_chunks),
                'call_relationships': len(all_calls),
                'elapsed_time': elapsed
            }
            
            logger.info(f"Ingestion complete in {elapsed:.2f}s: {result}")
            return result
        
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            raise
