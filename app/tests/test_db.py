from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.db.models import Availability, Location, ParkingZone, Reservation
from app.db.repository import (
    check_availability,
    create_reservation,
    get_location_by_name,
    get_locations,
    get_zones_for_location,
)


class TestGetLocations:
    def test_returns_all_locations(self):
        mock_db = MagicMock()
        locations = [
            Location(id=1, name="Downtown Garage"),
            Location(id=2, name="Riverside Lot"),
        ]
        mock_db.query.return_value.all.return_value = locations

        result = get_locations(mock_db)
        assert len(result) == 2
        assert result[0].name == "Downtown Garage"

    def test_returns_empty_list(self):
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []
        result = get_locations(mock_db)
        assert result == []


class TestGetLocationByName:
    def test_finds_location_case_insensitive(self):
        mock_db = MagicMock()
        location = Location(id=1, name="Downtown Garage")
        mock_db.query.return_value.filter.return_value.first.return_value = location

        result = get_location_by_name(mock_db, "downtown")
        assert result is not None
        assert result.name == "Downtown Garage"

    def test_returns_none_for_unknown(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_location_by_name(mock_db, "nonexistent")
        assert result is None


class TestCheckAvailability:
    def test_returns_available_spaces(self):
        mock_db = MagicMock()
        avail = Availability(id=1, zone_id=1, date=date(2025, 1, 15), available_spaces=50)
        mock_db.query.return_value.filter.return_value.first.return_value = avail

        result = check_availability(mock_db, zone_id=1, target_date=date(2025, 1, 15))
        assert result == 50

    def test_returns_zero_when_no_record(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = check_availability(mock_db, zone_id=1, target_date=date(2025, 12, 31))
        assert result == 0


class TestCreateReservation:
    def test_creates_and_decrements_availability(self):
        mock_db = MagicMock()
        avail = MagicMock()
        avail.available_spaces = 10
        mock_db.query.return_value.filter.return_value.first.return_value = avail

        reservation = create_reservation(
            db=mock_db,
            location_id=1,
            zone_id=1,
            customer_name="Test User",
            customer_email="test@example.com",
            license_plate="XY-1234",
            vehicle_type="standard",
            start_time=datetime(2025, 1, 15, 9, 0),
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert avail.available_spaces == 9
