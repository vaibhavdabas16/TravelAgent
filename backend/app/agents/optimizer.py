"""
Itinerary Optimizer Agent

Handles itinerary optimization with adaptive constraint handling.
If optimization fails, suggests adjustments (unless in strict mode).
"""

import logging
from typing import Dict, List, Optional
from app.models.state import TravelAgentState, ItineraryItem, OptimizationParameters, OptimizationSuggestion
from app.services.optimizer import ItineraryOptimizer
from app.services.google_maps import get_google_maps_service
from app.tools.optimizer import estimate_day_feasibility

logger = logging.getLogger(__name__)


def optimize_itinerary_node(state: TravelAgentState) -> Dict:
    """
    LangGraph node that optimizes the itinerary with adaptive constraint handling.
    
    Workflow:
    1. Check if we have enough POIs to optimize
    2. Try optimization with current parameters
    3. If fails and not strict_mode, generate suggestions
    4. Return optimized itinerary or suggestions
    
    Args:
        state: Current travel agent state
        
    Returns:
        State updates with itinerary or optimization suggestions
    """
    logger.info("=" * 70)
    logger.info("OPTIMIZER AGENT: Starting itinerary optimization")
    logger.info("=" * 70)
    
    # Get POIs
    potential_pois = state.get('potential_pois', [])
    if len(potential_pois) < 2:
        logger.warning("Not enough POIs to optimize (need at least 2)")
        return {
            'error_message': 'Need at least 2 locations to create an itinerary',
            'current_stage': 'optimization_failed'
        }
    
    # Get or set default optimization parameters
    opt_params = state.get('optimization_params')
    if not opt_params:
        opt_params = {
            'day_start_hour': 9,
            'day_end_hour': 22,
            'travel_mode': 'transit', # Changed from 'walking' to 'transit' as safer default
            'strict_mode': False,
            'optimization_goal': 'balanced'
        }
        logger.info(f"Using default optimization parameters: {opt_params}")
    else:
        logger.info(f"Using provided parameters: {opt_params}")
    
    # Track attempts
    attempts = state.get('optimization_attempts', 0)
    max_attempts = 3 if not opt_params.get('strict_mode') else 1
    
    logger.info(f"Optimization attempt {attempts + 1}/{max_attempts}")
    
    # Prepare POIs for optimizer
    pois_for_optimizer = _prepare_pois_for_optimization(potential_pois, state)
    
    logger.info(f"Prepared {len(pois_for_optimizer)} POIs for optimization")
    for poi in pois_for_optimizer:
        logger.info(f"  - {poi['name']}: {poi.get('time_to_visit_minutes', 60)} min")
    
    # Try optimization
    try:
        result = _run_optimization(pois_for_optimizer, opt_params)
        
        if result and result.get('success'):
            logger.info("✅ Optimization successful!")
            logger.info(f"   Route: {' → '.join([item['name'] for item in result['schedule']])}")
            logger.info(f"   Total time: {result['total_travel_time_minutes'] + result['total_visit_time_minutes']} min")
            
            # Convert to ItineraryItems
            itinerary = _convert_to_itinerary_items(result)
            
            return {
                'itinerary': itinerary,
                'optimization_params': opt_params,
                'optimization_attempts': attempts + 1,
                'optimization_suggestions': [],
                'current_stage': 'optimization_complete',
                'error_message': None
            }
        else:
            logger.warning("⚠️  Optimization failed")
            
            # If strict mode, return failure immediately
            if opt_params.get('strict_mode'):
                logger.info("Strict mode: returning failure without suggestions")
                return {
                    'error_message': 'Cannot create itinerary with current constraints (strict mode)',
                    'current_stage': 'optimization_failed',
                    'optimization_attempts': attempts + 1
                }
            
            # Generate suggestions
            logger.info("Generating constraint relaxation suggestions...")
            suggestions = _generate_suggestions(pois_for_optimizer, opt_params, state)
            
            if attempts + 1 < max_attempts and suggestions:
                # Try the best suggestion automatically
                best_suggestion = suggestions[0]
                logger.info(f"Trying suggestion: {best_suggestion['suggestion_type']}")
                
                new_params = _apply_suggestion(opt_params, best_suggestion)
                return {
                    'optimization_params': new_params,
                    'optimization_suggestions': suggestions,
                    'optimization_attempts': attempts + 1,
                    'current_stage': 'retrying_optimization'
                }
            else:
                # Max attempts reached, return suggestions to user
                logger.info(f"Max attempts reached, presenting {len(suggestions)} suggestions to user")
                return {
                    'optimization_suggestions': suggestions,
                    'optimization_attempts': attempts + 1,
                    'current_stage': 'needs_user_input_for_constraints',
                    'error_message': None
                }
                
    except Exception as e:
        logger.error(f"Error during optimization: {e}", exc_info=True)
        return {
            'error_message': f'Optimization error: {str(e)}',
            'current_stage': 'optimization_failed',
            'optimization_attempts': attempts + 1
        }


