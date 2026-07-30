"""
SearchApi.io Service
Wrapper for SearchApi.io to perform Google Searches (Web, Flights, etc.)
"""
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)

class SearchApiService:
    """Service to interact with SearchApi.io"""
    
    BASE_URL = "https://www.searchapi.io/api/v1/search"
    
    def __init__(self, api_key: Optional[str] = None):
        # If specific key provided, use it (single key mode)
        # Otherwise load all available keys from settings
        if api_key:
            self.api_keys = [api_key]
        else:
            self.api_keys = settings.search_api_keys
            
        self.current_key_index = 0
        
        if not self.api_keys:
            logger.warning("No SEARCH_API_KEYs set. Search functionality will be limited.")

    def _get_current_key(self) -> Optional[str]:
        if not self.api_keys:
            return None
        return self.api_keys[self.current_key_index % len(self.api_keys)]

    def _rotate_key(self):
        if not self.api_keys:
            return
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"Rotated to SearchApi key index {self.current_key_index}")

    async def search(self, query: str, engine: str = "google", params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a search query with automatic key rotation on failure.
        """
        if not self.api_keys:
            return {"error": "API key not configured"}
            
        # Try each key at least once if needed
        max_retries = len(self.api_keys)
        attempts = 0
        
        while attempts < max_retries:
            current_key = self._get_current_key()
            
            default_params = {
                "engine": engine,
                "q": query,
                "api_key": current_key
            }
            
            if params:
                default_params.update(params)
                # Ensure api_key in params doesn't override our rotation
                default_params["api_key"] = current_key
                
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.BASE_URL, params=default_params) as response:
                        if response.status == 200:
                            return await response.json()
                        
                        # If unauthorized or rate limited, rotate key
                        if response.status in [401, 403, 429]:
                            logger.warning(f"SearchApi key failed with status {response.status}. Rotating key...")
                            self._rotate_key()
                            attempts += 1
                            continue
                        
                        # Other errors
                        error_text = await response.text()
                        logger.error(f"SearchApi error ({response.status}): {error_text}")
                        return {"error": f"API error: {response.status}"}
                        
            except Exception as e:
                logger.error(f"Error calling SearchApi: {e}")
                # Network error? Maybe try next key just in case? 
                # Usually network error is not key related, but let's be robust.
                self._rotate_key()
                attempts += 1
        
        return {"error": "All API keys failed"}

    async def search_flights(self, origin: str, destination: str, date: str, return_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for flights using Google Flights engine or Web Search fallback.
        
        Args:
            origin: Origin airport/city
            destination: Destination airport/city
            date: Date string
            return_date: Optional return date string
            
        Returns:
            List of flight options
        """
        # Try specific flight query on Google Flights engine
        params = {
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": date,
            "currency": "USD",
            "hl": "en"
        }
        
        if return_date:
            params["return_date"] = return_date
        
        return await self.search("flights", engine="google_flights", params=params)

    async def search_transport_options(self, origin: str, destination: str) -> Dict[str, Any]:
        """
        General transport search (flights, trains, buses).
        """
        query = f"transport from {origin} to {destination}"
        return await self.search(query)

# Singleton
_search_api_service = None

def get_search_api_service():
    global _search_api_service
    if not _search_api_service:
        _search_api_service = SearchApiService()
    return _search_api_service
