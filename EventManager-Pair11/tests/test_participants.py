import threading
import pytest
from pydantic import ValidationError

from app.models import Participant as ParticipantModel, Registration as RegistrationModel
from app.routers.participants import router as participants_router
from app.routers.registrations import router as registrations_router
from app.schemas import Participant, Registration as RegistrationSchema
from app.utils import (
    check_duplicate_registration,
    has_available_capacity,
)


# --- Happy Path Tests ---

def test_valid_participant(sample_participant_dict):
    participant = Participant(**sample_participant_dict)

    assert participant.name == "Soheib"
    assert participant.email == "soheib@example.com"


def test_has_available_capacity_success():
    assert has_available_capacity(current_count=50, max_capacity=100) is True


def test_check_duplicate_registration_success():
    assert check_duplicate_registration(registered_ids=[1, 2, 3], new_id=4) is True


# --- Boundary Value Tests ---

def test_capacity_boundary_below_max():
    assert has_available_capacity(current_count=99, max_capacity=100) is True


def test_capacity_boundary_at_max():
    assert has_available_capacity(current_count=100, max_capacity=100) is False


def test_capacity_boundary_above_max():
    assert has_available_capacity(current_count=101, max_capacity=100) is False


def test_minimum_name_length(sample_participant_dict):
    sample_participant_dict["name"] = "Al"

    participant = Participant(**sample_participant_dict)

    assert participant.name == "Al"


# --- Negative Tests ---

def test_short_name_rejected(sample_participant_dict):
    sample_participant_dict["name"] = "A"

    with pytest.raises(ValidationError):
        Participant(**sample_participant_dict)


def test_invalid_email_rejected(sample_participant_dict):
    sample_participant_dict["email"] = "not-an-email"

    with pytest.raises(ValidationError):
        Participant(**sample_participant_dict)


def test_duplicate_registration_raises_error():
    """Negative test: registering an already existing participant ID must raise ValueError with exact message."""
    with pytest.raises(ValueError, match="^Participant already registered$"):
        check_duplicate_registration(registered_ids=[1, 2, 3], new_id=2)


# --- Lab 3 Mutation Testing & Coverage Enhancements (Student B Domain) ---

@pytest.mark.parametrize("invalid_email", [
    "plainaddress",
    "@missingusername.com",
    "missingdomain@",
    "missingdot@domain",
    "user with spaces@domain.com",
    "two@@domain.com",
])
def test_email_format_mutants_rejected(invalid_email, sample_participant_dict):
    """Kill regex validation mutants by testing invalid email address patterns."""
    sample_participant_dict["email"] = invalid_email
    with pytest.raises(ValidationError):
        Participant(**sample_participant_dict)


def test_name_max_length_boundary_mutants():
    """Kill name max_length boundary mutants (e.g. 100 mutated to 101)."""
    # Exact max length of 100 characters must pass
    valid_p = Participant(name="A" * 100, email="user100@example.com")
    assert len(valid_p.name) == 100

    # 101 characters must be rejected
    with pytest.raises(ValidationError):
        Participant(name="A" * 101, email="user101@example.com")


def test_capacity_guard_boundary_zero():
    """Kill boundary mutation when current and max capacity are both zero or equal."""
    assert has_available_capacity(current_count=0, max_capacity=0) is False
    assert has_available_capacity(current_count=5, max_capacity=5) is False


def test_check_duplicate_registration_empty_store():
    """Verify duplicate check passes with empty registered set."""
    assert check_duplicate_registration(registered_ids=[], new_id=1) is True


def test_participant_and_registration_schema_config():
    """Kill mutants in app/schemas.py for Participant and Registration defaults & ORM config."""
    p = Participant(name="Karim", email="karim@example.com")
    assert p.id is None

    class DummyPartObj:
        id = 10
        name = "Karim"
        email = "karim@example.com"

    p_orm = Participant.model_validate(DummyPartObj())
    assert p_orm.id == 10
    assert p_orm.name == "Karim"
    assert p_orm.email == "karim@example.com"

    class DummyRegObj:
        id = 99
        event_id = 7
        participant_id = 10

    reg_orm = RegistrationSchema.model_validate(DummyRegObj())
    assert reg_orm.id == 99
    assert reg_orm.event_id == 7
    assert reg_orm.participant_id == 10


def test_get_db_generator():
    """Test get_db dependency generator cleanup."""
    from app.database import get_db
    gen = get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass


def test_main_app_metadata():
    """Kill metadata mutations in app/main.py."""
    from app.main import app
    assert app.title == "Event Manager API"
    assert app.description == "A teaching project for Git, Docker and CI/CD"
    assert app.version == "1.0.0"


def test_database_configuration():
    """Kill configuration mutations in app/database.py."""
    from app.database import DATABASE_URL, SessionLocal
    assert "events.db" in DATABASE_URL
    assert SessionLocal.kw.get("autocommit") is False
    assert SessionLocal.kw.get("autoflush") is False


def test_database_thread_concurrency():
    """Kill mutant changing check_same_thread to True in app/database.py."""
    from app.database import engine
    conn = engine.raw_connection()
    error = None

    def worker():
        nonlocal error
        try:
            conn.driver_connection.cursor()
        except Exception as exc:
            error = exc

    t = threading.Thread(target=worker)
    t.start()
    t.join()
    conn.close()

    assert error is None, f"check_same_thread should be False but got thread error: {error}"


