"""Tests for the itinerary optimizer service."""

import pytest
from app.services.optimizer import ItineraryOptimizer


class TestItineraryOptimizer:
    """Tests for OR-Tools based itinerary optimization."""
    
    @pytest.fixture
    def optimizer(self):
        """Create an optimizer instance."""
        return ItineraryOptimizer()
    
    @pytest.fixture
    def sample_pois(self):
        """Sample POIs for testing."""
        return [
            {
                'name': 'Hotel',
                'poi_id': 'hotel_1',
                'time_to_visit_minutes': 0,  # No time needed at hotel
                'opening_time': 0,  # Always open
                'closing_time': 24 * 3600
            },
            {
                'name': 'Louvre Museum',
                'poi_id': 'louvre_1',
                'time_to_visit_minutes': 120,  # 2 hours
                'opening_time': 9 * 3600,  # 9 AM
                'closing_time': 18 * 3600  # 6 PM
            },
            {
                'name': 'Eiffel Tower',
                'poi_id': 'eiffel_1',
                'time_to_visit_minutes': 90,  # 1.5 hours
                'opening_time': 9 * 3600,  # 9 AM
                'closing_time': 23 * 3600  # 11 PM
            },
            {
                'name': 'Notre Dame',
                'poi_id': 'notredame_1',
                'time_to_visit_minutes': 60,  # 1 hour
                'opening_time': 8 * 3600,  # 8 AM
                'closing_time': 19 * 3600  # 7 PM
            },
            {
                'name': 'Lunch Restaurant',
                'poi_id': 'restaurant_1',
                'time_to_visit_minutes': 75,  # 1.25 hours
                'opening_time': 12 * 3600,  # 12 PM
                'closing_time': 14 * 3600  # 2 PM
            }
        ]
    
    @pytest.fixture
    def sample_travel_matrix(self):
        """
        Sample travel time matrix (seconds).
        
        Represents travel times between:
        [Hotel, Louvre, Eiffel, Notre Dame, Restaurant]
        """
        return [
            [0, 900, 1200, 600, 1500],      # From Hotel
            [900, 0, 1800, 300, 600],       # From Louvre
            [1200, 1800, 0, 1500, 900],     # From Eiffel
            [600, 300, 1500, 0, 450],       # From Notre Dame
            [1500, 600, 900, 450, 0]        # From Restaurant
        ]
    
    def test_optimizer_initialization(self, optimizer):
        """Test that optimizer initializes correctly."""
        assert optimizer is not None
        assert optimizer.solution_time_limit_seconds == 30
    
    def test_optimize_simple_itinerary(self, optimizer, sample_pois, sample_travel_matrix):
        """Test optimization of a simple day itinerary."""
        result = optimizer.optimize_day_itinerary(
            pois=sample_pois,
            travel_time_matrix=sample_travel_matrix,
            start_location_idx=0,  # Start at hotel
            day_start_time=9 * 3600,  # 9 AM
            day_end_time=22 * 3600  # 10 PM
        )
        
        assert result is not None, "Optimizer should find a solution"
        assert result['success'] is True
        assert 'route' in result
        assert 'schedule' in result
        assert len(result['route']) == len(sample_pois)
        assert result['route'][0] == 0, "Should start at hotel (index 0)"
    
    def test_schedule_respects_time_windows(self, optimizer, sample_pois, sample_travel_matrix):
        """Test that the optimized schedule respects POI opening hours."""
        result = optimizer.optimize_day_itinerary(
            pois=sample_pois,
            travel_time_matrix=sample_travel_matrix,
            start_location_idx=0
        )
        
        assert result is not None
        
        # Check each scheduled item
        for item in result['schedule']:
            poi_idx = item['index']
            poi = sample_pois[poi_idx]
            
            arrival_sec = item['arrival_time_seconds']
            departure_sec = item['departure_time_seconds']
            
            # Arrival should be after opening time
            if 'opening_time' in poi:
                assert arrival_sec >= poi['opening_time'], \
                    f"{poi['name']} arrival {item['arrival_time']} before opening"
            
            # Departure should be before closing time
            if 'closing_time' in poi:
                assert departure_sec <= poi['closing_time'], \
                    f"{poi['name']} departure {item['departure_time']} after closing"
    
    def test_schedule_includes_travel_times(self, optimizer, sample_pois, sample_travel_matrix):
        """Test that schedule includes travel time information."""
        result = optimizer.optimize_day_itinerary(
            pois=sample_pois,
            travel_time_matrix=sample_travel_matrix,
            start_location_idx=0
        )
        
        assert result is not None
        assert result['total_travel_time_minutes'] > 0, "Should have some travel time"
        
        # Check that travel times are included in schedule
        for i, item in enumerate(result['schedule'][:-1]):  # All except last
            assert 'travel_to_next_minutes' in item, f"Item {i} should have travel time to next"
            assert item['travel_to_next_minutes'] >= 0
    
    def test_insufficient_pois_returns_none(self, optimizer, sample_travel_matrix):
        """Test that optimizer returns None with too few POIs."""
        single_poi = [{
            'name': 'Hotel',
            'poi_id': 'hotel_1',
            'time_to_visit_minutes': 0
        }]
        
        result = optimizer.optimize_day_itinerary(
            pois=single_poi,
            travel_time_matrix=[[0]],
            start_location_idx=0
        )
        
        assert result is None, "Should return None with only 1 POI"
    
    def test_mismatched_matrix_size_returns_none(self, optimizer, sample_pois):
        """Test that optimizer handles mismatched matrix size."""
        wrong_matrix = [[0, 100], [100, 0]]  # 2x2 matrix for 5 POIs
        
        result = optimizer.optimize_day_itinerary(
            pois=sample_pois,
            travel_time_matrix=wrong_matrix,
            start_location_idx=0
        )
        
        assert result is None, "Should return None with mismatched matrix"
    
    def test_time_string_conversion(self, optimizer):
        """Test time string conversion utilities."""
        # Test seconds to time string
        assert optimizer._seconds_to_time_string(0) == "00:00"
        assert optimizer._seconds_to_time_string(9 * 3600) == "09:00"
        assert optimizer._seconds_to_time_string(14 * 3600 + 30 * 60) == "14:30"
        assert optimizer._seconds_to_time_string(23 * 3600 + 59 * 60) == "23:59"
        
        # Test time string to seconds
        assert optimizer.seconds_from_time_string("00:00") == 0
        assert optimizer.seconds_from_time_string("09:00") == 9 * 3600
        assert optimizer.seconds_from_time_string("14:30") == 14 * 3600 + 30 * 60
        assert optimizer.seconds_from_time_string("23:59") == 23 * 3600 + 59 * 60
    
    def test_realistic_paris_itinerary(self, optimizer):
        """Test with a realistic Paris day trip scenario."""
        paris_pois = [
            {
                'name': 'Hotel in Le Marais',
                'poi_id': 'hotel_marais',
                'time_to_visit_minutes': 0,
                'opening_time': 0,
                'closing_time': 24 * 3600
            },
            {
                'name': 'Louvre Museum',
                'poi_id': 'louvre',
                'time_to_visit_minutes': 180,  # 3 hours
                'opening_time': 9 * 3600,
                'closing_time': 18 * 3600
            },
            {
                'name': 'Lunch at Café',
                'poi_id': 'cafe_lunch',
                'time_to_visit_minutes': 60,
                'opening_time': 12 * 3600,
                'closing_time': 15 * 3600
            },
            {
                'name': 'Eiffel Tower',
                'poi_id': 'eiffel',
                'time_to_visit_minutes': 120,  # 2 hours
                'opening_time': 9 * 3600,
                'closing_time': 23 * 3600
            },
            {
                'name': 'Seine River Cruise',
                'poi_id': 'seine_cruise',
                'time_to_visit_minutes': 90,
                'opening_time': 10 * 3600,
                'closing_time': 22 * 3600
            }
        ]
        
        # Realistic Paris travel times (in seconds)
        travel_matrix = [
            [0, 1200, 600, 1800, 900],      # From Hotel
            [1200, 0, 800, 2400, 1500],     # From Louvre
            [600, 800, 0, 1200, 600],       # From Café
            [1800, 2400, 1200, 0, 300],     # From Eiffel
            [900, 1500, 600, 300, 0]        # From Cruise
        ]
        
        result = optimizer.optimize_day_itinerary(
            pois=paris_pois,
            travel_time_matrix=travel_matrix,
            start_location_idx=0,
            day_start_time=8 * 3600,  # Start at 8 AM
            day_end_time=23 * 3600   # End by 11 PM
        )
        
        assert result is not None, "Should find solution for realistic Paris itinerary"
        assert result['success'] is True
        
        # Verify lunch happens during lunch hours
        lunch_scheduled = False
        for item in result['schedule']:
            if item['poi_id'] == 'cafe_lunch':
                lunch_scheduled = True
                # Lunch should start between 12 PM and 3 PM
                assert 12 * 3600 <= item['arrival_time_seconds'] <= 15 * 3600, \
                    f"Lunch scheduled at {item['arrival_time']}, should be 12:00-15:00"
        
        assert lunch_scheduled, "Lunch should be in the schedule"
        
        print("\n=== Optimized Paris Itinerary ===")
        for item in result['schedule']:
            print(f"{item['arrival_time']} - {item['departure_time']}: {item['name']} "
                  f"({item['visit_duration_minutes']} min)")
            if 'travel_to_next_minutes' in item:
                print(f"  → Travel {item['travel_to_next_minutes']} min to next location")
        print(f"\nTotal travel time: {result['total_travel_time_minutes']} minutes")
        print(f"Total visit time: {result['total_visit_time_minutes']} minutes")
        print(f"Day ends at: {result['day_end_time']}")









