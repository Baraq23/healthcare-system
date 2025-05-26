from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, time, datetime, timedelta, timezone

from database import get_db
from models.appointment import Appointment as AppointmentModel
from models.appointment import AppointmentStatus as AppointmentStatusModel
from core.redis import (
    acquire_doctor_lock, release_doctor_lock,
    acquire_patient_lock, release_patient_lock
)
from schemas.appointment import (
    AppointmentCreate as AppointmentCreateModel,
    AppointmentResponse as AppointmentResponseModel,
    Appointment as AppointmentModel, 
)

from utils.helpers import (
    doctor_exists,
    patient_exists,
    check_doctor_availability,
    patient_has_future_appointment_with_doctor,
)

from core.redis import (
    acquire_doctor_lock, release_doctor_lock,
    acquire_patient_lock, release_patient_lock
)

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("/", response_model=AppointmentResponseModel)
def create_appointment(appointment: AppointmentCreateModel, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    scheduled_datetime_utc = appointment.scheduled_datetime.astimezone(timezone.utc)

    # Check if scheduled_datetime is in the past
    if scheduled_datetime_utc < now:
        raise HTTPException(status_code=400, detail="Appointments can only be scheduled for future time slots.")

    # Check working hours (optional, but recommended)
    appointment_time = scheduled_datetime_utc.time()
    if not (time(9, 0) <= appointment_time < time(17, 0)):
        raise HTTPException(status_code=400, detail="Appointments can only be scheduled between 0900hrs and 1700hrs.")

    # Check doctor and patient existence FIRST
    if not doctor_exists(db, appointment.doctor_id):
        raise HTTPException(status_code=404, detail="Doctor not found")
    if not patient_exists(db, appointment.patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check if patient already has a future appointment with this doctor
    if patient_has_future_appointment_with_doctor(db, appointment.patient_id, appointment.doctor_id, now):
        raise HTTPException(status_code=409, detail="You already have a future appointment with this doctor. Please cancel or complete it before booking another.")

    # Try to acquire both locks
    doctor_lock_acquired = acquire_doctor_lock(appointment.doctor_id, appointment.scheduled_datetime)
    patient_lock_acquired = acquire_patient_lock(appointment.patient_id, appointment.scheduled_datetime)

    if not doctor_lock_acquired:
        raise HTTPException(status_code=409, detail="Doctor is already booked at this time. Please try another slot.")
    if not patient_lock_acquired:
        release_doctor_lock(appointment.doctor_id, appointment.scheduled_datetime)
        raise HTTPException(status_code=409, detail="You already have an appointment at this time. Please check your schedule.")

    try:
        # Check for doctor conflicts (buffered window)
        start_time = appointment.scheduled_datetime - timedelta(minutes=59)
        end_time = appointment.scheduled_datetime + timedelta(minutes=59)
        if not check_doctor_availability(db, appointment.doctor_id, start_time, end_time):
            raise HTTPException(status_code=409, detail="Time slot already booked.")

        # Create and save the appointment
        db_appointment = AppointmentModel(**appointment.model_dump())
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)
        return db_appointment

    finally:
        release_doctor_lock(appointment.doctor_id, appointment.scheduled_datetime)
        release_patient_lock(appointment.patient_id, appointment.scheduled_datetime)