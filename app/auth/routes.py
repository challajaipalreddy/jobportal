from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User
from app.forms import LoginForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        input_val = form.email.data.strip().lower()
        user = User.query.filter(
            (User.email.ilike(input_val)) | (User.username.ilike(input_val))
        ).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)

            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('admin.dashboard')
            return redirect(next_page)
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('admin/login.html', form=form, title='Admin Login - Campus to Career')

@auth_bp.route('/admin/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))
