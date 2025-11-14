# tests/test_api.py
import os
import tempfile
import pytest
from app import create_app
from models import db, Bank, Branch

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    with app.app_context():
        db.init_app(app)
        db.create_all()
        # insert sample data
        bank = Bank(name="Test Bank")
        db.session.add(bank)
        db.session.flush()
        branch = Branch(ifsc="TEST0001", bank_id=bank.id, branch="Test Branch", address="Addr", city="City", district="D", state="S", micr="123")
        db.session.add(branch)
        db.session.commit()

    with app.test_client() as client:
        yield client

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json["status"] == "ok"

def test_banks(client):
    r = client.get("/banks")
    assert r.status_code == 200
    assert r.json['total'] >= 1
    assert any(b['name'] == "Test Bank" for b in r.json['banks'])

def test_branch_ifsc(client):
    r = client.get("/branches/TEST0001")
    assert r.status_code == 200
    assert r.json['ifsc'] == "TEST0001"
    assert r.json['bank']['name'] == "Test Bank"
