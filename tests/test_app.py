"""
Comprehensive tests for the Mergington High School Activities API
Tests follow the AAA (Arrange-Act-Assert) pattern for clarity and maintainability
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Arrange: Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
    }
    
    # Clear and reset
    activities.clear()
    activities.update(original_activities)
    yield
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """GET /activities should return all activities"""
        # Arrange
        # (client fixture provides test client)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data

    def test_activity_has_correct_structure(self, client):
        """Activity object should contain required fields"""
        # Arrange
        # (client fixture provides test client)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        # Assert
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_participants_list_is_accurate(self, client):
        """Participants list should match initially registered students"""
        # Arrange
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        actual_participants = data["Chess Club"]["participants"]
        
        # Assert
        assert len(actual_participants) == len(expected_participants)
        for participant in expected_participants:
            assert participant in actual_participants


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_new_participant_signup_succeeds(self, client):
        """A new participant should successfully sign up for an activity"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_email in data["message"]

    def test_signup_adds_participant_to_list(self, client):
        """After signup, participant should appear in the activity's participants list"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        assert new_email in data[activity_name]["participants"]

    def test_duplicate_signup_fails_with_400(self, client):
        """Attempting to sign up an already-registered participant should return 400"""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_to_nonexistent_activity_fails_with_404(self, client):
        """Signing up for a non-existent activity should return 404"""
        # Arrange
        nonexistent_activity = "Fake Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_is_case_sensitive(self, client):
        """Email addresses with different cases should be treated as different participants"""
        # Arrange
        activity_name = "Programming Class"
        uppercase_email = "NEWSTUDENT@MERGINGTON.EDU"
        lowercase_email = "newstudent@mergington.edu"
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": uppercase_email}
        )
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": lowercase_email}
        )
        
        # Assert
        assert response.status_code == 200  # Different case = different email
        data = client.get("/activities").json()
        participants = data[activity_name]["participants"]
        assert uppercase_email in participants
        assert lowercase_email in participants

    def test_signup_with_empty_email_fails(self, client):
        """Attempting to sign up with empty email should return validation error"""
        # Arrange
        activity_name = "Chess Club"
        empty_email = ""
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": empty_email}
        )
        
        # Assert
        assert response.status_code == 422


class TestUnregisterFromActivity:
    """Test suite for DELETE /activities/{activity_name}/participants endpoint"""

    def test_existing_participant_unregister_succeeds(self, client):
        """An existing participant should successfully unregister from an activity"""
        # Arrange
        activity_name = "Chess Club"
        participant_to_remove = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": participant_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_from_participant_list(self, client):
        """After unregistering, participant should no longer appear in the list"""
        # Arrange
        activity_name = "Chess Club"
        participant_to_remove = "michael@mergington.edu"
        
        # Act
        client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": participant_to_remove}
        )
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        assert participant_to_remove not in data[activity_name]["participants"]

    def test_unregister_nonexistent_participant_fails_with_404(self, client):
        """Attempting to unregister a non-participant should return 404"""
        # Arrange
        activity_name = "Chess Club"
        nonexistent_email = "notexist@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": nonexistent_email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_from_nonexistent_activity_fails_with_404(self, client):
        """Unregistering from a non-existent activity should return 404"""
        # Arrange
        nonexistent_activity = "Fake Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_with_empty_email_fails(self, client):
        """Attempting to unregister with empty email should return validation error"""
        # Arrange
        activity_name = "Chess Club"
        empty_email = ""
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": empty_email}
        )
        
        # Assert
        assert response.status_code == 422


class TestRootEndpoint:
    """Test suite for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Root endpoint should redirect to static index.html"""
        # Arrange
        # (client fixture provides test client)
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestActivityWorkflows:
    """Integration tests for complete user workflows"""

    def test_full_signup_and_unregister_workflow(self, client):
        """Complete workflow: verify initial state → signup → verify joined → unregister → verify left"""
        # Arrange
        email = "integration@mergington.edu"
        activity = "Programming Class"
        
        # Act & Assert - Step 1: Verify student not initially signed up
        response = client.get("/activities")
        initial_participants = response.json()[activity]["participants"]
        assert email not in initial_participants
        initial_count = len(initial_participants)
        
        # Act & Assert - Step 2: Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Act & Assert - Step 3: Verify student is now signed up
        response = client.get("/activities")
        after_signup = response.json()[activity]["participants"]
        assert email in after_signup
        assert len(after_signup) == initial_count + 1
        
        # Act & Assert - Step 4: Unregister
        unreg_response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        assert unreg_response.status_code == 200
        
        # Act & Assert - Step 5: Verify student is no longer signed up
        response = client.get("/activities")
        after_unregister = response.json()[activity]["participants"]
        assert email not in after_unregister
        assert len(after_unregister) == initial_count

    def test_multiple_participants_signup_and_selective_unregister(self, client):
        """Multiple students should be able to signup; unregistering one should not affect others"""
        # Arrange
        activity = "Gym Class"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        initial_response = client.get("/activities")
        initial_participants = set(initial_response.json()[activity]["participants"])
        
        # Act - Step 1: Sign up multiple students
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert - Step 2: Verify all are signed up
        response = client.get("/activities")
        after_signups = set(response.json()[activity]["participants"])
        for email in emails:
            assert email in after_signups
        
        # Act - Step 3: Unregister the middle student
        client.delete(
            f"/activities/{activity}/participants",
            params={"email": emails[1]}
        )
        
        # Assert - Step 4: Verify only that one was removed
        response = client.get("/activities")
        after_unregister = set(response.json()[activity]["participants"])
        assert emails[0] in after_unregister
        assert emails[1] not in after_unregister
        assert emails[2] in after_unregister

    def test_signup_unregister_then_signup_again(self, client):
        """A student should be able to signup after unregistering"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act & Assert - Step 1: Unregister
        unreg_response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        assert unreg_response.status_code == 200
        
        # Assert - Step 2: Verify unregistered
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Act & Assert - Step 3: Sign up again
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Assert - Step 4: Verify signed up
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
