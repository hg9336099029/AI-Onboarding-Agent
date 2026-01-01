"""
Code Retriever - Semantic search and metadata-based retrieval

Combines vector similarity search with metadata filtering to find
the most relevant code segments for a given question.
"""

from typing import List, Dict, Any, Optional
import numpy as np


class CodeRetriever:
    """Retrieves relevant code chunks using semantic search and metadata"""
    
    def __init__(self, vector_store, metadata_db):
        """
        Args:
            vector_store: FAISS vector store instance
            metadata_db: Database with code metadata (functions, classes, etc.)
        """
        self.vector_store = vector_store
        self.metadata_db = metadata_db
        self.top_k = 10  # Number of chunks to retrieve
    
    def retrieve(
        self, 
        question: str, 
        repo_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant code chunks for a question
        
        Args:
            question: User's natural language question
            repo_id: Repository identifier
            filters: Optional metadata filters (e.g., file_type, function_name)
        
        Returns:
            List of code chunks with metadata and scores
        """
        # 1. Semantic search using vector similarity
        semantic_results = self._semantic_search(question, repo_id, filters)
        
        # 2. Enhance with metadata (dependencies, call graph)
        enhanced_results = self._enhance_with_metadata(semantic_results, repo_id)
        
        # 3. Re-rank based on relevance signals
        ranked_results = self._rerank_results(question, enhanced_results)
        
        return ranked_results[:self.top_k]
    
    def retrieve_by_identifier(
        self, 
        identifier: str, 
        repo_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve code by exact function/class name
        
        Args:
            identifier: Function or class name
            repo_id: Repository identifier
        
        Returns:
            Code chunk dictionary or None
        """
        result = self.metadata_db.query(
            f"SELECT * FROM code_chunks WHERE repo_id = ? AND identifier = ?",
            (repo_id, identifier)
        )
        
        if result:
            return self._format_chunk(result[0])
        return None
    
    def _semantic_search(
        self, 
        question: str, 
        repo_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        # Generate question embedding
        question_embedding = self.vector_store.embed_query(question)
        
        # Search in vector store
        results = self.vector_store.similarity_search_with_score(
            question_embedding,
            k=self.top_k * 2,  # Retrieve more for re-ranking
            filter={'repo_id': repo_id, **(filters or {})}
        )
        
        return [
            {
                'chunk_id': doc.metadata['chunk_id'],
                'score': score,
                'content': doc.page_content,
                'metadata': doc.metadata
            }
            for doc, score in results
        ]
    
    def _enhance_with_metadata(
        self, 
        chunks: List[Dict[str, Any]], 
        repo_id: str
    ) -> List[Dict[str, Any]]:
        """Add call graph and dependency information"""
        enhanced = []
        
        for chunk in chunks:
            chunk_id = chunk['chunk_id']
            
            # Get metadata from database
            metadata = self.metadata_db.get_chunk_metadata(chunk_id, repo_id)
            
            if metadata:
                chunk.update({
                    'file_path': metadata.get('file_path'),
                    'start_line': metadata.get('start_line'),
                    'end_line': metadata.get('end_line'),
                    'identifier': metadata.get('identifier'),
                    'language': metadata.get('language'),
                    'dependencies': metadata.get('dependencies', []),
                    'callers': metadata.get('callers', []),
                    'callees': metadata.get('callees', []),
                    'code': metadata.get('code', chunk['content'])
                })
                enhanced.append(chunk)
        
        return enhanced
    
    def _rerank_results(
        self, 
        question: str, 
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Re-rank results using multiple signals"""
        question_lower = question.lower()
        
        for chunk in chunks:
            # Boost score if identifier matches question keywords
            identifier = chunk.get('identifier', '').lower()
            if identifier and any(word in identifier for word in question_lower.split()):
                chunk['score'] *= 1.3
            
            # Boost if file path is relevant
            file_path = chunk.get('file_path', '').lower()
            if any(word in file_path for word in question_lower.split()):
                chunk['score'] *= 1.2
            
            # Boost if has dependencies (more context)
            if chunk.get('dependencies'):
                chunk['score'] *= 1.1
        
        # Sort by adjusted score
        return sorted(chunks, key=lambda x: x['score'], reverse=True)
    
    def _format_chunk(self, raw_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Format chunk for consistent structure"""
        return {
            'chunk_id': raw_chunk.get('id'),
            'file_path': raw_chunk.get('file_path'),
            'start_line': raw_chunk.get('start_line'),
            'end_line': raw_chunk.get('end_line'),
            'identifier': raw_chunk.get('identifier'),
            'language': raw_chunk.get('language'),
            'code': raw_chunk.get('code'),
            'dependencies': raw_chunk.get('dependencies', []),
            'callers': raw_chunk.get('callers', []),
            'callees': raw_chunk.get('callees', [])
        }
    
    def retrieve_related_code(
        self, 
        chunk_id: str, 
        repo_id: str,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Retrieve related code based on call graph
        
        Args:
            chunk_id: Starting chunk ID
            repo_id: Repository identifier
            depth: How many levels deep to traverse
        
        Returns:
            List of related code chunks
        """
        related = set()
        to_process = [(chunk_id, 0)]
        processed = set()
        
        while to_process:
            current_id, current_depth = to_process.pop(0)
            
            if current_id in processed or current_depth > depth:
                continue
            
            processed.add(current_id)
            chunk = self.metadata_db.get_chunk(current_id, repo_id)
            
            if chunk:
                related.add(current_id)
                
                # Add callees for next level
                if current_depth < depth:
                    for callee in chunk.get('callees', []):
                        callee_chunk = self.retrieve_by_identifier(callee, repo_id)
                        if callee_chunk:
                            to_process.append((callee_chunk['chunk_id'], current_depth + 1))
        
        return [
            self.metadata_db.get_chunk(cid, repo_id) 
            for cid in related
        ]
