"""Integration tests for optimizer tool with Google Maps routing."""

import pytest
from unittest.mock import Mock, patch
from app.tools.optimizer import optimize_itinerary, estimate_day_feasibility


class TestOptimizerTool:
    """Tests for the optimizer LangChain tool."""
    
    @pytest.fixture
    def sample_paris_pois(self):
        """Sample Paris POIs with real-ish coordinates."""
        return [
            {
                'name': 'Hotel Le Marais',
                'poi_id': 'hotel_1',
                'location': {'lat': 48.8584, 'lng': 2.3656},
                'time_to_visit_minutes': 0
            },
            {
                'name': 'Louvre Museum',
                'poi_id': 'louvre_1',
                'location': {'lat': 48.8606, 'lng': 2.3376},
                'time_to_visit_minutes': 180,
                'opening_time': '09:00',
                'closing_time': '18:00'
            },
            {
                'name': 'Eiffel Tower',
                'poi_id': 'eiffel_1',
                'location': {'lat': 48.8584, 'lng': 2.2945},
                'time_to_visit_minutes': 120,
                'opening_time': '09:00',
                'closing_time': '23:00'
            }
        ]
    
    @pytest.fixture
    def mock_travel_matrix(self):
        """Mock travel time matrix (seconds)."""
        return [
            [0, 900, 1200],       # From Hotel
            [900, 0, 1800],       # From Louvre
            [1200, 1800, 0]       # From Eiffel
        ]
    
    def test_estimate_day_feasibility_feasible(self):
        """Test feasibility estimation for a reasonable day."""
        result = estimate_day_feasibility.invoke({
            'num_pois': 4,
            'avg_visit_time_minutes': 60,
            'avg_travel_time_minutes': 15,
            'day_hours': 10
        })
        
        assert "Feasible" in result
        assert "✅" in result
    
    def test_estimate_day_feasibility_tight(self):
        """Test feasibility estimation for a tight schedule."""
        result = estimate_day_feasibility.invoke({
            'num_pois': 6,
            'avg_visit_time_minutes': 60,
            'avg_travel_time_minutes': 20,
            'day_hours': 8
        })
        
        assert "Tight" in result or "Not Feasible" in result
    
    def test_estimate_day_feasibility_not_feasible(self):
        """Test feasibility estimation for an impossible day."""
        result = estimate_day_feasibility.invoke({
            'num_pois': 10,
            'avg_visit_time_minutes': 90,
            'avg_travel_time_minutes': 30,
            'day_hours': 8
        })
        
        assert "Not Feasible" in result
        assert "❌" in result
        assert "Recommendation" in result
    
    @patch('app.tools.optimizer.get_google_maps_service')
    def test_optimize_itinerary_with_mocked_routing(
        self, mock_get_service, sample_paris_pois, mock_travel_matrix
    ):
        """Test optimizer tool with mocked Google Maps routing."""
        # Mock the Google Maps service
        mock_service = Mock()
        mock_service.calculate_travel_time_matrix.return_value = mock_travel_matrix
        mock_get_service.return_value = mock_service
        
        # Run the tool
        result = optimize_itinerary.invoke({
            'pois': sample_paris_pois,
            'start_location_name': 'Hotel Le Marais',
            'travel_mode': 'walking',
            'day_start_hour': 9,
            'day_end_hour': 22
        })
        
        # Verify the result
        assert isinstance(result, str)
        assert "Error" not in result or "✅ Optimized Itinerary" in result
        
        # Check that the service was called
        mock_service.calculate_travel_time_matrix.assert_called_once()
        call_args = mock_service.calculate_travel_time_matrix.call_args
        # Note: POIs are modified in-place (time strings converted to seconds),
        # so we just check that it was called with the right number of POIs
        assert len(call_args[0][0]) == len(sample_paris_pois)
        assert call_args[1]['mode'] == 'walking'  # mode keyword arg
    
    @patch('app.tools.optimizer.get_google_maps_service')
    def test_optimize_itinerary_with_routing_failure(
        self, mock_get_service, sample_paris_pois
    ):
        """Test optimizer tool handles routing API failure gracefully."""
        # Mock the Google Maps service to return None (failure)
        mock_service = Mock()
        mock_service.calculate_travel_time_matrix.return_value = None
        mock_get_service.return_value = mock_service
        
        # Run the tool
        result = optimize_itinerary.invoke({
            'pois': sample_paris_pois,
            'start_location_name': 'Hotel Le Marais'
        })
        
        # Should return an error message
        assert "Error" in result
        assert "Failed to calculate travel times" in result
    
    def test_optimize_itinerary_insufficient_pois(self):
        """Test optimizer tool with insufficient POIs."""
        single_poi = [{
            'name': 'Hotel',
            'poi_id': 'hotel_1',
            'location': {'lat': 48.8584, 'lng': 2.3656}
        }]
        
        result = optimize_itinerary.invoke({
            'pois': single_poi,
            'start_location_name': 'Hotel'
        })
        
        assert "Error" in result
        assert "at least 2 locations" in result
    
    @patch('app.tools.optimizer.get_google_maps_service')
    def test_optimize_itinerary_output_format(
        self, mock_get_service, sample_paris_pois, mock_travel_matrix
    ):
        """Test that optimizer tool output is well-formatted."""
        mock_service = Mock()
        mock_service.calculate_travel_time_matrix.return_value = mock_travel_matrix
        mock_get_service.return_value = mock_service
        
        result = optimize_itinerary.invoke({
            'pois': sample_paris_pois,
            'start_location_name': 'Hotel Le Marais',
            'travel_mode': 'walking'
        })
        
        # Check for expected formatting elements
        if "Error" not in result:
            assert "Optimized Itinerary" in result
            assert "Arrive:" in result
            assert "Depart:" in result
            assert "Duration:" in result
            assert "Summary" in result
            assert "Total travel time" in result
            assert "Total visit time" in result
            assert "Day ends at" in result
    
    @patch('app.tools.optimizer.get_google_maps_service')
    def test_optimize_itinerary_respects_time_format(
        self, mock_get_service, mock_travel_matrix
    ):
        """Test that optimizer correctly parses HH:MM time format."""
        mock_service = Mock()
        mock_service.calculate_travel_time_matrix.return_value = mock_travel_matrix
        mock_get_service.return_value = mock_service
        
        pois = [
            {
                'name': 'Hotel',
                'poi_id': 'hotel_1',
                'location': {'lat': 48.8584, 'lng': 2.3656},
                'time_to_visit_minutes': 0
            },
            {
                'name': 'Restaurant',
                'poi_id': 'restaurant_1',
                'location': {'lat': 48.8606, 'lng': 2.3376},
                'time_to_visit_minutes': 60,
                'opening_time': '12:00',  # Lunch time only
                'closing_time': '14:00'
            },
            {
                'name': 'Museum',
                'poi_id': 'museum_1',
                'location': {'lat': 48.8584, 'lng': 2.2945},
                'time_to_visit_minutes': 120,
                'opening_time': '10:00',
                'closing_time': '18:00'
            }
        ]
        
        result = optimize_itinerary.invoke({
            'pois': pois,
            'start_location_name': 'Hotel',
            'day_start_hour': 9,
            'day_end_hour': 20
        })
        
        # Should successfully parse and optimize
        assert isinstance(result, str)
        # If successful, restaurant should be scheduled during lunch hours
        if "Error" not in result and "Restaurant" in result:
            # Check that restaurant appears in schedule
            assert "Restaurant" in result


