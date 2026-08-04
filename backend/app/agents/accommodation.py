"""Accommodation Agent - LangGraph Node (Phase 2.3 - Week 4).

This agent is responsible for:
1. Searching for hotels using accommodation providers
2. Calculating location convenience scores (avg commute to POIs)
3. AI-powered analysis and recommendations
4. Integration with budget constraints
5. Providing top hotel recommendations

The agent uses the swappable provider architecture to support multiple
accommodation sources (Amadeus, SerpAPI, custom scrapers).
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import date, timedelta

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.models.state import TravelAgentState
from app.config import settings
from app.services.providers.accommodation.google_places import GooglePlacesHotelProvider
from app.services.providers.transport.google_routes import get_google_routes_provider
from app.services.providers.base import Hotel

logger = logging.getLogger(__name__)


class AccommodationAgent:
    """Agent for finding and recommending accommodations.
    
    Features:
    - Multi-provider hotel search
    - Location convenience scoring (avg commute to POIs)
    - Budget alignment analysis
    - AI-powered recommendations
    - Integration with trip state
    """
    
    def __init__(self):
        """Initialize the accommodation agent."""
        self.hotel_provider = GooglePlacesHotelProvider()
        self.route_provider = get_google_routes_provider()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0.7
        )
        logger.info("AccommodationAgent initialized")
    
    async def search_hotels(
        self,
        destination: str,
        checkin_date: date,
        checkout_date: date,
        num_guests: int,
        budget_preference: str,
        max_results: int = 20,
        location_coords: Optional[dict] = None,
        radius_km: int = 10
    ) -> List[Hotel]:
        """Search for hotels matching criteria.
        
        Args:
            destination: City code or name
            checkin_date: Check-in date
            checkout_date: Check-out date
            num_guests: Number of guests
            budget_preference: "budget", "moderate", or "luxury"
            max_results: Maximum number of results
            location_coords: Optional {"lat": float, "lng": float}
        
        Returns:
            List of Hotel objects
        """
        logger.info(f"Searching hotels in {destination} for {num_guests} guests")
        
        # Map budget to price filters
        budget_filters = {
            'budget': {'max_results': max_results, 'currency': 'USD'},
            'moderate': {'max_results': max_results, 'currency': 'USD'},
            'luxury': {'max_results': max_results, 'ratings': ['4', '5'], 'currency': 'USD'}
        }
        
        filters = budget_filters.get(budget_preference.lower(), budget_filters['moderate']).copy()
        filters['radius'] = radius_km
        
        hotels = await self.hotel_provider.search(
            destination=destination,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            num_guests=num_guests,
            filters=filters,
            location_coords=location_coords
        )
        
        logger.info(f"Found {len(hotels)} hotels")
        return hotels
    
    async def calculate_location_score(
        self,
        hotel: Hotel,
        pois: List[dict],
        preferred_transport_mode: str = "walking"
    ) -> float:
        """Calculate location convenience score (0-100).
        
        Based on average commute time to POIs.
        
        Args:
            hotel: Hotel object
            pois: List of POIs to visit
            preferred_transport_mode: Travel mode ("walking", "transit", "driving")
        
        Returns:
            Score from 0-100 (higher is better)
        """
        if not pois:
            return 50.0  # Neutral score if no POIs
        
        hotel_loc = {"lat": hotel.latitude, "lng": hotel.longitude}
        
        # Calculate travel times to all POIs
        travel_times = []
        for poi in pois[:10]:  # Limit to first 10 POIs for performance
            # POIs have lat/lng directly, not nested in 'location'
            poi_loc = {
                "lat": poi.get('lat', 0),
                "lng": poi.get('lng', 0)
            }
            
            route = await self.route_provider.get_route(
                origin=hotel_loc,
                destination=poi_loc,
                mode=preferred_transport_mode
            )
            
            if route:
                travel_times.append(route.duration_seconds)
            else:
                # Penalty for unreachable POI
                travel_times.append(3600)  # 1 hour
        
        if not travel_times:
            return 50.0
        
        # Calculate average commute time
        avg_time_minutes = (sum(travel_times) / len(travel_times)) / 60
        
        # Score based on average time
        # < 15 min: 90-100
        # 15-30 min: 70-90
        # 30-45 min: 50-70
        # 45-60 min: 30-50
        # > 60 min: 0-30
        
        if avg_time_minutes < 15:
            score = 90 + (15 - avg_time_minutes) / 15 * 10
        elif avg_time_minutes < 30:
            score = 70 + (30 - avg_time_minutes) / 15 * 20
        elif avg_time_minutes < 45:
            score = 50 + (45 - avg_time_minutes) / 15 * 20
        elif avg_time_minutes < 60:
            score = 30 + (60 - avg_time_minutes) / 15 * 20
        else:
            score = max(0, 30 - (avg_time_minutes - 60) / 30 * 30)
        
        # Store avg commute time in hotel object
        hotel.avg_commute_time_minutes = int(avg_time_minutes)
        
        logger.debug(f"Hotel {hotel.name}: avg commute {avg_time_minutes:.1f}m → score {score:.1f}")
        return min(100.0, max(0.0, score))
    
    async def calculate_price_value_score(
        self,
        hotel: Hotel,
        budget_preference: str,
        avg_price: float
    ) -> float:
        """Calculate price-value score (0-100).
        
        Considers both absolute price and price relative to budget.
        
        Args:
            hotel: Hotel object
            budget_preference: "budget", "moderate", or "luxury"
            avg_price: Average price of all hotels in search
        
        Returns:
            Score from 0-100 (higher is better value)
        """
        price = hotel.total_price
        
        # Budget target prices (per night)
        budget_targets = {
            'budget': 100,
            'moderate': 200,
            'luxury': 400
        }
        
        target = budget_targets.get(budget_preference.lower(), 200)
        price_per_night = hotel.price_per_night
        
        # Calculate deviation from target
        deviation_pct = abs(price_per_night - target) / target
        
        # Score based on deviation
        # Within 20%: 80-100
        # Within 50%: 60-80
        # Within 100%: 40-60
        # > 100%: 0-40
        
        if deviation_pct < 0.2:
            base_score = 80 + (0.2 - deviation_pct) / 0.2 * 20
        elif deviation_pct < 0.5:
            base_score = 60 + (0.5 - deviation_pct) / 0.3 * 20
        elif deviation_pct < 1.0:
            base_score = 40 + (1.0 - deviation_pct) / 0.5 * 20
        else:
            base_score = max(0, 40 - (deviation_pct - 1.0) * 20)
        
        # Bonus for below average price
        if price < avg_price:
            price_bonus = min(20, (avg_price - price) / avg_price * 20)
            base_score = min(100, base_score + price_bonus)
        
        return base_score
    
    async def calculate_overall_score(
        self,
        hotel: Hotel,
        location_score: float,
        price_value_score: float
    ) -> float:
        """Calculate overall AI score (0-100).
        
        Weighted combination of:
        - Location convenience (40%)
        - Price-value ratio (30%)
        - Hotel rating (20%)
        - Review count/popularity (10%)
        
        Args:
            hotel: Hotel object
            location_score: Location convenience score
            price_value_score: Price-value score
        
        Returns:
            Overall score from 0-100
        """
        # Rating score (0-100)
        rating_score = (hotel.rating / 5.0 * 100) if hotel.rating else 50.0
        
        # Popularity score (0-100) - logarithmic scale
        review_count = hotel.review_count or 0
        import math
        if review_count > 0:
            popularity_score = min(100, math.log10(review_count) / 4 * 100)
        else:
            popularity_score = 30  # Low score if no reviews
        
        # Weighted average
        overall_score = (
            location_score * 0.40 +
            price_value_score * 0.30 +
            rating_score * 0.20 +
            popularity_score * 0.10
        )
        
        hotel.ai_score = round(overall_score, 1)
        return overall_score
    
    async def generate_recommendations(
        self,
        hotels: List[Hotel],
        user_preferences: Dict[str, Any],
        budget_preference: str,
        num_recommendations: int = 3
    ) -> str:
        """Generate AI-powered hotel recommendations.
        
        Args:
            hotels: List of scored hotels
            user_preferences: User preferences dict
            budget_preference: Budget category
            num_recommendations: Number of hotels to recommend
        
        Returns:
            Formatted recommendation text
        """
        # Get top hotels
        top_hotels = sorted(hotels, key=lambda h: h.ai_score, reverse=True)[:num_recommendations]
        
        # Prepare context for LLM
        hotel_details = []
        for i, hotel in enumerate(top_hotels, 1):
            details = f"""
