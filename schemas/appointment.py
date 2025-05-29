from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class Appointment(BaseModel):
    doctor_id: int
    patient_id: int
    scheduled_datetime: datetime

class AppointmentCreate(Appointment):
    pass

class AppointmentUpdate(BaseModel):
    status: str

class AppointmentResponse(Appointment):
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AvailabilityResponse(BaseModel):
    doctor_id: int
    available_slots: list[datetime]
