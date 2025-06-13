from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    printer_ip = db.Column(db.String(50), default="0.0.0.0")
    printer_port = db.Column(db.Integer, default=9100)
    is_admin = db.Column(db.Boolean, default=False)

