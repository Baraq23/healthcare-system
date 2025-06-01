from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Specialization(Base):
    __tablename__ = "specializations"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    doctors = relationship("Doctor", back_populates="specialization")  # One-to-many
