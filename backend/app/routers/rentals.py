from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Hardware, HardwareStatus, Rental, User
from ..schemas import HardwareOut, RentalOut
from .hardware import get_hardware_or_404

router = APIRouter(tags=["rentals"])


@router.post("/hardware/{hardware_id}/rent", response_model=HardwareOut)
def rent_hardware(
    hardware_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hardware = get_hardware_or_404(db, hardware_id)

    # Atomic conditional update: only succeeds if the row is still 'available'
    # at the moment of the UPDATE, so two concurrent rent requests can't both win.
    result = db.execute(
        update(Hardware)
        .where(Hardware.id == hardware_id, Hardware.status == HardwareStatus.AVAILABLE)
        .values(status=HardwareStatus.IN_USE)
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hardware is not available (current status: {hardware.status.value})",
        )

    db.add(Rental(hardware_id=hardware_id, user_id=current_user.id))
    db.commit()
    db.refresh(hardware)
    return hardware


@router.post("/hardware/{hardware_id}/return", response_model=HardwareOut)
def return_hardware(
    hardware_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hardware = get_hardware_or_404(db, hardware_id)

    open_rental = (
        db.query(Rental)
        .filter(Rental.hardware_id == hardware_id, Rental.returned_at.is_(None))
        .first()
    )
    if open_rental is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This item is not currently rented")
    if open_rental.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only return your own rentals")

    open_rental.returned_at = datetime.utcnow()
    hardware.status = HardwareStatus.AVAILABLE
    db.commit()
    db.refresh(hardware)
    return hardware


@router.get("/rentals/mine", response_model=list[RentalOut])
def my_rentals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Rental)
        .filter(Rental.user_id == current_user.id, Rental.returned_at.is_(None))
        .order_by(Rental.rented_at)
        .all()
    )
