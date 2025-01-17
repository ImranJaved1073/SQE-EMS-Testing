import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from dotenv import load_dotenv
from app import app, format_response, login_required, admin_required
import pytest
from flask import session
from datetime import datetime
from bson.objectid import ObjectId
from flask_pymongo import PyMongo
    
load_dotenv()

# Create a fixture to initialize the Flask app and MongoDB
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    app.config["MONGO_DBNAME"] = "test"  # Use the test database
    mongo = PyMongo(app)  # Initialize PyMongo here

    with app.test_client() as client:
        with app.app_context():
            yield client, mongo  # Pass both client and mongo to the tests

# UNIT TESTS
def test_format_response():
    with app.app_context():
        response = format_response(True, "Success")
        assert response.json == {"success": True, "message": "Success", "data": None}

def test_format_response_with_data():
    with app.app_context():
        response = format_response(True, "Success", data={"id": 1})
        assert response.json == {"success": True, "message": "Success", "data": {"id": 1}}

def test_login_invalid_credentials(client):
    client, mongo = client  # Get client and mongo from fixture
    response = client.post('/login', json={"cnic": "0000000000000", "dob": "2000-01-01"})
    assert response.json['success'] == False
    assert response.json['message'] == "Invalid credentials"

def test_login_no_data(client):
    client, mongo = client  # Get client and mongo from fixture
    response = client.post('/login', json={})
    assert response.json['success'] == False
    assert response.json['message'] == "Invalid credentials"


def test_login_required_decorator():
    def mock_protected_route():
        return "Protected"
    decorated = login_required(mock_protected_route)
    with app.test_request_context():
        session['user'] = {"id": "test_user", "role": "voter"}
        result = decorated()
    assert result == "Protected"


def test_admin_required_decorator():
    def mock_protected_route():
        return "Admin Protected"
    decorated = admin_required(mock_protected_route)
    with app.test_request_context():
        session['user'] = {"id": "test_admin", "role": "admin"}
        result = decorated()
    assert result == "Admin Protected"

# INTEGRATION TESTS - Authentication
def test_login_voter(client):
    client, mongo = client  # Get client and mongo from fixture
    # Insert a test voter
    mongo.db.voters.insert_one({
        "name": "Imran",
        "cnic": "3520237223175",
        "dob": "2003-02-03",
        "age": 21,
        "voted": False
    })
    response = client.post('/login', json={
        "cnic": "3520237223175",
        "dob": "2003-02-03"
    })
    print("Login response:", response.json)
    assert response.json['success'] == True
    mongo.db.voters.delete_one({"cnic": "3520237223175"})  # Clean up

def test_login_admin(client):
    client, mongo = client  # Get client and mongo from fixture
    # Insert a test admin
    mongo.db.admins.insert_one({
        "admin_id": "adminImran",
        "name": "Admin User",
        "cnic": "11111",
        "dob": "1999-01-01"
    })
    response = client.post('/login', json={
        "cnic": "11111",
        "dob": "1999-01-01"
    })
    print("Admin login response:", response.json)
    assert response.json['success'] == True
    mongo.db.admins.delete_one({"cnic": "11111"})  # Clean up

# Voter Management
def test_register_voter(client):
    client, mongo = client  # Get client and mongo from fixture
    with client.session_transaction() as sess:
        sess['user'] = {"id": "adminImran", "role": "admin"}
    response = client.post('/register_voter', json={
        "name": "John Doe",
        "cnic": "11111",
        "dob": "2000-01-01"
    })
    print("Register response:", response.json)
    assert response.json['success'] == True
    mongo.db.voters.delete_one({"cnic": "11111"})  # Clean up


def test_add_candidate_success(client):
    client, mongo = client  # Get client and mongo from fixture

    # Login as admin
    with client.session_transaction() as sess:
        sess['user'] = {"id": "adminImran", "role": "admin"}

    # Add a valid candidate
    response = client.post('/add_candidate', json={
        "name": "Candidate A",
        "party": "Party A",
        "cnic": "1234567890123",
        "dob": "1980-01-01"
    })
    assert response.status_code == 200
    assert response.json['success'] == True
    assert response.json['message'] == "Candidate added successfully."

    # Cleanup: Remove the candidate after test
    mongo.db.candidates.delete_one({"cnic": "1234567890123"})


