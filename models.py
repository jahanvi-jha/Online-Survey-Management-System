from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    surveys = db.relationship('Survey', backref='creator', cascade="all, delete-orphan", lazy=True)

class Survey(db.Model):
    __tablename__ = 'surveys'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    questions = db.relationship('Question', backref='survey', cascade="all, delete-orphan", lazy=True)
    responses = db.relationship('Response', backref='survey', cascade="all, delete-orphan", lazy=True)

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'), nullable=False)
    
   
    options = db.relationship('QuestionOption', backref='question', cascade="all, delete-orphan", lazy=True)
    responses = db.relationship('Response', backref='question', cascade="all, delete-orphan", lazy=True)

class QuestionOption(db.Model):
    __tablename__ = 'question_options'
    id = db.Column(db.Integer, primary_key=True)
    option_text = db.Column(db.String(255), nullable=False)
    
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    responses = db.relationship('Response', backref='option', lazy=True)

class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key=True)
    
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('question_options.id'), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='responses')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)