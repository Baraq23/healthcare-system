from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.sql import func
from database import SessionLocal, Base  # Direct import

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())