"""
Code Chunker - Create semantic chunks from parsed code

Converts AST-parsed code into embeddable chunks with metadata.
"""

from typing import List, Dict, Any
import uuid
import hashlib


class CodeChunker:
    """Create semantic code chunks for embedding"""
    
    def chunk_file(
        self, 
        file_data: Dict[str, Any],
        file_content: str,
        repo_id: str
    ) -> List[Dict[str, Any]]:
        """
        Create chunks from parsed file
        
        Args:
            file_data: Parsed file data from AST parser
            file_content: Full file content
            repo_id: Repository identifier
        
        Returns:
            List of code chunks
        """
        chunks = []
        file_path = file_data['file_path']
        language = file_data.get('language', 'unknown')
        
        # Chunk functions
        for func in file_data.get('functions', []):
            chunk = self._create_function_chunk(
                func, 
                file_path,
                file_content,
                repo_id,
                language
            )
            chunks.append(chunk)
        
        # Chunk classes
        for cls in file_data.get('classes', []):
            chunk = self._create_class_chunk(
                cls,
                file_path,
                file_content,
                repo_id,
                language
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_function_chunk(
        self,
        func: Dict[str, Any],
        file_path: str,
        file_content: str,
        repo_id: str,
        language: str
    ) -> Dict[str, Any]:
        """Create chunk for a function"""
        start_line = func.get('start_line', 0)
        end_line = func.get('end_line', 0)
        
        # Extract code lines
        code = self._extract_lines(file_content, start_line, end_line)
        
        # Generate unique chunk ID
        chunk_id = self._generate_chunk_id(repo_id, file_path, func['name'])
        
        return {
            'id': chunk_id,
            'repo_id': repo_id,
            'file_path': file_path,
            'identifier': func.get('name'),
            'chunk_type': func.get('type', 'function'),
            'language': language,
            'code': code,
            'docstring': func.get('docstring'),
            'start_line': start_line,
            'end_line': end_line,
            'dependencies': func.get('dependencies', []),
            'params': func.get('params'),
            'returns': func.get('returns')
        }
    
    def _create_class_chunk(
        self,
        cls: Dict[str, Any],
        file_path: str,
        file_content: str,
        repo_id: str,
        language: str
    ) -> Dict[str, Any]:
        """Create chunk for a class"""
        start_line = cls.get('start_line', 0)
        end_line = cls.get('end_line', 0)
        
        code = self._extract_lines(file_content, start_line, end_line)
        chunk_id = self._generate_chunk_id(repo_id, file_path, cls['name'])
        
        return {
            'id': chunk_id,
            'repo_id': repo_id,
            'file_path': file_path,
            'identifier': cls.get('name'),
            'chunk_type': 'class',
            'language': language,
            'code': code,
            'docstring': cls.get('docstring'),
            'start_line': start_line,
            'end_line': end_line,
            'dependencies': cls.get('bases', []),
            'params': None,
            'returns': None
        }
    
    def _extract_lines(self, content: str, start: int, end: int) -> str:
        """Extract lines from content"""
        if not content or start == 0:
            return ''
        
        lines = content.split('\n')
        # Convert to 0-indexed
        start_idx = max(0, start - 1)
        end_idx = min(len(lines), end)
        
        return '\n'.join(lines[start_idx:end_idx])
    
    def _generate_chunk_id(self, repo_id: str, file_path: str, identifier: str) -> str:
        """Generate unique chunk ID"""
        # Use hash for consistent IDs
        unique_str = f"{repo_id}:{file_path}:{identifier}"
        hash_obj = hashlib.md5(unique_str.encode())
        return hash_obj.hexdigest()
