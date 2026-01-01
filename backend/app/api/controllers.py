"""
API Controllers - Business logic for handling requests

Controllers orchestrate the interaction between API routes and
the underlying services (agent, ingestion, storage).
"""

from typing import Dict, Any
import time
import uuid
from datetime import datetime

from ..models.schemas import (
    RepositoryIngestRequest,
    RepositoryIngestResponse,
    QueryRequest,
    QueryResponse,
    FileRequest,
    FileResponse,
    ImpactAnalysisRequest,
    ImpactAnalysisResponse,
    Citation,
    CodeSnippet,
    ExecutionStep,
    ImpactedCode
)


class RepositoryController:
    """Handles repository operations"""
    
    def __init__(self, ingestion_service, storage_service):
        """
        Args:
            ingestion_service: Service for repository ingestion
            storage_service: Service for data storage
        """
        self.ingestion_service = ingestion_service
        self.storage_service = storage_service
    
    async def ingest_repository(
        self, 
        request: RepositoryIngestRequest
    ) -> RepositoryIngestResponse:
        """
        Ingest a Git repository
        
        Args:
            request: Repository ingestion request
        
        Returns:
            Ingestion result with repo_id and stats
        """
        start_time = time.time()
        
        # Generate repo ID
        repo_id = self._generate_repo_id(request.repo_url)
        
        # Check if already ingested
        existing = await self.storage_service.get_repository(repo_id)
        if existing:
            return RepositoryIngestResponse(
                repo_id=repo_id,
                status="already_exists",
                message="Repository already ingested",
                files_processed=existing.get('files_processed', 0),
                functions_extracted=existing.get('functions_extracted', 0),
                ingestion_time=0.0
            )
        
        # Clone and process repository
        result = await self.ingestion_service.ingest(
            repo_url=request.repo_url,
            repo_id=repo_id,
            branch=request.branch
        )
        
        # Save metadata
        await self.storage_service.save_repository({
            'id': repo_id,
            'url': request.repo_url,
            'branch': request.branch,
            'files_processed': result['files_processed'],
            'functions_extracted': result['functions_extracted']
        })
        
        ingestion_time = time.time() - start_time
        
        return RepositoryIngestResponse(
            repo_id=repo_id,
            status="success",
            message=f"Successfully ingested {result['files_processed']} files",
            files_processed=result['files_processed'],
            functions_extracted=result['functions_extracted'],
            ingestion_time=ingestion_time
        )
    
    def _generate_repo_id(self, repo_url: str) -> str:
        """Generate unique repository ID from URL"""
        # Extract owner/repo from URL
        parts = repo_url.rstrip('/').split('/')
        if len(parts) >= 2:
            owner_repo = f"{parts[-2]}_{parts[-1]}"
            return owner_repo.replace('.git', '')
        return str(uuid.uuid4())


class QueryController:
    """Handles code querying operations"""
    
    def __init__(self, agent, storage_service):
        """
        Args:
            agent: CodebaseAgent instance
            storage_service: Service for data storage
        """
        self.agent = agent
        self.storage_service = storage_service
    
    async def query_codebase(
        self, 
        request: QueryRequest
    ) -> QueryResponse:
        """
        Answer a question about the codebase
        
        Args:
            request: Query request with question and repo_id
        
        Returns:
            Answer with citations and optional flow
        """
        # Verify repository exists
        repo = await self.storage_service.get_repository(request.repo_id)
        if not repo:
            raise ValueError(f"Repository {request.repo_id} not found")
        
        # Use agent to answer question
        result = await self.agent.answer_question(
            question=request.question,
            repo_id=request.repo_id,
            include_execution_flow=request.include_execution_flow
        )
        
        # Convert to response format
        citations = [
            Citation(**citation) 
            for citation in result.get('citations', [])
        ]
        
        code_snippet = None
        if result.get('code_snippet'):
            code_snippet = CodeSnippet(**result['code_snippet'])
        
        execution_flow = None
        if result.get('execution_flow'):
            execution_flow = [
                ExecutionStep(**step) 
                for step in result['execution_flow']
            ]
        
        return QueryResponse(
            answer=result['answer'],
            citations=citations,
            confidence=result.get('confidence', 'medium'),
            code_snippet=code_snippet,
            execution_flow=execution_flow
        )
    
    async def analyze_impact(
        self, 
        request: ImpactAnalysisRequest
    ) -> ImpactAnalysisResponse:
        """Analyze impact of code changes"""
        result = await self.agent.analyze_impact(
            identifier=request.identifier,
            repo_id=request.repo_id
        )
        
        if 'error' in result:
            raise ValueError(result['error'])
        
        return ImpactAnalysisResponse(
            modified_code=ImpactedCode(**result['modified_code']),
            direct_impact=[ImpactedCode(**item) for item in result['direct_impact']],
            indirect_impact=[ImpactedCode(**item) for item in result['indirect_impact']],
            risk_level=result['risk_level'],
            summary=result['summary']
        )


class FileController:
    """Handles file operations"""
    
    def __init__(self, storage_service):
        """
        Args:
            storage_service: Service for data storage
        """
        self.storage_service = storage_service
    
    async def get_file(
        self, 
        request: FileRequest
    ) -> FileResponse:
        """
        Get file content from repository
        
        Args:
            request: File request with path and repo_id
        
        Returns:
            File content and metadata
        """
        # Get file from storage
        file_data = await self.storage_service.get_file(
            repo_id=request.repo_id,
            file_path=request.file_path
        )
        
        if not file_data:
            raise ValueError(f"File {request.file_path} not found")
        
        content = file_data['content']
        
        # Apply line range if specified
        if request.start_line or request.end_line:
            lines = content.split('\n')
            start = (request.start_line or 1) - 1
            end = request.end_line or len(lines)
            content = '\n'.join(lines[start:end])
        
        return FileResponse(
            file_path=request.file_path,
            content=content,
            language=file_data.get('language', 'text'),
            total_lines=len(file_data['content'].split('\n')),
            repo_id=request.repo_id
        )
