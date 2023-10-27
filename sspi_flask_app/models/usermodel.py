from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from .. import db
from dataclasses import dataclass


@dataclass
class User(db.Model, UserMixin, SerializerMixin):
    id:int = db.Column(db.Integer, primary_key=True)
    username:str = db.Column(db.String(20), nullable=False, unique=True)
    password:str = db.Column(db.String(80), nullable=False)
    apikey:str = db.Column(db.String(80), nullable=False)