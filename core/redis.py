from datetime import datetime
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def acquire_doctor_lock(doctor_id: int, scheduled_datetime: datetime, timeout: int = 10) -> bool:
    lock_key = f"appointment:doctor:{doctor_id}:{scheduled_datetime.isoformat()}"
    return redis_client.set(lock_key, "locked", nx=True, ex=timeout) is not None

def release_doctor_lock(doctor_id: int, scheduled_datetime: datetime):
    lock_key = f"appointment:doctor:{doctor_id}:{scheduled_datetime.isoformat()}"
    redis_client.delete(lock_key)

def acquire_patient_lock(patient_id: int, scheduled_datetime: datetime, timeout: int = 10) -> bool:
    lock_key = f"appointment:patient:{patient_id}:{scheduled_datetime.isoformat()}"
    return redis_client.set(lock_key, "locked", nx=True, ex=timeout) is not None

def release_patient_lock(patient_id: int, scheduled_datetime: datetime):
    lock_key = f"appointment:patient:{patient_id}:{scheduled_datetime.isoformat()}"
    redis_client.delete(lock_key)
