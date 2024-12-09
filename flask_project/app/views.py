from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_user, login_required, logout_user
from . import db
from .models import Account, Event
from . import login_manager

main_bp = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return Account.query.get(int(user_id))

@main_bp.before_app_request
def before_request():
    g.user = current_user

@main_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        action = request.form['action']
        is_organizer = 'is_organizer' in request.form

        if action == 'login':
            user = Account.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('main.home'))
            else:
                flash('Invalid username or password. Please try again.', 'danger')

        elif action == 'signup':
            existing_user = Account.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists. Please choose a different username.', 'danger')
            else:
                new_account = Account(username=username, is_organizer=is_organizer)
                new_account.set_password(password)
                db.session.add(new_account)
                db.session.commit()
                flash('Account created successfully! You can now log in.', 'success')
                return redirect(url_for('main.login'))

    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out!', 'success')
    return redirect(url_for('main.login'))

@main_bp.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)

    if event.organizer != current_user.username:
        flash("You are not authorized to edit this event.", 'danger')
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        event.event_name = request.form.get('event_name', event.event_name)
        event.event_type = request.form.get('event_type', event.event_type)
        event.date = request.form.get('date', event.date)
        event.time = request.form.get('time', event.time)
        event.location = request.form.get('location', event.location)
        event.tags = request.form.get('tags', event.tags)
        event.desc = request.form.get('desc', event.desc)

        db.session.commit()
        flash("Event updated successfully!", 'success')
        return redirect(url_for('main.home'))

    return render_template('edit_event.html', event=event)

@main_bp.route('/event/<int:event_id>')
@login_required
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('events_details.html', event=event)

@main_bp.route('/signup/<int:event_id>', methods=['POST'])
@login_required
def signup(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user not in event.user_id_attendance:
        event.user_id_attendance.append(current_user)
        db.session.commit()
        flash(f"You have successfully signed up for {event.event_name}!", 'success')
    else:
        flash("You are already signed up for this event.", 'info')
    return redirect(url_for('main.event_details', event_id=event.id))

@main_bp.route('/decline_event/<int:event_id>', methods=['POST'])
@login_required
def decline_event(event_id):
    event = Event.query.get_or_404(event_id)

    # Remove the user from the event's attendance list if they are attending
    if current_user in event.user_id_attendance:
        event.user_id_attendance.remove(current_user)
        db.session.commit()
        flash(f"You have successfully removed yourself from {event.event_name}.", 'success')
    else:
        flash("You are not attending this event.", 'info')

    return redirect(url_for('main.home'))

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = current_user

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        desc = request.form['desc']
        hobbies = request.form['hobbies']
        age = request.form['age']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if first_name != user.first_name:
            user.first_name = first_name
        if last_name != user.last_name:
            user.last_name = last_name

        user.desc = desc
        user.hobbies = hobbies
        user.age = age

        if username != user.username:
            user.username = username

        if password:
            if password == confirm_password:
                user.set_password(password)
            else:
                flash("Passwords do not match. Please try again.", 'danger')
                return redirect(url_for('main.settings'))

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.settings'))

    return render_template('settings.html', user=user)

@main_bp.route('/profile')
@login_required
def profile():
    user = current_user

    if not user:
        flash("You need to be logged in to view your profile.", 'danger')
        return redirect(url_for('main.login'))

    return render_template('profile.html', profile=user)

@main_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if query:
        events = Event.query.filter(Event.event_name.ilike(f'%{query}%')).all()
        return jsonify([event.event_name for event in events])
    return jsonify([])

@main_bp.route('/manager')
def manager_dashboard():
    events = Event.query.filter_by(organizer="current_manager").all()
    return render_template('events.html', events=events)

@main_bp.route('/home')
@login_required
def home():
    user = current_user  # current_user should be available via Flask-Login
    featured_events = Event.query.order_by(Event.date.asc()).limit(6).all()
    managed_events = Event.query.filter_by(organizer=user.username).all() if user.is_organizer else []
    attended_events = user.event_attendance if not user.is_organizer else []  # Fetch the attended events for non-organizers

    return render_template(
        'home.html',
        user=user,  # Explicitly pass the user
        featured_events=featured_events,
        managed_events=managed_events,
        attended_events=attended_events
    )

@main_bp.route('/create_event', methods=['GET'])
@login_required
def create_event_page():
    return render_template('create_event.html')

@main_bp.route('/create_event', methods=['POST'])
@login_required
def create_event():
    title = request.form.get('event_name')
    event_type = request.form.get('event_type')
    description = request.form.get('description')
    date = request.form.get('date')
    time = request.form.get('time')
    location = request.form.get('location')
    tags = request.form.get('tags')

    if not title or not description or not date or not time or not location:
        flash("All fields except 'Tags' are required.", 'danger')
        return redirect(url_for('main.create_event_page'))

    try:
        event = Event(
            event_name=title,
            event_type=event_type,
            desc=description,
            date=date,
            time=time,
            location=location,
            tags=tags,
            organizer=current_user.username
        )
        db.session.add(event)
        db.session.commit()
        flash("Event created successfully!", 'success')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'danger')

    return redirect(url_for('main.home'))

@main_bp.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)

    if event.organizer != current_user.username:
        flash("You are not authorized to delete this event.", 'danger')
        return redirect(url_for('main.home'))

    try:
        db.session.delete(event)
        db.session.commit()
        flash(f"Event '{event.event_name}' has been successfully deleted.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the event: {str(e)}", 'danger')

    return redirect(url_for('main.home'))

@main_bp.route('/attend_event/<int:event_id>', methods=['POST'])
@login_required
def attend_event(event_id):
    event = Event.query.get_or_404(event_id)

    # Add the user to the event's attendance list if not already attending
    if current_user not in event.user_id_attendance:
        event.user_id_attendance.append(current_user)
        db.session.commit()
        flash(f"You have successfully signed up for {event.event_name}!", 'success')
    else:
        flash("You are already attending this event.", 'info')

    return redirect(url_for('main.home'))
