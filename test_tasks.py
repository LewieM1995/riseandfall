import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock, ANY
from database_operations import database_operations
from systems.unit_training import queue_unit_training
from systems.resources.resources import get_player_total_resources
from routes.army import get_army_units
from routes.resources import resource_bp
from flask import Flask
from datetime import datetime, timedelta
import json

@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.register_blueprint(resource_bp)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestGetAllForEachTable:
 
    def test_get_all_test_real_db(self):
        result = database_operations.get_all_test()

        assert len(result) > 0
        assert 'id' in result[0]
        assert 'player_id' in result[0]
        assert 'location_settlement_id' in result[0]
        assert 'target_settlement_id' in result[0]
        assert 'eta' in result[0]
        
    def test_players_seeded(self):
        players = database_operations.get_all_players()
        assert any(p['username'] == 'player_one' for p in players)
        

class TestSystems:
    
    @patch('systems.unit_training.connect_db')
    @patch('systems.unit_training.datetime')
    def test_queue_unit_training(self, mock_datetime, mock_connect_db):
        fixed_time = datetime(2025, 1,1,12,0,0)
        mock_datetime.utcnow.return_value = fixed_time
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect_db.return_value = mock_conn
        
        queue_unit_training(
            player_id = 1,
            settlement_id = 1,
            unit = "archer",
            quantity = 10,
            duration_minutes = 60
        )
        
        mock_cursor.execute.assert_called_once()
        
        sql, params = mock_cursor.execute.call_args[0]
        
        assert "INSERT INTO action_queue" in sql
        assert params[0] == 1
        assert params[1] == 1
        
        payload = json.loads(params[2])
        assert payload == {"unit": "archer", "quantity": 10}
        
        assert params[3] == fixed_time
        assert params[4] == fixed_time + timedelta(minutes=60)
        
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()


    @patch('systems.resources.resources.connect_db')
    def test_get_player_total_resources_mocked(self, mock_connect_db):
        """Test with mocked database"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect_db.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = (500, 300, 100, 50, 10)
        
        result = get_player_total_resources(1)
        
        mock_cursor.execute.assert_called_once()
        sql, params = mock_cursor.execute.call_args[0]
        
        assert 'SUM(s.food)' in sql 
        assert 'SUM(s.wood)' in sql
        assert 'SUM(s.stone)' in sql
        assert 'SUM(s.silver)' in sql
        assert 'SUM(s.gold)' in sql
        assert 'FROM players p' in sql
        assert 'LEFT JOIN settlements s' in sql
        assert 'WHERE p.id = ?' in sql
        assert params == (1,)
        
        assert result == (500, 300, 100, 50, 10)
        
        mock_conn.close.assert_called_once()
        
    @patch('systems.resources.resources.connect_db')
    def test_get_resouce_ticks(self, mock_connect_db):
        """Test resource tick application"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect_db.return_value = mock_conn
        
        last_tick_time = datetime.utcnow() - timedelta(seconds=3600)
        mock_cursor.fetchone.return_value = {
            "food": 100,
            "wood": 100,
            "stone": 100,
            "silver": 100,
            "gold": 50,
            "last_resource_tick": last_tick_time.isoformat(),
            "food_rate": 60.0,
            "wood_rate": 36.0,
            "stone_rate": 24.0,
            "silver_rate": 12.0,
        }
        
        from systems.resources.resource_tick import apply_resource_tick
        apply_resource_tick(1, mock_cursor)
        
        update_call = mock_cursor.execute.call_args_list[1]
        sql, params = update_call[0]
        
        assert 'UPDATE settlements' in sql
        assert 'SET food = ?, wood = ?, stone = ?, silver = ?' in sql
        
        # After 1 hour (3600 seconds) with hourly rates:
        assert params[0] == 160  # food: 100 + (3600 * 60/3600) = 100 + 60
        assert params[1] == 136  # wood: 100 + (3600 * 36/3600) = 100 + 36
        assert params[2] == 124  # stone: 100 + (3600 * 24/3600) = 100 + 24
        assert params[3] == 112  # silver: 100 + (3600 * 12/3600) = 100 + 12
        # params[4] is timestamp
        assert params[5] == 1    # settlement_id


class TestEndpoints:
    """Test Flask API endpoints"""
    
    def test_get_total_resources_success(self, client):
        with patch('routes.resources.get_player_total_resources') as mock_get:
            mock_get.return_value = (500, 300, 100, 50, 10)
            
            response = client.get('/total_resources?player_id=1') 
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['food'] == 500
            assert data['wood'] == 300
            assert data['stone'] == 100
            assert data['silver'] == 50
            assert data['gold'] == 10
    
    def test_get_total_resources_not_found(self, client):
        with patch('routes.resources.get_player_total_resources') as mock_get:
            mock_get.return_value = None
            
            response = client.get('/total_resources?player_id=999')
            
            assert response.status_code == 404
            assert 'error' in response.get_json()

# use pytest test_tasks.py -v to run