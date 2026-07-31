"""
Itinerary Optimization Service using Google OR-Tools.

This service solves the Vehicle Routing Problem with Time Windows (VRPTW)
to generate optimized day-by-day itineraries that respect:
- POI opening hours
- User-specified time constraints
- Travel times between locations
- Time spent at each location
"""

import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

logger = logging.getLogger(__name__)


class ItineraryOptimizer:
    """
    Optimizer for travel itineraries using OR-Tools VRPTW solver.
    
    Models the problem as a Vehicle Routing Problem with Time Windows where:
    - "Vehicle" = traveler's day
    - "Depot" = starting location (e.g., hotel)
    - "Locations" = POIs to visit
    - "Time Windows" = opening hours + user constraints
    """
    
    def __init__(self):
        """Initialize the optimizer."""
        self.solution_time_limit_seconds = 30  # Max time to find solution
        
    def optimize_day_itinerary(
        self,
        pois: List[Dict],
        travel_time_matrix: List[List[int]],
        start_location_idx: int = 0,
        day_start_time: int = 9 * 3600,  # 9 AM in seconds from midnight
        day_end_time: int = 22 * 3600,   # 10 PM in seconds from midnight
    ) -> Optional[Dict]:
        """
        Optimize an itinerary for a single day.
        
        Args:
            pois: List of POI dictionaries with:
                - name: str
                - poi_id: str
                - time_to_visit_minutes: int (estimated time at location)
                - opening_time: Optional[int] (seconds from midnight)
                - closing_time: Optional[int] (seconds from midnight)
            travel_time_matrix: NxN matrix of travel times in seconds
                where N = len(pois). Matrix[i][j] = travel time from POI i to j.
            start_location_idx: Index of starting location (usually hotel)
            day_start_time: Earliest start time in seconds from midnight
            day_end_time: Latest end time in seconds from midnight
            
        Returns:
            Dictionary with optimized itinerary or None if no solution found:
            {
                "route": List[int],  # Ordered indices of POIs to visit
                "schedule": List[Dict],  # Detailed schedule with times
                "total_travel_time_minutes": int,
                "total_visit_time_minutes": int,
                "day_end_time": int
            }
        """
        if not pois or len(pois) < 2:
            logger.warning("Need at least 2 POIs to optimize")
            return None
            
        if len(travel_time_matrix) != len(pois):
            logger.error(f"Travel matrix size {len(travel_time_matrix)} doesn't match POIs {len(pois)}")
            return None
            
        try:
            # Prepare data for OR-Tools
            data = self._create_data_model(
                pois, travel_time_matrix, start_location_idx,
                day_start_time, day_end_time
            )
            
            # Solve the problem
            manager, routing, solution = self._solve_vrptw(data)
            
            if solution is None:
                logger.warning("No solution found for itinerary optimization")
                return None
                
            # Format the solution
            result = self._format_solution(manager, routing, solution, pois, data)
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing itinerary: {e}", exc_info=True)
            return None
    
    def _create_data_model(
        self,
        pois: List[Dict],
        travel_time_matrix: List[List[int]],
        depot_idx: int,
        day_start: int,
        day_end: int
    ) -> Dict:
        """Create data model for OR-Tools solver."""
        data = {}
        data['time_matrix'] = travel_time_matrix
        data['num_vehicles'] = 1  # Single traveler
        data['depot'] = depot_idx
        
        # Service times (time spent at each location in seconds)
        data['service_times'] = [
            poi.get('time_to_visit_minutes', 60) * 60  # Default 1 hour
            for poi in pois
        ]
        
        # Time windows for each location
        time_windows = []
        for i, poi in enumerate(pois):
            if i == depot_idx:
                # Depot: can start anytime, must return by day_end
                time_windows.append((day_start, day_end))
            else:
                # Use POI's opening hours, or default to day hours
                opening = poi.get('opening_time')
                closing = poi.get('closing_time')
                
                # If no opening hours specified, use day boundaries
                if opening is None:
                    opening = day_start
                if closing is None:
                    closing = day_end
                
                # Ensure we can visit (close time - service time)
                latest_arrival = closing - data['service_times'][i]
                if latest_arrival < opening:
                    logger.warning(f"POI {poi['name']} has impossible time window")
                    latest_arrival = closing
                    
                time_windows.append((opening, latest_arrival))
                
        data['time_windows'] = time_windows
        
        return data
    
    def _solve_vrptw(self, data: Dict) -> Tuple:
        """
        Solve the VRPTW problem using OR-Tools.
        
        Returns:
            Tuple of (manager, routing, solution)
        """
        # Create routing index manager
        manager = pywrapcp.RoutingIndexManager(
            len(data['time_matrix']),
            data['num_vehicles'],
            data['depot']
        )
        
        # Create routing model
        routing = pywrapcp.RoutingModel(manager)
        
        # Define cost of each arc (travel time + service time)
        def time_callback(from_index, to_index):
            """Returns travel time + service time at from_node."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['time_matrix'][from_node][to_node] + data['service_times'][from_node]
        
        transit_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add time dimension with time windows
        time_dimension_name = 'Time'
        routing.AddDimension(
            transit_callback_index,
            30 * 60,  # Slack: 30 minutes waiting time allowed
            24 * 3600,  # Maximum time: 24 hours
            False,  # Don't force start cumul to zero
            time_dimension_name
        )
        time_dimension = routing.GetDimensionOrDie(time_dimension_name)
        
        # Add time window constraints for each location
        for location_idx, time_window in enumerate(data['time_windows']):
            if location_idx == data['depot']:
                continue
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
        
        # Add time window for depot (start/end)
        depot_idx = manager.NodeToIndex(data['depot'])
        time_dimension.CumulVar(depot_idx).SetRange(
            data['time_windows'][data['depot']][0],
            data['time_windows'][data['depot']][1]
        )
        
        # Minimize route end time
        for vehicle_id in range(data['num_vehicles']):
            routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(routing.Start(vehicle_id))
            )
            routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(routing.End(vehicle_id))
            )
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.time_limit.seconds = self.solution_time_limit_seconds
        
        # Solve
        solution = routing.SolveWithParameters(search_parameters)
        
        return manager, routing, solution
    
    def _format_solution(
        self,
        manager: pywrapcp.RoutingIndexManager,
        routing: pywrapcp.RoutingModel,
        solution: pywrapcp.Assignment,
        pois: List[Dict],
        data: Dict
    ) -> Dict:
        """Format the solution into a readable itinerary."""
        time_dimension = routing.GetDimensionOrDie('Time')
        
        route_indices = []
        schedule = []
        total_travel_time = 0
        total_visit_time = 0
        
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            time_var = time_dimension.CumulVar(index)
            arrival_time = solution.Min(time_var)
            departure_time = solution.Max(time_var)
            
            route_indices.append(node_index)
            
            poi = pois[node_index]
            # Get the actual service time (visit duration) from the data model
            visit_duration_seconds = data['service_times'][node_index]
            # Calculate when we actually depart (arrival + visit time)
            actual_departure = arrival_time + visit_duration_seconds
            
            schedule.append({
                'poi_id': poi.get('poi_id'),
                'name': poi.get('name'),
                'arrival_time': self._seconds_to_time_string(arrival_time),
                'departure_time': self._seconds_to_time_string(actual_departure),
                'arrival_time_seconds': arrival_time,
                'departure_time_seconds': actual_departure,
                'visit_duration_minutes': visit_duration_seconds // 60,
                'index': node_index
            })
            
            total_visit_time += visit_duration_seconds
            
            # Get travel time to next location
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            if not routing.IsEnd(index):
                from_node = manager.IndexToNode(previous_index)
                to_node = manager.IndexToNode(index)
                travel_time = data['time_matrix'][from_node][to_node]
                total_travel_time += travel_time
                schedule[-1]['travel_to_next_minutes'] = travel_time // 60
        
        # Handle final return to depot
        final_node = manager.IndexToNode(index)
        time_var = time_dimension.CumulVar(index)
        final_time = solution.Min(time_var)
        
        return {
            'route': route_indices,
            'schedule': schedule,
            'total_travel_time_minutes': total_travel_time // 60,
            'total_visit_time_minutes': total_visit_time // 60,
            'day_end_time': self._seconds_to_time_string(final_time),
            'day_end_time_seconds': final_time,
            'success': True
        }
    
    @staticmethod
    def _seconds_to_time_string(seconds: int) -> str:
        """Convert seconds from midnight to HH:MM format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    
    @staticmethod
    def seconds_from_time_string(time_str: str) -> int:
        """Convert HH:MM format to seconds from midnight."""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 3600 + minutes * 60
        except (ValueError, AttributeError):
            return 0