def test_get_candidates(client):
    client, mongo = client  # Get client and mongo from fixture
    # Insert a test candidate
    candidate_id = mongo.db.candidates.insert_one({
        "name": "ahmad",
        "party": "A",
        "cnic": "66666",
        "dob": "1990-01-01"
    }).inserted_id
    with client.session_transaction() as sess:
        sess['user'] = {"id": "voter123", "role": "voter"}
    response = client.get('/get_candidates')
    print("Get candidates response:", response.json)
    assert response.json['success'] == True
    mongo.db.candidates.delete_one({"_id": candidate_id})  # Clean up

# Election management
def test_create_election(client):
    client, mongo = client  # Get client and mongo from fixture
    candidate_id = mongo.db.candidates.insert_one({
        "name": "Iman",
        "party": "A",
        "cnic": "55555",
        "dob": "1990-01-01"
    }).inserted_id

    with client.session_transaction() as sess:
        sess['user'] = {"id": "adminImran", "role": "admin"}

    # Clean up: Ensure no conflicting elections exist
    mongo.db.elections.delete_many({})

    # Use simple date format 'YYYY-MM-DD HH:MM:SS' for start and end dates
    start_date = "2024-12-12 11:53:00"
    end_date = "2024-12-24 01:54:00"

    response = client.post('/create_election', json={
        "name": "pti election",
        "start_date": start_date,  # Passed as a string in 'YYYY-MM-DD HH:MM:SS' format
        "end_date": end_date,  # Passed as a string in 'YYYY-MM-DD HH:MM:SS' format
        "candidate_ids": [str(candidate_id)]
    })
    print("Create election response:", response.json)
    assert response.json['success'] == True
    mongo.db.elections.delete_one({"name": "pti election"})  # Clean up
    mongo.db.candidates.delete_one({"_id": candidate_id})  # Clean up

def test_edit_election(client):
    client, mongo = client  # Get client and mongo from fixture

    # Insert a candidate
    candidate_id = mongo.db.candidates.insert_one({
        "name": "Babar",
        "party": "A",
        "cnic": "55555",
        "dob": "1990-01-01"
    }).inserted_id

    # Insert an election
    election_id = mongo.db.elections.insert_one({
        "name": "pti election",
        "start_date": "2024-12-12 11:53:00",  # Simple date string without weekday and timezone
        "end_date": "2024-12-24 01:54:00",  # Simple date string without weekday and timezone
        "candidates": [{"_id": candidate_id, "name": "Babar", "party": "A"}],
        "votes": {}
    }).inserted_id

    with client.session_transaction() as sess:
        sess['user'] = {"id": "adminImran", "role": "admin"}

    # Ensure the election exists before attempting to edit it
    election = mongo.db.elections.find_one({"_id": election_id})
    assert election is not None, "Election was not found in the database before edit."

    # Attempt to edit the election
    start_date = "2024-12-12 11:53:00"  # Simple date string without weekday and timezone
    end_date = "2024-12-24 01:54:00"  # Simple date string without weekday and timezone

    try:
        response = client.put(f'/edit_election/{str(election_id)}', json={
            "name": "updated election",
            "start_date": start_date,
            "end_date": end_date,
            "candidate_ids": [str(candidate_id)]
        })
        print("Edit election response:", response.json)

        # Assert that the response indicates success
        assert response.json['success'] == True
    finally:
        # Clean up the test data after assertions
        mongo.db.elections.delete_one({"_id": election_id})  # Delete the election
        mongo.db.candidates.delete_one({"_id": candidate_id})  # Clean up candidate


def test_access_denied(client):
    client, mongo = client  # Get client and mongo from fixture
    # No session set (unauthorized)
    response = client.get('/admin_dashboard')
    # Ensure unauthorized access returns 403
    assert response.status_code == 403


def test_register_voter_duplicate(client):
    client, mongo = client  # Get client and mongo from fixture

    # Add a voter manually to simulate duplicate scenario
    mongo.db.voters.insert_one({
        "name": "John Doe",
        "cnic": "22222",
        "dob": "2000-01-01"
    })

    # Set session for admin user
    with client.session_transaction() as sess:
        sess['user'] = {"id": "adminImran", "role": "admin"}

    # Try registering the same voter again
    response = client.post('/register_voter', json={
        "name": "John Doe",
        "cnic": "22222",
        "dob": "2000-01-01"
    })
    print("Register response (duplicate):", response.json)

    # Assertions
    assert response.json['success'] == False
    assert response.json['message'] == "Voter already registered."

    # Cleanup
    mongo.db.voters.delete_one({"cnic": "22222"})