Hotel {i}: {hotel.name}
- Price: ${hotel.total_price:.2f} total (${hotel.price_per_night:.2f}/night)
- Rating: {hotel.rating or 'N/A'} stars
- Location Score: {hotel.ai_score:.1f}/100
- Avg Commute to Attractions: {hotel.avg_commute_time_minutes or 'N/A'} minutes
- Amenities: {', '.join(hotel.amenities[:5]) if hotel.amenities else 'Not listed'}
- Cancellation: {hotel.cancellation_policy or 'Check with hotel'}
"""
            hotel_details.append(details)
        
        system_prompt = f"""You are a travel expert helping users choose the best hotel for their trip.
The user has a {budget_preference} budget and these preferences: {user_preferences}.

Provide a brief, personalized recommendation for each hotel (2-3 sentences per hotel).
Focus on why each hotel is a good fit based on location, price, and amenities.
Be specific and helpful."""
        
        user_prompt = f"""Here are the top {num_recommendations} hotels I found:

{''.join(hotel_details)}

Please provide personalized recommendations for each hotel, highlighting their strengths."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            # Fallback to simple recommendations
            recs = []
            for i, hotel in enumerate(top_hotels, 1):
                recs.append(
                    f"{i}. **{hotel.name}** (${hotel.total_price:.2f}): "
                    f"Great location with {hotel.avg_commute_time_minutes or 'short'} min average commute. "
                    f"Rated {hotel.rating or 'well'}."
                )
            return "\n\n".join(recs)


