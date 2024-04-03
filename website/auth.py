from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db  
from flask_login import login_user, login_required, logout_user, current_user
from password_strength import PasswordPolicy

auth = Blueprint('auth', __name__)

policy = PasswordPolicy.from_names(
    length=7,  # Minimum length
    uppercase=1,  # Require at least one uppercase letter
    numbers=1,  # Require at least one digit
    special=1,  # Require at least one special character
)
# Login route separated for clarity and security
@auth.route('/login', methods=['GET'])
def login_get():
    # This route will only handle the display of the login form
    return render_template("login.html", user=current_user)

@auth.route('/login', methods=['POST'])
def login_post():
    # This route will handle the form submission for login
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        if user.is_active:
            user.failed_login_attempts = 0
            flash('Logged in successfully!', category='success')
            login_user(user, remember=True)
            session.permanent = True
            return redirect(url_for('views.home'))
        else:
            flash('Your account is blocked by admin. Please reach out to admin@book.ca', category='error')
    elif user:
        user.failed_login_attempts += 1
        db.session.commit()
        if user.failed_login_attempts >= 3:
                user.is_active = False
                db.session.commit()
                flash('Your account has been locked due to multiple failed login attempts.', category='error')
        else:
                flash('Incorrect password, try again.', category='error')
        
    else:
        flash('Email does not exist.', category='error')

    return redirect(url_for('auth.login_get'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login_get')) 

# Sign-up route separated for clarity and security
@auth.route('/sign-up', methods=['GET'])
def sign_up_get():
    # This route will only handle the display of the sign-up form
    return render_template("sign_up.html", user=current_user)

@auth.route('/sign-up', methods=['POST'])
def sign_up_post():
    # This route will handle the form submission for sign-up
    email = request.form.get('email')
    first_name = request.form.get('firstName')
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    user = User.query.filter_by(email=email).first()
    if user:
        flash('Email already exists.', category='error')
    elif len(email) < 4:
        flash('Email must be greater than 3 characters.', category='error')
    elif len(first_name) < 2:
        flash('First name must be greater than 1 character.', category='error')
    elif password1 != password2:
        flash('The new password and old password must be the same.', category='error')
    elif  policy.test(password1):
        flash('''Password does not meet the criteria. 
            Password should have mixed case, alphanumeric characters, symbols, 
            and length should be greater than 7''', category='error')
    else:
        role = request.form.get('role')
        if role not in ['customer', 'seller']:
            flash('Invalid role selected.', category='error')
            return redirect(url_for('auth.sign_up_get'))
        
        new_user = User(
            email=email,
            first_name=first_name,
            password=generate_password_hash(password1, method='pbkdf2:sha256'),
            role=role  # Save the role
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        flash('Account created!', category='success')
        return redirect(url_for('views.home'))

    return redirect(url_for('auth.sign_up_get'))


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    
    if request.method == 'POST':
        

        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
       
            # Verify current password
       
        if check_password_hash(current_user.password, request.form['current_password']):
                # Check if new password matches confirm password
            if new_password == confirm_password:
                    # Update password
                
                if not policy.test(new_password):
                    current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
                    db.session.commit()
                    flash("Your password updated successfully")
                    return redirect(url_for('auth.logout'))
                else:
                    print(policy.test(new_password))
                    flash('''New password does not meet the criteria. 
                        Password should have mixed case, alphanumeric characters, symbols, 
                        and length should be greater than 7''', category='error')
            else:
                flash( "New password and confirm password do not match!")
        else:
            flash("Incorrect current password!")
       
    
    return render_template('changepwd.html', user=current_user)