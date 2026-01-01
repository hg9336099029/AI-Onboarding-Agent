"""
Repository Pattern for Data Access

Provides clean interface for database operations.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from .models import Repository, CodeChunk, CallGraph, FileMetadata


class RepositoryDAO:
    """Data access object for repositories"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, repo_data: Dict[str, Any]) -> Repository:
        """Create a new repository"""
        repo = Repository(**repo_data)
        self.session.add(repo)
        self.session.flush()
        return repo
    
    def get(self, repo_id: str) -> Optional[Repository]:
        """Get repository by ID"""
        return self.session.query(Repository).filter_by(id=repo_id).first()
    
    def update(self, repo_id: str, updates: Dict[str, Any]) -> Optional[Repository]:
        """Update repository"""
        repo = self.get(repo_id)
        if repo:
            for key, value in updates.items():
                setattr(repo, key, value)
            self.session.flush()
        return repo
    
    def delete(self, repo_id: str) -> bool:
        """Delete repository"""
        repo = self.get(repo_id)
        if repo:
            self.session.delete(repo)
            return True
        return False


class CodeChunkDAO:
    """Data access object for code chunks"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_batch(self, chunks: List[Dict[str, Any]]) -> List[CodeChunk]:
        """Create multiple code chunks"""
        chunk_objects = [CodeChunk(**chunk) for chunk in chunks]
        self.session.bulk_save_objects(chunk_objects)
        self.session.flush()
        return chunk_objects
    
    def get(self, chunk_id: str) -> Optional[CodeChunk]:
        """Get chunk by ID"""
        return self.session.query(CodeChunk).filter_by(id=chunk_id).first()
    
    def get_by_identifier(self, repo_id: str, identifier: str) -> Optional[CodeChunk]:
        """Get chunk by function/class name"""
        return self.session.query(CodeChunk).filter_by(
            repo_id=repo_id,
            identifier=identifier
        ).first()
    
    def get_by_repo(self, repo_id: str, limit: int = 1000) -> List[CodeChunk]:
        """Get all chunks for a repository"""
        return self.session.query(CodeChunk).filter_by(repo_id=repo_id).limit(limit).all()
    
    def delete_by_repo(self, repo_id: str) -> int:
        """Delete all chunks for a repository"""
        count = self.session.query(CodeChunk).filter_by(repo_id=repo_id).delete()
        return count


class CallGraphDAO:
    """Data access object for call graph"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_batch(self, calls: List[Dict[str, Any]]) -> List[CallGraph]:
        """Create multiple call relationships"""
        call_objects = [CallGraph(**call) for call in calls]
        self.session.bulk_save_objects(call_objects)
        self.session.flush()
        return call_objects
    
    def get_callers(self, repo_id: str, identifier: str) -> List[str]:
        """Get all functions that call this identifier"""
        results = self.session.query(CallGraph.caller_identifier).filter_by(
            repo_id=repo_id,
            callee_identifier=identifier
        ).distinct().all()
        return [r[0] for r in results]
    
    def get_callees(self, repo_id: str, identifier: str) -> List[str]:
        """Get all functions called by this identifier"""
        results = self.session.query(CallGraph.callee_identifier).filter_by(
            repo_id=repo_id,
            caller_identifier=identifier
        ).distinct().all()
        return [r[0] for r in results]
    
    def get_edges(self, repo_id: str) -> List[tuple]:
        """Get all call graph edges"""
        results = self.session.query(
            CallGraph.caller_identifier,
            CallGraph.callee_identifier
        ).filter_by(repo_id=repo_id).all()
        return results


