from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..llm import SemanticSearchUnavailable, find_matching_ids
from ..models import Hardware
from ..schemas import HardwareOut

router = APIRouter(prefix="/hardware", tags=["search"])


@router.get("/semantic-search", response_model=list[HardwareOut])
def semantic_search(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    hardware = db.query(Hardware).all()
    inventory = [
        {
            "id": item.id,
            "name": item.name,
            "brand": item.brand,
            "purchase_date": item.purchase_date.isoformat() if item.purchase_date else None,
            "notes": item.notes,
            "status": item.status.value,
        }
        for item in hardware
    ]

    try:
        matching_ids = find_matching_ids(q, inventory)
    except SemanticSearchUnavailable as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Semantic search is temporarily unavailable - try the filters instead.",
        ) from err

    by_id = {item.id: item for item in hardware}
    return [by_id[hardware_id] for hardware_id in matching_ids if hardware_id in by_id]
