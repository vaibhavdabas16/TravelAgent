"""
Vector Store Service using Pinecone for semantic POI search (Phase 2.2)
"""

import logging
from typing import List, Dict, Optional, Any

from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for vector-based semantic search using Pinecone."""
    
    def __init__(self):
        """Initialize Pinecone client and embedding service."""
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.embedding_dim = 768  # Gemini embedding dimension
        self.index = None
        
        # Configure Gemini for embeddings
        genai.configure(api_key=settings.gemini_api_key)
        
        logger.info(f"VectorStoreService initialized (index: {self.index_name})")
    
    async def initialize_collection(self, recreate: bool = False):
        """
        Initialize the Pinecone index.
        
        Args:
            recreate: If True, delete existing index and create new one
        """
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            index_exists = any(idx.name == self.index_name for idx in existing_indexes)
            
            if index_exists and recreate:
                logger.info(f"Deleting existing index: {self.index_name}")
                self.pc.delete_index(self.index_name)
                index_exists = False
            
            if not index_exists:
                logger.info(f"Creating index: {self.index_name}")
                # Pinecone free tier: use AWS us-east-1 (most common free tier region)
                # If using GCP starter, the region must match your plan's availability
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dim,
                    metric="cosine",  # Cosine similarity
                    spec=ServerlessSpec(
                        cloud="aws",  # Free tier supports AWS
                        region="us-east-1"  # Free tier region
                    )
                )
                logger.info(f"✅ Index '{self.index_name}' created")
            else:
                logger.info(f"Index '{self.index_name}' already exists")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone index: {e}")
            logger.warning("Vector search will be disabled")
            self.index = None
    
    def generate_embedding(self, text: str, retry_count: int = 0) -> List[float]:
        """
        Generate embedding vector for text using Gemini.
        
        Args:
            text: Text to embed (POI description, user query, etc.)
            retry_count: Internal retry counter (don't set manually)
            
        Returns:
            768-dimensional embedding vector (or zero vector if rate limited)
        """
        import time
        
        try:
            # Use Gemini's embedding model
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            
            embedding = result['embedding']
            
            # Ensure correct dimensionality
            if len(embedding) != self.embedding_dim:
                logger.warning(f"Unexpected embedding dimension: {len(embedding)}, expected {self.embedding_dim}")
                # Pad or truncate as needed
                if len(embedding) < self.embedding_dim:
                    embedding += [0.0] * (self.embedding_dim - len(embedding))
                else:
                    embedding = embedding[:self.embedding_dim]
            
            return embedding
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error (429)
            if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                if retry_count < 2:  # Try up to 2 retries
                    wait_time = (2 ** retry_count) * 2  # Exponential backoff: 2s, 4s
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {retry_count + 1}/2")
                    time.sleep(wait_time)
                    return self.generate_embedding(text, retry_count + 1)
                else:
                    logger.error(f"Rate limit exceeded after retries. Returning zero vector.")
                    logger.info("💡 Tip: Vector search will be disabled temporarily. Consider upgrading Gemini API quota.")
            else:
                logger.error(f"Error generating embedding: {e}")
            
            # Return zero vector as fallback
            return [0.0] * self.embedding_dim
    
    async def index_poi(
        self,
        poi_id: str,
        name: str,
        description: str,
        category: Optional[str] = None,
        location: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Index a POI in the vector store.
        
        Args:
            poi_id: Unique POI identifier (Google place_id)
            name: POI name
            description: POI description (for embedding)
            category: POI category (museum, restaurant, etc.)
            location: {"lat": float, "lng": float}
            metadata: Additional metadata to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self.index:
            logger.warning("Pinecone index not initialized, skipping indexing")
            return False
        
        try:
            # Create text for embedding
            embed_text = f"{name}. {description}"
            if category:
                embed_text = f"{category}: {embed_text}"
            
            # Generate embedding
            embedding = self.generate_embedding(embed_text)
            
            # Prepare metadata (Pinecone has metadata size limits)
            poi_metadata = {
                "poi_id": poi_id,
                "name": name,
                "description": description[:500] if description else "",  # Limit size
                "category": category or "general",
            }
            
            if location:
                poi_metadata["lat"] = location.get("lat")
                poi_metadata["lng"] = location.get("lng")
            
            if metadata:
                # Add custom metadata, but keep it small
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        poi_metadata[key] = value
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[
                    {
                        "id": poi_id,
                        "values": embedding,
                        "metadata": poi_metadata
                    }
                ]
            )
            
            logger.debug(f"Indexed POI: {name} ({poi_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing POI {poi_id}: {e}")
            return False
    
    async def search_similar_pois(
        self,
        query: str,
        limit: int = 20,
        category_filter: Optional[str] = None,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar POIs.
        
        Args:
            query: Natural language search query
                   e.g. "quiet artsy neighborhood cafes"
            limit: Maximum number of results
            category_filter: Filter by category (e.g., "restaurant")
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of POIs with scores
        """
        if not self.index:
            logger.warning("Pinecone index not initialized, returning empty results")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Prepare filter
            filter_dict = None
            if category_filter:
                filter_dict = {"category": {"$eq": category_filter}}
            
            # Search
            results = self.index.query(
                vector=query_embedding,
                filter=filter_dict,
                top_k=limit,
                include_metadata=True
            )
            
            # Format results
            pois = []
            for match in results.matches:
                if match.score >= score_threshold:
                    metadata = match.metadata
                    poi = {
                        "poi_id": metadata.get("poi_id"),
                        "name": metadata.get("name"),
                        "description": metadata.get("description"),
                        "category": metadata.get("category"),
                        "location": {
                            "lat": metadata.get("lat"),
                            "lng": metadata.get("lng")
                        },
                        "score": match.score,
                        "metadata": {k: v for k, v in metadata.items() 
                                    if k not in ["poi_id", "name", "description", "category", "lat", "lng"]}
                    }
                    pois.append(poi)
            
            logger.info(f"Semantic search for '{query}': found {len(pois)} results")
            return pois
            
        except Exception as e:
            logger.error(f"Error searching POIs: {e}")
            return []
    
    async def get_poi_by_id(self, poi_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific POI by ID.
        
        Args:
            poi_id: Google place_id
            
        Returns:
            POI data or None if not found
        """
        if not self.index:
            return None
        
        try:
            result = self.index.fetch(ids=[poi_id])
            
            if poi_id in result.vectors:
                vector_data = result.vectors[poi_id]
                metadata = vector_data.metadata
                
                return {
                    "poi_id": metadata.get("poi_id"),
                    "name": metadata.get("name"),
                    "description": metadata.get("description"),
                    "category": metadata.get("category"),
                    "location": {
                        "lat": metadata.get("lat"),
                        "lng": metadata.get("lng")
                    },
                    "metadata": metadata
                }
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving POI {poi_id}: {e}")
            return None
    
    async def delete_poi(self, poi_id: str) -> bool:
        """Delete a POI from the vector store."""
        if not self.index:
            return False
        
        try:
            self.index.delete(ids=[poi_id])
            logger.info(f"Deleted POI: {poi_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting POI {poi_id}: {e}")
            return False
    
    async def count_pois(self) -> int:
        """Get total number of indexed POIs."""
        if not self.index:
            return 0
        
        try:
            stats = self.index.describe_index_stats()
            return stats.total_vector_count
        except Exception as e:
            logger.error(f"Error counting POIs: {e}")
            return 0
    
    async def bulk_index_pois(self, pois: List[Dict[str, Any]]) -> int:
        """
        Index multiple POIs in batch.
        
        Args:
            pois: List of POI dicts with keys:
                  - poi_id, name, description, category, location, metadata
        
        Returns:
            Number of successfully indexed POIs
        """
        if not self.index:
            return 0
        
        success_count = 0
        vectors_to_upsert = []
        
        for poi in pois:
            try:
                # Create text for embedding
                name = poi.get("name", "")
                description = poi.get("description", "")
                category = poi.get("category")
                
                embed_text = f"{name}. {description}"
                if category:
                    embed_text = f"{category}: {embed_text}"
                
                # Generate embedding
                embedding = self.generate_embedding(embed_text)
                
                # Prepare metadata
                location = poi.get("location", {})
                poi_metadata = {
                    "poi_id": poi.get("poi_id"),
                    "name": name,
                    "description": description[:500] if description else "",
                    "category": category or "general",
                    "lat": location.get("lat"),
                    "lng": location.get("lng")
                }
                
                vectors_to_upsert.append({
                    "id": poi.get("poi_id"),
                    "values": embedding,
                    "metadata": poi_metadata
                })
                
            except Exception as e:
                logger.error(f"Error preparing POI for bulk index: {e}")
                continue
        
        # Upsert in batches of 100 (Pinecone limit)
        batch_size = 100
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            try:
                self.index.upsert(vectors=batch)
                success_count += len(batch)
            except Exception as e:
                logger.error(f"Error in bulk upsert batch: {e}")
        
        logger.info(f"Bulk indexed {success_count}/{len(pois)} POIs")
        return success_count


# Singleton instance
_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    """Get or create VectorStoreService singleton."""
    global _vector_store_service
    
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    
    return _vector_store_service
