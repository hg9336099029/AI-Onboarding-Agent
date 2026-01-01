"""
Main AI Agent - RAG Orchestrator

Coordinates retrieval, reasoning, and LLM generation to answer
questions about codebases with citation-backed responses.
"""

from typing import Dict, Any, List, Optional
from .retriever import CodeRetriever
from .reasoner import CodeReasoner
from .prompts import create_qa_prompt, create_flow_prompt, SYSTEM_PROMPT


class CodebaseAgent:
    """Main orchestrator for code Q&A using RAG"""
    
    def __init__(
        self, 
        llm,
        vector_store,
        metadata_db,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            llm: Language model instance (e.g., OpenAI, Anthropic)
            vector_store: FAISS vector store
            metadata_db: Database with code metadata
            config: Optional configuration parameters
        """
        self.llm = llm
        self.retriever = CodeRetriever(vector_store, metadata_db)
        self.reasoner = CodeReasoner(metadata_db, self.retriever)
        self.metadata_db = metadata_db
        
        # Configuration
        self.config = config or {}
        self.include_flow = self.config.get('include_flow', True)
        self.max_flow_depth = self.config.get('max_flow_depth', 5)
    
    async def answer_question(
        self, 
        question: str, 
        repo_id: str,
        include_execution_flow: bool = None
    ) -> Dict[str, Any]:
        """
        Answer a question about the codebase
        
        Args:
            question: User's natural language question
            repo_id: Repository identifier
            include_execution_flow: Whether to analyze execution flow
        
        Returns:
            Dictionary with answer, citations, and optional flow
        """
        # 1. Retrieve relevant code chunks
        retrieved_chunks = self.retriever.retrieve(question, repo_id)
        
        if not retrieved_chunks:
            return {
                'answer': "I couldn't find any relevant code for your question. Please try rephrasing or asking about a different aspect of the codebase.",
                'citations': [],
                'confidence': 'low'
            }
        
        # 2. Detect if user is asking about execution flow
        include_flow = include_execution_flow if include_execution_flow is not None else self.include_flow
        needs_flow = self._detect_flow_question(question) and include_flow
        
        # 3. Generate response based on question type
        if needs_flow:
            return await self._answer_with_flow(question, retrieved_chunks, repo_id)
        else:
            return await self._answer_simple(question, retrieved_chunks)
    
    async def _answer_simple(
        self, 
        question: str, 
        code_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate answer for non-flow questions"""
        # Create prompt with retrieved code
        prompt = create_qa_prompt(question, code_chunks)
        
        # Generate response using LLM
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.1,  # Low temperature for factual responses
            max_tokens=1000
        )
        
        # Extract citations
        citations = self._extract_citations(code_chunks)
        
        return {
            'answer': response.strip(),
            'citations': citations,
            'confidence': self._assess_confidence(code_chunks),
            'code_snippet': self._select_best_snippet(code_chunks) if code_chunks else None
        }
    
    async def _answer_with_flow(
        self, 
        question: str, 
        code_chunks: List[Dict[str, Any]],
        repo_id: str
    ) -> Dict[str, Any]:
        """Generate answer with execution flow analysis"""
        # Find entry point (function mentioned in question or top retrieved)
        entry_point = self._identify_entry_point(question, code_chunks)
        
        if not entry_point:
            return await self._answer_simple(question, code_chunks)
        
        # Analyze execution flow
        execution_flow = self.reasoner.analyze_execution_flow(
            entry_point, 
            repo_id,
            max_depth=self.max_flow_depth
        )
        
        # Build call graph for visualization
        identifiers = [step['function_name'] for step in execution_flow]
        call_graph = self.reasoner.build_call_graph(identifiers, repo_id)
        
        # Create flow-aware prompt
        prompt = create_flow_prompt(question, code_chunks, call_graph)
        
        # Generate response
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=1500
        )
        
        return {
            'answer': response.strip(),
            'citations': self._extract_citations(code_chunks),
            'execution_flow': execution_flow,
            'confidence': self._assess_confidence(code_chunks),
            'code_snippet': self._select_best_snippet(code_chunks)
        }
    
    async def analyze_impact(
        self, 
        identifier: str, 
        repo_id: str
    ) -> Dict[str, Any]:
        """
        Analyze impact of modifying a function/class
        
        Args:
            identifier: Function or class name
            repo_id: Repository identifier
        
        Returns:
            Impact analysis
        """
        impact = self.reasoner.analyze_impact(identifier, repo_id)
        
        if 'error' in impact:
            return impact
        
        # Generate explanation
        summary = f"Modifying '{identifier}' would affect:\n"
        summary += f"- {len(impact['direct_impact'])} direct callers\n"
        summary += f"- {len(impact['indirect_impact'])} indirect callers\n"
        summary += f"Risk Level: {impact['risk_level'].upper()}"
        
        impact['summary'] = summary
        return impact
    
    def _detect_flow_question(self, question: str) -> bool:
        """Detect if question is asking about execution flow"""
        flow_keywords = [
            'flow', 'execution', 'process', 'workflow', 'step',
            'sequence', 'order', 'how does', 'what happens when'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in flow_keywords)
    
    def _identify_entry_point(
        self, 
        question: str, 
        code_chunks: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Identify the entry point function from question or chunks"""
        # Try to extract function name from question
        question_lower = question.lower()
        
        for chunk in code_chunks:
            identifier = chunk.get('identifier', '')
            if identifier and identifier.lower() in question_lower:
                return identifier
        
        # Fall back to highest scoring chunk
        if code_chunks:
            return code_chunks[0].get('identifier')
        
        return None
    
    def _extract_citations(
        self, 
        code_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract citation information from code chunks"""
        citations = []
        
        for chunk in code_chunks:
            citations.append({
                'file_path': chunk.get('file_path'),
                'start_line': chunk.get('start_line'),
                'end_line': chunk.get('end_line'),
                'function_name': chunk.get('identifier'),
                'score': chunk.get('score', 0.0)
            })
        
        return citations
    
    def _select_best_snippet(
        self, 
        code_chunks: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Select the best code snippet to show"""
        if not code_chunks:
            return None
        
        best_chunk = code_chunks[0]  # Already sorted by score
        
        return {
            'file_path': best_chunk.get('file_path'),
            'code': best_chunk.get('code'),
            'language': best_chunk.get('language'),
            'highlighted_lines': list(range(
                best_chunk.get('start_line', 0),
                best_chunk.get('end_line', 0) + 1
            ))
        }
    
    def _assess_confidence(
        self, 
        code_chunks: List[Dict[str, Any]]
    ) -> str:
        """Assess confidence in the answer based on retrieval quality"""
        if not code_chunks:
            return 'low'
        
        top_score = code_chunks[0].get('score', 0)
        
        if top_score > 0.85:
            return 'high'
        elif top_score > 0.70:
            return 'medium'
        else:
            return 'low'
