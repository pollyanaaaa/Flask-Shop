from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Integer, String, ForeignKey
import os
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from sqlalchemy.orm import relationship
from enum import Enum

app = Flask(__name__)
app.config['SECRET_KEY'] = '192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
jwt = JWTManager(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'store.db')
app.config['UPLOAD_FOLDER'] = 'static/images'
db = SQLAlchemy(app)
engine = create_engine('sqlite:///' + os.path.join(basedir, 'store.db'))
migrate = Migrate(app, db)


class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.Integer, db.ForeignKey('category.category_id'))
    brand = db.Column(db.Integer, db.ForeignKey('brand.brand_id'))
    images = db.relationship('Image', back_populates='product', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return '<Product %r>' % self.product_id


class Image(db.Model):
    image_id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    product = db.relationship('Product', back_populates='images')

    def __repr__(self):
        return '<Image %r>' % self.image_id


class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return '<Category %r>' % self.category_id


class Brand(db.Model):
    brand_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return '<Brand %r>' % self.brand_id


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.user_id


class Basket(db.Model):
    basket_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'))

    def __repr__(self):
        return '<Basket %r>' % self.basket_id


class History(db.Model):
        history_id = db.Column(Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
        product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'))

        def __repr__(self):
            return '<History %r>' % self.history_id

db.metadata.create_all(bind=engine)
