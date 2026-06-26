"""Backend tests for the Mergington High School activities API.

Tests follow the Arrange-Act-Assert (AAA) pattern and exercise the
signup and unregister flows, including their validation paths.
"""

import copy
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Make the application package importable from the src directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import app, activities  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    """Snapshot the shared in-memory state before each test and restore it after."""
    # Arrange: keep a pristine copy so tests stay isolated
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities_returns_catalog():
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_adds_participant():
    # Arrange
    email = "tester@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert email in participants


def test_signup_rejects_duplicate():
    # Arrange
    email = "dupe@mergington.edu"
    client.post("/activities/Chess Club/signup", params={"email": email})

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_unknown_activity_returns_404():
    # Act
    response = client.post(
        "/activities/Nonexistent Club/signup", params={"email": "x@mergington.edu"}
    )

    # Assert
    assert response.status_code == 404


def test_unregister_removes_participant():
    # Arrange: use a pre-seeded participant
    email = "michael@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/unregister", params={"email": email})

    # Assert
    assert response.status_code == 200
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert email not in participants


def test_unregister_when_not_signed_up_returns_400():
    # Act
    response = client.post(
        "/activities/Chess Club/unregister", params={"email": "ghost@mergington.edu"}
    )

    # Assert
    assert response.status_code == 400


def test_unregister_unknown_activity_returns_404():
    # Act
    response = client.post(
        "/activities/Nonexistent Club/unregister", params={"email": "x@mergington.edu"}
    )

    # Assert
    assert response.status_code == 404
