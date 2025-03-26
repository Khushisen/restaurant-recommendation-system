from flask import Blueprint, render_template, redirect, url_for, flash,request
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from app.models import Restaurant
from .forms import LoginForm, RegisterForm
from . import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):  # Verify hashed password
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if the user already exists
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('main.login'))

        # Create a new user
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)  # Hash the password
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.index'))

@main.route('/recommend')
@login_required
def recommend():
    # Get filters from URL parameters (e.g., /recommend?city=Delhi&cuisine=North+Indian)
    city = request.args.get('city', '').strip()           # Default: All cities
    cuisine = request.args.get('cuisine', current_user.preferred_cuisines.split(',')[0] if current_user.preferred_cuisines else '').strip()
    # Default: All cuisines
    min_rating = float(request.args.get('min_rating', 0))
    max_cost = int(request.args.get('max_cost', 1500 if current_user.budget_preference == '$$$' else 500 if current_user.budget_preference == '$' else 1000))  # Default: No max cost

    # Build query
    query = Restaurant.query
    if city:
        query = query.filter(Restaurant.city.ilike(f"%{city}%"))
    if cuisine:
        query = query.filter(Restaurant.cuisine.ilike(f"%{cuisine}%"))
    if min_rating:
        query = query.filter(Restaurant.rating >= min_rating)
    if max_cost:
        query = query.filter(Restaurant.cost <= max_cost)

    # Sort by rating (descending) and limit to top 20
    restaurants = query.order_by(Restaurant.rating.desc()).limit(20).all()
    
    if not restaurants:
        flash(f"No restaurants found in {city} for {cuisine} cuisine.",'warning')
        return redirect(url_for('main.dashboard'))
    
    return render_template('recommendations.html', restaurants=restaurants)

@main.route('/save_preferences', methods=['POST'])
@login_required
def save_preferences():
    # Get user preferences from form
    favorite_cuisines = request.form.getlist('cuisine')  # Gets all checked boxes
    budget = request.form.get('budget')

    # Update user preferences in database
    current_user.preferred_cuisines = ",".join(favorite_cuisines[:3])  # Store as comma-separated string
    current_user.budget_preference = budget
    db.session.commit()

    flash('Your preferences have been saved!', 'success')
    return redirect(url_for('main.dashboard'))

@main.route('/suggest', methods=['GET', 'POST'])
def suggest():
    if request.method == 'POST':
        # Handle form submission (save to database)
        flash('Thanks for your suggestion!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('suggest.html')