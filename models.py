# models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()

class Bank(db.Model):
    __tablename__ = 'banks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, index=True, unique=True)
    # relationship defined on Branch side if using ORM relationships

class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    ifsc = db.Column(db.String, nullable=False, unique=True, index=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=False, index=True)
    branch = db.Column(db.String, nullable=False)
    address = db.Column(db.String)
    city = db.Column(db.String)
    district = db.Column(db.String)
    state = db.Column(db.String)
    micr = db.Column(db.String)
    # optional: phone/email columns if present
