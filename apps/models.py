# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from email.policy import default
from apps import db
from sqlalchemy.exc import SQLAlchemyError
from apps.exceptions.exception import InvalidUsage
import datetime as dt
from sqlalchemy.orm import relationship
from apps.authentication.models import Users

#__MODELS__
class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_time = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user = db.relationship('Users', backref=db.backref('categories', lazy=True, cascade='all, delete-orphan'))
    parent = db.relationship('Category', remote_side=[id], backref=db.backref('children', lazy=True, cascade='all, delete-orphan'))  # 父分类 -> 子分类

class Note(db.Model):

    __tablename__ = 'Note'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('Users', backref=db.backref('notes', lazy=True))

    #__Note_FIELDS__
    title = db.Column(db.Text, nullable=False)
    content_md = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category = db.relationship('Category', backref=db.backref('notes', lazy=True))
    tags = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    solution = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.Integer, nullable=False)
    created_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_time = db.Column(db.DateTime, default=db.func.current_timestamp())

    #__Note_FIELDS__END

    def __init__(self, **kwargs):
        super(Note, self).__init__(**kwargs)

#__MODELS__END
