from fastapi import FastAPI
from database import Base, engine  
from routers import patients  

# Creating tables before creating FastAPI app
Base.metadata.create_all(bind=engine)

app = FastAPI()

# creating FastAPI app instance
app.include_router(patients.router)

@app.get("/")
def root():
    return {"message": " Welcome to Healthcare API..."}