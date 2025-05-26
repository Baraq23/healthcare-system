from datetime import timedelta, datetime
from sqlalchemy.orm import Session
from core.redis import acquire_lock, release_lock
from models.appointment import Appointment as AppointmentModel
from models.appointment import AppointmentStatus as  AppointmentStatusModel

def check_availability(db: Session, doctor_id: int, start: datetime, end: datetime):
    return db.query(AppointmentModel).filter(
        AppointmentModel.doctor_id == doctor_id,
        AppointmentModel.scheduled_datetime >= start,
        AppointmentModel.scheduled_datetime < end,
        AppointmentModel.status != AppointmentStatusModel.CANCELLED
    ).all()

def create_appointment_with_lock(db: Session, appointment_data: dict):
    scheduled_datetime = appointment_data["scheduled_datetime"]
    if not acquire_lock(appointment_data["doctor_id"], scheduled_datetime):
        raise ValueError("Appointment slot is being booked by another user. Please try again.")
    try:
        # Check for doctor and patient conflicts (as before)
        start_time = scheduled_datetime - timedelta(minutes=59)
        end_time = scheduled_datetime + timedelta(minutes=59)
        conflicts = check_availability(db, appointment_data["doctor_id"], start_time, end_time)
        if conflicts:
            raise ValueError("Doctor has conflicting appointment")
        patient_conflict = db.query(AppointmentModel).filter(
            AppointmentModel.patient_id == appointment_data["patient_id"],
            AppointmentModel.scheduled_datetime == scheduled_datetime,
            AppointmentModel.status != AppointmentStatusModel.CANCELLED
        ).first()
        if patient_conflict:
            raise ValueError("Patient has conflicting appointment")
        appointment = AppointmentModel(**appointment_data)
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment
    finally:
        release_lock(appointment_data["doctor_id"], scheduled_datetime)
