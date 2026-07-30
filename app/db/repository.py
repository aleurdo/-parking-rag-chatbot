from datetime import date, datetime

from sqlalchemy.orm import Session

from app.db.models import Availability, Location, ParkingZone, Reservation


def get_locations(db: Session) -> list[Location]:
    return db.query(Location).all()


def get_location_by_name(db: Session, name: str) -> Location | None:
    return db.query(Location).filter(Location.name.ilike(f"%{name}%")).first()


def get_zones_for_location(db: Session, location_id: int, vehicle_type: str = "standard") -> list[ParkingZone]:
    type_map = {
        "standard": "standard",
        "ev": "ev",
        "motorcycle": "motorcycle",
        "oversized": "oversized",
    }
    zone_type = type_map.get(vehicle_type, "standard")
    return (
        db.query(ParkingZone)
        .filter(ParkingZone.location_id == location_id, ParkingZone.zone_type == zone_type)
        .all()
    )


def check_availability(db: Session, zone_id: int, target_date: date) -> int:
    avail = (
        db.query(Availability)
        .filter(Availability.zone_id == zone_id, Availability.date == target_date)
        .first()
    )
    if avail:
        return avail.available_spaces
    return 0


def create_reservation(
    db: Session,
    location_id: int,
    zone_id: int,
    customer_name: str,
    customer_email: str,
    license_plate: str,
    vehicle_type: str,
    start_time: datetime,
    end_time: datetime | None = None,
) -> Reservation:
    reservation = Reservation(
        location_id=location_id,
        zone_id=zone_id,
        customer_name=customer_name,
        customer_email=customer_email,
        license_plate=license_plate,
        vehicle_type=vehicle_type,
        start_time=start_time,
        end_time=end_time,
        status="confirmed",
    )
    db.add(reservation)

    avail = (
        db.query(Availability)
        .filter(
            Availability.zone_id == zone_id,
            Availability.date == start_time.date(),
        )
        .first()
    )
    if avail and avail.available_spaces > 0:
        avail.available_spaces -= 1

    db.commit()
    db.refresh(reservation)
    return reservation


def get_reservation_by_id(db: Session, reservation_id: int) -> Reservation | None:
    return db.query(Reservation).filter(Reservation.id == reservation_id).first()