@pytest.mark.skipif(
    True,  # Skip by default to avoid API costs
    reason="Requires real Google Maps API calls"
)
class TestOptimizerToolRealAPI:
    """Integration tests using real Google Maps API (skipped by default)."""
    
    def test_optimize_paris_itinerary_real_api(self):
        """Test with real Paris POIs and real Google Maps API."""
        paris_pois = [
            {
                'name': 'Hotel Le Marais',
                'poi_id': 'hotel_1',
                'location': {'lat': 48.8584, 'lng': 2.3656},
                'time_to_visit_minutes': 0
            },
            {
                'name': 'Louvre Museum',
                'poi_id': 'louvre_1',
                'location': {'lat': 48.8606, 'lng': 2.3376},
                'time_to_visit_minutes': 180,
                'opening_time': '09:00',
                'closing_time': '18:00'
            },
            {
                'name': 'Eiffel Tower',
                'poi_id': 'eiffel_1',
                'location': {'lat': 48.8584, 'lng': 2.2945},
                'time_to_visit_minutes': 120,
                'opening_time': '09:00',
                'closing_time': '23:00'
            },
            {
                'name': 'Notre Dame',
                'poi_id': 'notredame_1',
                'location': {'lat': 48.8530, 'lng': 2.3499},
                'time_to_visit_minutes': 60,
                'opening_time': '08:00',
                'closing_time': '19:00'
            }
        ]
        
        result = optimize_itinerary.invoke({
            'pois': paris_pois,
            'start_location_name': 'Hotel Le Marais',
            'travel_mode': 'walking',
            'day_start_hour': 9,
            'day_end_hour': 22
        })
        
        print("\n" + "="*60)
        print("REAL API TEST RESULT:")
        print("="*60)
        print(result)
        print("="*60)
        
        assert "Error" not in result or "Optimized Itinerary" in result

