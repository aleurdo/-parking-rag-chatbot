from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Time,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    total_capacity = Column(Integer, nullable=False)
    location_type = Column(String(50), nullable=False, default="garage")
    created_at = Column(DateTime, default=datetime.utcnow)

    zones = relationship("ParkingZone", back_populates="location")
    operating_hours = relationship("OperatingHours", back_populates="location")


class ParkingZone(Base):
    __tablename__ = "parking_zones"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    zone_name = Column(String(50), nullable=False)
    zone_type = Column(String(50), nullable=False, default="standard")
    capacity = Column(Integer, nullable=False)
    hourly_rate = Column(Numeric(6, 2))
    daily_max = Column(Numeric(6, 2))

    location = relationship("Location", back_populates="zones")


class OperatingHours(Base):
    __tablename__ = "operating_hours"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    day_of_week = Column(Integer, nullable=False)
    open_time = Column(Time, nullable=False)
    close_time = Column(Time, nullable=False)
    is_24h = Column(Boolean, default=False)

    location = relationship("Location", back_populates="operating_hours")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    zone_id = Column(Integer, ForeignKey("parking_zones.id"))
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(255), nullable=False)
    license_plate = Column(String(20), nullable=False)
    vehicle_type = Column(String(50), nullable=False, default="standard")
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(String(20), nullable=False, default="confirmed")
    created_at = Column(DateTime, default=datetime.utcnow)


class Availability(Base):
    __tablename__ = "availability"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    zone_id = Column(Integer, ForeignKey("parking_zones.id"))
    date = Column(Date, nullable=False)
    available_spaces = Column(Integer, nullable=False)