def test_models_metadata_and_constraints():
    """Kill table names, column types, lengths, indices, and constraints in app/models.py."""
    # Table names
    assert ParticipantModel.__tablename__ == "participants"
    assert RegistrationModel.__tablename__ == "registrations"

    # Participant columns
    assert ParticipantModel.id.property.columns[0].primary_key is True
    assert ParticipantModel.id.property.columns[0].index is True
    assert ParticipantModel.name.property.columns[0].nullable is False
    assert ParticipantModel.name.property.columns[0].type.length == 100
    assert ParticipantModel.email.property.columns[0].nullable is False
    assert ParticipantModel.email.property.columns[0].type.length == 150
    assert ParticipantModel.email.property.columns[0].unique is True
    assert ParticipantModel.email.property.columns[0].index is True

    # Registration columns and constraints
    assert RegistrationModel.id.property.columns[0].primary_key is True
    assert RegistrationModel.id.property.columns[0].index is True
    assert RegistrationModel.event_id.property.columns[0].nullable is False
    assert RegistrationModel.participant_id.property.columns[0].nullable is False
    assert RegistrationModel.__table_args__[0].name == "uq_event_participant"


def test_routers_metadata():
    """Kill router tags and prefix mutations for participants and registrations."""
    assert participants_router.prefix == "/participants"
    assert participants_router.tags == ["Participants"]
    assert registrations_router.prefix == "/events"
    assert registrations_router.tags == ["Registrations"]


def test_participant_crud_api(client):
    """Test POST, GET, and DELETE operations on /participants/ endpoint."""
    # Create valid participant
    create_resp = client.post("/participants/", json={
        "name": "Sarah",
        "email": "sarah@example.com"
    })
    assert create_resp.status_code == 201
    participant_id = create_resp.json()["id"]
    assert create_resp.json()["name"] == "Sarah"

    # Duplicate email conflict (HTTP 409 with exact detail message)
    dup_resp = client.post("/participants/", json={
        "name": "Sarah Duplicate",
        "email": "sarah@example.com"
    })
    assert dup_resp.status_code == 409
    assert dup_resp.json()["detail"] == "Email is already registered."

    # List participants
    list_resp = client.get("/participants/")
    assert list_resp.status_code == 200
    assert any(p["id"] == participant_id for p in list_resp.json())

    # Get single participant
    get_resp = client.get(f"/participants/{participant_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "sarah@example.com"

    # Get non-existent participant (HTTP 404 with exact detail message)
    get_404 = client.get("/participants/9999")
    assert get_404.status_code == 404
    assert get_404.json()["detail"] == "Participant not found."

    # Delete existing participant
    del_resp = client.delete(f"/participants/{participant_id}")
    assert del_resp.status_code == 204

    # Delete non-existent participant (HTTP 404 with exact detail message)
    del_404 = client.delete("/participants/9999")
    assert del_404.status_code == 404
    assert del_404.json()["detail"] == "Participant not found."


def test_registration_flow_and_guard_mutants(client):
    """Test event registration flow, duplicate check (409), and capacity guard mutants."""
    from datetime import date, timedelta
    event_date = (date.today() + timedelta(days=20)).isoformat()

    # 1. Create an event with capacity = 1
    ev_resp = client.post("/events/", json={
        "title": "Exclusive Meetup",
        "date": event_date,
        "location": "Constantine",
        "capacity": 1
    })
    event_id = ev_resp.json()["id"]

    # 2. Create two participants
    p1_resp = client.post("/participants/", json={"name": "Alice", "email": "alice@example.com"})
    p1_id = p1_resp.json()["id"]

    p2_resp = client.post("/participants/", json={"name": "Bob", "email": "bob@example.com"})
    p2_id = p2_resp.json()["id"]

    # 3. Registration with non-existent event (HTTP 404 with exact detail)
    reg_err1 = client.post(f"/events/9999/register/{p1_id}")
    assert reg_err1.status_code == 404
    assert reg_err1.json()["detail"] == "Event not found."

    # 4. Registration with non-existent participant (HTTP 404 with exact detail)
    reg_err2 = client.post(f"/events/{event_id}/register/9999")
    assert reg_err2.status_code == 404
    assert reg_err2.json()["detail"] == "Participant not found."

    # 5. Successful registration (1 spot filled, now at full capacity)
    reg_ok = client.post(f"/events/{event_id}/register/{p1_id}")
    assert reg_ok.status_code == 201

    # 6. Duplicate registration guard: registering p1 again to event must fail with HTTP 409
    dup_reg = client.post(f"/events/{event_id}/register/{p1_id}")
    assert dup_reg.status_code == 409
    assert dup_reg.json()["detail"] == "Participant is already registered."

    # 7. Capacity guard mutant: event capacity=1 is reached, p2 cannot register
    cap_reg = client.post(f"/events/{event_id}/register/{p2_id}")
    assert cap_reg.status_code == 409
    assert cap_reg.json()["detail"] == "Event capacity has been reached."

    # 8. List event participants with exact structure (kills "XXidXX" and "XXemailXX" mutants)
    part_resp = client.get(f"/events/{event_id}/participants")
    assert part_resp.status_code == 200
    assert part_resp.json() == [{
        "id": p1_id,
        "name": "Alice",
        "email": "alice@example.com"
    }]

    # 9. List participants for non-existent event (HTTP 404 with exact detail)
    part_404 = client.get("/events/9999/participants")
    assert part_404.status_code == 404
    assert part_404.json()["detail"] == "Event not found."
