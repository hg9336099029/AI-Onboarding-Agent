"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime


# Request Models
class RepositoryIngestRequest(BaseModel):
    """Request to ingest a repository"""
    repo_url: str = Field(..., description="Git repository URL (GitHub, GitLab, etc.)")
    branch: Optional[str] = Field("main", description="Branch to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "repo_url": "https://github.com/username/repository",
                "branch": "main"
            }
        }


class QueryRequest(BaseModel):
    """Request to query the codebase"""
    question: str = Field(..., min_length=1, description="Natural language question about the code")
    repo_id: str = Field(..., description="Repository identifier")
    include_execution_flow: Optional[bool] = Field(True, description="Include execution flow analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "How does user authentication work?",
                "repo_id": "repo_123",
                "include_execution_flow": True
            }
        }


class FileRequest(BaseModel):
    """Request to get file content"""
    file_path: str = Field(..., description="Path to file in repository")
    repo_id: str = Field(..., description="Repository identifier")
    start_line: Optional[int] = Field(None, description="Start line number")
    end_line: Optional[int] = Field(None, description="End line number")


# Response Models
class Citation(BaseModel):
    """Code citation with location info"""
    file_path: str
    start_line: int
    end_line: int
    function_name: Optional[str] = None
    score: Optional[float] = None


class CodeSnippet(BaseModel):
    """Code snippet with metadata"""
    file_path: str
    code: str
    language: str
    highlighted_lines: List[int] = []


class ExecutionStep(BaseModel):
    """Single step in execution flow"""
    step: int
    function_name: str
    file_path: str
    start_line: Optional[int] = None
    depth: int
    description: Optional[str] = None
    params: Optional[str] = None


class RepositoryIngestResponse(BaseModel):
    """Response after repository ingestion"""
    repo_id: str
    status: str
    message: str
    files_processed: int
    functions_extracted: int
    ingestion_time: float


class QueryResponse(BaseModel):
    """Response to codebase question"""
    answer: str
    citations: List[Citation]
    confidence: str = Field(..., description="Confidence level: low, medium, high")
    code_snippet: Optional[CodeSnippet] = None
    execution_flow: Optional[List[ExecutionStep]] = None


class FileResponse(BaseModel):
    """Response with file content"""
    file_path: str
    content: str
    language: str
    total_lines: int
    repo_id: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime


# Impact Analysis Models
class ImpactAnalysisRequest(BaseModel):
    """Request for impact analysis"""
    identifier: str = Field(..., description="Function or class name")
    repo_id: str


class ImpactedCode(BaseModel):
    """Code affected by changes"""
    identifier: str
    file_path: str


class ImpactAnalysisResponse(BaseModel):
    """Impact analysis result"""
    modified_code: ImpactedCode
    direct_impact: List[ImpactedCode]
    indirect_impact: List[ImpactedCode]
    risk_level: str
    summary: str
