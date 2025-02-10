import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Base, get_db
from app import app

# Configure the test database
TEST_DATABASE_URL = "postgresql://postgres:123456@localhost:5432/mydb"  # Using SQLite for testing

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override the database dependency in the app
@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=test_engine)
    try:
        yield TestSessionLocal()
    finally:
        Base.metadata.drop_all(bind=test_engine)

@app.dependency_overrides[get_db]
def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test client
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

# Test data
USER_DATA = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
}

@pytest.fixture
def create_user(client):
    """Fixture to create a user for testing"""
    response = client.post("/register", json=USER_DATA)
    return response

def test_register_user(client):
    response = client.post("/register", json=USER_DATA)
    assert response.status_code == 200
    assert response.json()["email"] == USER_DATA["email"]

def test_register_duplicate_user(client, create_user):
    response = client.post("/register", json=USER_DATA)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_user(client, create_user):
    response = client.post("/login", json=USER_DATA)
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_get_users(client, create_user):
    # Login to get the token
    login_response = client.post("/login", json=USER_DATA)
    token = login_response.json()["access_token"]

    # Use token to access protected route
    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_get_user_by_id(client, create_user):
    # Login to get the token
    login_response = client.post("/login", json=USER_DATA)
    token = login_response.json()["access_token"]

    # Fetch user details
    response = client.get("/users/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == USER_DATA["username"]

def test_update_user(client, create_user):
    # Login to get the token
    login_response = client.post("/login", json=USER_DATA)
    token = login_response.json()["access_token"]

    # Update user details
    updated_data = {
        "username": "updateduser",
        "email": "updated@example.com",
        "password": "newpassword123",
    }
    response = client.put(
        "/users/1",
        json=updated_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == updated_data["username"]

def test_delete_user(client, create_user):
    # Login to get the token
    login_response = client.post("/login", json=USER_DATA)
    token = login_response.json()["access_token"]

    # Delete user
    response = client.delete("/users/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["detail"] == "User deleted"
