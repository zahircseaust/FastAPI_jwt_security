from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from passlib.hash import bcrypt
from sqlalchemy.orm import Session
from schema import UserLogin, UserCreate
from database import get_db
from response import create_response
from services.auth_service import authenticate_user, create_tokens
from response import ApiResponse

router = APIRouter()

@router.post("/register", response_model=UserCreate)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return authenticate_user(user, db)

@router.post("/login", response_model=ApiResponse)
def login(user: UserLogin, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    db_user = authenticate_user(user, db)
    if not db_user:
        return create_response(success=False, message="Invalid credentials")

    access_token, refresh_token = create_tokens(db_user, Authorize)
    
    return create_response(
        success=True,
        message="Login successful",
        data={"access_token": access_token, "refresh_token": refresh_token}
    )

@router.post("/refresh")
def refresh(Authorize: AuthJWT = Depends()):
    return create_response(success=True, message="Token refreshed", data={"access_token": Authorize.create_access_token(subject="user_id")})

