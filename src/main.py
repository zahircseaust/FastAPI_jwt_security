from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from passlib.hash import bcrypt
from pydantic import BaseModel
from database import Base, engine, SessionLocal
from models import User
from schema import UserCreate, UserResponse,UserLogin
from response import create_response,ApiResponse
from schema import get_db
import secrets
import os
from fastapi.responses import JSONResponse
from fastapi_jwt_auth.exceptions import MissingTokenError, InvalidHeaderError
from fastapi import Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from fastapi import FastAPI, Depends
from fastapi_jwt_auth import AuthJWT
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Initialize DB
Base.metadata.create_all(bind=engine)

# JWT Configuration

class Settings(BaseModel):
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
    authjwt_secret_key: str = jwt_secret_key

@AuthJWT.load_config
def get_config():
    return Settings()

# Exception Handler for JWT Errors
@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request, exc):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
    )
@app.exception_handler(MissingTokenError)
async def missing_token_exception_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={"detail": "Missing token. Please provide a valid JWT token in the Authorization header."},
    )

@app.exception_handler(InvalidHeaderError)
async def invalid_header_exception_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid token. Please provide a valid JWT token."},
    )

# Register User
@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = bcrypt.hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)  
    return db_user
    
@app.post("/login", response_model=ApiResponse)
def login(user: UserLogin, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    # Retrieve user from the database
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not bcrypt.verify(user.password, db_user.password):
        return create_response(success=False, message="Invalid credentials")

    # Create access and refresh tokens
    access_token = Authorize.create_access_token(subject=db_user.id)
    refresh_token = Authorize.create_refresh_token(subject=db_user.id)

    # Include user details in the response
    user_data = {
        "username": db_user.username,
        "email": db_user.email,
        "is_active": db_user.is_active
    }

    return create_response(
        success=True,
        message="Login successful",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_data
        }
    )


@app.post("/refresh")
def refresh(Authorize: AuthJWT = Depends()):
    try:
        # Ensure the refresh token is valid
        Authorize.jwt_refresh_token_required()

        # Get the subject (user ID) from the refresh token
        current_user = Authorize.get_jwt_subject()

        # Create a new access token
        new_access_token = Authorize.create_access_token(subject=current_user)
        return {"access_token": new_access_token}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")

@app.get("/get-users")
def get_users(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()  # Ensure this is called to enforce token validation

    # Fetch all users from the database
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
        for user in users
    ]

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.username = user.username
    db_user.email = user.email
    db_user.password = bcrypt.hash(user.password)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"detail": "User deleted"}


# Customize Swagger with JWT
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
        description="API documentation with JWT auth",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/protected")
def protected(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    return {"message": "You are authorized!"}

@app.get("/openapi.json")
async def openapi():
    # Define the authorization scheme
    from fastapi.openapi.models import APIKeyScheme, APIKeyIn

    security_scheme = APIKeyScheme(
        type="apiKey", in_=APIKeyIn.HEADER, name="Authorization"
    )
    openapi_schema = app.openapi()
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": security_scheme
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    return openapi_schema

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

