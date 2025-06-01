import logging
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from fastapi import HTTPException

from app.models.appointment import Appointment as AppointmentModel, AppointmentStatus as AppointmentStatusModel
from app.utils.helper import check_doctor_availability, check_patient_available_at_time
from app.core.redis import acquire_doctor_lock, release_doctor_lock, acquire_patient_lock, release_patient_lock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_appointment_with_lock(db: Session, appointment_data: dict) -> AppointmentModel:
    """
    Create an appointment with Redis locking to prevent double-booking.
    """
    scheduled_datetime = appointment_data["scheduled_datetime"]
    doctor_id = appointment_data["doctor_id"]
    patient_id = appointment_data["patient_id"]

    # Acquire locks for doctor and patient
    if not acquire_doctor_lock(doctor_id, scheduled_datetime):
        logger.warning(f"Failed to acquire doctor lock for doctor ID={doctor_id}, time={scheduled_datetime}")
        raise HTTPException(status_code=409, detail="Doctor is already booked at this time.")
    if not acquire_patient_lock(patient_id, scheduled_datetime):
        release_doctor_lock(doctor_id, scheduled_datetime)
        logger.warning(f"Failed to acquire patient lock for patient ID={patient_id}, time={scheduled_datetime}")
        raise HTTPException(status_code=409, detail="Patient is already booked at this time.")

    try:
        # Check for conflicts using helper functions
        start_time = scheduled_datetime - timedelta(minutes=30)
        end_time = scheduled_datetime + timedelta(minutes=30)
        if not check_doctor_availability(db, doctor_id, start_time, end_time):
            raise HTTPException(status_code=409, detail="Doctor has a conflicting appointment.")
        if not check_patient_available_at_time(db, patient_id, scheduled_datetime):
            raise HTTPException(status_code=409, detail="Patient has a conflicting appointment.")

        # Create and save appointment
        appointment = AppointmentModel(**appointment_data)
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        logger.info(f"Appointment created in service layer: ID={appointment.id}, Doctor={doctor_id}, Patient={patient_id}")
        return appointment
    except Exception as e:
        logger.error(f"Error creating appointment in service layer: {str(e)}")
        raise
    finally:
        release_doctor_lock(doctor_id, scheduled_datetime)
        release_patient_lock(patient_id, scheduled_datetime)