from app.database import SessionLocal
from app.models.specialization import Specialization
import os



file_name = "specializations.txt"
file_path = os.path.join(os.path.dirname(__file__), file_name)


def read_specializations(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Specializations file not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        # Read lines, strip whitespace and ignore empty lines
        specializations = [line.strip() for line in f if line.strip()]
    return specializations

def insert_specializations():
    specializations_list = read_specializations(file_path)
    db = SessionLocal()
    try:
        for name in specializations_list:
            exists = db.query(Specialization).filter(Specialization.name == name).first()
            if not exists:
                specialization = Specialization(name=name)
                db.add(specialization)
        db.commit()
        print("Specializations inserted successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error inserting specializations: {e}")
    finally:
        db.close()

    