def test_register_voter_success(client):
    client, mongo = client  # Get client and mongo from fixture
    
    # Cleanup: Ensure the voter doesn't already exist
    mongo.db.voters.delete_one({"cnic": "12345"})

    # Set session for admin user
    with client.session_transaction() as sess:
        sess['user'] = {"id": "adminImran", "role": "admin"}

    # Register voter
    response = client.post('/register_voter', json={
        "name": "John Doe",
        "cnic": "12345",
        "dob": "2000-01-01"
    })
    print("Register response (valid case):", response.json)

    # Assertions
    assert response.json is not None, "Response should not be None"
    assert response.json['success'] == True
    assert response.json['message'] == "Voter registered successfully."

    # Ensure voter exists in database
    voter = mongo.db.voters.find_one({"cnic": "12345"})
    assert voter is not None
    assert voter['name'] == "John Doe"
    assert voter['dob'] == "2000-01-01"

    # Cleanup
    mongo.db.voters.delete_one({"cnic": "12345"})


def test_register_voter_unauthorized(client):
    client, mongo = client  # Get client and mongo from fixture

    # No session set (unauthorized)
    response = client.post('/register_voter', json={
        "name": "John Doe",
        "cnic": "1234567890123",
        "dob": "2000-01-01"
    })

    # Ensure unauthorized access returns 403
    assert response.status_code == 403

    # Check if the response is JSON and contains the expected message
    if response.is_json:
        response_json = response.get_json()
        assert response_json is not None
        assert 'success' in response_json
        assert response_json['success'] is False
        assert 'message' in response_json
        assert "Unauthorized access" in response_json['message']  # Adjust based on actual error message
    else:
        # If the response is not JSON, assert that it's a forbidden message
        assert "Access Denied" in response.data.decode()  # Adjust based on actual error message

def test_register_voter_invalid_data(client):
    client, mongo = client  # Get client and mongo from fixture

    # Set session for admin user
    with client.session_transaction() as sess:
        sess['user'] = {"id": "adminImran", "role": "admin"}

    # Try registering a voter with invalid data
    response = client.post('/register_voter', json={
        "name": "John Doe",
        "cnic": "asd",
        "dob": "2000-01-01"
    })
    print("Register response (invalid data):", response.json)

def test_register_voter_underage(client):
    client, mongo = client  # Get client and mongo from fixture

    # Set session for admin user
    with client.session_transaction() as sess:
        sess['user'] = {"id": "adminImran", "role": "admin"}

    # Try registering a voter who is underage
    response = client.post('/register_voter', json={
        "name": "John Doe",
        "cnic": "1234567890123",
        "dob": "2010-01-01"
    })
    assert response.json['success'] == False
    assert response.json['message'] == "Voter must be at least 18 years old."


def test_add_candidate_duplicate(client):
    client, mongo = client  # Get client and mongo from fixture

    with client.session_transaction() as sess:
        sess['user'] = {"id": "adminImran", "role": "admin"}

    # Add a candidate
    mongo.db.candidates.insert_one({
        "name": "Candidate A",
        "party": "Party A",
        "cnic": "11111",
        "dob": "1980-01-01"
    })

    # Try adding the same candidate again
    response = client.post('/add_candidate', json={
        "name": "Candidate A",
        "party": "Party A",
        "cnic": "11111",
        "dob": "1980-01-01"
    })
    assert response.json['success'] == False
    assert response.json['message'] == "Candidate already exists."

    # Cleanup
    mongo.db.candidates.delete_one({"cnic": "11111"})



def test_create_election_conflict(client):
    client, mongo = client  # Get client and mongo from fixture

    with client.session_transaction() as sess:
        sess['user'] = {"id": "adminImran", "role": "admin"}

    # Add a candidate
    candidate_id = mongo.db.candidates.insert_one({
        "name": "Candidate C",
        "party": "Party C",
        "cnic": "33333",
        "dob": "1980-01-01"
    }).inserted_id

    # Create an election
    mongo.db.elections.insert_one({
        "name": "Election A",
        "start_date": datetime(2024, 12, 1),
        "end_date": datetime(2024, 12, 10),
        "candidates": [{"_id": candidate_id, "name": "Candidate C", "party": "Party C"}]
    })

    # Try creating another election with conflicting dates
    response = client.post('/create_election', json={
        "name": "Election B",
        "start_date": "2024-12-05",
        "end_date": "2024-12-15",
        "candidate_ids": [str(candidate_id)]
    })
    assert response.json['success'] == False
    assert response.json['message'] == "Election schedule conflicts with an existing election."

    # Cleanup
    mongo.db.elections.delete_many({})
    mongo.db.candidates.delete_one({"_id": candidate_id})