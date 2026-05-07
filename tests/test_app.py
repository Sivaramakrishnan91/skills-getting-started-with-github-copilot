"""
Tests for the Mergington High School Activities API

Using AAA (Arrange-Act-Assert) pattern for clear test structure.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Arrange: Create a test client for the FastAPI app
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture to reset activities to initial state before each test
    This ensures test isolation and prevents cross-test pollution
    """
    # Store original state
    original_activities = {
        name: {
            "description": detail["description"],
            "schedule": detail["schedule"],
            "max_participants": detail["max_participants"],
            "participants": detail["participants"].copy()
        }
        for name, detail in activities.items()
    }
    
    yield
    
    # Reset activities after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client, reset_activities):
        """
        Test that GET /activities returns all activities with correct structure
        
        Arrange: TestClient is ready
        Act: Make GET request to /activities
        Assert: Verify response status, structure, and all activities returned
        """
        # Arrange
        expected_activity_count = 9
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == expected_activity_count
        
        # Verify structure of each activity
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_activities_have_participants(self, client, reset_activities):
        """
        Test that existing activities have their initial participants
        
        Arrange: TestClient is ready
        Act: Get activities data
        Assert: Verify activities have pre-populated participants
        """
        # Arrange
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client, reset_activities):
        """
        Test successful signup for an activity
        
        Arrange: Prepare valid input (activity and email)
        Act: Make POST request to signup
        Assert: Verify response status, message, and participant list updated
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
        assert new_email in activities[activity_name]["participants"]
    
    def test_duplicate_signup_fails(self, client, reset_activities):
        """
        Test that duplicate signup is rejected
        
        Arrange: Prepare email already signed up
        Act: Try to signup with existing participant email
        Assert: Verify 400 error with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"
    
    def test_signup_to_nonexistent_activity_fails(self, client, reset_activities):
        """
        Test that signup to non-existent activity returns 404
        
        Arrange: Prepare non-existent activity name
        Act: Try to signup to activity that doesn't exist
        Assert: Verify 404 error with appropriate message
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_increments_participant_count(self, client, reset_activities):
        """
        Test that signup properly increments participant count
        
        Arrange: Get initial participant count
        Act: Perform signup
        Assert: Verify participant count increased by 1
        """
        # Arrange
        activity_name = "Programming Class"
        initial_count = len(activities[activity_name]["participants"])
        new_email = "programmer@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count + 1


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_successful_unregister(self, client, reset_activities):
        """
        Test successful unregister from activity
        
        Arrange: Identify participant to remove
        Act: Make DELETE request to unregister
        Assert: Verify response status, message, and participant removed
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email_to_remove}"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email_to_remove} from {activity_name}"
        assert email_to_remove not in activities[activity_name]["participants"]
    
    def test_unregister_from_nonexistent_activity_fails(self, client, reset_activities):
        """
        Test that unregister from non-existent activity returns 404
        
        Arrange: Prepare non-existent activity name
        Act: Try to unregister from activity that doesn't exist
        Assert: Verify 404 error with appropriate message
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_not_signed_up_fails(self, client, reset_activities):
        """
        Test that unregister for non-participant returns 400
        
        Arrange: Prepare email not signed up for activity
        Act: Try to unregister someone not in participants
        Assert: Verify 400 error with appropriate message
        """
        # Arrange
        activity_name = "Soccer Team"
        email = "noone@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student not signed up for this activity"
    
    def test_unregister_decrements_participant_count(self, client, reset_activities):
        """
        Test that unregister properly decrements participant count
        
        Arrange: Get initial participant count
        Act: Perform unregister
        Assert: Verify participant count decreased by 1
        """
        # Arrange
        activity_name = "Gym Class"
        email_to_remove = "john@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email_to_remove}"
        )
        
        # Assert
        assert response.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count - 1


class TestRoot:
    """Tests for GET / redirect endpoint"""
    
    def test_root_redirects_to_static(self, client, reset_activities):
        """
        Test that root path redirects to static HTML
        
        Arrange: TestClient is ready
        Act: Make GET request to /
        Assert: Verify redirect status and location
        """
        # Arrange
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_and_unregister_flow(self, client, reset_activities):
        """
        Test complete flow: signup -> verify -> unregister -> verify
        
        Arrange: Prepare activity and new email
        Act: Signup, check presence, unregister, check absence
        Assert: Verify all operations succeeded
        """
        # Arrange
        activity_name = "Drama Club"
        email = "actor@mergington.edu"
        
        # Act: Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert: Signup successful
        assert signup_response.status_code == 200
        assert email in activities[activity_name]["participants"]
        
        # Act: Get activities to verify presence
        get_response = client.get("/activities")
        
        # Assert: Participant is in list
        assert email in get_response.json()[activity_name]["participants"]
        
        # Act: Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert: Unregister successful
        assert unregister_response.status_code == 200
        assert email not in activities[activity_name]["participants"]
    
    def test_multiple_signups_to_activity(self, client, reset_activities):
        """
        Test that multiple different participants can signup to same activity
        
        Arrange: Prepare multiple emails for same activity
        Act: Signup each participant
        Assert: All are added to participants list
        """
        # Arrange
        activity_name = "Science Olympiad"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Act & Assert: Signup each student
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            assert response.status_code == 200
            assert email in activities[activity_name]["participants"]
        
        # Assert: All are present
        assert len([e for e in emails if e in activities[activity_name]["participants"]]) == 3
