from datetime import date, timedelta
import pytest
from pydantic import ValidationError
from sqlalchemy import Text

from app.models import Event as EventModel
from app.routers.events import router as events_router
from app.schemas import Event
from app.utils import (
    filter_events_by_location,
    filter_events_by_title,
)


# --- Happy Path Tests ---

def test_valid_event(sample_event_dict):
    event = Event(**sample_event_dict)

    assert event.title == "Python Workshop"
    assert event.capacity == 100
    assert event.location == "Constantine"


def test_filter_by_location(prepopulated_event_store):
    result = filter_events_by_location(
        prepopulated_event_store,
        "constantine"
    )

    assert len(result) == 2


def test_filter_by_title(prepopulated_event_store):
    result = filter_events_by_title(
        prepopulated_event_store,
        "PYTHON"
    )

    assert len(result) == 1
    assert result[0]["title"] == "Python Workshop"


# --- Boundary Value Tests ---

def test_minimum_capacity(sample_event_dict):
    sample_event_dict["capacity"] = 1

    event = Event(**sample_event_dict)

    assert event.capacity == 1


def test_maximum_capacity(sample_event_dict):
    sample_event_dict["capacity"] = 10000

    event = Event(**sample_event_dict)

    assert event.capacity == 10000


def test_minimum_title_length(sample_event_dict):
    sample_event_dict["title"] = "ABC"

    event = Event(**sample_event_dict)

    assert event.title == "ABC"


# --- Negative Tests ---

def test_short_title_rejected(sample_event_dict):
    sample_event_dict["title"] = "AB"

    with pytest.raises(ValidationError):
        Event(**sample_event_dict)


def test_zero_capacity_rejected(sample_event_dict):
    sample_event_dict["capacity"] = 0

    with pytest.raises(ValidationError):
        Event(**sample_event_dict)


def test_negative_capacity_rejected(sample_event_dict):
    sample_event_dict["capacity"] = -1

    with pytest.raises(ValidationError):
        Event(**sample_event_dict)


def test_excessive_capacity_rejected(sample_event_dict):
    sample_event_dict["capacity"] = 10001

    with pytest.raises(ValidationError):
        Event(**sample_event_dict)


# --- Lab 3 Mutation Testing & Coverage Enhancements (Student A Domain) ---

def test_filter_by_title_mixed_case(prepopulated_event_store):
    """Kill casefold/lower mutants with mixed-case search queries."""
    res1 = filter_events_by_title(prepopulated_event_store, "pYtHoN")
    assert len(res1) == 1
    assert res1[0]["title"] == "Python Workshop"

    res2 = filter_events_by_title(prepopulated_event_store, "cYbEr")
    assert len(res2) == 1
    assert res2[0]["title"] == "Cyber Security"

    res_empty = filter_events_by_title(prepopulated_event_store, "NonExistent")
    assert len(res_empty) == 0


def test_filter_by_location_mixed_case(prepopulated_event_store):
    """Kill casefold mutants for location filter with mixed case."""
    res = filter_events_by_location(prepopulated_event_store, "cOnStAnTiNe")
    assert len(res) == 2


def test_event_schema_defaults_and_from_attributes():
    """Kill mutants in app/schemas.py related to Event defaults and ORM mode."""
    ev = Event(title="DevOps Camp", location="Constantine", capacity=50)
    assert ev.description is None
    assert ev.date == date.today()
    assert ev.id is None

    class DummyEventObj:
        id = 42
        title = "DevOps Camp"
        description = "Intensive workshop"
        date = date.today()
        location = "Constantine"
        capacity = 50

    orm_event = Event.model_validate(DummyEventObj())
    assert orm_event.id == 42
    assert orm_event.title == "DevOps Camp"
    assert orm_event.description == "Intensive workshop"
    assert orm_event.date == date.today()


def test_event_model_metadata_and_constraints():
    """Kill column types, nullability, indices, and table name mutants for Event model."""
    assert EventModel.__tablename__ == "events"
    assert EventModel.id.property.columns[0].primary_key is True
    assert EventModel.id.property.columns[0].index is True
    assert EventModel.title.property.columns[0].nullable is False
    assert EventModel.title.property.columns[0].type.length == 100
    assert EventModel.description.property.columns[0].nullable is True
    assert isinstance(EventModel.description.property.columns[0].type, Text)
    assert EventModel.date.property.columns[0].nullable is False
    assert EventModel.location.property.columns[0].nullable is False
    assert EventModel.location.property.columns[0].type.length == 100
    assert EventModel.capacity.property.columns[0].nullable is False


def test_events_router_metadata():
    """Kill router tags and prefix mutations in app/routers/events.py."""
    assert events_router.prefix == "/events"
    assert events_router.tags == ["Events"]


