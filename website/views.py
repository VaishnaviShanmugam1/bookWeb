from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Feedback, Product, Cart, User
from flask_mail import Message, Mail
from . import db
import requests
from flask import jsonify 
from .admin import admin_bp

views = Blueprint('views', __name__)
CART_ROUTE = 'views.cart'

# Global variables are not recommended, consider removing them and using session instead

# Adjusted Route for Home Page to only handle GET requests
@views.route('/')
@login_required
def home():
    print("Current user role:", current_user.role)  # Ad
    if current_user.role == 'customer':
        
        product_list = Product.query.filter(Product.is_approved==True).all()
        my_list = [{
            'Name': prod.name,
            'Price': prod.price,
            'Author': prod.author,
            'Year': prod.year,
            'Image_url': prod.image_url
        } for prod in product_list]
        return render_template('market.html', list=my_list, user=current_user)
    elif current_user.role == 'seller':
        listed_books = Product.query.filter_by(user_id=current_user.id).all()
        return render_template('list_book.html', user=current_user, listed_books=listed_books)
    else:
        users = User.query.all()
        products = Product.query.all()
        return render_template('admin.html', users=users, products=products)

@views.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    name = request.form.get("Name")
    price = request.form.get("Price")
    existing_item = Cart.query.filter_by(name=name, user_id=current_user.id).first()
    if existing_item:
        existing_item.quantity += 1
        existing_item.Final_Amount = existing_item.price * existing_item.quantity
        flash('Increased quantity of the product in your cart!', category='success')
    else:
        new_item = Cart(name=name, price=price, user_id=current_user.id, quantity=1, Final_Amount=price)
        db.session.add(new_item)
        flash('Product has been added successfully to the cart!', category='success')
    db.session.commit()
    return redirect(url_for('views.home'))

@views.route('/cart', methods=['GET'])
@login_required
def cart():
    # Retrieve the cart items for the current user
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    # Calculate total count and total value
    total_count = sum(item.quantity for item in cart_items)  # Now it counts the quantity of each item
    total_val = sum(item.price * item.quantity for item in cart_items)  # Now it accounts for the quantity of each item

    return render_template('cart.html', cart_items=cart_items, user=current_user, total_count=total_count, total_amount=total_val)



@views.route('/pay', methods=['POST'])
@login_required
def pay():
    # Check if the cart is empty
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty. Please add some products before proceeding to payment.', category='error')
        # Redirect the user back to the cart or another relevant page
        return redirect(url_for(CART_ROUTE))

    # Get card details from the form
    #card_number = request.form.get("card_number")
    #card_expiry = request.form.get("card_expiry")
    #card_cvv = request.form.get("card_cvv")
    

    # If payment is successful, clear the cart
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    flash('Payment successful. Your cart has been cleared.', category='success')
    
    # Redirect the user to the home page or another relevant page
    return redirect(url_for('views.home'))

@views.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        rating = request.form.get("rating")  # Capture the rating value from the form
        
        # Assuming the rating is mandatory, you might want to validate it
        if not rating:
            flash('Please select a rating.', category='error')
            return render_template('feedback.html', user=current_user)

        # Convert rating to integer
        rating = int(rating)

        feedback = Feedback(name=name, email=email, message=message, rating=rating)
        db.session.add(feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!', category='success')
        return redirect(url_for('views.feedback'))
    
    feedbacks = Feedback.query.all()  # Retrieve all feedbacks from the database
    return render_template('feedback.html', user=current_user, feedbacks=feedbacks)


@views.route('/update-cart-item/<int:item_id>/<action>', methods=['POST'])
@login_required
def update_cart_item(item_id, action):
    cart_item = Cart.query.filter_by(id=item_id, user_id=current_user.id).first()
    if cart_item:
        if action == 'add':
            cart_item.quantity += 1
            cart_item.Final_Amount = cart_item.price * cart_item.quantity
            flash('Cart updated successfully!', category='success')
        elif action == 'subtract':
            cart_item.quantity -= 1

            # If quantity is 0, remove the item from the cart
            if cart_item.quantity == 0:
                db.session.delete(cart_item)
                flash('Item removed from cart.', category='success')
            else:
                # Update the final amount for the cart item
                cart_item.Final_Amount = cart_item.price * cart_item.quantity
                flash('Cart updated successfully!', category='success')
        
       

        db.session.commit()
        
    else:
        flash('Item not found in cart.', category='error')
    
    return redirect(url_for(CART_ROUTE))


@views.route('/remove-from-cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = Cart.query.filter_by(id=item_id, user_id=current_user.id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart.', category='success')
    else:
        flash('Item not found in cart.', category='error')
    
    return redirect(url_for(CART_ROUTE))

@views.route('/contactus', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        
        flash('Your message has been sent. Thank you for contacting us!', category='success')
        
    return render_template('contactus.html')

@views.route('/list-book', methods=['GET', 'POST'])
@login_required
def list_book():
    if request.method == 'POST':
        isbn = request.form.get('isbn')
        author_name = request.form.get('author')  # Renamed for clarity
        price = request.form.get('price')
        if not Product.query.filter_by(id =isbn):
            base_url = "https://www.googleapis.com/books/v1/volumes"
            query = f"isbn:{isbn}+inauthor:{author_name}"  # Adjusted query format
            response = requests.get(f"{base_url}?q={query}")
           

            if response.status_code == 200:
                data = response.json()
                print(response.json())
                if data['totalItems'] > 0:
                # Assuming you want the first result
                    book_info = data['items'][0]['volumeInfo']
                    name = book_info.get("title")
                    authors = ", ".join(book_info.get("authors", []))
                    publisher = book_info.get("publisher")
                    year = book_info.get("publishedDate")[:4] if book_info.get("publishedDate") else None  # Extract year
                    image_url = book_info.get("imageLinks", {}).get("thumbnail")
                
                # Create and add new Product instance
                    new_book = Product(id = isbn, name=name, author=authors, publisher=publisher, price=price, year=year, image_url=image_url, user_id=current_user.id)
                    db.session.add(new_book)
                    db.session.commit()
                    flash(f'Thanks for choosing us to sell your collections!. We will verify your "{name}" book and bring it to readers', 'success')
                else:
                    flash('Please verify the ISBN and author fields. Couldn\'t find the book in Google Books API.', 'error')
            else:
                flash('Failed to fetch book details from Google Books API.', 'error')
            
        else:
            flash('Book has been already available in the database', 'error')
    return redirect(url_for('views.home'))

@views.route('/edit-book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = Product.query.get_or_404(book_id)
    if request.method == 'POST':
        if book.user_id == current_user.id:
            new_price = request.form['new_price']
            book.price = new_price
            db.session.commit()
            flash('Book price updated.', 'success')
        else:
            flash('You are not authorized to edit this book.')
        #return redirect(url_for('views.list_book'))
    # GET request logic if necessary
    return redirect(url_for('views.home'))

# Route to handle removing a book
@views.route('/remove-book/<int:book_id>', methods=['POST'])
@login_required
def remove_book(book_id):
    book = Product.query.get_or_404(book_id)
    if book.user_id == current_user.id:
        db.session.delete(book)
        db.session.commit()
        flash('Book removed successfully.', 'success')
    else:
        flash('You are not authorized to remove this book.', 'danger')
    return redirect(url_for('views.home'))


