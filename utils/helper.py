from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from models.doctor import Doctor as DoctorModel
from models.patient import Patient as PatientModel
from models.specialization import Specialization as SpecializationModel
from models.appointment import Appointment as AppointmentModel, AppointmentStatus as AppointmentStatusModel

# -------------------- Doctors ----------------------------

def doctor_exists(db: Session, doctor_id: int) -> bool:
    """Check if a doctor with the given ID exists."""
    return db.query(DoctorModel).filter(DoctorModel.id == doctor_id).first() is not None

def get_doctor_by_id(db: Session, doctor_id: int) -> Optional[DoctorModel]:
    """Get a doctor by ID, or None if not found."""
    return db.query(DoctorModel).filter(DoctorModel.id == doctor_id).first()

def get_doctor_by_id_or_404(db: Session, doctor_id: int) -> DoctorModel:
    """Get a doctor by ID, or raise 404."""
    doctor = get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail=f"Doctor with id {doctor_id} not found")
    return doctor

# -------------------- Patients ----------------------------

def patient_exists(db: Session, patient_id: int) -> bool:
    """Check if a patient with the given ID exists."""
    return db.query(PatientModel).filter(PatientModel.id == patient_id).first() is not None

def get_patient_by_id(db: Session, patient_id: int) -> Optional[PatientModel]:
    """Get a patient by ID, or None if not found."""
    return db.query(PatientModel).filter(PatientModel.id == patient_id).first()

def get_patient_by_id_or_404(db: Session, patient_id: int) -> PatientModel:
    """Get a patient by ID, or raise 404."""
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient with id {patient_id} not found")
    return patient

# -------------------- Specializations ---------------------

def get_specialization_by_name(db: Session, name: str) -> Optional[SpecializationModel]:
    """Get a specialization by name (case-insensitive), or None if not found."""
    return db.query(SpecializationModel).filter(SpecializationModel.name.ilike(name)).first()

def get_specialization_by_id(db: Session, specialization_id: int) -> Optional[SpecializationModel]:
    """Get a specialization by ID, or None if not found."""
    return db.query(SpecializationModel).filter(SpecializationModel.id == specialization_id).first()

def get_specialization_by_id_or_404(db: Session, specialization_id: int) -> SpecializationModel:
    """Get a specialization by ID, or raise 404."""
    spec = get_specialization_by_id(db, specialization_id)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Specialization with id {specialization_id} not found")
    return spec

def specialization_exists_by_id(db: Session, specialization_id: int) -> bool:
    """Check if a specialization with the given ID exists."""
    return get_specialization_by_id(db, specialization_id) is not None

def specialization_exists_by_name(db: Session, name: str) -> bool:
    """Check if a specialization with the given name exists (case-insensitive)."""
    return get_specialization_by_name(db, name) is not None

# -------------------- Appointment Checks --------------------

def check_doctor_availability(db: Session, doctor_id: int, start_time: datetime, end_time: datetime) -> bool:
    """Return True if doctor is available (no conflicting appointments)."""
    return not db.query(AppointmentModel).filter(
        AppointmentModel.doctor_id == doctor_id,
        AppointmentModel.scheduled_datetime >= start_time,
        AppointmentModel.scheduled_datetime < end_time,
        AppointmentModel.status != AppointmentStatusModel.CANCELLED
    ).first()

def patient_has_future_appointment_with_doctor(db: Session, patient_id: int, doctor_id: int, now: datetime) -> bool:
    """Return True if patient already has a future appointment with this doctor (not cancelled/completed)."""
    return db.query(AppointmentModel).filter(
        AppointmentModel.patient_id == patient_id,
        AppointmentModel.doctor_id == doctor_id,
        AppointmentModel.scheduled_datetime >= now,
        AppointmentModel.status.not_in([AppointmentStatusModel.CANCELLED, AppointmentStatusModel.COMPLETED])
    ).first() is not None

def check_patient_available_at_time(db: Session, patient_id: int, scheduled_datetime: datetime) -> bool:
    """Return True if patient does not have another appointment at the same time (not cancelled)."""
    return not db.query(AppointmentModel).filter(
        AppointmentModel.patient_id == patient_id,
        AppointmentModel.scheduled_datetime == scheduled_datetime,
        AppointmentModel.status != AppointmentStatusModel.CANCELLED
    ).first()

# -------------------- Appointment Queries --------------------

def get_booked_slots_for_doctor(db: Session, doctor_id: int, start_time: datetime, end_time: datetime) -> List[datetime]:
    """Return all booked slots for a doctor in a given time range (excluding cancelled)."""
    appointments = db.query(AppointmentModel).filter(
        AppointmentModel.doctor_id == doctor_id,
        AppointmentModel.scheduled_datetime >= start_time,
        AppointmentModel.scheduled_datetime < end_time,
        AppointmentModel.status != AppointmentStatusModel.CANCELLED
    ).all()
    return [appt.scheduled_datetime for appt in appointments]

def get_all_appointments_for_patient(db: Session, patient_id: int) -> List[AppointmentModel]:
    """Return all appointments for a patient."""
    return db.query(AppointmentModel).filter(AppointmentModel.patient_id == patient_id).all()

def get_all_appointments_for_doctor(db: Session, doctor_id: int) -> List[AppointmentModel]:
    """Return all appointments for a doctor."""
    return db.query(AppointmentModel).filter(AppointmentModel.doctor_id == doctor_id).all()

# -------------------- Slot Generation --------------------

def generate_available_slots(
    booked_slots: set, working_start: datetime, working_end: datetime, slot_interval_minutes: int, now: datetime
) -> List[datetime]:
    """Generate available slots for a doctor, filtering out booked and past slots."""
    slots = []
    current_slot = working_start
    while current_slot < working_end:
        if current_slot not in booked_slots and current_slot >= now:
            slots.append(current_slot)
        current_slot += timedelta(minutes=slot_interval_minutes)
    return slots