def test_root_endpoint(client):
    """Test API root welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Event Manager API"}


def test_create_and_list_events_api(client):
    """Test POST /events/ and GET /events/ including search query parameter and boundary dates."""
    future_date = (date.today() + timedelta(days=10)).isoformat()
    today_date = date.today().isoformat()
    past_date = (date.today() - timedelta(days=1)).isoformat()

    # Valid creation with future date
    payload_future = {
        "title": "DevOps Summit",
        "description": "Annual conference",
        "date": future_date,
        "location": "Constantine",
        "capacity": 200
    }
    create_resp = client.post("/events/", json=payload_future)
    assert create_resp.status_code == 201
    created_id = create_resp.json()["id"]
    assert create_resp.json()["title"] == "DevOps Summit"

    # Valid creation with today's date (kills mutants changing < date.today() to <=)
    payload_today = {
        "title": "Today Meetup",
        "description": "Happening right now",
        "date": today_date,
        "location": "Batna",
        "capacity": 25
    }
    resp_today = client.post("/events/", json=payload_today)
    assert resp_today.status_code == 201
    assert resp_today.json()["title"] == "Today Meetup"

    # Past date validation error (HTTP 400) - exact message kills detail mutants
    payload_past = {
        "title": "Past Conference",
        "date": past_date,
        "location": "Constantine",
        "capacity": 100
    }
    resp_past = client.post("/events/", json=payload_past)
    assert resp_past.status_code == 400
    assert resp_past.json()["detail"] == "Event date cannot be in the past."

    # List all events
    list_resp = client.get("/events/")
    assert list_resp.status_code == 200
    assert any(ev["id"] == created_id for ev in list_resp.json())

    # List with search filter
    search_resp = client.get("/events/?search=Summit")
    assert search_resp.status_code == 200
    assert len(search_resp.json()) >= 1
    assert any(ev["title"] == "DevOps Summit" for ev in search_resp.json())


def test_get_update_delete_event_api(client):
    """Test GET /events/{id}, PUT /events/{id}, and DELETE /events/{id} endpoints."""
    future_date = (date.today() + timedelta(days=5)).isoformat()
    today_date = date.today().isoformat()
    past_date = (date.today() - timedelta(days=5)).isoformat()

    # Create event to work with
    create_resp = client.post("/events/", json={
        "title": "Cloud Workshop",
        "description": "Kubernetes hands-on",
        "date": future_date,
        "location": "Constantine",
        "capacity": 50
    })
    event_id = create_resp.json()["id"]

    # Filter via get_events endpoint with location (kills format mutants in ilike)
    loc_resp = client.get(f"/events/{event_id}?location=constantine")
    assert loc_resp.status_code == 200
    assert len(loc_resp.json()) >= 1
    assert any(ev["id"] == event_id for ev in loc_resp.json())

    # Filter via get_events endpoint with title (kills format mutants in ilike)
    title_resp = client.get(f"/events/{event_id}?title=cloud")
    assert title_resp.status_code == 200
    assert len(title_resp.json()) >= 1
    assert any(ev["id"] == event_id for ev in title_resp.json())

    # Update with today's date succeeds (kills <= date.today() mutant)
    update_today = client.put(f"/events/{event_id}", json={
        "title": "Cloud Workshop Today",
        "description": "Rescheduled for today",
        "date": today_date,
        "location": "Constantine",
        "capacity": 60
    })
    assert update_today.status_code == 200
    assert update_today.json()["title"] == "Cloud Workshop Today"

    # Successful update with future date
    updated_date = (date.today() + timedelta(days=15)).isoformat()
    update_resp = client.put(f"/events/{event_id}", json={
        "title": "Updated Cloud Workshop",
        "description": "Updated description",
        "date": updated_date,
        "location": "Algiers",
        "capacity": 75
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated Cloud Workshop"

    # Update with past date fails with exact message
    update_past = client.put(f"/events/{event_id}", json={
        "title": "Updated Cloud Workshop",
        "description": "Updated description",
        "date": past_date,
        "location": "Algiers",
        "capacity": 75
    })
    assert update_past.status_code == 400
    assert update_past.json()["detail"] == "Event date cannot be in the past."

    # Update non-existent event (HTTP 404 with exact detail)
    update_404 = client.put("/events/9999", json={
        "title": "Ghost Event",
        "date": updated_date,
        "location": "Nowhere",
        "capacity": 10
    })
    assert update_404.status_code == 404
    assert update_404.json()["detail"] == "Event found." or update_404.json()["detail"] == "Event not found."
    assert update_404.json()["detail"] == "Event not found."

    # Delete non-existent event (HTTP 404 with exact detail)
    delete_404 = client.delete("/events/9999")
    assert delete_404.status_code == 404
    assert delete_404.json()["detail"] == "Event not found."

    # Delete existing event
    delete_resp = client.delete(f"/events/{event_id}")
    assert delete_resp.status_code == 204
