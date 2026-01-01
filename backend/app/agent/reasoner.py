"""
Code Reasoner - Flow and impact analysis

Analyzes execution flows, traces dependencies, and provides
impact analysis for code changes.
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, deque


class CodeReasoner:
    """Analyzes code flow and dependencies"""
    
    def __init__(self, metadata_db, retriever):
        """
        Args:
            metadata_db: Database with code metadata
            retriever: CodeRetriever instance for fetching related code
        """
        self.metadata_db = metadata_db
        self.retriever = retriever
    
    def analyze_execution_flow(
        self, 
        entry_point: str, 
        repo_id: str,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Trace execution flow from an entry point
        
        Args:
            entry_point: Function/method name to start from
            repo_id: Repository identifier
            max_depth: Maximum call depth to trace
        
        Returns:
            Ordered list of function calls in execution order
        """
        flow = []
        visited = set()
        
        def trace_flow(identifier: str, depth: int, path: List[str]):
            if depth > max_depth or identifier in visited:
                return
            
            visited.add(identifier)
            chunk = self.retriever.retrieve_by_identifier(identifier, repo_id)
            
            if not chunk:
                return
            
            # Add to flow
            flow.append({
                'step': len(flow) + 1,
                'function_name': identifier,
                'file_path': chunk.get('file_path'),
                'start_line': chunk.get('start_line'),
                'depth': depth,
                'path': path + [identifier],
                'description': self._generate_step_description(chunk)
            })
            
            # Recursively trace callees
            for callee in chunk.get('callees', []):
                trace_flow(callee, depth + 1, path + [identifier])
        
        trace_flow(entry_point, 0, [])
        return flow
    
    def find_dependencies(
        self, 
        identifier: str, 
        repo_id: str,
        include_indirect: bool = True
    ) -> Dict[str, List[str]]:
        """
        Find all dependencies for a function/class
        
        Args:
            identifier: Function or class name
            repo_id: Repository identifier
            include_indirect: Include transitive dependencies
        
        Returns:
            Dictionary with direct and indirect dependencies
        """
        chunk = self.retriever.retrieve_by_identifier(identifier, repo_id)
        if not chunk:
            return {'direct': [], 'indirect': []}
        
        direct_deps = chunk.get('dependencies', [])
        indirect_deps = []
        
        if include_indirect:
            # Find dependencies of dependencies
            for dep in direct_deps:
                dep_chunk = self.retriever.retrieve_by_identifier(dep, repo_id)
                if dep_chunk:
                    indirect_deps.extend(dep_chunk.get('dependencies', []))
            
            # Remove duplicates and direct deps from indirect
            indirect_deps = list(set(indirect_deps) - set(direct_deps) - {identifier})
        
        return {
            'direct': direct_deps,
            'indirect': indirect_deps
        }
    
    def analyze_impact(
        self, 
        identifier: str, 
        repo_id: str
    ) -> Dict[str, Any]:
        """
        Analyze the impact of modifying a function/class
        
        Args:
            identifier: Function or class name
            repo_id: Repository identifier
        
        Returns:
            Impact analysis with affected code
        """
        chunk = self.retriever.retrieve_by_identifier(identifier, repo_id)
        if not chunk:
            return {'error': 'Identifier not found'}
        
        # Find all callers (who uses this code)
        direct_callers = chunk.get('callers', [])
        
        # Find indirect callers (who calls the callers)
        indirect_callers = set()
        for caller in direct_callers:
            caller_chunk = self.retriever.retrieve_by_identifier(caller, repo_id)
            if caller_chunk:
                indirect_callers.update(caller_chunk.get('callers', []))
        
        indirect_callers = list(indirect_callers - set(direct_callers) - {identifier})
        
        return {
            'modified_code': {
                'identifier': identifier,
                'file_path': chunk.get('file_path'),
                'lines': f"{chunk.get('start_line')}-{chunk.get('end_line')}"
            },
            'direct_impact': [
                {
                    'identifier': caller,
                    'file_path': self._get_file_path(caller, repo_id)
                }
                for caller in direct_callers
            ],
            'indirect_impact': [
                {
                    'identifier': caller,
                    'file_path': self._get_file_path(caller, repo_id)
                }
                for caller in indirect_callers
            ],
            'risk_level': self._assess_risk(len(direct_callers), len(indirect_callers))
        }
    
    def build_call_graph(
        self, 
        identifiers: List[str], 
        repo_id: str
    ) -> List[Tuple[str, str]]:
        """
        Build call graph for a set of functions
        
        Args:
            identifiers: List of function/class names
            repo_id: Repository identifier
        
        Returns:
            List of (caller, callee) tuples
        """
        edges = []
        
        for identifier in identifiers:
            chunk = self.retriever.retrieve_by_identifier(identifier, repo_id)
            if chunk:
                for callee in chunk.get('callees', []):
                    edges.append((identifier, callee))
        
        return edges
    
    def find_common_callers(
        self, 
        identifiers: List[str], 
        repo_id: str
    ) -> List[str]:
        """
        Find functions that call all given identifiers
        
        Args:
            identifiers: List of function names
            repo_id: Repository identifier
        
        Returns:
            List of common caller identifiers
        """
        if not identifiers:
            return []
        
        # Get callers for each identifier
        caller_sets = []
        for identifier in identifiers:
            chunk = self.retriever.retrieve_by_identifier(identifier, repo_id)
            if chunk:
                caller_sets.append(set(chunk.get('callers', [])))
        
        if not caller_sets:
            return []
        
        # Find intersection
        common = caller_sets[0]
        for caller_set in caller_sets[1:]:
            common &= caller_set
        
        return list(common)
    
    def _generate_step_description(self, chunk: Dict[str, Any]) -> str:
        """Generate human-readable description of a code chunk"""
        identifier = chunk.get('identifier', 'unknown')
        file_path = chunk.get('file_path', 'unknown')
        
        description = f"Function '{identifier}' in {file_path}"
        
        if chunk.get('dependencies'):
            description += f" (uses: {', '.join(chunk['dependencies'][:3])})"
        
        return description
    
    def _get_file_path(self, identifier: str, repo_id: str) -> str:
        """Get file path for an identifier"""
        chunk = self.retriever.retrieve_by_identifier(identifier, repo_id)
        return chunk.get('file_path', 'unknown') if chunk else 'unknown'
    
    def _assess_risk(self, direct_count: int, indirect_count: int) -> str:
        """Assess risk level based on impact"""
        total = direct_count + indirect_count
        
        if total == 0:
            return 'low'
        elif total < 5:
            return 'medium'
        else:
            return 'high'
