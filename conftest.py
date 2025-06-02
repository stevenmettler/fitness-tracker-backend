import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.database.database import Base, get_db
from main import app

# Test environment setup
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENVIRONMENT"] = "test"

# Use PostgreSQL for testing - matches production environment
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://localhost/fitness_tracker_test"  # Default test DB
)

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine for the entire test session"""
    engine = create_engine(TEST_DATABASE_URL)
    
    # Create all tables at start of test session
    Base.metadata.create_all(bind=engine)
    yield engine
    
    # Optional: Drop all tables after test session (uncomment if desired)
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a fresh database session for each test"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up data between tests (but keep table structure)
        with test_engine.connect() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE"))
            connection.commit()

@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()