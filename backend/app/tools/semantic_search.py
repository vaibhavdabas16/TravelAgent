"""
LangChain tools for semantic POI search using Qdrant (Phase 2.2)
"""

import logging
from typing import List, Dict, Optional, Any
from langchain_core.tools import tool

from app.services.vector_store import get_vector_store_service

logger = logging.getLogger(__name__)


@tool
async def semantic_search_pois(
    query: str,
    limit: int = 20,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Perform semantic search for points of interest based on natural language query.
    
    This tool uses vector embeddings to find POIs that match the semantic meaning
    of the query, not just keyword matches.
    
    Args:
        query: Natural language search query.
               Examples:
               - "quiet cafes with good wifi for working"
               - "romantic restaurants with city views"
               - "hidden gem art galleries"
               - "family-friendly outdoor activities"
        limit: Maximum number of results to return (default: 20)
        category: Optional category filter (e.g., "restaurant", "museum", "park")
    
    Returns:
        List of POI dictionaries with similarity scores:
        [
            {
                "poi_id": "ChIJ...",
                "name": "Blue Bottle Coffee",
                "description": "Minimalist cafe known for its artisanal coffee...",
                "category": "cafe",
                "location": {"lat": 37.7749, "lng": -122.4194},
                "score": 0.89  # Similarity score (0-1)
            },
            ...
        ]
    
    Example:
        >>> results = semantic_search_pois(
        ...     query="cozy bookstores with reading nooks",
        ...     limit=10,
        ...     category="bookstore"
        ... )
        >>> for poi in results:
        ...     print(f"{poi['name']}: {poi['score']}")
    """
    try:
        vector_store = get_vector_store_service()
        
        # Perform semantic search
        results = await vector_store.search_similar_pois(
            query=query,
            limit=limit,
            category_filter=category,
            score_threshold=0.6  # Minimum 60% similarity
        )
        
        if not results:
            logger.info(f"No semantic search results for: '{query}'")
            return []
        
        logger.info(f"Semantic search for '{query}': found {len(results)} POIs")
        return results
        
    except Exception as e:
        logger.error(f"Error in semantic_search_pois: {e}")
        return []


@tool
async def index_poi_for_search(
    poi_id: str,
    name: str,
    description: str,
    category: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None
) -> bool:
    """
    Index a POI in the vector store for semantic search.
    
    This tool should be called when discovering new POIs to make them
    searchable via semantic queries.
    
    Args:
        poi_id: Unique identifier (Google place_id)
        name: POI name
        description: Detailed description of the POI
        category: Category (e.g., "museum", "restaurant")
        lat: Latitude
        lng: Longitude
    
    Returns:
        True if indexing succeeded, False otherwise
    
    Example:
        >>> success = index_poi_for_search(
        ...     poi_id="ChIJ...",
        ...     name="MoMA",
        ...     description="Modern art museum featuring contemporary works...",
        ...     category="museum",
        ...     lat=40.7614,
        ...     lng=-73.9776
        ... )
    """
    try:
        vector_store = get_vector_store_service()
        
        location = None
        if lat is not None and lng is not None:
            location = {"lat": lat, "lng": lng}
        
        success = await vector_store.index_poi(
            poi_id=poi_id,
            name=name,
            description=description,
            category=category,
            location=location
        )
        
        if success:
            logger.info(f"✅ Indexed POI for semantic search: {name}")
        else:
            logger.warning(f"⚠️  Failed to index POI: {name}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in index_poi_for_search: {e}")
        return False


@tool
async def get_vector_store_stats() -> Dict[str, Any]:
    """
    Get statistics about the vector store.
    
    Returns:
        Dictionary with stats:
        {
            "total_pois": 1543,
            "collection_name": "pois",
            "status": "healthy"
        }
    """
    try:
        vector_store = get_vector_store_service()
        
        total_pois = await vector_store.count_pois()
        
        return {
            "total_pois": total_pois,
            "collection_name": vector_store.collection_name,
            "status": "healthy" if total_pois >= 0 else "error"
        }
        
    except Exception as e:
        logger.error(f"Error getting vector store stats: {e}")
        return {
            "total_pois": 0,
            "status": "error",
            "error": str(e)
        }





