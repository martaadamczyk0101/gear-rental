from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from .models import HardwareStatus, RentalRequestStatus


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


class HardwareNotesUpdate(BaseModel):
    notes: Optional[str] = None


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
