"""
FastAPI Routes - HTTP endpoints

Defines all API endpoints and handles HTTP request/response.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from ..models.schemas import (
    RepositoryIngestRequest,
    RepositoryIngestResponse,
    QueryRequest,
    QueryResponse,
    FileRequest,
    FileResponse,
    HealthResponse,
    ErrorResponse,
    ImpactAnalysisRequest,
    ImpactAnalysisResponse
)
from .controllers import RepositoryController, QueryController, FileController


# Create routers
router = APIRouter(prefix="/api/v1")


# Initialize controllers (will be dependency injected)
repo_controller: RepositoryController = None
query_controller: QueryController = None
file_controller: FileController = None


def init_routes(
    repository_controller: RepositoryController,
    query_ctrl: QueryController,
    file_ctrl: FileController
):
    """Initialize route handlers with controllers"""
    global repo_controller, query_controller, file_controller
    repo_controller = repository_controller
    query_controller = query_ctrl
    file_controller = file_ctrl


# Health check endpoint
@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the API is running"
)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


# Repository endpoints
@router.post(
    "/repository/ingest",
    response_model=RepositoryIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Repository",
    description="Ingest a Git repository for analysis"
)
async def ingest_repository(request: RepositoryIngestRequest):
    """
    Ingest a Git repository
    
    - **repo_url**: URL of the Git repository (GitHub, GitLab, etc.)
    - **branch**: Branch to analyze (default: main)
    
    Returns repository ID and ingestion statistics.
    """
    try:
        result = await repo_controller.ingest_repository(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Query endpoints
@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query Codebase",
    description="Ask a question about the codebase"
)
async def query_codebase(request: QueryRequest):
    """
    Ask a question about the codebase
    
    - **question**: Natural language question about the code
    - **repo_id**: Repository identifier from ingestion
    - **include_execution_flow**: Whether to analyze execution flow (optional)
    
    Returns answer with citations, code snippets, and optional execution flow.
    """
    try:
        result = await query_controller.query_codebase(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/impact-analysis",
    response_model=ImpactAnalysisResponse,
    summary="Analyze Impact",
    description="Analyze the impact of modifying a function or class"
)
async def analyze_impact(request: ImpactAnalysisRequest):
    """
    Analyze impact of code changes
    
    - **identifier**: Function or class name
    - **repo_id**: Repository identifier
    
    Returns impact analysis with affected code and risk level.
    """
    try:
        result = await query_controller.analyze_impact(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# File endpoints
@router.get(
    "/file",
    response_model=FileResponse,
    summary="Get File Content",
    description="Retrieve content of a specific file"
)
async def get_file(
    file_path: str,
    repo_id: str,
    start_line: int = None,
    end_line: int = None
):
    """
    Get file content
    
    - **file_path**: Path to file in repository
    - **repo_id**: Repository identifier
    - **start_line**: Optional start line number
    - **end_line**: Optional end line number
    
    Returns file content and metadata.
    """
    try:
        request = FileRequest(
            file_path=file_path,
            repo_id=repo_id,
            start_line=start_line,
            end_line=end_line
        )
        result = await file_controller.get_file(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
