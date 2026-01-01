"""
Unified Code Embedder - Supports both OpenAI and HuggingFace embeddings

Provides embeddings for semantic code search with options for:
- OpenAI (paid, high quality)
- HuggingFace (free, local)
"""

from typing import List, Dict, Any, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class CodeEmbedder:
    """Generate embeddings for code chunks with multiple provider support"""
    
    def __init__(
        self, 
        provider: str = "huggingface",
        api_key: Optional[str] = None,
        model: str = "all-MiniLM-L6-v2",
        max_tokens: int = 512
    ):
        """
        Initialize embedder with chosen provider
        
        Args:
            provider: "openai" or "huggingface"
            api_key: API key (required for OpenAI)
            model: Model name
            max_tokens: Maximum tokens for embedding
        """
        self.provider = provider.lower()
        self.model = model
        self.max_tokens = max_tokens
        
        if self.provider == "openai":
            self._init_openai(api_key)
        elif self.provider == "huggingface":
            self._init_huggingface()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        logger.info(f"Initialized CodeEmbedder with {provider} - {model}")
    
    def _init_openai(self, api_key: str):
        """Initialize OpenAI embedder"""
        from openai import AsyncOpenAI
        import tiktoken
        
        if not api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = AsyncOpenAI(api_key=api_key)
        
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        self.dimension = 1536  # OpenAI ada-002 dimension
    
    def _init_huggingface(self):
        """Initialize HuggingFace embedder (free, local)"""
        from sentence_transformers import SentenceTransformer
        
        self.model_obj = SentenceTransformer(self.model)
        self.dimension = self.model_obj.get_sentence_embedding_dimension()
        self.tokenizer = None  # HuggingFace handles tokenization internally
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if self.provider == "openai":
            return await self._embed_openai([text])[0]
        else:
            return self._embed_huggingface([text])[0]
    
    async def embed_batch(
        self, 
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if self.provider == "openai":
            return await self._embed_openai_batch(texts, batch_size)
        else:
            return self._embed_huggingface_batch(texts, batch_size)
    
    async def embed_code_chunk(self, chunk: Dict[str, Any]) -> List[float]:
        """Generate embedding for a code chunk with metadata"""
        text = self._format_chunk_for_embedding(chunk)
        return await self.embed_text(text)
    
    async def embed_code_chunks(
        self, 
        chunks: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[List[float]]:
        """Generate embeddings for multiple code chunks"""
        texts = [self._format_chunk_for_embedding(chunk) for chunk in chunks]
        return await self.embed_batch(texts, batch_size)
    
    async def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """OpenAI embedding implementation"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}")
            raise
    
    async def _embed_openai_batch(
        self, 
        texts: List[str],
        batch_size: int
    ) -> List[List[float]]:
        """OpenAI batch embedding"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self._embed_openai(batch)
            embeddings.extend(batch_embeddings)
            logger.info(f"Generated OpenAI embeddings for batch {i//batch_size + 1}")
        
        return embeddings
    
    def _embed_huggingface(self, texts: List[str]) -> List[List[float]]:
        """HuggingFace embedding implementation (synchronous, runs locally)"""
        try:
            embeddings = self.model_obj.encode(
                texts,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating HuggingFace embedding: {e}")
            raise
    
    def _embed_huggingface_batch(
        self, 
        texts: List[str],
        batch_size: int
    ) -> List[List[float]]:
        """HuggingFace batch embedding"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self._embed_huggingface(batch)
            all_embeddings.extend(batch_embeddings)
            logger.info(f"Generated HuggingFace embeddings for batch {i//batch_size + 1}")
        
        return all_embeddings
    
    def _format_chunk_for_embedding(self, chunk: Dict[str, Any]) -> str:
        """Format code chunk with metadata for better embeddings"""
        parts = []
        
        if chunk.get('file_path'):
            parts.append(f"File: {chunk['file_path']}")
        
        if chunk.get('identifier'):
            parts.append(f"Name: {chunk['identifier']}")
        
        if chunk.get('docstring'):
            parts.append(f"Description: {chunk['docstring']}")
        
        if chunk.get('code'):
            parts.append(f"Code:\n{chunk['code']}")
        
        if chunk.get('dependencies'):
            deps = ', '.join(chunk['dependencies'][:5])
            parts.append(f"Uses: {deps}")
        
        text = '\n'.join(parts)
        
        # Truncate if needed (especially for HuggingFace models)
        if len(text) > self.max_tokens * 4:  # Rough estimate
            text = text[:self.max_tokens * 4]
        
        return text
    
    def count_tokens(self, text: str) -> int:
        """Count tokens (OpenAI only)"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough estimate for HuggingFace
            return len(text.split())
    
    async def similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        
        if norm_product == 0:
            return 0.0
        
        return float(dot_product / norm_product)
