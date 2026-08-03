import logging
import json
from typing import Dict, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings

logger = logging.getLogger(__name__)

class QueryGenerator:
    """
    Generates optimized search queries for Google Places API based on user constraints.
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0.3,
            response_mime_type="application/json"
        )
        
    async def generate_queries(
        self, 
        category: str, 
        destination: str, 
        constraints: Dict
    ) -> Dict[str, str]:
        """
        Generate primary and fallback search queries.
        
        Args:
            category: "dining", "activities", "entertainment", etc.
            destination: Target city/location
            constraints: User preferences (vibe, budget, companions, etc.)
            
        Returns:
            Dict with 'primary_query' and 'fallback_query'
        """
        vibe = constraints.get("vibe", "balanced")
        companions = constraints.get("travelers", 1)
        budget = constraints.get("budget", "moderate")
        interests = constraints.get("interests", [])
        
        system_prompt = """You are an expert travel assistant. Your task is to generate Google Maps search queries to find the best places for a user.
        
        You will be given a category (e.g., dining, activities), a destination, and user preferences.
        
        Output a JSON object with two fields:
        1. 'primary_query': A specific, descriptive query that targets the user's specific vibe and preferences.
           - Example: "romantic candlelight dinner italian restaurant in Manali"
           - Example: "adventure sports paragliding in Manali"
        2. 'fallback_query': A broad, safe query to ensure we get results if the specific one fails.
           - Example: "top rated restaurants in Manali"
           - Example: "tourist attractions in Manali"
           
        Keep queries concise (under 10 words) for best Google Maps performance.
        """
        
        user_prompt = f"""
        Category: {category}
        Destination: {destination}
        Vibe: {vibe}
        Budget: {budget}
        Interests: {interests}
        Travelers: {companions}
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            result = json.loads(response.content)
            logger.info(f"Generated queries for {category} in {destination}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating queries: {e}")
            # Return safe defaults if LLM fails
            return {
                "primary_query": f"top {category} in {destination}",
                "fallback_query": f"{category} in {destination}"
            }
