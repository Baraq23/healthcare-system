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
    AppointmentUpdate as AppointmentUpdateModel,
    AvailabilityResponse as AvailabilityResponseModel
)
import os
from dotenv import load_dotenv

load_dotenv()  # Loads environment variables from the .env file

SLOT_INTERVAL_MINUTES = int(os.getenv('SLOT_INTERVAL_MINUTES', 60))
TIME_BETWEEN_APPOINTMENTS_MINUTES = int(os.getenv('TIME_BETWEEN_APPOINTMENTS_MINUTES', 58))
WORKING_HOURS_START = int(os.getenv('WORKING_HOURS_START', 9))
WORKING_HOURS_END = int(os.getenv('WORKING_HOURS_END', 17))


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
    scheduled_datetime_utc = appointment.scheduled_datetime.astimezone(timezone.utc)

    # Check if scheduled_datetime is in the past
    if scheduled_datetime_utc < now:
        raise HTTPException(
            status_code=400,
            detail="Appointments can only be scheduled for future time slots."
        )
    
    # Extract the time part (hour, minute)
    appointment_time = scheduled_datetime_utc.time()
    if not (time(WORKING_HOURS_START, 0) <= appointment_time < time(WORKING_HOURS_END, 0)):
        raise HTTPException(
            status_code=400,
            detail="Appointments can only be scheduled between 0900hrs and 1700hrs."
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
        start_time = appointment.scheduled_datetime - timedelta(minutes=TIME_BETWEEN_APPOINTMENTS_MINUTES)
        end_time = appointment.scheduled_datetime + timedelta(minutes=TIME_BETWEEN_APPOINTMENTS_MINUTES)
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
    date: date,  # Changed to date, not datetime
    db: Session = Depends(get_db)
):
    # Check if scheduled_datetime is in the past
    if date < datetime.now().date():
        raise HTTPException(
            status_code=400,
            detail="You can only check doctor's availability for today and future time."
        )
        
    # Set the start and end of the requested day (timezone-aware)
    start_time = datetime(
        date.year, date.month, date.day,
        tzinfo=timezone.utc  # or your preferred timezone
    )
    end_time = start_time + timedelta(days=1)

    # Get existing appointments (exclude cancelled)
    appointments = db.query(AppointmentModel).filter(
        AppointmentModel.doctor_id == doctor_id,
        AppointmentModel.scheduled_datetime >= start_time,
        AppointmentModel.scheduled_datetime < end_time,
        AppointmentModel.status != AppointmentStatusModel.CANCELLED
    ).all()
    booked_slots = {appt.scheduled_datetime for appt in appointments}

    # Generate available slots (every 60 minutes)
    current_slot = start_time
    now = datetime.now(timezone.utc)

    # Generate all possible slots (every 60 minutes, 9:00-17:00)
    working_start = start_time.replace(hour=WORKING_HOURS_START, minute=0, second=0)
    working_end = start_time.replace(hour=WORKING_HOURS_END, minute=0, second=0)

    all_slots = []
    current_slot = working_start
    while current_slot < working_end:
        all_slots.append(current_slot)
        current_slot += timedelta(minutes=SLOT_INTERVAL_MINUTES)

    # Filter out booked slots
    available_slots = [slot for slot in all_slots if slot not in booked_slots]

    # Optionally, filter out slots in the past
    available_slots = [slot for slot in available_slots if slot >= now]

    return AvailabilityResponseModel(
        doctor_id=doctor_id,
        available_slots=available_slots
    )


    
@router.get("/doctors/{doctor_id}/booked-slots", response_model=List[datetime])
def get_doctor_booked_slots(doctor_id: int, db: Session = Depends(get_db)):
    """
    Returns a list of booked time slots for the given doctor.
    """
    # Query all appointments for the doctor (excluding cancelled)
    appointments = db.query(AppointmentModel.scheduled_datetime).filter(
        AppointmentModel.doctor_id == doctor_id,
        AppointmentModel.status != AppointmentStatusModel.CANCELLED
    ).all()

    # Extract the datetime objects
    booked_slots = [appt.scheduled_datetime for appt in appointments]

    return booked_slots