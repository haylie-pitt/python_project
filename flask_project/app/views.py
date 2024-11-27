from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import Account, Event

main_bp = Blueprint('main', __name__)

# Route for the login page (with sign-up functionality built in)
@main_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        action = request.form['action']  # 'login' or 'signup'

        if action == 'login':
            # Check if the account exists
            user = Account.query.filter_by(username=username).first()
            if user and user.check_password(password):  # Check if password is correct
                flash('Login successful!', 'success')
                return redirect(url_for('main.home'))  # Redirect to the homepage
            else:
                flash('Invalid username or password. Please try again.', 'danger')

        elif action == 'signup':
            # Check if the username already exists
            existing_user = Account.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists. Please choose a different username.', 'danger')
            else:
                # Create a new account and hash the password
                new_account = Account(username=username)
                new_account.set_password(password)  # Hash the password before saving
                db.session.add(new_account)
                db.session.commit()
                flash('Account created successfully! You can now log in.', 'success')
                return redirect(url_for('main.login'))  # Redirect to login page after signup

    return render_template('login.html')

# Route to handle the search functionality
@main_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')  # Get the search term from the query parameter
    if query:
        # Search for events that match the query (case-insensitive)
        events = Event.query.filter(Event.event_name.ilike(f'%{query}%')).all()
        return jsonify([event.event_name for event in events])  # Return the list of event names
    return jsonify([])  # Return empty if no search query
