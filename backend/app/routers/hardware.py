from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_admin
from ..database import get_db
from ..models import Hardware, HardwareStatus
from ..schemas import HardwareCreate, HardwareOut, HardwareUpdate

router = APIRouter(prefix="/hardware", tags=["hardware"])

SORT_COLUMNS = {
    "name": Hardware.name,
    "brand": Hardware.brand,
    "purchase_date": Hardware.purchase_date,
    "status": Hardware.status,
}


def get_hardware_or_404(db: Session, hardware_id: int) -> Hardware:
    hardware = db.get(Hardware, hardware_id)
    if hardware is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hardware not found")
    return hardware


@router.get("", response_model=list[HardwareOut])
def list_hardware(
    status_filter: Optional[HardwareStatus] = Query(default=None, alias="status"),
    brand: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Literal["name", "brand", "purchase_date", "status"] = "name",
    sort_dir: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    query = db.query(Hardware)

    if status_filter is not None:
        query = query.filter(Hardware.status == status_filter)
    if brand:
        query = query.filter(Hardware.brand.ilike(f"%{brand}%"))
    if search:
        query = query.filter(Hardware.name.ilike(f"%{search}%"))

    column = SORT_COLUMNS[sort_by]
    query = query.order_by(column.desc() if sort_dir == "desc" else column.asc())

    return query.all()


@router.post("", response_model=HardwareOut, status_code=status.HTTP_201_CREATED)
def create_hardware(
    payload: HardwareCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    hardware = Hardware(
        name=payload.name,
        brand=payload.brand,
        purchase_date=payload.purchase_date,
        notes=payload.notes,
        status=HardwareStatus.AVAILABLE,
    )
    db.add(hardware)
    db.commit()
    db.refresh(hardware)
    return hardware


@router.delete("/{hardware_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hardware(
    hardware_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    hardware = get_hardware_or_404(db, hardware_id)
    if hardware.status == HardwareStatus.IN_USE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete hardware that is currently in use",
        )
    db.delete(hardware)
    db.commit()


@router.patch("/{hardware_id}/repair-toggle", response_model=HardwareOut)
def toggle_repair_status(
    hardware_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    hardware = get_hardware_or_404(db, hardware_id)
    if hardware.status == HardwareStatus.IN_USE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot change repair status while hardware is in use",
        )
    hardware.status = (
        HardwareStatus.AVAILABLE if hardware.status == HardwareStatus.IN_REPAIR else HardwareStatus.IN_REPAIR
    )
    db.commit()
    db.refresh(hardware)
    return hardware


@router.patch("/{hardware_id}", response_model=HardwareOut)
def update_hardware(
    hardware_id: int,
    payload: HardwareUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    hardware = get_hardware_or_404(db, hardware_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(hardware, field, value)
    db.commit()
    db.refresh(hardware)
    return hardware
