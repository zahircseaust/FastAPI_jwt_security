# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from typing import Optional

# To create a user (Pydantic schema)
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# To return user data (Pydantic schema)
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool

    class Config:
        orm_mode = True  # Enables the conversion from SQLAlchemy models to Pydantic models
