from fastapi.testclient import TestClient
from src.main import app
from src.models.wine_models import WineData
import json

client = TestClient(app)

def test_create_wine():
    wine_data = {
        "name": "Test Wine",
        "type": "Red",
        "alcohol": 12.5,
        "sugar": 5.0,
        "acidity": 3.5,
        "quality": 7
    }
    response = client.post("/wines/", json=wine_data)
    assert response.status_code == 201
    assert response.json()["name"] == wine_data["name"]

def test_read_wine():
    response = client.get("/wines/1")
    assert response.status_code == 200
    assert "name" in response.json()

def test_update_wine():
    updated_data = {
        "name": "Updated Test Wine",
        "type": "Red",
        "alcohol": 13.0,
        "sugar": 4.0,
        "acidity": 3.0,
        "quality": 8
    }
    response = client.put("/wines/1", json=updated_data)
    assert response.status_code == 200
    assert response.json()["name"] == updated_data["name"]

def test_delete_wine():
    response = client.delete("/wines/1")
    assert response.status_code == 204

def test_get_all_wines():
    response = client.get("/wines/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)