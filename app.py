from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, WorkoutCategory, Exercise, WorkoutSession, WorkoutExercise
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gym.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'

db.init_app(app)

with app.app_context():
    db.create_all()
    # Seed data
    if not User.query.first():
        u = User(username='demo', email='demo@example.com')
        db.session.add(u)
        db.session.commit()
    if not WorkoutCategory.query.first():
        c1 = WorkoutCategory(name="Strength")
        c2 = WorkoutCategory(name="Hypertrophy")
        db.session.add_all([c1, c2])
        db.session.commit()
        e1 = Exercise(name="Bench Press", category_id=c1.id)
        e2 = Exercise(name="Squat", category_id=c1.id)
        db.session.add_all([e1, e2])
        db.session.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/workouts")
def list_workouts():
    workouts = WorkoutSession.query.order_by(WorkoutSession.date.desc()).all()
    return render_template("workouts.html", workouts=workouts)

@app.route("/workouts/new", methods=["GET", "POST"])
def new_workout():
    if request.method == "POST":
        date_str = request.form.get("date")
        duration = request.form.get("duration_minutes")
        notes = request.form.get("notes")

        user = User.query.first()
        workout_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.utcnow().date()
        workout = WorkoutSession(date=workout_date, duration_minutes=duration or 0, notes=notes, user_id=user.id)
        db.session.add(workout)
        db.session.commit()
        flash("Workout created successfully!", "success")
        return redirect(url_for("view_workout", id=workout.id))
    
    return render_template("workout_form.html", workout=None)

@app.route("/workouts/<int:id>")
def view_workout(id):
    workout = WorkoutSession.query.get_or_404(id)
    exercises = Exercise.query.all()
    return render_template("workout_detail.html", workout=workout, available_exercises=exercises)

@app.route("/workouts/<int:id>/edit", methods=["GET", "POST"])
def edit_workout(id):
    workout = WorkoutSession.query.get_or_404(id)
    if request.method == "POST":
        date_str = request.form.get("date")
        workout.duration_minutes = request.form.get("duration_minutes") or 0
        workout.notes = request.form.get("notes")
        if date_str:
            workout.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        db.session.commit()
        flash("Workout updated successfully!", "success")
        return redirect(url_for("view_workout", id=workout.id))
        
    return render_template("workout_form.html", workout=workout)

@app.route("/workouts/<int:id>/delete", methods=["POST"])
def delete_workout(id):
    workout = WorkoutSession.query.get_or_404(id)
    db.session.delete(workout)
    db.session.commit()
    flash("Workout deleted.", "info")
    return redirect(url_for("list_workouts"))

@app.route("/workouts/<int:id>/add_exercise", methods=["POST"])
def add_workout_exercise(id):
    workout = WorkoutSession.query.get_or_404(id)
    exercise_id = request.form.get("exercise_id")
    sets = request.form.get("sets") or 0
    reps = request.form.get("reps") or 0
    weight = request.form.get("weight") or 0.0
    
    we = WorkoutExercise(workout_session_id=workout.id, exercise_id=exercise_id, sets=sets, reps=reps, weight=weight)
    db.session.add(we)
    db.session.commit()
    flash("Exercise logged!", "success")
    return redirect(url_for('view_workout', id=workout.id))

@app.route("/workout_exercises/<int:we_id>/delete", methods=["POST"])
def delete_workout_exercise(we_id):
    we = WorkoutExercise.query.get_or_404(we_id)
    workout_id = we.workout_session_id
    db.session.delete(we)
    db.session.commit()
    flash("Exercise log deleted.", "info")
    return redirect(url_for('view_workout', id=workout_id))

@app.route("/report", methods=["GET", "POST"])
def report():
    categories = WorkoutCategory.query.all()
    exercises = Exercise.query.all()
    
    results = None
    stats = {}
    
    if request.method == "POST":
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        category_id = request.form.get("category_id")
        exercise_id = request.form.get("exercise_id")
        
        query = db.session.query(WorkoutExercise).join(WorkoutSession).join(Exercise)
        
        if start_date_str:
            sd = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            query = query.filter(WorkoutSession.date >= sd)
        if end_date_str:
            ed = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            query = query.filter(WorkoutSession.date <= ed)
        if category_id:
            query = query.filter(Exercise.category_id == category_id)
        if exercise_id:
            query = query.filter(Exercise.id == exercise_id)
            
        results = query.all()
        
        if results:
            stats['total_logs'] = len(results)
            stats['avg_weight'] = sum(r.weight for r in results if r.weight) / len(results)
            stats['max_weight'] = max((r.weight for r in results if r.weight), default=0)
            stats['total_workouts'] = len(set(r.workout_session_id for r in results))
            
    return render_template("report.html", categories=categories, exercises=exercises, results=results, stats=stats)

@app.route("/exercises", methods=["GET", "POST"])
def manage_exercises():
    if request.method == "POST":
        name = request.form.get("name")
        category_id = request.form.get("category_id")
        if name and category_id:
            ex = Exercise(name=name, category_id=category_id)
            db.session.add(ex)
            db.session.commit()
            flash(f"Exercise '{name}' added successfully!", "success")
            return redirect(url_for("manage_exercises"))
            
    categories = WorkoutCategory.query.all()
    exercises = Exercise.query.join(WorkoutCategory).order_by(WorkoutCategory.name, Exercise.name).all()
    return render_template("exercises.html", categories=categories, exercises=exercises)

@app.route("/workout_exercises/<int:we_id>/edit", methods=["GET", "POST"])
def edit_workout_exercise(we_id):
    we = WorkoutExercise.query.get_or_404(we_id)
    if request.method == "POST":
        we.sets = request.form.get("sets") or 0
        we.reps = request.form.get("reps") or 0
        we.weight = request.form.get("weight") or 0.0
        db.session.commit()
        flash("Exercise log updated!", "success")
        return redirect(url_for('view_workout', id=we.workout_session_id))
    return render_template("workout_exercise_form.html", we=we)

if __name__ == '__main__':
    app.run(debug=True, port=8080)