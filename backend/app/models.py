import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from .database import Base


class HardwareStatus(str, enum.Enum):
    AVAILABLE = "available"
    IN_USE = "in use"
    IN_REPAIR = "in repair"


class RentalRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    rentals = relationship("Rental", back_populates="user")


class Hardware(Base):
    __tablename__ = "hardware"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    purchase_date = Column(Date, nullable=True)
    status = Column(
        SQLEnum(HardwareStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=HardwareStatus.AVAILABLE,
    )
    notes = Column(Text, nullable=True)

    rentals = relationship("Rental", back_populates="hardware")


class Rental(Base):
    __tablename__ = "rentals"

    id = Column(Integer, primary_key=True)
    hardware_id = Column(Integer, ForeignKey("hardware.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rented_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    returned_at = Column(DateTime, nullable=True)

    hardware = relationship("Hardware", back_populates="rentals")
    user = relationship("User", back_populates="rentals")


class RentalRequest(Base):
    __tablename__ = "rental_requests"

    id = Column(Integer, primary_key=True)
    hardware_id = Column(Integer, ForeignKey("hardware.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(
        SQLEnum(RentalRequestStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=RentalRequestStatus.PENDING,
    )
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
    decided_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    hardware = relationship("Hardware", foreign_keys=[hardware_id])
    user = relationship("User", foreign_keys=[user_id])
