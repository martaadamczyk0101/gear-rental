from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from .models import HardwareStatus, RentalRequestStatus


def _reject_future_purchase_date(value: Optional[date]) -> Optional[date]:
    if value is not None and value > date.today():
        raise ValueError("purchase_date cannot be in the future")
    return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_admin: bool
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    is_admin: bool = False


class HardwareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    brand: str
    purchase_date: Optional[date]
    status: HardwareStatus
    notes: Optional[str]


class HardwareCreate(BaseModel):
    name: str
    brand: str
    purchase_date: Optional[date] = None
    notes: Optional[str] = None

    _validate_purchase_date = field_validator("purchase_date")(_reject_future_purchase_date)


class HardwareUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    purchase_date: Optional[date] = None
    notes: Optional[str] = None

    _validate_purchase_date = field_validator("purchase_date")(_reject_future_purchase_date)


class RentalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rented_at: datetime
    returned_at: Optional[datetime]
    hardware: HardwareOut


class RentActionResult(BaseModel):
    outcome: Literal["rented", "requested"]
    hardware: HardwareOut


class RentalRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: RentalRequestStatus
    requested_at: datetime
    decided_at: Optional[datetime]
    hardware: HardwareOut
    user: UserOut
