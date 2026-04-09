"""Unit tests for input validators."""

import pytest
from pydantic import ValidationError

from validators import TODRequest, ImmobilizationRow


class TestImmobilizationRow:
    """Test ImmobilizationRow model."""

    def test_valid_row(self):
        """Test valid immobilization row."""
        row = ImmobilizationRow(
            position=1,
            vehicleNumber="1 234-5",
            handremCount=2,
            woodenBlockCount=4,
            metalBlockCount=0,
        )
        assert row.position == 1
        assert row.vehicleNumber == "1 234-5"

    def test_invalid_vehicle_number(self):
        """Test invalid vehicle number format."""
        with pytest.raises(ValidationError) as exc_info:
            ImmobilizationRow(
                position=1,
                vehicleNumber="invalid",
                handremCount=2,
                woodenBlockCount=4,
                metalBlockCount=0,
            )
        assert "vehicle number" in str(exc_info.value).lower()

    def test_position_out_of_range(self):
        """Test position exceeds max (12)."""
        with pytest.raises(ValidationError):
            ImmobilizationRow(
                position=13,
                vehicleNumber="1 234-5",
                handremCount=2,
                woodenBlockCount=4,
                metalBlockCount=0,
            )


class TestTODRequest:
    """Test TODRequest model."""

    def test_valid_request(self):
        """Test valid TOD request."""
        data = {
            "employeeName": "John Doe",
            "date": "2026-04-09",
            "time": "14:30",
            "location": "Antwerpen",
            "trackNumber": "T001",
            "firstVehicleNumber": "1 234-5",
            "lastVehicleNumber": "1 234-9",
            "isOnAir": True,
            "immobilizationRows": [
                {
                    "position": 1,
                    "vehicleNumber": "1 234-5",
                    "handremCount": 2,
                    "woodenBlockCount": 4,
                    "metalBlockCount": 0,
                }
            ],
            "endSignal": "lamps",
            "brakeRegime": "P",
            "fullBrakeTest": True,
        }
        request = TODRequest(**data)
        assert request.employeeName == "John Doe"
        assert request.date == "2026-04-09"

    def test_invalid_date_format(self):
        """Test invalid date format."""
        data = {
            "employeeName": "John Doe",
            "date": "09-04-2026",  # Wrong format
            "time": "14:30",
            "location": "Antwerpen",
            "trackNumber": "T001",
            "firstVehicleNumber": "1 234-5",
            "lastVehicleNumber": "1 234-9",
            "isOnAir": True,
            "immobilizationRows": [],
        }
        with pytest.raises(ValidationError):
            TODRequest(**data)

    def test_invalid_time_format(self):
        """Test invalid time format."""
        data = {
            "employeeName": "John Doe",
            "date": "2026-04-09",
            "time": "25:00",  # Invalid hour
            "location": "Antwerpen",
            "trackNumber": "T001",
            "firstVehicleNumber": "1 234-5",
            "lastVehicleNumber": "1 234-9",
            "isOnAir": True,
            "immobilizationRows": [],
        }
        with pytest.raises(ValidationError):
            TODRequest(**data)

    def test_duplicate_positions(self):
        """Test duplicate position numbers."""
        data = {
            "employeeName": "John Doe",
            "date": "2026-04-09",
            "time": "14:30",
            "location": "Antwerpen",
            "trackNumber": "T001",
            "firstVehicleNumber": "1 234-5",
            "lastVehicleNumber": "1 234-9",
            "isOnAir": True,
            "immobilizationRows": [
                {
                    "position": 1,
                    "vehicleNumber": "1 234-5",
                    "handremCount": 2,
                    "woodenBlockCount": 4,
                    "metalBlockCount": 0,
                },
                {
                    "position": 1,  # Duplicate
                    "vehicleNumber": "1 234-6",
                    "handremCount": 2,
                    "woodenBlockCount": 4,
                    "metalBlockCount": 0,
                },
            ],
        }
        with pytest.raises(ValidationError):
            TODRequest(**data)

    def test_rows_auto_sorted(self):
        """Test that rows are auto-sorted by position."""
        data = {
            "employeeName": "John Doe",
            "date": "2026-04-09",
            "time": "14:30",
            "location": "Antwerpen",
            "trackNumber": "T001",
            "firstVehicleNumber": "1 234-5",
            "lastVehicleNumber": "1 234-9",
            "isOnAir": True,
            "immobilizationRows": [
                {"position": 3, "vehicleNumber": "1 234-7", "handremCount": 0, "woodenBlockCount": 0, "metalBlockCount": 0},
                {"position": 1, "vehicleNumber": "1 234-5", "handremCount": 0, "woodenBlockCount": 0, "metalBlockCount": 0},
                {"position": 2, "vehicleNumber": "1 234-6", "handremCount": 0, "woodenBlockCount": 0, "metalBlockCount": 0},
            ],
        }
        request = TODRequest(**data)
        positions = [row.position for row in request.immobilizationRows]
        assert positions == [1, 2, 3]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
