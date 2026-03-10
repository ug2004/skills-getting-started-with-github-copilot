import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activity state before/after each test."""
    original = copy.deepcopy(activities)

    # Arrange: ensure a clean starting state for each test
    activities.clear()
    activities.update(copy.deepcopy(original))

    yield

    # Cleanup: restore original state after the test
    activities.clear()
    activities.update(copy.deepcopy(original))


@pytest.fixture
def client():
    return TestClient(app)


def test_get_activities_returns_expected_structure(client):
    # Arrange: nothing special (use the fixture state)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_adds_participant_and_blocks_duplicates(client):
    # Arrange
    email = "newstudent@mergington.edu"

    # Act: first signup
    signup_resp = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert first signup
    assert signup_resp.status_code == 200
    assert email in client.get("/activities").json()["Chess Club"]["participants"]

    # Act: duplicate signup
    dup_resp = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert duplicate is rejected
    assert dup_resp.status_code == 400
    assert "already signed up" in dup_resp.json().get("detail", "").lower()


def test_delete_participant_removes_them_and_errors_if_missing(client):
    # Arrange
    email = "michael@mergington.edu"
    assert email in client.get("/activities").json()["Chess Club"]["participants"]

    # Act: delete participant
    delete_resp = client.delete(
        "/activities/Chess%20Club/participants", params={"email": email}
    )

    # Assert removal
    assert delete_resp.status_code == 200
    assert email not in client.get("/activities").json()["Chess Club"]["participants"]

    # Act: delete again
    missing_resp = client.delete(
        "/activities/Chess%20Club/participants", params={"email": email}
    )

    # Assert 404 when not found
    assert missing_resp.status_code == 404
