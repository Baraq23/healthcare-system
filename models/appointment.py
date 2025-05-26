from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SQLAlchemyEnum, func
from sqlalchemy.orm import declarative_base
from enum import Enum

Base = declarative_base()

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    scheduled_datetime = Column(DateTime, nullable=False)

    status = Column(
        SQLAlchemyEnum(AppointmentStatus),
        default=AppointmentStatus.SCHEDULED
    )

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