async def accommodation_agent_node(state: TravelAgentState) -> Dict[str, Any]:
    """LangGraph node for accommodation recommendations.
    
    This node:
    1. Searches for hotels using accommodation providers
    2. Scores hotels based on location and price-value
    3. Generates AI recommendations
    4. Updates state with hotel recommendations
    
    Args:
        state: Current travel agent state
    
    Returns:
        State updates dict
    """
    logger.info("=" * 60)
    logger.info("ACCOMMODATION AGENT NODE")
    logger.info("=" * 60)
    
    agent = AccommodationAgent()
    
    try:
        # Extract info from state
        constraints = state.get('constraints') or {}
        destination = constraints.get('destination')
        budget = constraints.get('budget', 'moderate')
        num_days = constraints.get('num_days', 3)
        num_guests = constraints.get('num_travelers', 1)
        pois = state.get('potential_pois') or []
        destination_coords = state.get('destination_coords')  # Extract coords
        
        # Calculate dates (default: 2 weeks from now)
        checkin = date.today() + timedelta(days=14)
        checkout = checkin + timedelta(days=num_days)
        
        logger.info(f"Searching hotels for {destination}")
        if destination_coords:
            logger.info(f"Using coordinates: {destination_coords}")
            
        logger.info(f"Dates: {checkin} to {checkout} ({num_days} nights)")
        logger.info(f"Guests: {num_guests}, Budget: {budget}")
        
        # Step 1: Search for hotels
        hotels = await agent.search_hotels(
            destination=destination,
            checkin_date=checkin,
            checkout_date=checkout,
            num_guests=num_guests,
            budget_preference=budget,
            max_results=20,
            location_coords=destination_coords  # Pass coords
        )
        
        if not hotels:
            logger.info("No hotels found with default radius. Retrying with 50km radius at destination.")
            hotels = await agent.search_hotels(
                destination=destination,
                checkin_date=checkin,
                checkout_date=checkout,
                num_guests=num_guests,
                budget_preference=budget,
                max_results=20,
                location_coords=destination_coords,
                radius_km=50
            )

        if not hotels and pois:
            logger.info("No hotels found at destination. Attempting fallback search near top POI.")
            # Try to find a POI with coordinates
            fallback_coords = None
            fallback_poi_name = "Top POI"
            
            for poi in pois:
                if 'lat' in poi and 'lng' in poi:
                    fallback_coords = {'lat': poi['lat'], 'lng': poi['lng']}
                    fallback_poi_name = poi.get('name', 'Top POI')
                    break
            
            if fallback_coords:
                logger.info(f"Fallback search near {fallback_poi_name} ({fallback_coords}) with 50km radius")
                hotels = await agent.search_hotels(
                    destination=destination,
                    checkin_date=checkin,
                    checkout_date=checkout,
                    num_guests=num_guests,
                    budget_preference=budget,
                    max_results=20,
                    location_coords=fallback_coords,
                    radius_km=50
                )


        if not hotels:
            logger.warning("No hotels found")
            return {
                "messages": [f"⚠️ No hotels found in {destination}. Try different dates or location."],
                "recommended_hotels": [],
                "current_stage": "accommodation_complete"
            }
        
        logger.info(f"Found {len(hotels)} hotels, scoring them...")
        
        # Step 2: Calculate scores for each hotel
        avg_price = sum(h.total_price for h in hotels) / len(hotels)
        
        for hotel in hotels:
            # Location score
            location_score = await agent.calculate_location_score(
                hotel=hotel,
                pois=pois,
                preferred_transport_mode="walking"
            )
            
            # Price-value score
            price_value_score = await agent.calculate_price_value_score(
                hotel=hotel,
                budget_preference=budget,
                avg_price=avg_price
            )
            
            # Overall score
            await agent.calculate_overall_score(
                hotel=hotel,
                location_score=location_score,
                price_value_score=price_value_score
            )
        
        # Step 3: Sort by AI score
        hotels.sort(key=lambda h: h.ai_score, reverse=True)
        
        # Step 4: Generate recommendations
        logger.info("Generating AI recommendations...")
        recommendations_text = await agent.generate_recommendations(
            hotels=hotels,
            user_preferences=constraints.get('preferences', {}),
            budget_preference=budget,
            num_recommendations=3
        )
        
        # Step 5: Format results
        top_hotels = hotels[:3]
        summary = f"\n🏨 **Hotel Recommendations for {destination}**\n\n"
        
        for i, hotel in enumerate(top_hotels, 1):
            summary += f"**{i}. {hotel.name}**\n"
            summary += f"   💰 Price: ${hotel.total_price:.2f} (${hotel.price_per_night:.2f}/night)\n"
            summary += f"   ⭐ Rating: {hotel.rating or 'N/A'}\n"
            summary += f"   📍 Location Score: {hotel.ai_score:.1f}/100\n"
            if hotel.avg_commute_time_minutes:
                summary += f"   🚶 Avg Commute: {hotel.avg_commute_time_minutes} min\n"
            summary += f"\n"
        
        summary += f"\n**AI Analysis:**\n{recommendations_text}\n"
        
        logger.info(f"✅ Accommodation agent complete - {len(hotels)} hotels scored")
        
        return {
            "messages": [summary],
            "recommended_hotels": [h.__dict__ for h in top_hotels],  # Convert to dict for serialization
            "current_stage": "accommodation_complete"
        }
        
    except Exception as e:
        logger.error(f"Error in accommodation agent: {e}")
        import traceback
        traceback.print_exc()
        return {
            "messages": [f"❌ Error finding hotels: {str(e)}"],
            "errors": [f"accommodation_agent: {str(e)}"],
            "current_stage": "accommodation_complete"
        }

