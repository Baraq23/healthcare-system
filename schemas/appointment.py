from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class AppointmentBase(BaseModel):
    doctor_id: int
    patient_id: int
    scheduled_datetime: datetime

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    status: str

class AppointmentResponse(AppointmentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AvailabilityResponse(BaseModel):
    doctor_id: int
    available_slots: list[datetime]
