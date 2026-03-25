from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # Relationships
    workouts = db.relationship('WorkoutSession', backref='user', lazy=True)

class WorkoutCategory(db.Model):
    __tablename__ = 'workout_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    
    # Relationships
    exercises = db.relationship('Exercise', backref='category', lazy=True)

class Exercise(db.Model):
    __tablename__ = 'exercises'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('workout_categories.id'), nullable=False, index=True)

class WorkoutSession(db.Model):
    __tablename__ = 'workout_sessions'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow, index=True)
    duration_minutes = db.Column(db.Integer)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Relationships
    exercises = db.relationship('WorkoutExercise', backref='session', lazy=True, cascade='all, delete-orphan')

class WorkoutExercise(db.Model):
    __tablename__ = 'workout_exercises'
    id = db.Column(db.Integer, primary_key=True)
    workout_session_id = db.Column(db.Integer, db.ForeignKey('workout_sessions.id'), nullable=False, index=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False, index=True)
    sets = db.Column(db.Integer)
    reps = db.Column(db.Integer)
    weight = db.Column(db.Float)
    
    # Relationships
    exercise = db.relationship('Exercise', backref='workout_exercises')
