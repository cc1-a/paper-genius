from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    img = db.Column(db.String(200), nullable=False)
    years_available = db.Column(db.PickleType, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    school = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    town = db.Column(db.String(200), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

class cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    original_item_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    img = db.Column(db.String(200), nullable=False)
    years_available = db.Column(db.PickleType, nullable=False)
    selected_years = db.Column(db.PickleType, nullable=False)
    design_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    order_items = db.Column(db.Text, nullable=False) 
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pending")
    additional_info = db.Column(db.Text, nullable=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)