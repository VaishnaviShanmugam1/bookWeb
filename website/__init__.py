from flask import Flask, session, g
from flask_sqlalchemy import SQLAlchemy
import os
from os import path
from flask_login import LoginManager, logout_user
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect, CSRFError
from dotenv import load_dotenv
from functools import wraps
from flask_migrate import Migrate
import base64

DB_NAME = "database.db"
load_dotenv() 
db = SQLAlchemy()


def check_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if session is permanent and if it has expired
        if 'user_id' in session and not session.permanent:
            # Session is , log the user out
            logout_user()
            return redirect(url_for('auth.login_get'))
        return f(*args, **kwargs)
    return decorated_function


    
def create_app():
    app = Flask(__name__)
    secret_key = os.getenv("FLASK_SECRET_KEY")
    if not secret_key:
        raise ValueError("No FLASK_SECRET_KEY found in environment. The application cannot start without a secret key.")
    
    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True 
    db.init_app(app)
    CSRFProtect(app) 
    migrate = Migrate(app, db)

    from .views import views
    from .auth import auth
    from .admin import admin_bp
    from .models import User, Product, Cart, Feedback  # Import Product model here

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login_get'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
        
    @app.before_request
    def set_csp_nonce():
        g.csp_nonce = base64.b64encode(os.urandom(16)).decode('utf-8')

    @app.after_request
    def apply_csp(response):
        nonce = g.get('csp_nonce', '')
        csp_policy = f"default-src 'self'; script-src 'self' 'nonce-{nonce}' https://ajax.googleapis.com https://code.jquery.com https://cdnjs.cloudflare.com https://maxcdn.bootstrapcdn.com; connect-src 'self'; style-src 'self' 'nonce-{nonce}' https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com https://fonts.googleapis.com https://use.fontawesome.com; img-src 'self' http://books.google.com; font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; form-action 'self';"
        response.headers['Content-Security-Policy'] = csp_policy
        return response
    
    @app.before_request
    @check_session
    def before_request():
        session.modified = True
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logout_user()
        # You can flash a message to the user here if you want
        return redirect(url_for('auth.login_get'))
    
    # Inside the app context
    with app.app_context():
        # Create all tables if not exists
        #Feedback.__table__.drop(db.engine)
        #User.__table__.drop(db.engine)
        #Product.__table__.drop(db.engine)
        db.create_all()

       

        # Commit the session to persist all the changes to the database
        db.session.commit()

    # Call the function to delete duplicate products and pass the app object
    # delete_duplicate_products(app)  # Uncomment this line if necessary

    return app
