import logging
import redis
from datetime import datetime
from time import sleep

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection with pooling
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    max_connections=10,  # Connection pool size
    decode_responses=True  # Automatically decode responses to strings
)

def acquire_doctor_lock(doctor_id: int, scheduled_datetime: datetime, timeout: int = 10, retries: int = 3, delay: float = 0.5) -> bool:
    """
    Acquire a lock for a doctor's time slot with retry logic.
    """
    lock_key = f"appointment:doctor:{doctor_id}:{scheduled_datetime.isoformat()}"
    for attempt in range(retries):
        if redis_client.set(lock_key, "locked", nx=True, ex=timeout):
            logger.debug(f"Acquired doctor lock: {lock_key}")
            return True
        logger.debug(f"Failed to acquire doctor lock: {lock_key}, attempt {attempt + 1}/{retries}")
        sleep(delay)
    return False

def release_doctor_lock(doctor_id: int, scheduled_datetime: datetime) -> None:
    """
    Release a lock for a doctor's time slot.
    """
    lock_key = f"appointment:doctor:{doctor_id}:{scheduled_datetime.isoformat()}"
    redis_client.delete(lock_key)
    logger.debug(f"Released doctor lock: {lock_key}")

def acquire_patient_lock(patient_id: int, scheduled_datetime: datetime, timeout: int = 10, retries: int = 3, delay: float = 0.5) -> bool:
    """
    Acquire a lock for a patient's time slot with retry logic.
    """
    lock_key = f"appointment:patient:{patient_id}:{scheduled_datetime.isoformat()}"
    for attempt in range(retries):
        if redis_client.set(lock_key, "locked", nx=True, ex=timeout):
            logger.debug(f"Acquired patient lock: {lock_key}")
            return True
        logger.debug(f"Failed to acquire patient lock: {lock_key}, attempt {attempt + 1}/{retries}")
        sleep(delay)
    return False

def release_patient_lock(patient_id: int, scheduled_datetime: datetime) -> None:
    """
    Release a lock for a patient's time slot.
    """
    lock_key = f"appointment:patient:{patient_id}:{scheduled_datetime.isoformat()}"
    redis_client.delete(lock_key)
    logger.debug(f"Released patient lock: {lock_key}")