from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone

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
    AppointmentUpdate as AppointmentUpdateModel,
    AvailabilityResponse as AvailabilityResponseModel
)

router = APIRouter(prefix="/appointments", tags=["appointments"])

def check_availability(db: Session, doctor_id: int, start_time: datetime, end_time: datetime):
    existing = db.query(AppointmentModel).filter(
        AppointmentModel.doctor_id == doctor_id,
        AppointmentModel.scheduled_datetime >= start_time,
        AppointmentModel.scheduled_datetime < end_time,
        AppointmentModel.status != AppointmentStatusModel.CANCELLED
    ).all()
    return existing

@router.post("/", response_model=AppointmentResponseModel)
def create_appointment(appointment: AppointmentCreateModel, db: Session = Depends(get_db)):
    

    now = datetime.now(timezone.utc)
    scheduled_datetime_utc = appointment.scheduled_datetime.replace(tzinfo=timezone.utc)

    # Check if scheduled_datetime is in the past
    if scheduled_datetime_utc < now:
        raise HTTPException(
            status_code=400,
            detail="Appointments can only be scheduled for future time slots."
        )
    
    scheduled_datetime = appointment.scheduled_datetime
    # Try to acquire both locks
    doctor_lock_acquired = acquire_doctor_lock(appointment.doctor_id, scheduled_datetime)
    patient_lock_acquired = acquire_patient_lock(appointment.patient_id, scheduled_datetime)

    if not doctor_lock_acquired:
        raise HTTPException(
            status_code=409,
            detail="Doctor is already booked at this time. Please try another slot."
        )
    if not patient_lock_acquired:
        release_doctor_lock(appointment.doctor_id, scheduled_datetime)
        raise HTTPException(
            status_code=409,
            detail="You already have an appointment at this time. Please check your schedule."
        )

    try:
        # Check for doctor conflicts (optional, since lock already prevents double-booking)
        start_time = appointment.scheduled_datetime - timedelta(minutes=59)
        end_time = appointment.scheduled_datetime + timedelta(minutes=59)
        conflicts = check_availability(db, appointment.doctor_id, start_time, end_time)
        if conflicts:
            raise HTTPException(status_code=409, detail="Time slot already booked.")

        # Check patient doesn't have overlapping appointments (optional, since lock already prevents double-booking)
        patient_conflict = db.query(AppointmentModel).filter(
            AppointmentModel.patient_id == appointment.patient_id,
            AppointmentModel.scheduled_datetime == appointment.scheduled_datetime,
            AppointmentModel.status != AppointmentStatusModel.CANCELLED
        ).first()
        if patient_conflict:
            raise HTTPException(status_code=409, detail="You already have an appointment at this time.")

        # Create and save the appointment
        db_appointment = AppointmentModel(**appointment.model_dump())
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)
        return db_appointment

    finally:
        # Always release both locks
        release_doctor_lock(appointment.doctor_id, scheduled_datetime)
        release_patient_lock(appointment.patient_id, scheduled_datetime)



@router.patch("/{appointment_id}", response_model=AppointmentResponseModel)
def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentUpdateModel,
    db: Session = Depends(get_db)
):
    appointment = db.query(AppointmentModel).get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    valid_transitions = {
        AppointmentStatusModel.SCHEDULED: [AppointmentStatusModel.COMPLETED, AppointmentStatusModel.CANCELLED],
        AppointmentStatusModel.CANCELLED: [AppointmentStatusModel.SCHEDULED]
    }

    if status_update.status not in valid_transitions.get(appointment.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {appointment.status}"
        )

    appointment.status = status_update.status
    db.commit()
    db.refresh(appointment)
    return appointment

@router.get("/availability/{doctor_id}", response_model=AvailabilityResponseModel)
def get_availability(
    doctor_id: int,
    date: datetime,
    db: Session = Depends(get_db)
):
    # Generate time slots for the given date
    start_time = datetime(date.year, date.month, date.day)
    end_time = start_time + timedelta(days=1)
    
    # Get existing appointments
    appointments = check_availability(db, doctor_id, start_time, end_time)
    booked_slots = [appt.scheduled_datetime for appt in appointments]
    
    # Generate available slots (every 30 minutes)
    available_slots = []
    current_slot = start_time
    while current_slot < end_time:
        if current_slot not in booked_slots and current_slot > datetime.now():
            available_slots.append(current_slot)
        current_slot += timedelta(minutes=30)
    
    return AvailabilityResponseModel(
        doctor_id=doctor_id,
        available_slots=available_slots
    )
    