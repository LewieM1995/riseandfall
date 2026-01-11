import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock, ANY
from database_operations import database_operations
from systems.unit_training import queue_unit_training
from systems.resources.resources import get_player_total_resources_for_user
from routes.army import get_army_units
from flask import Flask
from datetime import datetime, timedelta
import json
from functools import wraps

# Create a mock auth decorator that sets user_id
def mock_require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        # Set a default user_id for testing
        if not hasattr(request, 'user_id'):
            request.user_id = 1
        return f(*args, **kwargs)
    return decorated_function

# Patch the auth decorator BEFORE importing the blueprint
with patch('auth_decorator.auth_decorator.require_auth', mock_require_auth):
    from routes.resources import resource_bp
    from routes.settlements import settlement_bp
    
@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.register_blueprint(resource_bp)
    app.register_blueprint(settlement_bp)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()
    
    
class TestEndpoints:
    """Test Flask API endpoints"""
    
    @patch('routes.resources.get_player_id_for_user')
    @patch('routes.resources.get_player_total_resources_for_user')
    def test_get_total_resources_success(self, mock_get_resources, mock_get_player_id, client, app):
        # Mock the functions
        mock_get_player_id.return_value = 1
        mock_get_resources.return_value = {
            'total_food': 500,
            'total_wood': 300,
            'total_stone': 100,
            'total_silver': 50,
            'total_gold': 10
        }
        
        response = client.get('/total_resources') 
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['player_id'] == 1
        assert data['food'] == 500
        assert data['wood'] == 300
        assert data['stone'] == 100
        assert data['silver'] == 50
        assert data['gold'] == 10
    
    @patch('routes.resources.get_player_id_for_user')
    @patch('routes.resources.get_player_total_resources_for_user')
    def test_get_total_resources_not_found(self, mock_get_resources, mock_get_player_id, client, app):
        # Mock to return None
        mock_get_player_id.return_value = 999
        mock_get_resources.return_value = None
        
        response = client.get('/total_resources')
        
        assert response.status_code == 404
        assert 'error' in response.get_json()
        
    @patch('routes.settlements.require_auth', mock_require_auth)
    @patch('routes.settlements.get_player_settlements_for_user')
    @patch('routes.settlements.get_player_id_for_user')
    def test_get_my_settlements_success(
        self, mock_get_player_id, mock_get_settlements, client
    ):
        """Test successful retrieval of settlements."""
        mock_get_player_id.return_value = 1
        mock_get_settlements.return_value = [
            {
                "id": 1,
                "name": "Settlement 1",
                "settlement_type": "town",
                "x": 10,
                "y": 20,
                "food": 100,
                "wood": 50,
                "stone": 30,
                "silver": 10,
                "gold": 5,
                "created_at": "2025-01-01"
            }
        ]
        
        response = client.get('/my_settlements')
        
        assert response.status_code == 200
        assert response.json['player_id'] == 1
        assert len(response.json['settlements']) == 1


    @patch('routes.settlements.require_auth', mock_require_auth)
    @patch('routes.settlements.get_player_settlements_for_user')
    @patch('routes.settlements.get_player_id_for_user')
    def test_get_my_settlements_empty_list(
        self, mock_get_player_id, mock_get_settlements, client
    ):
        """Test when player has no settlements - returns only settlements array."""
        mock_get_player_id.return_value = 1
        mock_get_settlements.return_value = []
        
        response = client.get('/my_settlements')
        
        assert response.status_code == 200
        # When settlements is empty, player_id is NOT included in response
        assert 'player_id' not in response.json
        assert 'settlements' in response.json
        assert response.json['settlements'] == []


    @patch('routes.settlements.require_auth', mock_require_auth)
    @patch('routes.settlements.get_player_settlements_for_user')
    @patch('routes.settlements.get_player_id_for_user')
    def test_get_my_settlements_multiple_settlements(
        self, mock_get_player_id, mock_get_settlements, client
    ):
        """Test when player has multiple settlements."""
        mock_get_player_id.return_value = 1
        mock_get_settlements.return_value = [
            {
                "id": 1,
                "name": "Settlement 1",
                "settlement_type": "town",
                "x": 10,
                "y": 20,
                "food": 100,
                "wood": 50,
                "stone": 30,
                "silver": 10,
                "gold": 5,
                "created_at": "2025-01-01"
            },
            {
                "id": 2,
                "name": "Settlement 2",
                "settlement_type": "village",
                "x": 15,
                "y": 25,
                "food": 200,
                "wood": 100,
                "stone": 60,
                "silver": 20,
                "gold": 10,
                "created_at": "2025-01-02"
            },
            {
                "id": 3,
                "name": "Settlement 3",
                "settlement_type": "city",
                "x": 30,
                "y": 40,
                "food": 500,
                "wood": 300,
                "stone": 200,
                "silver": 50,
                "gold": 25,
                "created_at": "2025-01-03"
            }
        ]
        
        response = client.get('/my_settlements')
        
        assert response.status_code == 200
        assert response.json['player_id'] == 1
        assert len(response.json['settlements']) == 3
        assert response.json['settlements'][0]['name'] == "Settlement 1"
        assert response.json['settlements'][1]['name'] == "Settlement 2"
        assert response.json['settlements'][2]['name'] == "Settlement 3"


    @patch('routes.settlements.require_auth', mock_require_auth)
    @patch('routes.settlements.get_player_settlements_for_user')
    @patch('routes.settlements.get_player_id_for_user')
    def test_get_my_settlements_database_error(
        self, mock_get_player_id, mock_get_settlements, client
    ):
        """Test when database query raises an exception."""
        mock_get_player_id.return_value = 1
        mock_get_settlements.side_effect = Exception("Database connection error")
        
        response = client.get('/my_settlements')
        
        assert response.status_code == 500
        assert 'error' in response.json
        assert response.json['error'] == "Database connection error"


    @patch('routes.settlements.require_auth', mock_require_auth)
    @patch('routes.settlements.get_player_settlements_for_user')
    @patch('routes.settlements.get_player_id_for_user')
    def test_get_my_settlements_player_id_error(
        self, mock_get_player_id, mock_get_settlements, client
    ):
        """Test when getting player ID raises an exception."""
        mock_get_player_id.side_effect = Exception("User has no player")
        mock_get_settlements.return_value = []
        
        response = client.get('/my_settlements')
        
        assert response.status_code == 500
        assert 'error' in response.json


    @patch('routes.settlements.require_auth', mock_require_auth)
    @patch('routes.settlements.get_player_settlements_for_user')
    @patch('routes.settlements.get_player_id_for_user')
    def test_get_my_settlements_verify_all_fields(
        self, mock_get_player_id, mock_get_settlements, client
    ):
        """Test that all settlement fields are returned correctly."""
        mock_get_player_id.return_value = 42
        mock_get_settlements.return_value = [
            {
                "id": 99,
                "name": "Test Settlement",
                "settlement_type": "fortress",
                "x": 100,
                "y": 200,
                "food": 1000,
                "wood": 500,
                "stone": 300,
                "silver": 100,
                "gold": 50,
                "created_at": "2025-01-15"
            }
        ]
        
        response = client.get('/my_settlements')
        
        assert response.status_code == 200
        assert response.json['player_id'] == 42
        
        settlement = response.json['settlements'][0]
        assert settlement['id'] == 99
        assert settlement['name'] == "Test Settlement"
        assert settlement['settlement_type'] == "fortress"
        assert settlement['x'] == 100
        assert settlement['y'] == 200
        assert settlement['food'] == 1000
        assert settlement['wood'] == 500
        assert settlement['stone'] == 300
        assert settlement['silver'] == 100
        assert settlement['gold'] == 50
        assert settlement['created_at'] == "2025-01-15"


    @patch('routes.settlements.require_auth', mock_require_auth)
    @patch('routes.settlements.get_player_settlements_for_user')
    @patch('routes.settlements.get_player_id_for_user')
    def test_get_my_settlements_zero_resources(
        self, mock_get_player_id, mock_get_settlements, client
    ):
        """Test settlements with zero resources."""
        mock_get_player_id.return_value = 1
        mock_get_settlements.return_value = [
            {
                "id": 1,
                "name": "Empty Settlement",
                "settlement_type": "village",
                "x": 0,
                "y": 0,
                "food": 0,
                "wood": 0,
                "stone": 0,
                "silver": 0,
                "gold": 0,
                "created_at": "2025-01-01"
            }
        ]
        
        response = client.get('/my_settlements')
        
        assert response.status_code == 200
        assert response.json['settlements'][0]['food'] == 0
        assert response.json['settlements'][0]['gold'] == 0


    @patch('routes.settlements.require_auth', mock_require_auth)
    @patch('routes.settlements.get_player_settlements_for_user')
    @patch('routes.settlements.get_player_id_for_user')
    def test_get_my_settlements_player_id_none(
        self, mock_get_player_id, mock_get_settlements, client
    ):
        """Test when player_id is None but get_settlements doesn't raise error."""
        mock_get_player_id.return_value = None
        mock_get_settlements.return_value = []
        
        response = client.get('/my_settlements')
        
        # Should return 200 with empty settlements since no exception is raised
        assert response.status_code == 200
        assert response.json['settlements'] == []


    @patch('routes.settlements.require_auth', mock_require_auth)
    @patch('routes.settlements.get_player_settlements_for_user')
    @patch('routes.settlements.get_player_id_for_user')
    def test_get_my_settlements_settlement_types(
        self, mock_get_player_id, mock_get_settlements, client
    ):
        """Test different settlement types."""
        mock_get_player_id.return_value = 1
        mock_get_settlements.return_value = [
            {
                "id": 1,
                "name": "Village One",
                "settlement_type": "village",
                "x": 10,
                "y": 20,
                "food": 100,
                "wood": 50,
                "stone": 30,
                "silver": 10,
                "gold": 5,
                "created_at": "2025-01-01"
            },
            {
                "id": 2,
                "name": "Town Central",
                "settlement_type": "town",
                "x": 15,
                "y": 25,
                "food": 200,
                "wood": 100,
                "stone": 60,
                "silver": 20,
                "gold": 10,
                "created_at": "2025-01-02"
            },
            {
                "id": 3,
                "name": "City Capital",
                "settlement_type": "city",
                "x": 30,
                "y": 40,
                "food": 500,
                "wood": 300,
                "stone": 200,
                "silver": 50,
                "gold": 25,
                "created_at": "2025-01-03"
            }
        ]
        
        response = client.get('/my_settlements')
        
        assert response.status_code == 200
        types = [s['settlement_type'] for s in response.json['settlements']]
        assert 'village' in types
        assert 'town' in types
        assert 'city' in types


# use pytest test_endpoints.py -v to run