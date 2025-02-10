from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from database import SessionLocal
from typing import Generator
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str  # Required during registration
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr  # Only email and password for login
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        orm_mode = True

        
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()  # Create a new session
    try:
        yield db  # Yield the session to be used
    finally:
        db.close()

