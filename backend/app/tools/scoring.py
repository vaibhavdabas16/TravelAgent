"""POI scoring tool for LangGraph agents."""
import logging
from typing import Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def calculate_quality_score(rating: Optional[float]) -> float:
    """Calculate quality score from Google rating (0-5 scale)."""
    if rating is None or rating == 0:
        return 50.0  # Neutral score for unrated places
    # Convert 0-5 scale to 0-100 scale
    return (rating / 5.0) * 100


def calculate_popularity_score(review_count: int) -> float:
    """Calculate popularity score from number of reviews."""
    if review_count >= 5000:
        return 100.0
    elif review_count >= 1000:
        return 90.0
    elif review_count >= 500:
        return 80.0
    elif review_count >= 100:
        return 70.0
    elif review_count >= 50:
        return 60.0
    elif review_count >= 10:
        return 50.0
    else:
        return 40.0  # Few reviews


def calculate_price_fit_score(poi_price_level: Optional[int], budget_preference: str) -> float:
    """
    Calculate how well the place's price fits the user's budget.
    
    Args:
        poi_price_level: Google's price level (0=Free, 1=Inexpensive, 2=Moderate, 3=Expensive, 4=Very Expensive)
        budget_preference: User's budget ("budget", "moderate", "luxury")
    """
    if poi_price_level is None:
        return 75.0  # Neutral score if price unknown
    
    # Score matrix: how well each price level fits each budget preference
    score_matrix = {
        "budget": {0: 100, 1: 95, 2: 60, 3: 30, 4: 10},
        "moderate": {0: 85, 1: 90, 2: 100, 3: 85, 4: 60},
        "luxury": {0: 50, 1: 60, 2: 75, 3: 95, 4: 100}
    }
    
    if budget_preference is None:
        budget_lower = "moderate"
    else:
        budget_lower = budget_preference.lower()
        if budget_lower not in score_matrix:
            budget_lower = "moderate"  # Default
    
    return float(score_matrix[budget_lower].get(poi_price_level, 70))


def generate_recommendation_reason(poi: dict, score_breakdown: dict) -> str:
    """Generate human-readable recommendation reason."""
    reasons = []
    name = poi.get('name', 'This place')
    
    # Quality
    if score_breakdown.get('quality', 0) >= 85:
        rating = poi.get('rating')
        reasons.append(f"highly rated ({rating}/5.0)")
    elif score_breakdown.get('quality', 0) >= 70:
        reasons.append("well-reviewed")
    
    # Popularity
    review_count = poi.get('user_ratings_total', 0)
    if score_breakdown.get('popularity', 0) >= 90:
        reasons.append(f"very popular ({review_count:,} reviews)")
    elif score_breakdown.get('popularity', 0) >= 70:
        reasons.append("popular with travelers")
    
    # Price fit
    if score_breakdown.get('price_fit', 0) >= 90:
        reasons.append("great value for your budget")
    elif score_breakdown.get('price_fit', 0) >= 75:
        reasons.append("fits your budget")
    
    if reasons:
        return f"{name} is recommended because it's " + ", ".join(reasons) + "."
    else:
        return f"{name} is a good match for your preferences."


@tool
def score_poi(poi: dict, user_constraints: dict) -> dict:
    """
    Scores a Point of Interest based on multiple factors.
    
    Calculates an AI recommendation score (0-100) using a weighted combination of:
    - Quality score (based on rating)
    - Popularity score (based on review count)
    - Price fit score (how well it matches budget)
    
    Args:
        poi: Dictionary with POI data including:
            - rating: Google rating (0-5)
            - user_ratings_total: Number of reviews
            - price_level: Price indicator (0-4)
        user_constraints: Dictionary with user preferences including:
            - budget: "budget", "moderate", or "luxury"
    
    Returns:
        POI dict with added fields:
        - ai_score: Overall score (0-100)
        - score_breakdown: Individual component scores
        - recommendation_reason: Human-readable explanation
    
    Example:
        Input POI: {"name": "Louvre", "rating": 4.7, "user_ratings_total": 150000, "price_level": 2}
        User constraints: {"budget": "moderate"}
        Output: {..., "ai_score": 92.5, "score_breakdown": {...}, "recommendation_reason": "..."}
    """
    try:
        # Extract POI attributes
        rating = poi.get('rating')
        review_count = poi.get('user_ratings_total', 0)
        price_level = poi.get('price_level')
        
        # Extract user preferences
        budget_pref = user_constraints.get('budget', 'moderate')
        
        # Calculate individual scores
        quality = calculate_quality_score(rating)
        popularity = calculate_popularity_score(review_count)
        price_fit = calculate_price_fit_score(price_level, budget_pref)
        
        score_breakdown = {
            "quality": round(quality, 1),
            "popularity": round(popularity, 1),
            "price_fit": round(price_fit, 1)
        }
        
        # Define weights (must sum to 1.0)
        weights = {
            "quality": 0.4,      # 40% weight on rating
            "popularity": 0.3,   # 30% weight on popularity
            "price_fit": 0.3     # 30% weight on price fit
        }
        
        # Calculate weighted average
        ai_score = (
            score_breakdown["quality"] * weights["quality"] +
            score_breakdown["popularity"] * weights["popularity"] +
            score_breakdown["price_fit"] * weights["price_fit"]
        )
        
        # Generate human-readable reason
        recommendation_reason = generate_recommendation_reason(poi, score_breakdown)
        
        # Add scoring fields to POI
        poi['ai_score'] = round(ai_score, 1)
        poi['score_breakdown'] = score_breakdown
        poi['recommendation_reason'] = recommendation_reason
        
        logger.info(f"Scored POI '{poi.get('name')}': {ai_score:.1f}")
        
        return poi
        
    except Exception as e:
        logger.error(f"Error scoring POI: {e}")
        # Return POI with default score on error
        poi['ai_score'] = 50.0
        poi['score_breakdown'] = {"quality": 50.0, "popularity": 50.0, "price_fit": 50.0}
        poi['recommendation_reason'] = "Match for your preferences."
        return poi


@tool
def score_poi_list(pois: list[dict], user_constraints: dict) -> list[dict]:
    """
    Scores a list of POIs and sorts them by score.
    
    Args:
        pois: List of POI dictionaries
        user_constraints: User preferences for scoring
    
    Returns:
        List of scored POIs, sorted by ai_score (highest first)
    """
    try:
        scored_pois = []
        for poi in pois:
            scored = score_poi.invoke({"poi": poi, "user_constraints": user_constraints})
            scored_pois.append(scored)
        
        # Sort by AI score (highest first)
        scored_pois.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
        
        logger.info(f"Scored and sorted {len(scored_pois)} POIs")
        return scored_pois
        
    except Exception as e:
        logger.error(f"Error scoring POI list: {e}")
        return pois  # Return original list on error