class FileMetadataDAO:
    """Data access object for file metadata"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_batch(self, files: List[Dict[str, Any]]) -> List[FileMetadata]:
        """Create multiple file records"""
        file_objects = [FileMetadata(**file) for file in files]
        self.session.bulk_save_objects(file_objects)
        self.session.flush()
        return file_objects
    
    def get(self, repo_id: str, file_path: str) -> Optional[FileMetadata]:
        """Get file by path"""
        return self.session.query(FileMetadata).filter_by(
            repo_id=repo_id,
            file_path=file_path
        ).first()
    
    def get_all_by_repo(self, repo_id: str) -> List[FileMetadata]:
        """Get all files for a repository"""
        return self.session.query(FileMetadata).filter_by(repo_id=repo_id).all()


class StorageService:
    """High-level storage service"""
    
    def __init__(self, database):
        """
        Initialize storage service
        
        Args:
            database: Database instance
        """
        self.database = database
    
    async def save_repository(self, repo_data: Dict[str, Any]) -> str:
        """Save repository metadata"""
        with self.database.get_session() as session:
            dao = RepositoryDAO(session)
            repo = dao.create(repo_data)
            return repo.id
    
    async def get_repository(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get repository metadata"""
        with self.database.get_session() as session:
            dao = RepositoryDAO(session)
            repo = dao.get(repo_id)
            if repo:
                return {
                    'repo_id': repo.id,
                    'repo_url': repo.url,
                    'branch': repo.branch,
                    'files_processed': repo.files_processed,
                    'functions_extracted': repo.functions_extracted,
                    'ingested_at': repo.ingested_at.isoformat() if repo.ingested_at else None
                }
            return None
    
    async def save_code_chunks(self, chunks: List[Dict[str, Any]]):
        """Save code chunks"""
        import json
        
        # Serialize JSON fields to text for SQLite
        serialized_chunks = []
        for chunk in chunks:
            chunk_copy = chunk.copy()
            if 'dependencies' in chunk_copy and isinstance(chunk_copy['dependencies'], list):
                chunk_copy['dependencies'] = json.dumps(chunk_copy['dependencies'])
            if 'params' in chunk_copy and chunk_copy['params'] is not None:
                chunk_copy['params'] = json.dumps(chunk_copy['params'])
            if 'returns' in chunk_copy and chunk_copy['returns'] is not None:
                chunk_copy['returns'] = json.dumps(chunk_copy['returns'])
            serialized_chunks.append(chunk_copy)
        
        with self.database.get_session() as session:
            dao = CodeChunkDAO(session)
            dao.create_batch(serialized_chunks)
    
    async def get_chunk(self, chunk_id: str, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get code chunk"""
        with self.database.get_session() as session:
            dao = CodeChunkDAO(session)
            chunk = dao.get(chunk_id)
            if chunk:
                return self._chunk_to_dict(chunk)
            return None
    
    async def get_chunk_metadata(self, chunk_id: str, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get chunk with call graph metadata"""
        with self.database.get_session() as session:
            chunk_dao = CodeChunkDAO(session)
            call_dao = CallGraphDAO(session)
            
            chunk = chunk_dao.get(chunk_id)
            if not chunk:
                return None
            
            # Get callers and callees
            callers = call_dao.get_callers(repo_id, chunk.identifier or '')
            callees = call_dao.get_callees(repo_id, chunk.identifier or '')
            
            result = self._chunk_to_dict(chunk)
            result['callers'] = callers
            result['callees'] = callees
            return result
    
    async def save_call_graph(self, calls: List[Dict[str, Any]]):
        """Save call graph relationships"""
        with self.database.get_session() as session:
            dao = CallGraphDAO(session)
            dao.create_batch(calls)
    
    async def save_files(self, files: List[Dict[str, Any]]):
        """Save file metadata"""
        import json
        
        # Serialize JSON fields
        serialized_files = []
        for file in files:
            file_copy = file.copy()
            if 'imports' in file_copy and isinstance(file_copy['imports'], list):
                file_copy['imports'] = json.dumps(file_copy['imports'])
            if 'exports' in file_copy and isinstance(file_copy['exports'], list):
                file_copy['exports'] = json.dumps(file_copy['exports'])
            serialized_files.append(file_copy)
        
        with self.database.get_session() as session:
            dao = FileMetadataDAO(session)
            dao.create_batch(serialized_files)
    
    async def get_file(self, repo_id: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file content"""
        with self.database.get_session() as session:
            dao = FileMetadataDAO(session)
            file = dao.get(repo_id, file_path)
            if file:
                return {
                    'file_path': file.file_path,
                    'content': file.content,
                    'language': file.language,
                    'line_count': file.line_count
                }
            return None
    
    def _chunk_to_dict(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Convert chunk model to dictionary"""
        import json
        
        # Deserialize JSON fields stored as text
        dependencies = chunk.dependencies
        if isinstance(dependencies, str):
            try:
                dependencies = json.loads(dependencies) if dependencies else []
            except:
                dependencies = []
        
        params = chunk.params
        if isinstance(params, str):
            try:
                params = json.loads(params) if params else None
            except:
                params = None
        
        return {
            'chunk_id': chunk.id,
            'repo_id': chunk.repo_id,
            'file_path': chunk.file_path,
            'identifier': chunk.identifier,
            'language': chunk.language,
            'code': chunk.code,
            'start_line': chunk.start_line,
            'end_line': chunk.end_line,
            'dependencies': dependencies or [],
            'params': params
        }