def _prepare_pois_for_optimization(potential_pois: List[Dict], state: TravelAgentState) -> List[Dict]:
    """
    Prepare POIs for the optimizer.
    
    - Adds location data
    - Sets time_to_visit if not present
    - Adds starting location (hotel) as first POI
    """
    prepared_pois = []
    
    # Add starting location (destination coords or first POI)
    dest_coords = state.get('destination_coords')
    if dest_coords:
        prepared_pois.append({
            'name': 'Starting Point',
            'poi_id': 'start',
            'location': {'lat': dest_coords['lat'], 'lng': dest_coords['lng']},
            'time_to_visit_minutes': 0
        })
    
    # Add POIs (limit for Distance Matrix API - max 100 elements)
    # Distance Matrix allows max 100 elements, so 10x10 = 100
    # Respect max_pois from params if set, otherwise default to 8
    max_pois = state.get('optimization_params', {}).get('max_pois', 8)
    max_pois = min(max_pois, 8)  # Never exceed 8 to stay within API limits
    
    for poi in potential_pois[:max_pois]:
        if poi.get('geometry') and poi['geometry'].get('location'):
            location = poi['geometry']['location']
        elif poi.get('lat') and poi.get('lng'):
            location = {'lat': poi['lat'], 'lng': poi['lng']}
        else:
            logger.warning(f"POI {poi.get('name')} has no location data, skipping")
            continue
        
        # Estimate time to visit based on type
        time_to_visit = poi.get('time_to_visit_minutes', 60)
        
        prepared_pois.append({
            'name': poi.get('name', 'Unknown'),
            'poi_id': poi.get('place_id', poi.get('poi_id', 'unknown')),
            'location': location,
            'time_to_visit_minutes': time_to_visit,
            'opening_time': poi.get('opening_time'),
            'closing_time': poi.get('closing_time')
        })
    
    return prepared_pois


def _run_optimization(pois: List[Dict], params: OptimizationParameters) -> Optional[Dict]:
    """Run the actual optimization."""
    maps_service = get_google_maps_service()
    optimizer_service = ItineraryOptimizer()
    
    # Calculate travel matrix
    logger.info(f"Calculating travel times ({params['travel_mode']})...")
    travel_matrix = maps_service.calculate_travel_time_matrix(pois, mode=params['travel_mode'])
    
    if not travel_matrix:
        logger.error("Failed to calculate travel matrix")
        return None
    
    # Convert time strings to seconds if present
    for poi in pois:
        if 'opening_time' in poi and isinstance(poi['opening_time'], str):
            poi['opening_time'] = optimizer_service.seconds_from_time_string(poi['opening_time'])
        if 'closing_time' in poi and isinstance(poi['closing_time'], str):
            poi['closing_time'] = optimizer_service.seconds_from_time_string(poi['closing_time'])
    
    # Run optimizer
    result = optimizer_service.optimize_day_itinerary(
        pois=pois,
        travel_time_matrix=travel_matrix,
        start_location_idx=0,
        day_start_time=params['day_start_hour'] * 3600,
        day_end_time=params['day_end_hour'] * 3600
    )
    
    return result


