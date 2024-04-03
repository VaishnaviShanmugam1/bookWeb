from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    role = db.Column(db.String(50), default='customer')
    products = db.relationship('Product', backref='user', lazy=True, cascade="all, delete-orphan")
    user_carts = db.relationship('Cart', backref='user', lazy=True, cascade="all, delete-orphan")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0)



class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    publisher = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255), nullable=False) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
  

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    Total_Value = db.Column(db.Integer, default=None)
    Total_Count = db.Column(db.Integer, default=None)
    quantity = db.Column(db.Integer, nullable=False, default=1) 
    Final_Amount = db.Column(db.Integer, nullable=False)
    #owner = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Define a relationship with the User model
    #owner = db.relationship('User', backref=db.backref('carts', lazy=True), overlaps="cart,user,user_carts")

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer,nullable=False)