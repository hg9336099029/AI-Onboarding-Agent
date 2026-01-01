"""
Vector Store - FAISS-based semantic search

Manages vector storage and similarity search for code embeddings.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
import pickle
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for code embeddings"""
    
    def __init__(
        self, 
        dimension: int = 1536,  # OpenAI ada-002 dimension
        index_path: Optional[str] = None
    ):
        """
        Initialize vector store
        
        Args:
            dimension: Embedding vector dimension
            index_path: Path to save/load index
        """
        self.dimension = dimension
        self.index_path = index_path
        
        # Initialize FAISS index (IndexFlatL2 for exact search)
        self.index = faiss.IndexFlatL2(dimension)
        
        # Metadata storage (maps index position to chunk metadata)
        self.metadata = []
        
        # Repository index mapping
        self.repo_indices = {}  # repo_id -> list of indices
        
        logger.info(f"Initialized VectorStore with dimension {dimension}")
    
    def add(
        self, 
        embeddings: List[List[float]], 
        metadata: List[Dict[str, Any]]
    ):
        """
        Add embeddings with metadata to the store
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries
        """
        if len(embeddings) != len(metadata):
            raise ValueError("Number of embeddings must match metadata")
        
        # Convert to numpy array
        vectors = np.array(embeddings, dtype=np.float32)
        
        # Get current index count
        start_idx = self.index.ntotal
        
        # Add to FAISS index
        self.index.add(vectors)
        
        # Store metadata
        self.metadata.extend(metadata)
        
        # Update repository indices
        for i, meta in enumerate(metadata):
            repo_id = meta.get('repo_id')
            if repo_id:
                if repo_id not in self.repo_indices:
                    self.repo_indices[repo_id] = []
                self.repo_indices[repo_id].append(start_idx + i)
        
        logger.info(f"Added {len(embeddings)} vectors to index")
    
    def search(
        self, 
        query_embedding: List[float],
        k: int = 10,
        repo_id: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar vectors
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            repo_id: Optional repository filter
        
        Returns:
            List of (metadata, distance) tuples
        """
        # Convert query to numpy array
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        if repo_id and repo_id in self.repo_indices:
            # Filter by repository
            return self._search_with_filter(query_vector, k, repo_id)
        else:
            # Search entire index
            distances, indices = self.index.search(query_vector, k)
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(self.metadata):
                    # Convert L2 distance to similarity score
                    similarity = self._distance_to_similarity(dist)
                    results.append((self.metadata[idx], similarity))
            
            return results
    
    def _search_with_filter(
        self, 
        query_vector: np.ndarray,
        k: int,
        repo_id: str
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search within a specific repository"""
        repo_indices_list = self.repo_indices.get(repo_id, [])
        
        if not repo_indices_list:
            logger.warning(f"No vectors found for repo_id: {repo_id}")
            return []
        
        # Search more to ensure we get k results after filtering
        search_k = min(k * 3, self.index.ntotal)
        distances, indices = self.index.search(query_vector, search_k)
        
        # Filter results by repo_id
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx in repo_indices_list and idx < len(self.metadata):
                similarity = self._distance_to_similarity(dist)
                results.append((self.metadata[idx], similarity))
                
                if len(results) >= k:
                    break
        
        return results
    
    def _distance_to_similarity(self, distance: float) -> float:
        """
        Convert L2 distance to similarity score (0-1)
        
        Args:
            distance: L2 distance
        
        Returns:
            Similarity score
        """
        # Use negative exponential to convert distance to similarity
        return float(np.exp(-distance / 10.0))
    
    def save(self, path: Optional[str] = None):
        """
        Save index and metadata to disk
        
        Args:
            path: Directory path to save files
        """
        save_path = path or self.index_path
        
        if not save_path:
            raise ValueError("No save path specified")
        
        # Create directory if it doesn't exist
        Path(save_path).mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = os.path.join(save_path, "index.faiss")
        faiss.write_index(self.index, index_file)
        
        # Save metadata
        metadata_file = os.path.join(save_path, "metadata.pkl")
        with open(metadata_file, 'wb') as f:
            pickle.dump({
                'metadata': self.metadata,
                'repo_indices': self.repo_indices,
                'dimension': self.dimension
            }, f)
        
        logger.info(f"Saved vector store to {save_path}")
    
    def load(self, path: Optional[str] = None):
        """
        Load index and metadata from disk
        
        Args:
            path: Directory path to load files from
        """
        load_path = path or self.index_path
        
        if not load_path:
            raise ValueError("No load path specified")
        
        # Load FAISS index
        index_file = os.path.join(load_path, "index.faiss")
        if os.path.exists(index_file):
            self.index = faiss.read_index(index_file)
        else:
            raise FileNotFoundError(f"Index file not found: {index_file}")
        
        # Load metadata
        metadata_file = os.path.join(load_path, "metadata.pkl")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'rb') as f:
                data = pickle.load(f)
                self.metadata = data['metadata']
                self.repo_indices = data['repo_indices']
                self.dimension = data['dimension']
        else:
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")
        
        logger.info(f"Loaded vector store from {load_path}")
    
    def delete_repository(self, repo_id: str):
        """
        Delete all vectors for a repository
        
        Args:
            repo_id: Repository identifier
        """
        if repo_id not in self.repo_indices:
            logger.warning(f"Repository {repo_id} not found in index")
            return
        
        # Get indices to remove
        indices_to_remove = set(self.repo_indices[repo_id])
        
        # FAISS doesn't support deletion, so we need to rebuild
        # Keep only vectors not in indices_to_remove
        new_vectors = []
        new_metadata = []
        new_repo_indices = {}
        
        for i in range(self.index.ntotal):
            if i not in indices_to_remove:
                # Get vector
                vector = self.index.reconstruct(i)
                new_vectors.append(vector)
                new_metadata.append(self.metadata[i])
                
                # Update repo indices
                meta_repo_id = self.metadata[i].get('repo_id')
                if meta_repo_id:
                    if meta_repo_id not in new_repo_indices:
                        new_repo_indices[meta_repo_id] = []
                    new_repo_indices[meta_repo_id].append(len(new_vectors) - 1)
        
        # Rebuild index
        if new_vectors:
            vectors_array = np.array(new_vectors, dtype=np.float32)
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(vectors_array)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
        
        self.metadata = new_metadata
        self.repo_indices = new_repo_indices
        
        logger.info(f"Deleted {len(indices_to_remove)} vectors for repo {repo_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'repositories': len(self.repo_indices),
            'repo_vector_counts': {
                repo_id: len(indices) 
                for repo_id, indices in self.repo_indices.items()
            }
        }
