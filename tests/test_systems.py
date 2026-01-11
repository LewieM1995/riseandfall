import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock, ANY
from systems.unit_training import queue_unit_training
from systems.resources.resources import get_player_total_resources_for_user
from flask import Flask
from datetime import datetime, timedelta
import json

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


    @patch('systems.resources.resources.get_player_id_for_user')
    @patch('systems.resources.resources.connect_db')
    def test_get_player_total_resources_mocked(self, mock_connect_db, mock_get_player_id):
        """Test with mocked database"""
        # Mock the player_id lookup
        mock_get_player_id.return_value = 1
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect_db.return_value = mock_conn
        
        # Mock fetchone to return a dict-like object (simulating sqlite3.Row)
        mock_cursor.fetchone.return_value = {
            'total_food': 500,
            'total_wood': 300,
            'total_stone': 100,
            'total_silver': 50,
            'total_gold': 10
        }
        
        result = get_player_total_resources_for_user(1)
        
        mock_cursor.execute.assert_called_once()
        sql, params = mock_cursor.execute.call_args[0]
        
        assert 'SUM(s.food)' in sql 
        assert 'SUM(s.wood)' in sql
        assert 'SUM(s.stone)' in sql
        assert 'SUM(s.silver)' in sql
        assert 'SUM(s.gold)' in sql
        assert 'FROM settlements s' in sql
        assert 'WHERE s.player_id = ?' in sql
        assert params == (1,)
        
        assert result == {
            'total_food': 500,
            'total_wood': 300,
            'total_stone': 100,
            'total_silver': 50,
            'total_gold': 10
        }
        
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


# use python3 -m pytest tests/test_systems.py -v to run