def _generate_suggestions(
    pois: List[Dict],
    params: OptimizationParameters,
    state: TravelAgentState
) -> List[OptimizationSuggestion]:
    """Generate suggestions for constraint relaxation."""
    suggestions = []
    
    # Calculate rough feasibility
    num_pois = len(pois) - 1  # Exclude starting point
    avg_visit = sum(poi.get('time_to_visit_minutes', 60) for poi in pois[1:]) / max(num_pois, 1)
    day_hours = params['day_end_hour'] - params['day_start_hour']
    
    # Suggestion 1: Extend day hours
    if day_hours < 14:
        new_start = max(6, params['day_start_hour'] - 2)
        new_end = min(23, params['day_end_hour'] + 2)
        suggestions.append({
            'suggestion_type': 'extend_hours',
            'original_value': f"{params['day_start_hour']}:00-{params['day_end_hour']}:00",
            'suggested_value': f"{new_start}:00-{new_end}:00",
            'reason': f"Extended day from {day_hours} to {new_end - new_start} hours allows more time",
            'feasibility_score': 0.8
        })
    
    # Suggestion 2: Reduce POIs  
    if num_pois > 4:
        suggested_pois = max(3, int(num_pois * 0.6))
        suggestions.append({
            'suggestion_type': 'reduce_pois',
            'original_value': f"{num_pois} locations",
            'suggested_value': f"{suggested_pois} locations",
            'reason': f"Visiting {suggested_pois} locations instead of {num_pois} makes the itinerary more feasible and enjoyable",
            'feasibility_score': 0.9
        })
    
    # Suggestion 3: Change travel mode
    if params['travel_mode'] == 'walking':
        suggestions.append({
            'suggestion_type': 'change_mode',
            'original_value': 'walking',
            'suggested_value': 'transit',
            'reason': 'Using public transit reduces travel time significantly',
            'feasibility_score': 0.7
        })
    
    # Sort by feasibility
    suggestions.sort(key=lambda s: s['feasibility_score'], reverse=True)
    
    return suggestions


def _apply_suggestion(params: OptimizationParameters, suggestion: OptimizationSuggestion) -> OptimizationParameters:
    """Apply a suggestion to the parameters."""
    new_params = params.copy()
    
    if suggestion['suggestion_type'] == 'extend_hours':
        # Parse suggested hours
        hours = suggestion['suggested_value'].split('-')
        new_params['day_start_hour'] = int(hours[0].split(':')[0])
        new_params['day_end_hour'] = int(hours[1].split(':')[0])
    elif suggestion['suggestion_type'] == 'change_mode':
        new_params['travel_mode'] = suggestion['suggested_value']
    elif suggestion['suggestion_type'] == 'reduce_pois':
        # Store the suggested POI limit for the next attempt
        try:
            suggested_count = int(suggestion['suggested_value'].split()[0])
            new_params['max_pois'] = suggested_count
        except:
            pass
    
    return new_params


def _convert_to_itinerary_items(result: Dict) -> List[ItineraryItem]:
    """Convert optimizer result to ItineraryItem list."""
    itinerary_items = []
    
    for item in result['schedule']:
        itinerary_items.append({
            'place_name': item['name'],
            'place_id': item.get('poi_id', 'unknown'),
            'address': item.get('address', ''),
            'start_time': item['arrival_time'],
            'end_time': item['departure_time'],
            'visit_duration_minutes': item.get('visit_duration_minutes', 0),
            'travel_time_to_next': item.get('travel_to_next_minutes'),
            'notes': None
        })
    
    return itinerary_items

