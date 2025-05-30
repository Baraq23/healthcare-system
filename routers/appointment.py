import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import time, datetime, timezone, date
from models.doctor import Doctor

from database import get_db
from models.appointment import Appointment as AppointmentModel, AppointmentStatus as AppointmentStatusModel
from schemas.appointment import AppointmentCreate as AppointmentCreateModel, AppointmentResponse as AppointmentResponseModel
from utils.helper import (
    doctor_exists,
    patient_exists,    
    patient_has_future_appointment_with_doctor,
    check_patient_available_at_time,
    get_all_appointments_for_patient,
    get_all_appointments_for_doctor,
    get_booked_slots_for_doctor,
    generate_available_slots,
)
from services.appointment_service import create_appointment_with_lock
from auth import get_current_doctor, get_current_patient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("/", response_model=AppointmentResponseModel)
def create_appointment(
    appointment: AppointmentCreateModel,
    db: Session = Depends(get_db),
    current_patient: dict = Depends(get_current_patient)
):
    """
    Schedule a new appointment if doctor and patient are available (requires patient authentication).
    """
    print("Start scheduling new appointment...")
    now = datetime.now(timezone.utc)
    scheduled_utc = appointment.scheduled_datetime.astimezone(timezone.utc)

    # Validate future time and working hours
    print("Validate future time and working hours...")
    if scheduled_utc < now:
        raise HTTPException(status_code=400, detail="Appointments must be scheduled for future time slots.")
    if not (time(9, 0) <= scheduled_utc.time() < time(17, 0)):
        raise HTTPException(status_code=400, detail="Appointments must be scheduled between 09:00 and 17:00.")
    
    # Validate slot alignment (30-minute intervals)
    print("Validate slot alignment (30-minute intervals)...")
    if scheduled_utc.minute % 30 != 0 or scheduled_utc.second != 0:
        raise HTTPException(status_code=400, detail="Appointments must be scheduled on 30-minute intervals (e.g., 09:00, 09:30).")

    # Check doctor and patient existence
    print("Check doctor and patient existence...")
    print("patient appointment value", appointment.patient_id)
    print("Doctor appointment value", appointment.doctor_id)
    print("Patient exists", patient_exists(db, appointment.patient_id))
    print("Doctor exists", doctor_exists(db, appointment.doctor_id))
    if not doctor_exists(db, appointment.doctor_id):
        raise HTTPException(status_code=404, detail="Doctor not found")
    if not patient_exists(db, appointment.patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")

    # Ensure the patient is booking for themselves
    print("Ensure the patient is booking for themselves...")
    if appointment.patient_id != current_patient.id:
        raise HTTPException(status_code=403, detail="Not authorized to book for another patient")

    # Check for existing appointments
    print("Check for existing appointments...")
    if patient_has_future_appointment_with_doctor(db, appointment.patient_id, appointment.doctor_id, now):
        raise HTTPException(
            status_code=409,
            detail="You already have a future appointment with this doctor. Please cancel or complete it first."
        )
    if not check_patient_available_at_time(db, appointment.patient_id, scheduled_utc):
        raise HTTPException(status_code=409, detail="You already have an appointment at this time.")

    try:
        # Delegate to service layer for creation with locking
        print("Delegate to service layer for creation with locking...")
        appointment_data = appointment.model_dump()
        db_appointment = create_appointment_with_lock(db, appointment_data)
        logger.info(f"Appointment created: ID={db_appointment.id}, Doctor={appointment.doctor_id}, Patient={appointment.patient_id}")
        return db_appointment
    except ValueError as e:
        logger.error(f"Error creating appointment: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating appointment: {str(e)}")
        raise HTTPException(status_code=409, detail="Doctor has another appointment at this time")

@router.get("/patient/{patient_id}", response_model=List[AppointmentResponseModel])
def get_patient_appointments(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_patient)
):
    """
    Retrieve all appointments for a patient (requires authentication).
    """
    if not patient_exists(db, patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Restrict access to patient's own appointments unless doctor
    if patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this patient's appointments")

    appointments = get_all_appointments_for_patient(db, patient_id)
    logger.info(f"Retrieved {len(appointments)} appointments for patient ID={patient_id}")
    return appointments

@router.get("/doctor/{doctor_id}", response_model=List[AppointmentResponseModel])
def get_doctor_appointments(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """
    Retrieve all appointments for a doctor (requires doctor authentication).
    """
    if not doctor_exists(db, doctor_id):
        raise HTTPException(status_code=404, detail="Doctor not found")
    if doctor_id != current_doctor.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this doctor's appointments")
    
    appointments = get_all_appointments_for_doctor(db, doctor_id)
    logger.info(f"Retrieved {len(appointments)} appointments for doctor ID={doctor_id}")
    return appointments

@router.put("/{appointment_id}/cancel", response_model=AppointmentResponseModel)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_patient)
):
    """
    Cancel an existing appointment. (requires authentication).
    """
    appointment = db.query(AppointmentModel).filter(AppointmentModel.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Only the patient or their doctor can cancel
    print("CURRENT USER: ", current_user)
    print("this appointment: ", appointment)
    if (appointment.patient_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")

    if appointment.status == AppointmentStatusModel.CANCELLED:
        raise HTTPException(status_code=400, detail="Appointment is already cancelled")
    if appointment.status == AppointmentStatusModel.COMPLETED:
        raise HTTPException(status_code=400, detail="Can not cancel a completed appointment")

    appointment.status = AppointmentStatusModel.CANCELLED
    db.commit()
    db.refresh(appointment)
    logger.info(f"Appointment cancelled: ID={appointment_id}")
    return appointment


@router.put("/{appointment_id}/complete", response_model=AppointmentResponseModel)
def complete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_doctor)
):
    """
    Mark appointment as complete. This is only availabel for Doctors(requires authentication).
    """
    appointment = db.query(AppointmentModel).filter(AppointmentModel.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Only the patient or their doctor can cancel
    if (appointment.doctor_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to mark this appointment as complete.")
    
    
    now = datetime.now(timezone.utc)
    created_at_aware = appointment.created_at.replace(tzinfo=timezone.utc)

    if created_at_aware >= now:
        raise HTTPException(status_code=400, detail="Can’t mark appointment as complete before scheduled time. Contact patient to cancel or reschedule.")
        
        
    if appointment.status == AppointmentStatusModel.CANCELLED:
        raise HTTPException(status_code=400, detail="Can not mark a canceled appointment as complete")
    if appointment.status == AppointmentStatusModel.COMPLETED:
        raise HTTPException(status_code=400, detail="Appointment already marked as completed.")

    appointment.status = AppointmentStatusModel.COMPLETED
    db.commit()
    db.refresh(appointment)
    logger.info(f"Appointment marked completed: ID={appointment_id}")
    return appointment

@router.get("/doctor/{doctor_id}/{date}", response_model=List[datetime])
def get_available_slots(
    doctor_id: int,
    date: date,
    db: Session = Depends(get_db),
):
    """
    Retrieve available appointment slots for a doctor on a given date.
    """
    print("DATE BOOKED RECIEVED IN BACKED: ", date)
    if not doctor_exists(db, doctor_id):
        raise HTTPException(status_code=404, detail="Doctor not found")

    now = datetime.now(timezone.utc)
    start_time = datetime.combine(date, time(9, 0)).astimezone(timezone.utc)
    end_time = datetime.combine(date, time(17, 0)).astimezone(timezone.utc)

    if start_time < now:
        raise HTTPException(status_code=400, detail="Cannot retrieve slots for past dates")

    booked_slots = set(get_booked_slots_for_doctor(db, doctor_id, start_time, end_time))
    slots = generate_available_slots(
        booked_slots=booked_slots,
        working_start=start_time,
        working_end=end_time,
        slot_interval_minutes=60,
        now=now
    )
    logger.info(f"Retrieved {len(slots)} available slots for doctor ID={doctor_id} on {date}")
    return slots