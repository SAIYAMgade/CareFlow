import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import get_db
from backend.app.db.init_db import init_database
from scripts.seed_data import seed_database

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    seed_database(random_seed=42)

@pytest.fixture
def client():
    return TestClient(app)
