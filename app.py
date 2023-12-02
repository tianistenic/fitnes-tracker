from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import joinedload
from datetime import datetime
import subprocess

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:istetian@localhost/fitnes_tracker'
app.secret_key = '098hudsfg0h97sadgfh0u9qt430h7934tq0u9hiojsahdgf'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    workouts = db.relationship('Workout', backref='user', lazy=True)
    nutritions = db.relationship('Nutrition', backref='user', lazy=True)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise_type = db.Column(db.String(50), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    repetitions = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)

class Nutrition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    nutrition_date = db.Column(db.Date, default=datetime.today().date, nullable=False)
    
@app.route('/register-api', methods=['POST'])
def register_api():
    data = request.get_json()
    if 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password in JSON data'}), 400

    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/workout-api', methods=['POST'])
def log_workout_api():
    data = request.get_json()

    if data is None:
        print("No JSON data provided")
        return jsonify({'error': 'No JSON data provided'}), 400

    user_id = session.get('user_id')

    if user_id is None:
        return jsonify({'error': 'User not authenticated'}), 401

    try:
        if any(field is None for field in [data.get('exercise_type'), data.get('sets'), data.get('repetitions'), data.get('weight')]):
            return jsonify({'error': 'Missing required fields in JSON data'}), 400

        new_workout = Workout(
            user_id=user_id,
            exercise_type=data.get('exercise_type'),
            sets=data.get('sets'),
            repetitions=data.get('repetitions'),
            weight=data.get('weight')
        )
        db.session.add(new_workout)
        db.session.commit()
        return jsonify({'message': 'Workout logged successfully'}), 201
    except KeyError as e:
        return jsonify({'error': f'Missing key in JSON data: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred while logging workout: {str(e)}'}), 500


@app.route('/nutrition-api', methods=['POST'])
def log_nutrition_api():
    data = request.get_json()

    if data is None:
        print("No JSON data provided")
        return jsonify({'error': 'No JSON data provided'}), 400

    user_id = session.get('user_id')

    if user_id is None:
        return jsonify({'error': 'User not authenticated'}), 401

    try:
        # Check for missing or None values
        if any(field is None for field in [data.get('calories'), data.get('fats'), data.get('carbs'), data.get('protein')]):
            return jsonify({'error': 'Missing required fields in JSON data'}), 400

        new_nutrition = Nutrition(
            user_id=user_id,
            calories=data.get('calories'),
            fats=data.get('fats'),
            carbs=data.get('carbs'),
            protein=data.get('protein')
        )
        db.session.add(new_nutrition)
        db.session.commit()
        return jsonify({'message': 'Nutrition logged successfully'}), 201
    except KeyError as e:
        return jsonify({'error': f'Missing key in JSON data: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred while logging nutrition: {str(e)}'}), 500

# Existing code...

# Web page routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register_web():
    if request.method == 'POST':
        data = request.form
        if 'username' not in data or 'password' not in data:
            flash('Missing username or password in the form', 'error')
            return redirect(url_for('register_web'))

        new_user = User(username=data['username'], password=data['password'])
        db.session.add(new_user)
        db.session.commit()

        flash('User registered successfully', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username = data['username']
        password = data['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session['user_id'] = user.id
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Inside the 'dashboard' route
@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')

    if user_id is None:
        flash('Please log in to access the dashboard', 'error')
        return redirect(url_for('login'))

    # Fetch user details along with associated workouts and nutritions
    user = User.query.filter_by(id=user_id).first()

    if user is None:
        flash('User not found', 'error')
        return redirect(url_for('login'))

    return render_template('dashboard.html', user=user)

@app.route('/workout', methods=['GET'])
def workout():
    user_id = session.get('user_id')

    if user_id is None:
        flash('Please log in to access your workouts', 'error')
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    if user is None:
        flash('User not found', 'error')
        return redirect(url_for('login'))

    workouts = user.workouts
    return render_template('workout.html', workouts=workouts)

# Inside the 'nutrition' route
@app.route('/nutrition', methods=['GET'])
def nutrition():
    user_id = session.get('user_id')

    if user_id is None:
        flash('Please log in to access your nutrition data', 'error')
        return redirect(url_for('login'))

    date_str = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
        return redirect(url_for('dashboard'))

    user = User.query.get(user_id)

    if user is None:
        flash('User not found', 'error')
        return redirect(url_for('login'))

    nutritions = Nutrition.query.filter(
        Nutrition.user_id == user_id,
        Nutrition.nutrition_date == date
    ).all()

    if not nutritions:
        flash(f'No nutrition data found for {date}', 'info')

    return render_template('nutrition.html', nutritions=nutritions)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)