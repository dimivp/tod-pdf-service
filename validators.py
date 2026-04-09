"""Input validation models for TOD PDF generation."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import date, time
import re


class ImmobilizationRow(BaseModel):
    """Model for a single immobilization row in the table."""
    position: int = Field(..., ge=1, le=12, description="Position in table (1-12)")
    vehicleNumber: str = Field(..., description="Vehicle number (formatted X XXX-X)")
    handremCount: int = Field(0, ge=0, description="Number of hand brakes")
    woodenBlockCount: int = Field(0, ge=0, description="Number of wooden blocks")
    metalBlockCount: int = Field(0, ge=0, description="Number of metal blocks")

    @validator("vehicleNumber")
    def validate_vehicle_number(cls, v):
        """Validate vehicle number format: X XXX-X"""
        if not re.match(r"^\d\s\d{3}-\d$", v):
            raise ValueError(
                f"Invalid vehicle number format: {v}. Expected format: X XXX-X"
            )
        return v


class TODRequest(BaseModel):
    """Main input model for TOD PDF generation request."""

    # Basic info
    employeeName: str = Field(..., description="Name of employee")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: str = Field(..., description="Time in HH:mm format")
    location: str = Field(..., description="Location of immobilization")
    trackNumber: str = Field(..., description="Track number")

    # Vehicle info
    firstVehicleNumber: str = Field(..., description="First vehicle number (X XXX-X)")
    lastVehicleNumber: str = Field(..., description="Last vehicle number (X XXX-X)")

    # Status
    isOnAir: bool = Field(..., description="Whether immobilization is on air")

    # Immobilization data
    immobilizationRows: List[ImmobilizationRow] = Field(
        ..., max_items=12, description="Immobilization table rows (max 12)"
    )

    # Signals and brake info
    endSignal: Optional[Literal["lamps", "plaques"]] = Field(
        None, description="End signal type (lamps or plaques)"
    )
    brakeRegime: Optional[Literal["P", "LL", "G"]] = Field(
        None, description="Brake regime (P, LL, or G)"
    )
    fullBrakeTest: bool = Field(False, description="Whether full brake test was performed")

    # Optional
    tripId: Optional[str] = Field(None, description="Trip ID for reference")

    @validator("date")
    def validate_date(cls, v):
        """Validate date format YYYY-MM-DD"""
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD")

    @validator("time")
    def validate_time(cls, v):
        """Validate time format HH:mm"""
        try:
            h, m = v.split(":")
            int(h), int(m)
            if not (0 <= int(h) < 24 and 0 <= int(m) < 60):
                raise ValueError("Invalid time values")
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid time format: {v}. Expected HH:mm")

    @validator("firstVehicleNumber", "lastVehicleNumber")
    def validate_vehicle_number(cls, v):
        """Validate vehicle number format: X XXX-X"""
        if not re.match(r"^\d\s\d{3}-\d$", v):
            raise ValueError(
                f"Invalid vehicle number format: {v}. Expected format: X XXX-X"
            )
        return v

    @validator("immobilizationRows")
    def validate_rows_unique(cls, v):
        """Validate that all positions are unique"""
        positions = [row.position for row in v]
        if len(positions) != len(set(positions)):
            raise ValueError("Immobilization row positions must be unique")
        return sorted(v, key=lambda r: r.position)

    class Config:
        json_schema_extra = {
            "example": {
                "employeeName": "John Doe",
                "date": "2026-04-09",
                "time": "14:30",
                "location": "Antwerpen",
                "trackNumber": "T001",
                "firstVehicleNumber": "1 234-5",
                "lastVehicleNumber": "5 678-9",
                "isOnAir": True,
                "tripId": "TRIP-123",
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
        }
