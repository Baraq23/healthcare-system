from fastapi import FastAPI
from database import Base, engine  
from routers import patient, doctor, specialization, appointment
from fastapi.middleware.cors import CORSMiddleware

# Creating tables before creating FastAPI app
try:
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")
except Exception as e:
    print(f"Error creating tables: {e}")


# Configure CORS

# creating FastAPI app instance
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(patient.router)
app.include_router(doctor.router)
app.include_router(specialization.router)
app.include_router(appointment.router)

@app.get("/")
def read_root():
    return {"details": "Welcome to healthcare fast api..."}

