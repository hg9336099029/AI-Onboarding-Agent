from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import json

Base = declarative_base()


# Helper for JSON storage in SQLite
class JSONEncodedText(Text):
    """Store JSON as text for SQLite compatibility"""
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class Repository(Base):
    """Repository metadata"""
    __tablename__ = 'repositories'
    
    id = Column(String(255), primary_key=True)  # repo_id
    url = Column(String(512), nullable=False)
    branch = Column(String(100), default='main')
    files_processed = Column(Integer, default=0)
    functions_extracted = Column(Integer, default=0)
    ingested_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_repo_url', 'url'),
    )


class CodeChunk(Base):
    """Code chunks with metadata"""
    __tablename__ = 'code_chunks'
    
    id = Column(String(255), primary_key=True)  # chunk_id
    repo_id = Column(String(255), ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False)
    file_path = Column(String(512), nullable=False)
    identifier = Column(String(255))  # Function/class name
    chunk_type = Column(String(50))  # 'function', 'class', 'method'
    language = Column(String(50))  # 'python', 'javascript'
    
    code = Column(Text, nullable=False)
    docstring = Column(Text)
    
    start_line = Column(Integer)
    end_line = Column(Integer)
    
    dependencies = Column(Text)  # JSON stored as text
    params = Column(Text)  # JSON stored as text
    returns = Column(Text)  # JSON stored as text
    
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_chunk_repo', 'repo_id'),
        Index('idx_chunk_identifier', 'identifier'),
        Index('idx_chunk_file', 'file_path'),
    )


class CallGraph(Base):
    """Function call relationships"""
    __tablename__ = 'call_graph'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String(255), ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False)
    
    caller_chunk_id = Column(String(255), ForeignKey('code_chunks.id', ondelete='CASCADE'))
    caller_identifier = Column(String(255), nullable=False)
    caller_file = Column(String(512))
    
    callee_identifier = Column(String(255), nullable=False)
    callee_file = Column(String(512))
    
    call_type = Column(String(50))  # 'direct', 'imported', 'dynamic'
    
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_call_repo', 'repo_id'),
        Index('idx_call_caller', 'caller_identifier'),
        Index('idx_call_callee', 'callee_identifier'),
    )


class FileMetadata(Base):
    """File-level metadata"""
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String(255), ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False)
    file_path = Column(String(512), nullable=False)
    language = Column(String(50))
    
    content = Column(Text)  # Full file content
    size_bytes = Column(Integer)
    line_count = Column(Integer)
    
    imports = Column(Text)  # JSON stored as text
    exports = Column(Text)  # JSON stored as text
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_file_repo', 'repo_id'),
        Index('idx_file_path', 'file_path'),
    )
