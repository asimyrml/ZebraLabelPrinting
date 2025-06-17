from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    printer_ip = db.Column(db.String(50), default="0.0.0.0")
    printer_port = db.Column(db.Integer, default=9100)
    zpl_code = db.Column(db.Text)
    zpl_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    api_token = db.Column(db.String(64), unique=True)
