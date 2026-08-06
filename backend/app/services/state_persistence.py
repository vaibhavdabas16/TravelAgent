"""
State Persistence Service - Save/load LangGraph state to/from database (Phase 2.2)
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.state import TravelAgentState, POI, ItineraryItem
from app.services.database import DatabaseService
from app.db import get_session_context

logger = logging.getLogger(__name__)


class StatePersistenceService:
    """Service for persisting and loading LangGraph state."""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        """
        Initialize the state persistence service.
        
        Args:
            session: Optional database session (will create one if not provided)
        """
        self.session = session
        self._owns_session = session is None
    
    async def __aenter__(self):
        """Context manager entry."""
        if self._owns_session:
            self._session_context = get_session_context()
            self.session = await self._session_context.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._owns_session and hasattr(self, '_session_context'):
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
    
    async def save_trip_state(
        self,
        trip_id: str,
        state: TravelAgentState
    ) -> bool:
        """
        Persist LangGraph state to database.
        
        This saves the current agent state to the database, enabling:
        - Session resumption
        - State recovery
        - Historical tracking
        
        Args:
            trip_id: Trip ID
            state: Current TravelAgentState from LangGraph
            
        Returns:
            True if successful, False otherwise
        """
        try:
            db = DatabaseService(self.session)
            
            # Update trip with current state
            trip = await db.get_trip_by_id(trip_id)
            if not trip:
                logger.error(f"Trip {trip_id} not found")
                return False
            
            # Save constraints and Phase 2 data (hotels, flights, transport)
            constraints_data = state.get('constraints', {}).copy()
            
            # Inject Phase 2 data into constraints for persistence
            if state.get('recommended_hotels'):
                constraints_data['recommended_hotels'] = state['recommended_hotels']
            if state.get('recommended_flights'):
                constraints_data['recommended_flights'] = state['recommended_flights']
            if state.get('local_transport'):
                constraints_data['local_transport'] = state['local_transport']
                
            trip.constraints = constraints_data
            
            # Save destination coordinates
            if state.get('destination_coords'):
                coords = state['destination_coords']
                trip.destination_lat = coords.get('lat')
                trip.destination_lng = coords.get('lng')
            
            # Save current stage
            if state.get('current_stage'):
                trip.current_stage = state['current_stage']
            
            # Save discovered POIs
            if state.get('potential_pois'):
                await self._save_discovered_pois(db, trip_id, state['potential_pois'])
            
            # Save optimized itinerary
            if state.get('itinerary'):
                await self._save_itinerary(db, trip_id, state['itinerary'])
            
            trip.updated_at = datetime.utcnow()
            await self.session.flush()
            
            logger.info(f"✅ Saved state for trip {trip_id} (stage: {state.get('current_stage')})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving trip state: {e}")
            return False
    
    async def _save_discovered_pois(
        self,
        db: DatabaseService,
        trip_id: str,
        potential_pois: list[POI]
    ):
        """Save discovered POIs to database."""
        for poi_data in potential_pois:
            # Create/update POI in cache
            poi = await db.get_or_create_poi(
                place_id=poi_data.get('place_id'),
                name=poi_data.get('name'),
                category=poi_data.get('types', [None])[0] if poi_data.get('types') else None,
                lat=poi_data.get('geometry', {}).get('location', {}).get('lat'),
                lng=poi_data.get('geometry', {}).get('location', {}).get('lng'),
                rating=poi_data.get('rating'),
                user_ratings_total=poi_data.get('user_ratings_total'),
                price_level=poi_data.get('price_level'),
                formatted_address=poi_data.get('formatted_address'),
                details=poi_data
            )
            
            # Link to trip with discovery context
            await db.add_poi_to_trip(
                trip_id=trip_id,
                poi_id=poi.id,
                ai_score=poi_data.get('ai_score'),
                score_breakdown=poi_data.get('score_breakdown'),
                recommendation_reason=poi_data.get('recommendation_reason')
            )
    
    async def _save_itinerary(
        self,
        db: DatabaseService,
        trip_id: str,
        itinerary: list[ItineraryItem]
    ):
        """Save optimized itinerary to database."""
        # Delete existing itinerary
        await db.delete_trip_itinerary(trip_id)
        
        # Create new itinerary items
        for idx, item in enumerate(itinerary):
            # Get POI by place_id if available
            poi_id = None
            if item.get('place_id'):
                poi = await db.get_poi_by_place_id(item['place_id'])
                if poi:
                    poi_id = poi.id
            
            await db.create_itinerary_item(
                trip_id=trip_id,
                poi_id=poi_id,
                day_number=1,  # TODO: Multi-day support
                sequence_order=idx,
                start_time=item['start_time'],
                end_time=item['end_time'],
                visit_duration_minutes=item.get('visit_duration_minutes'),
                travel_time_to_next_minutes=item.get('travel_time_to_next'),
                notes=item.get('notes')
            )
    
    async def load_trip_state(self, trip_id: str) -> Optional[TravelAgentState]:
        """
        Load LangGraph state from database.
        
        This reconstructs the agent state from the database, enabling
        session resumption.
        
        Args:
            trip_id: Trip ID
            
        Returns:
            TravelAgentState or None if not found
        """
        try:
            db = DatabaseService(self.session)
            
            # Load trip
            trip = await db.get_trip_by_id(trip_id, include_itinerary=True, include_pois=True)
            if not trip:
                logger.error(f"Trip {trip_id} not found")
                return None
            
            # Reconstruct state
            state: TravelAgentState = {
                'messages': [],  # TODO: Store message history
                'constraints': trip.constraints or {},
                'destination_coords': None,
                'potential_pois': [],
                'itinerary': [],
                'optimization_params': None,
                'optimization_suggestions': [],
                'optimization_attempts': 0,
                'current_stage': trip.current_stage or 'start',
                'error_message': None,
                'trip_id': trip_id,
                'created_at': trip.created_at.isoformat(),
                'updated_at': trip.updated_at.isoformat()
            }
            
            # Extract Phase 2 data from constraints if present
            constraints = trip.constraints or {}
            if 'recommended_hotels' in constraints:
                state['recommended_hotels'] = constraints['recommended_hotels']
            else:
                state['recommended_hotels'] = []
                
            if 'recommended_flights' in constraints:
                state['recommended_flights'] = constraints['recommended_flights']
            else:
                state['recommended_flights'] = []
                
            if 'local_transport' in constraints:
                state['local_transport'] = constraints['local_transport']
            else:
                state['local_transport'] = None
            
            # Restore destination coords
            if trip.destination_lat and trip.destination_lng:
                state['destination_coords'] = {
                    'lat': trip.destination_lat,
                    'lng': trip.destination_lng,
                    'formatted_address': trip.destination
                }
            
            # Restore discovered POIs
            trip_pois = await db.get_trip_pois(trip_id)
            for trip_poi in trip_pois:
                poi = trip_poi.poi
                poi_data = {
                    'place_id': poi.place_id,
                    'name': poi.name,
                    'geometry': {
                        'location': {
                            'lat': poi.lat,
                            'lng': poi.lng
                        }
                    },
                    'rating': poi.rating,
                    'user_ratings_total': poi.user_ratings_total,
                    'price_level': poi.price_level,
                    'formatted_address': poi.formatted_address,
                    'ai_score': trip_poi.ai_score,
                    'score_breakdown': trip_poi.score_breakdown,
                    'recommendation_reason': trip_poi.recommendation_reason,
                    **(poi.details or {})
                }
                state['potential_pois'].append(poi_data)
            
            # Restore itinerary
            itinerary_items = await db.get_trip_itinerary(trip_id)
            for item in itinerary_items:
                itinerary_item = {
                    'place_name': item.poi.name if item.poi else 'Starting Point',
                    'place_id': item.poi.place_id if item.poi else 'start',
                    'address': item.poi.formatted_address if item.poi else '',
                    'start_time': item.start_time,
                    'end_time': item.end_time,
                    'visit_duration_minutes': item.visit_duration_minutes,
                    'travel_time_to_next': item.travel_time_to_next_minutes,
                    'notes': item.notes
                }
                state['itinerary'].append(itinerary_item)
            
            logger.info(f"✅ Loaded state for trip {trip_id} (stage: {state['current_stage']})")
            return state
            
        except Exception as e:
            logger.error(f"Error loading trip state: {e}")
            return None
    
    async def create_trip_from_state(
        self,
        user_id: str,
        state: TravelAgentState
    ) -> Optional[str]:
        """
        Create a new trip from LangGraph state.
        
        Args:
            user_id: User ID
            state: Initial TravelAgentState
            
        Returns:
            Trip ID or None if failed
        """
        try:
            db = DatabaseService(self.session)
            
            # Extract destination
            destination = "Unknown"
            if state.get('constraints'):
                destination = state['constraints'].get('destination', 'Unknown')
            elif state.get('destination_coords'):
                destination = state['destination_coords'].get('formatted_address', 'Unknown')
            
            # Create trip
            trip = await db.create_trip(
                user_id=user_id,
                destination=destination,
                constraints=state.get('constraints'),
                destination_lat=state.get('destination_coords', {}).get('lat'),
                destination_lng=state.get('destination_coords', {}).get('lng')
            )
            
            # Save full state
            await self.save_trip_state(trip.id, state)
            
            logger.info(f"✅ Created trip {trip.id} from state")
            return trip.id
            
        except Exception as e:
            logger.error(f"Error creating trip from state: {e}")
            return None
    
    async def get_user_active_trips(self, user_id: str) -> list[Dict[str, Any]]:
        """Get all active trips for a user."""
        try:
            db = DatabaseService(self.session)
            
            trips = await db.get_user_trips(user_id, status="planning", limit=50)
            
            trip_summaries = []
            for trip in trips:
                trip_summaries.append({
                    "trip_id": trip.id,
                    "destination": trip.destination,
                    "status": trip.status,
                    "current_stage": trip.current_stage,
                    "created_at": trip.created_at.isoformat(),
                    "updated_at": trip.updated_at.isoformat()
                })
            
            return trip_summaries
            
        except Exception as e:
            logger.error(f"Error getting user trips: {e}")
            return []


# Convenience function
async def get_state_persistence_service(
    session: Optional[AsyncSession] = None
) -> StatePersistenceService:
    """Get a StatePersistenceService instance."""
    return StatePersistenceService(session=session)

















