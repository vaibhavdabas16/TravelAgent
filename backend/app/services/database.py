"""
DatabaseService - CRUD operations for all models (Phase 2.2)
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Trip, POI, TripPOI, ItineraryItem
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the database service with a session.
        
        Args:
            session: AsyncSession for database operations
        """
        self.session = session
    
    # ==================== User Operations ====================
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        preferences: Optional[Dict] = None
    ) -> User:
        """Create a new user."""
        # Truncate password to 72 bytes for bcrypt compatibility
        # bcrypt has a maximum password length of 72 bytes
        password_bytes = password.encode('utf-8')[:72]
        password_truncated = password_bytes.decode('utf-8', errors='ignore')
        
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password=pwd_context.hash(password_truncated),
            full_name=full_name,
            preferences=preferences or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(user)
        await self.session.flush()
        logger.info(f"Created user: {user.email}")
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict
    ) -> Optional[User]:
        """Update user preferences."""
        user = await self.get_user_by_id(user_id)
        if user:
            user.preferences = preferences
            user.updated_at = datetime.utcnow()
            await self.session.flush()
            logger.info(f"Updated preferences for user: {user.email}")
        return user
    
    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    # ==================== Trip Operations ====================
    
    async def create_trip(
        self,
        user_id: str,
        destination: str,
        constraints: Optional[Dict] = None,
        destination_lat: Optional[float] = None,
        destination_lng: Optional[float] = None,
        trip_id: Optional[str] = None
    ) -> Trip:
        """Create a new trip."""
        trip = Trip(
            id=trip_id or str(uuid.uuid4()),
            user_id=user_id,
            destination=destination,
            destination_lat=destination_lat,
            destination_lng=destination_lng,
            constraints=constraints or {},
            status="planning",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(trip)
        await self.session.flush()
        logger.info(f"Created trip: {trip.id} for user: {user_id}")
        return trip
    
    async def get_trip_by_id(
        self,
        trip_id: str,
        include_itinerary: bool = False,
        include_pois: bool = False
    ) -> Optional[Trip]:
        """Get trip by ID with optional relationships."""
        query = select(Trip).where(Trip.id == trip_id)
        
        if include_itinerary:
            query = query.options(selectinload(Trip.itinerary_items))
        if include_pois:
            query = query.options(selectinload(Trip.trip_pois))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_trips(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Trip]:
        """Get all trips for a user."""
        query = select(Trip).where(Trip.user_id == user_id)
        
        if status:
            query = query.where(Trip.status == status)
        
        query = query.order_by(Trip.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_trip(
        self,
        trip_id: str,
        **updates
    ) -> Optional[Trip]:
        """Update trip fields."""
        trip = await self.get_trip_by_id(trip_id)
        if trip:
            for key, value in updates.items():
                if hasattr(trip, key):
                    setattr(trip, key, value)
            trip.updated_at = datetime.utcnow()
            await self.session.flush()
            logger.info(f"Updated trip: {trip_id}")
        return trip
    
    async def delete_trip(self, trip_id: str) -> bool:
        """Delete a trip."""
        trip = await self.get_trip_by_id(trip_id)
        if trip:
            await self.session.delete(trip)
            await self.session.flush()
            logger.info(f"Deleted trip: {trip_id}")
            return True
        return False
    
    # ==================== POI Operations ====================
    
    async def get_or_create_poi(
        self,
        place_id: str,
        name: str,
        category: Optional[str] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        rating: Optional[float] = None,
        user_ratings_total: Optional[int] = None,
        price_level: Optional[int] = None,
        formatted_address: Optional[str] = None,
        details: Optional[Dict] = None,
        embedding: Optional[List[float]] = None,
        cache_ttl_hours: int = 24
    ) -> POI:
        """
        Get existing POI by place_id or create new one.
        
        This implements a cache: if POI exists and is fresh, return it.
        Otherwise, create/update it.
        """
        # Try to get existing POI
        result = await self.session.execute(
            select(POI).where(POI.place_id == place_id)
        )
        poi = result.scalar_one_or_none()
        
        now = datetime.utcnow()
        cache_expires = now + timedelta(hours=cache_ttl_hours)
        
        if poi:
            # Update if cache expired or new data provided
            if poi.cache_expires_at and poi.cache_expires_at < now:
                logger.info(f"Updating expired POI cache: {place_id}")
                poi.name = name
                poi.category = category
                poi.lat = lat
                poi.lng = lng
                poi.rating = rating
                poi.user_ratings_total = user_ratings_total
                poi.price_level = price_level
                poi.formatted_address = formatted_address
                poi.details = details or poi.details
                poi.embedding = embedding or poi.embedding
                poi.cached_at = now
                poi.cache_expires_at = cache_expires
                await self.session.flush()
            return poi
        
        # Create new POI with handling for concurrent inserts
        try:
            # Use a nested transaction (savepoint) to handle potential unique constraint violations
            # without rolling back the entire transaction
            async with self.session.begin_nested():
                poi = POI(
                    place_id=place_id,
                    name=name,
                    category=category,
                    formatted_address=formatted_address,
                    lat=lat,
                    lng=lng,
                    rating=rating,
                    user_ratings_total=user_ratings_total,
                    price_level=price_level,
                    details=details,
                    embedding=embedding,
                    cached_at=now,
                    cache_expires_at=cache_expires
                )
                self.session.add(poi)
                await self.session.flush()
                logger.info(f"Created POI: {name} ({place_id})")
                return poi
        except IntegrityError:
            logger.info(f"POI {place_id} created concurrently, fetching existing.")
            # It exists now (created by another transaction), so fetch it
            result = await self.session.execute(
                select(POI).where(POI.place_id == place_id)
            )
            poi = result.scalar_one_or_none()
            if poi:
                return poi
            # If we still can't find it, re-raise the error
            raise
    
    async def get_poi_by_place_id(self, place_id: str) -> Optional[POI]:
        """Get POI by Google Places ID."""
        result = await self.session.execute(
            select(POI).where(POI.place_id == place_id)
        )
        return result.scalar_one_or_none()
    
    async def search_pois_by_name(self, name_query: str, limit: int = 20) -> List[POI]:
        """Search POIs by name (simple text search)."""
        result = await self.session.execute(
            select(POI)
            .where(POI.name.ilike(f"%{name_query}%"))
            .limit(limit)
        )
        return result.scalars().all()
    
    # ==================== TripPOI Operations ====================
    
    async def add_poi_to_trip(
        self,
        trip_id: str,
        poi_id: int,
        ai_score: Optional[float] = None,
        score_breakdown: Optional[Dict] = None,
        recommendation_reason: Optional[str] = None
    ) -> TripPOI:
        """Add a POI to a trip with discovery context."""
        trip_poi = TripPOI(
            trip_id=trip_id,
            poi_id=poi_id,
            ai_score=ai_score,
            score_breakdown=score_breakdown,
            recommendation_reason=recommendation_reason,
            discovered_at=datetime.utcnow()
        )
        self.session.add(trip_poi)
        await self.session.flush()
        logger.info(f"Added POI {poi_id} to trip {trip_id}")
        return trip_poi
    
    async def get_trip_pois(
        self,
        trip_id: str,
        user_selected_only: bool = False
    ) -> List[TripPOI]:
        """Get all POIs for a trip."""
        query = select(TripPOI).where(TripPOI.trip_id == trip_id)
        
        if user_selected_only:
            query = query.where(TripPOI.user_selected == True)
        
        query = query.options(selectinload(TripPOI.poi))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_trip_poi_selection(
        self,
        trip_id: str,
        poi_id: int,
        selected: bool,
        user_notes: Optional[str] = None
    ) -> Optional[TripPOI]:
        """Update user selection status for a POI in a trip."""
        result = await self.session.execute(
            select(TripPOI).where(
                and_(TripPOI.trip_id == trip_id, TripPOI.poi_id == poi_id)
            )
        )
        trip_poi = result.scalar_one_or_none()
        
        if trip_poi:
            trip_poi.user_selected = selected
            trip_poi.user_rejected = not selected
            if user_notes:
                trip_poi.user_notes = user_notes
            await self.session.flush()
            logger.info(f"Updated POI selection: trip={trip_id}, poi={poi_id}, selected={selected}")
        
        return trip_poi
    
    # ==================== Itinerary Operations ====================
    
    async def create_itinerary_item(
        self,
        trip_id: str,
        poi_id: Optional[int],
        day_number: int,
        sequence_order: int,
        start_time: str,
        end_time: str,
        visit_duration_minutes: Optional[int] = None,
        travel_time_to_next_minutes: Optional[int] = None,
        travel_leg: Optional[Dict] = None,
        notes: Optional[str] = None
    ) -> ItineraryItem:
        """Create an itinerary item."""
        item = ItineraryItem(
            trip_id=trip_id,
            poi_id=poi_id,
            day_number=day_number,
            sequence_order=sequence_order,
            start_time=start_time,
            end_time=end_time,
            visit_duration_minutes=visit_duration_minutes,
            travel_time_to_next_minutes=travel_time_to_next_minutes,
            travel_leg=travel_leg,
            notes=notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(item)
        await self.session.flush()
        return item
    
    async def get_trip_itinerary(
        self,
        trip_id: str,
        day_number: Optional[int] = None
    ) -> List[ItineraryItem]:
        """Get itinerary for a trip."""
        query = (
            select(ItineraryItem)
            .where(ItineraryItem.trip_id == trip_id)
            .options(selectinload(ItineraryItem.poi))
        )
        
        if day_number is not None:
            query = query.where(ItineraryItem.day_number == day_number)
        
        query = query.order_by(
            ItineraryItem.day_number,
            ItineraryItem.sequence_order
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def delete_trip_itinerary(self, trip_id: str) -> int:
        """Delete all itinerary items for a trip."""
        result = await self.session.execute(
            delete(ItineraryItem).where(ItineraryItem.trip_id == trip_id)
        )
        await self.session.flush()
        logger.info(f"Deleted itinerary for trip: {trip_id}")
        return result.rowcount
    
    async def update_itinerary_item(
        self,
        item_id: int,
        **updates
    ) -> Optional[ItineraryItem]:
        """Update an itinerary item."""
        result = await self.session.execute(
            select(ItineraryItem).where(ItineraryItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if item:
            for key, value in updates.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            item.updated_at = datetime.utcnow()
            await self.session.flush()
        
        return item
    
    # ==================== Analytics Operations ====================
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user."""
        # Count trips by status
        result = await self.session.execute(
            select(Trip.status, select([Trip.id]).count().label("count"))
            .where(Trip.user_id == user_id)
            .group_by(Trip.status)
        )
        
        stats = {
            "total_trips": 0,
            "trips_by_status": {},
            "destinations_visited": []
        }
        
        trips = await self.get_user_trips(user_id, limit=1000)
        stats["total_trips"] = len(trips)
        
        for trip in trips:
            status = trip.status
            stats["trips_by_status"][status] = stats["trips_by_status"].get(status, 0) + 1
            if trip.status in ["completed", "booked"]:
                stats["destinations_visited"].append(trip.destination)
        
        return stats
    
    async def get_popular_pois(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most popular POIs based on user selections."""
        result = await self.session.execute(
            select(
                POI,
                select([TripPOI.poi_id]).where(TripPOI.user_selected == True).count().label("selection_count")
            )
            .join(TripPOI, POI.id == TripPOI.poi_id, isouter=True)
            .group_by(POI.id)
            .order_by(select([TripPOI.poi_id]).where(TripPOI.user_selected == True).count().desc())
            .limit(limit)
        )
        
        popular_pois = []
        for row in result:
            poi, count = row
            popular_pois.append({
                "poi": poi,
                "selection_count": count or 0
            })
        
        return popular_pois


# Convenience function to get database service
def get_database_service(session: AsyncSession) -> DatabaseService:
    """Get a DatabaseService instance with the given session."""
    return DatabaseService(session)





