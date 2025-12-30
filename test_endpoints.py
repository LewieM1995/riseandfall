import pytest
from flask import Flask
from routes.army import army_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(army_bp, url_prefix='/army')
    with app.test_client() as client:
        yield client

def test_get_army_units(client):
    response = client.get('/army/units')
    assert response.status_code == 200
    assert response.json == {"status": "api running"}


# use pytest test_endpoints.py -v to run