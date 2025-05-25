from fastapi import FastAPI
from database import Base, engine  
from routers import patient, doctor, specialization

# Creating tables before creating FastAPI app
Base.metadata.create_all(bind=engine)

# creating FastAPI app instance
app = FastAPI()

app.include_router(patient.router)
app.include_router(doctor.router)
app.include_router(specialization.router)

@app.get("/")
def root():
    return {"message": " Welcome to Healthcare API..."}