from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.auth import create_token, verify_token
from src.models.user_models import User
from src.models.token_models import Token

app = FastAPI()

# Test client for the FastAPI application
client = TestClient(app)

def test_create_token():
    user = User(username="testuser", password="testpassword")
    token = create_token(user)
    assert token is not None

def test_verify_token():
    user = User(username="testuser", password="testpassword")
    token = create_token(user)
    verified_user = verify_token(token)
    assert verified_user.username == user.username

def test_invalid_token():
    invalid_token = "invalidtoken"
    verified_user = verify_token(invalid_token)
    assert verified_user is None