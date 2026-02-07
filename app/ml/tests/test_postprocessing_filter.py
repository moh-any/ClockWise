"""
Test the applied post-processing filter to verify the zero-demand bug is fixed
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.main import (
    zero_out_closed_hours,
    PlaceData,
    OpeningHoursDay
)


class TestPostProcessingFilter:
    """Test that the post-processing filter correctly fixes zero-demand bug"""
    
    def test_filter_zeros_out_closed_sunday(self):
        """Test filter zeros out all hours on closed Sunday"""
        place = PlaceData(
            place_id="test_123",
            place_name="Test Restaurant",
            type="restaurant",
            latitude=55.6761,
            longitude=12.5683,
            waiting_time=30,
            receiving_phone=True,
            delivery=True,
            opening_hours={
                "monday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "tuesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "wednesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "thursday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "friday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "saturday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "sunday": OpeningHoursDay(closed=True)
            },
            fixed_shifts=True,
            number_of_shifts_per_day=3,
            shift_times=["10:00-14:00", "14:00-18:00", "18:00-22:00"],
            rating=4.5,
            accepting_orders=True
        )
        
        # Simulate model predictions (phantom demand)
        predictions = np.array([[5, 2]] * 24)  # Model predicts 5 items, 2 orders per hour
        
        # Create datetime info for Sunday
        base_date = datetime(2024, 1, 14)  # Sunday
        datetime_info = pd.DataFrame({
            'datetime': [base_date + timedelta(hours=h) for h in range(24)],
            'date': [base_date.date()] * 24,
            'hour': list(range(24))
        })
        
        # Apply filter
        filtered = zero_out_closed_hours(predictions, datetime_info, place)
        
        # All predictions should be zero
        assert np.all(filtered[:, 0] == 0), "Some item predictions are non-zero on closed Sunday"
        assert np.all(filtered[:, 1] == 0), "Some order predictions are non-zero on closed Sunday"
        assert filtered.sum() == 0, "Total predictions should be zero on closed day"
    
    def test_filter_zeros_out_closed_hours(self):
        """Test filter zeros out hours outside operating hours"""
        place = PlaceData(
            place_id="test_123",
            place_name="Test Restaurant",
            type="restaurant",
            latitude=55.6761,
            longitude=12.5683,
            waiting_time=30,
            receiving_phone=True,
            delivery=True,
            opening_hours={
                "monday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "tuesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "wednesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "thursday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "friday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "saturday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "sunday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"})
            },
            fixed_shifts=True,
            number_of_shifts_per_day=3,
            shift_times=["10:00-14:00", "14:00-18:00", "18:00-22:00"],
            rating=4.5,
            accepting_orders=True
        )
        
        # Simulate model predictions
        predictions = np.array([[5, 2]] * 24)
        
        # Create datetime info for Monday
        base_date = datetime(2024, 1, 15)  # Monday
        datetime_info = pd.DataFrame({
            'datetime': [base_date + timedelta(hours=h) for h in range(24)],
            'date': [base_date.date()] * 24,
            'hour': list(range(24))
        })
        
        # Apply filter
        filtered = zero_out_closed_hours(predictions, datetime_info, place)
        
        # Hours 0-9 should be zero (closed)
        assert np.all(filtered[0:10, 0] == 0), "Early morning hours should be zero"
        assert np.all(filtered[0:10, 1] == 0), "Early morning hours should be zero"
        
        # Hours 22-23 should be zero (closed)
        assert np.all(filtered[22:24, 0] == 0), "Late night hours should be zero"
        assert np.all(filtered[22:24, 1] == 0), "Late night hours should be zero"
        
        # Hours 10-21 should be preserved (open)
        assert np.all(filtered[10:22, 0] > 0), "Open hours should have predictions"
        assert np.all(filtered[10:22, 1] > 0), "Open hours should have predictions"
    
    def test_filter_preserves_open_hours(self):
        """Test that filter doesn't change predictions during open hours"""
        place = PlaceData(
            place_id="test_123",
            place_name="Test Restaurant",
            type="restaurant",
            latitude=55.6761,
            longitude=12.5683,
            waiting_time=30,
            receiving_phone=True,
            delivery=True,
            opening_hours={
                "monday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "tuesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "wednesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "thursday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "friday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "saturday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "sunday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"})
            },
            fixed_shifts=True,
            number_of_shifts_per_day=3,
            shift_times=["10:00-14:00", "14:00-18:00", "18:00-22:00"],
            rating=4.5,
            accepting_orders=True
        )
        
        # Varying predictions
        predictions = np.array([[i, i//2] for i in range(24)])
        original_predictions = predictions.copy()
        
        # Create datetime info for Monday
        base_date = datetime(2024, 1, 15)
        datetime_info = pd.DataFrame({
            'datetime': [base_date + timedelta(hours=h) for h in range(24)],
            'date': [base_date.date()] * 24,
            'hour': list(range(24))
        })
        
        # Apply filter
        filtered = zero_out_closed_hours(predictions, datetime_info, place)
        
        # During open hours (10-21), predictions should be unchanged
        assert np.array_equal(filtered[10:22], original_predictions[10:22]), \
            "Open hour predictions should be preserved"
    
    def test_filter_handles_overnight_shifts(self):
        """Test filter correctly handles overnight shifts (e.g., 22:00-06:00)"""
        place = PlaceData(
            place_id="test_123",
            place_name="24/7 Diner",
            type="restaurant",
            latitude=55.6761,
            longitude=12.5683,
            waiting_time=30,
            receiving_phone=True,
            delivery=True,
            opening_hours={
                "monday": OpeningHoursDay(**{"from": "22:00", "to": "06:00"}),  # Overnight
                "tuesday": OpeningHoursDay(**{"from": "22:00", "to": "06:00"}),
                "wednesday": OpeningHoursDay(**{"from": "22:00", "to": "06:00"}),
                "thursday": OpeningHoursDay(**{"from": "22:00", "to": "06:00"}),
                "friday": OpeningHoursDay(**{"from": "22:00", "to": "06:00"}),
                "saturday": OpeningHoursDay(**{"from": "22:00", "to": "06:00"}),
                "sunday": OpeningHoursDay(**{"from": "22:00", "to": "06:00"})
            },
            fixed_shifts=True,
            number_of_shifts_per_day=1,
            shift_times=["22:00-06:00"],
            rating=4.5,
            accepting_orders=True
        )
        
        predictions = np.array([[5, 2]] * 24)
        
        base_date = datetime(2024, 1, 15)  # Monday
        datetime_info = pd.DataFrame({
            'datetime': [base_date + timedelta(hours=h) for h in range(24)],
            'date': [base_date.date()] * 24,
            'hour': list(range(24))
        })
        
        filtered = zero_out_closed_hours(predictions, datetime_info, place)
        
        # Hours 22-23 should have predictions (open)
        assert np.all(filtered[22:24, 0] > 0), "Late night should be open"
        
        # Hours 0-5 should have predictions (open, overnight)
        assert np.all(filtered[0:6, 0] > 0), "Early morning (overnight) should be open"
        
        # Hours 6-21 should be zero (closed)
        assert np.all(filtered[6:22, 0] == 0), "Daytime hours should be closed"
    
    def test_filter_cost_savings(self):
        """Test that filter eliminates phantom demand and saves costs"""
        place = PlaceData(
            place_id="test_123",
            place_name="Test Restaurant",
            type="restaurant",
            latitude=55.6761,
            longitude=12.5683,
            waiting_time=30,
            receiving_phone=True,
            delivery=True,
            opening_hours={
                "monday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "tuesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "wednesday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "thursday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "friday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "saturday": OpeningHoursDay(**{"from": "10:00", "to": "22:00"}),
                "sunday": OpeningHoursDay(closed=True)
            },
            fixed_shifts=True,
            number_of_shifts_per_day=3,
            shift_times=["10:00-14:00", "14:00-18:00", "18:00-22:00"],
            rating=4.5,
            accepting_orders=True
        )
        
        # One week of predictions
        predictions_week = []
        datetime_info_week = []
        
        for day in range(7):
            base_date = datetime(2024, 1, 8) + timedelta(days=day)
            for hour in range(24):
                predictions_week.append([3, 1])  # Phantom demand: 3 items, 1 order per hour
                datetime_info_week.append({
                    'datetime': base_date + timedelta(hours=hour),
                    'date': base_date.date(),
                    'hour': hour
                })
        
        predictions = np.array(predictions_week)
        datetime_info = pd.DataFrame(datetime_info_week)
        
        # Total phantom demand before filtering
        phantom_items = predictions[:, 0].sum()
        phantom_orders = predictions[:, 1].sum()
        
        # Apply filter
        filtered = zero_out_closed_hours(predictions, datetime_info, place)
        
        # Calculate savings
        items_eliminated = phantom_items - filtered[:, 0].sum()
        orders_eliminated = phantom_orders - filtered[:, 1].sum()
        
        # Should eliminate demand from:
        # - Sunday: 24 hours
        # - Other days: 12 hours/day × 6 days = 72 hours
        # Total: 96 hours
        expected_eliminated_hours = 96
        actual_eliminated_hours = np.sum((predictions[:, 0] > 0) & (filtered[:, 0] == 0))
        
        assert actual_eliminated_hours == expected_eliminated_hours, \
            f"Should eliminate {expected_eliminated_hours} hours, got {actual_eliminated_hours}"
        
        # Calculate cost savings (rough estimate)
        # If scheduler allocates 1 employee per 10 items @ $20/hour
        # Cost before: (phantom_items / 10) * 20
        # Cost after: (filtered_items / 10) * 20
        cost_savings = (items_eliminated / 10) * 20
        
        assert cost_savings > 0, "Should save money by eliminating phantom demand"
        assert items_eliminated >= 250, f"Should eliminate significant phantom demand (got {items_eliminated})"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
