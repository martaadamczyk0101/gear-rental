from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_admin
from ..database import get_db
from ..models import Hardware, HardwareStatus, Rental, RentalRequest, RentalRequestStatus, User
from ..schemas import RentalRequestOut

router = APIRouter(prefix="/rental-requests", tags=["rental-requests"])


def _get_request_or_404(db: Session, request_id: int) -> RentalRequest:
    request = db.get(RentalRequest, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental request not found")
    return request


@router.get("", response_model=list[RentalRequestOut])
def list_rental_requests(
    status_filter: RentalRequestStatus = Query(default=RentalRequestStatus.PENDING, alias="status"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return (
        db.query(RentalRequest)
        .filter(RentalRequest.status == status_filter)
        .order_by(RentalRequest.requested_at)
        .all()
    )


@router.get("/pending-count")
def pending_count(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    count = (
        db.query(RentalRequest)
        .filter(RentalRequest.status == RentalRequestStatus.PENDING)
        .count()
    )
    return {"pending": count}


@router.get("/mine", response_model=list[RentalRequestOut])
def my_rental_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(RentalRequest)
        .filter(
            RentalRequest.user_id == current_user.id,
            RentalRequest.status == RentalRequestStatus.PENDING,
        )
        .order_by(RentalRequest.requested_at)
        .all()
    )


@router.post("/{request_id}/approve", response_model=RentalRequestOut)
def approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    request = _get_request_or_404(db, request_id)
    if request.status != RentalRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This request has already been decided"
        )

    # Same atomic conditional update used by the direct rent endpoint: only
    # succeeds if the item is still 'available' at this exact moment, so two
    # admins approving competing requests for the same item can't both win.
    result = db.execute(
        update(Hardware)
        .where(Hardware.id == request.hardware_id, Hardware.status == HardwareStatus.AVAILABLE)
        .values(status=HardwareStatus.IN_USE)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This item is no longer available")

    db.add(Rental(hardware_id=request.hardware_id, user_id=request.user_id))

    now = datetime.utcnow()
    request.status = RentalRequestStatus.APPROVED
    request.decided_at = now
    request.decided_by_user_id = admin.id

    # Approving one request means every other pending request for the same
    # item is no longer satisfiable - auto-reject them so they can't be
    # accepted afterwards.
    siblings = (
        db.query(RentalRequest)
        .filter(
            RentalRequest.hardware_id == request.hardware_id,
            RentalRequest.status == RentalRequestStatus.PENDING,
            RentalRequest.id != request.id,
        )
        .all()
    )
    for sibling in siblings:
        sibling.status = RentalRequestStatus.REJECTED
        sibling.decided_at = now
        sibling.decided_by_user_id = admin.id

    db.commit()
    db.refresh(request)
    return request


@router.post("/{request_id}/reject", response_model=RentalRequestOut)
def reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    request = _get_request_or_404(db, request_id)
    if request.status != RentalRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This request has already been decided"
        )

    request.status = RentalRequestStatus.REJECTED
    request.decided_at = datetime.utcnow()
    request.decided_by_user_id = admin.id
    db.commit()
    db.refresh(request)
    return request
