from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import User, Product
from werkzeug.security import generate_password_hash
from . import db

admin_bp = Blueprint('admin_bp', __name__)


@admin_bp.route('/manage-users/<user_type>')
@login_required
def manage_users(user_type):
    print(user_type)
    # Assuming there's an attribute 'role' in your User model
    users = User.query.filter_by(role=user_type).all()
    return render_template('manageselluser.html', users=users, user_type=user_type)

@admin_bp.route('/manage-products')
@login_required
def manage_products():
    products = Product.query.all()
    return render_template('manage_prod.html', products=products)

@admin_bp.route('/remove-user/<user_id>', methods=['POST'])
@login_required
def remove_user(user_id):
    print(user_id)
    user_to_delete = User.query.get(user_id)
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()
        
    # Redirect back to the user management page
    return redirect(url_for('admin_bp.manage_users', user_type=user_to_delete.role))

@admin_bp.route('/remove-product/<product_id>', methods=['POST'])
@login_required
def remove_product(product_id):
    print(product_id)
    product_to_delete = Product.query.get(product_id)
    if product_to_delete:
        db.session.delete(product_to_delete)
        db.session.commit()
        
    
    # After deleting the product, instead of redirecting, return the updated HTML fragment
    products = Product.query.all()  # Fetch all the products again
    return render_template('partials/manage_prod.html', products=products)

@admin_bp.route('/block-user/<user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    user_to_block = User.query.get(user_id)
    if user_to_block:
        user_to_block.is_active = False  # Set a flag or field to mark the user as blocked
        db.session.commit()
       
    return redirect(url_for('admin_bp.manage_users', user_type=user_to_block.role))

@admin_bp.route('/unblock-user/<user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    user_to_unblock = User.query.get(user_id)
    if user_to_unblock:
        user_to_unblock.is_active = True  # Reset the flag or field to unblock the user
        db.session.commit()
        
    return redirect(url_for('admin_bp.manage_users', user_type=user_to_unblock.role))

@admin_bp.route('/approve-product/<product_id>', methods=['POST'])
@login_required
def approve_product(product_id):
    product_to_approve = Product.query.get(product_id)
    if product_to_approve:
        product_to_approve.is_approved = True
        db.session.commit()
        
    # After approving the product, return the updated HTML fragment or JSON response
    products = Product.query.all()
    return render_template('partials/manage_prod.html', products=products)
