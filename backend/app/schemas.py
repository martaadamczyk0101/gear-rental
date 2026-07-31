from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from .models import HardwareStatus


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
