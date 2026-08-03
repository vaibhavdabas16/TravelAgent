"""Intake Agent - Extracts structured trip constraints from user input using Gemini."""
import logging
from typing import Optional

from app.services.gemini import get_gemini_service
from app.models.state import TripConstraints

logger = logging.getLogger(__name__)


INTAKE_SYSTEM_PROMPT = """You are the Intake Agent for an intelligent travel planning system.

Your task: Extract structured trip constraints from the user's natural language input.

Return a JSON object with these keys (set to null if not mentioned):
- destination: string (city and/or country, be specific)
- arrival_date: string (YYYY-MM-DD format, null if not specified)
- departure_date: string (YYYY-MM-DD format, null if not specified)
- num_people: integer (number of travelers, null if not specified)
- budget: string (MUST be one of: "budget", "moderate", "luxury", null if not specified)
- vibe: string (travel style - examples: "relaxed", "adventurous", "cultural", "family", "romantic", "party", null if not specified)
- must_see: array of strings (specific places or types of places they want to see)
- avoid: array of strings (things to avoid - crowds, certain activities, etc.)
- dietary_prefs: array of strings (dietary restrictions or preferences)

Important rules:
1. For budget, ONLY use: "budget", "moderate", or "luxury". Infer from context if mentioned indirectly.
2. For vibe, pick the most relevant single word or short phrase that captures the travel style.
3. Always use proper city/country format for destination (e.g., "Paris, France" not just "Paris")
4. If dates are relative (e.g., "next month", "in June"), set them to null - don't guess specific dates.
5. Return ONLY valid JSON, no other text.

Examples:

User: "I want to visit Paris for 5 days in June with my partner, we love art"
Output:
{
  "destination": "Paris, France",
  "arrival_date": null,
  "departure_date": null,
  "num_people": 2,
  "budget": "moderate",
  "vibe": "cultural",
  "must_see": ["art museums", "galleries"],
  "avoid": [],
  "dietary_prefs": []
}

User: "Planning a budget backpacking trip to Thailand for 2 weeks, love beaches and street food"
Output:
{
  "destination": "Thailand",
  "arrival_date": null,
  "departure_date": null,
  "num_people": 1,
  "budget": "budget",
  "vibe": "adventurous",
  "must_see": ["beaches", "street food markets"],
  "avoid": [],
  "dietary_prefs": []
}

User: "Luxury honeymoon in Maldives from July 10-17, 2025, vegetarian food"
Output:
{
  "destination": "Maldives",
  "arrival_date": "2025-07-10",
  "departure_date": "2025-07-17",
  "num_people": 2,
  "budget": "luxury",
  "vibe": "romantic",
  "must_see": [],
  "avoid": [],
  "dietary_prefs": ["vegetarian"]
}

Now extract constraints from the user's message. Return ONLY the JSON object."""


def extract_constraints(user_message: str) -> Optional[TripConstraints]:
    """
    Intake Agent: Extract trip constraints from user message using Gemini.
    
    Args:
        user_message: Natural language trip description from user
        
    Returns:
        TripConstraints dict with extracted information, or None on error
    """
    try:
        gemini = get_gemini_service()
        
        # Create full prompt
        full_prompt = f"{INTAKE_SYSTEM_PROMPT}\n\nUser message: \"{user_message}\""
        
        # Generate structured output
        constraints = gemini.generate_structured(full_prompt, temperature=0.1)
        
        # Validate that we got the expected structure
        if not isinstance(constraints, dict):
            logger.error(f"Gemini returned non-dict response: {type(constraints)}")
            return None
        
        # Ensure arrays exist (even if empty)
        constraints.setdefault('must_see', [])
        constraints.setdefault('avoid', [])
        constraints.setdefault('dietary_prefs', [])
        
        # Log successful extraction
        destination = constraints.get('destination', 'Unknown')
        logger.info(f"Successfully extracted constraints for destination: {destination}")
        logger.debug(f"Full constraints: {constraints}")
        
        return constraints
        
    except ValueError as e:
        logger.error(f"JSON parsing error in Intake Agent: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in Intake Agent: {e}")
        return None


def refine_constraints(
    current_constraints: TripConstraints,
    additional_message: str
) -> Optional[TripConstraints]:
    """
    Refine existing constraints based on additional user input.
    
    Args:
        current_constraints: Existing trip constraints
        additional_message: New user message to incorporate
        
    Returns:
        Updated TripConstraints dict
    """
    try:
        gemini = get_gemini_service()
        
        refine_prompt = f"""You are updating trip constraints based on new user input.

Current constraints:
{current_constraints}

New user message: "{additional_message}"

Update the constraints JSON to incorporate the new information. Keep existing fields unless explicitly changed.
Return ONLY the updated JSON object with the same structure."""
        
        updated_constraints = gemini.generate_structured(refine_prompt, temperature=0.1)
        
        # Ensure arrays exist
        updated_constraints.setdefault('must_see', [])
        updated_constraints.setdefault('avoid', [])
        updated_constraints.setdefault('dietary_prefs', [])
        
        logger.info("Successfully refined trip constraints")
        return updated_constraints
        
    except Exception as e:
        logger.error(f"Error refining constraints: {e}")
        return current_constraints  # Return original on error






