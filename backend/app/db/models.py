"""
SQLAlchemy Database Models for Phase 2.2
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model for authentication and preferences."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)  # UUID
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # User preferences stored as JSON
    preferences = Column(JSON, nullable=True)
    # {
    #     "budget": "moderate",
    #     "favorite_categories": ["museums", "food"],
    #     "avoid": ["crowded_places"],
    #     "dietary": ["vegetarian"]
    # }
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Trip(Base):
    """Trip model for storing user's travel plans."""
    __tablename__ = "trips"
    
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Trip constraints (from Intake Agent)
    destination = Column(String(255), nullable=False)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)
    
    constraints = Column(JSON, nullable=True)
    # {
    #     "budget": "moderate",
    #     "vibe": "cultural",
    #     "must_see": ["temples", "museums"],
    #     "dates": {"start": "2025-11-01", "end": "2025-11-05"}
    # }
    
    # Trip status
    status = Column(String(50), default="planning", nullable=False)
    # Status: "planning", "optimized", "booked", "completed", "cancelled"
    
    current_stage = Column(String(50), nullable=True)
    # LangGraph stage: "intake_complete", "discovery_complete", "optimization_complete"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="trips")
    itinerary_items = relationship("ItineraryItem", back_populates="trip", cascade="all, delete-orphan")
    trip_pois = relationship("TripPOI", back_populates="trip", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Trip(id={self.id}, destination={self.destination}, status={self.status})>"


class POI(Base):
    """POI model for caching place details."""
    __tablename__ = "pois"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    place_id = Column(String(255), unique=True, nullable=False, index=True)  # Google Places ID
    
    # Basic info
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # "museum", "restaurant", "temple", etc.
    formatted_address = Column(Text, nullable=True)
    
    # Location
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    
    # Quality metrics
    rating = Column(Float, nullable=True)
    user_ratings_total = Column(Integer, nullable=True)
    price_level = Column(Integer, nullable=True)  # 0-4
    
    # Details (cached from Google Places API)
    details = Column(JSON, nullable=True)
    # {
    #     "opening_hours": {...},
    #     "website": "...",
    #     "phone": "...",
    #     "reviews": [...]
    # }
    
    # Embedding for semantic search (stored as JSON array)
    embedding = Column(JSON, nullable=True)
    
    # Cache management
    cached_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    cache_expires_at = Column(DateTime, nullable=True)  # TTL for cache invalidation
    
    # Relationships
    trip_pois = relationship("TripPOI", back_populates="poi")
    
    def __repr__(self):
        return f"<POI(id={self.id}, name={self.name}, place_id={self.place_id})>"


class TripPOI(Base):
    """Many-to-many relationship between Trips and POIs with additional context."""
    __tablename__ = "trip_pois"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    poi_id = Column(Integer, ForeignKey("pois.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Discovery context
    ai_score = Column(Float, nullable=True)  # Score from Discovery Agent
    score_breakdown = Column(JSON, nullable=True)  # {"quality": 90, "popularity": 85, ...}
    recommendation_reason = Column(Text, nullable=True)
    
    # User interaction
    user_selected = Column(Boolean, default=False, nullable=False)
    user_rejected = Column(Boolean, default=False, nullable=False)
    user_notes = Column(Text, nullable=True)
    
    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    trip = relationship("Trip", back_populates="trip_pois")
    poi = relationship("POI", back_populates="trip_pois")
    
    def __repr__(self):
        return f"<TripPOI(trip_id={self.trip_id}, poi_id={self.poi_id}, ai_score={self.ai_score})>"


class ItineraryItem(Base):
    """Optimized itinerary items (scheduled POIs)."""
    __tablename__ = "itinerary_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    poi_id = Column(Integer, ForeignKey("pois.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Schedule
    day_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    sequence_order = Column(Integer, nullable=False)  # Order within the day
    
    start_time = Column(String(10), nullable=False)  # "HH:MM"
    end_time = Column(String(10), nullable=False)    # "HH:MM"
    
    visit_duration_minutes = Column(Integer, nullable=True)
    travel_time_to_next_minutes = Column(Integer, nullable=True)
    
    # Travel leg details
    travel_leg = Column(JSON, nullable=True)
    # {
    #     "mode": "walking",
    #     "distance_meters": 1200,
    #     "duration_seconds": 900,
    #     "instructions": [...]
    # }
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    trip = relationship("Trip", back_populates="itinerary_items")
    poi = relationship("POI")
    
    def __repr__(self):
        return f"<ItineraryItem(trip_id={self.trip_id}, day={self.day_number}, order={self.sequence_order})>"

















