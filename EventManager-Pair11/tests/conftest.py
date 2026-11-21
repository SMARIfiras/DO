import pytest


@pytest.fixture
def sample_event_dict():
    return {
        "title": "Python Workshop",
        "location": "Constantine",
        "capacity": 100
    }


@pytest.fixture
def sample_participant_dict():
    return {
        "name": "Soheib",
        "email": "soheib@example.com"
    }


@pytest.fixture
def mock_event_store():
    store = []
    yield store
    store.clear()


@pytest.fixture
def prepopulated_event_store(mock_event_store):
    mock_event_store.extend([
        {
            "title": "Python Workshop",
            "location": "Constantine",
            "capacity": 100
        },
        {
            "title": "Cyber Security",
            "location": "Algiers",
            "capacity": 50
        },
        {
            "title": "Network Security",
            "location": "Constantine",
            "capacity": 30
        }
    ])
    return mock_event_store


@pytest.fixture(autouse=True)
def global_environment_logger():
    print("\n[SETUP] Test starting")
    yield
    print("\n[TEARDOWN] Test finished")


@pytest.fixture
def db_session():
    """In-memory SQLite database session isolated for API testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """TestClient configured with dependency overrides for database."""
    from fastapi.testclient import TestClient
    from app.database import get_db
    from app.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

    