from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import *
import psycopg2.extras
from auth import *
from functools import wraps
import os # for uploading files and managing on system
from werkzeug.utils import secure_filename # hell yeah worktrain
import uuid 


app = Flask(__name__)
app.secret_key = 'wubahubalub3456765' #no one guessing ts


UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

"""In check_user_permission() in database.py, I assigned each role to a number
Customer = 1, Vendor = 2, Employee = 3, Admin = 4
The require_role() decorator checks this
if a page requires Vendor to access it, Employee and Admin can also access it
If a page requires Employee, only Employee and Admin can see it, not Vendor or Customer"""

# this is for security and consistency
# it is a security vulnerability to allow unknown files to be uploaded to the system
# this function was written by ChatGPT because idk how to do this (i do now)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def require_role(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_auth():
                return redirect(url_for('login'))
            
            user_id = session.get('user_id')
            if not user_id:
                flash('Please log in')
                return redirect(url_for('login'))
            
            if not check_user_permission(user_id, required_role):
                user_role = get_user_role(user_id)
                flash(f'ACCESS DENIED! Required role: {required_role}')
                if user_role == 'Vendor':
                    return redirect(url_for('vendor_dashboard'))
                elif user_role == 'Employee':
                    return redirect(url_for('employee_dashboard'))
                else:
                    return redirect(url_for('login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user_role():
    if not check_auth():
        return None
    return get_user_role(session.get('user_id'))

def check_auth():
    return 'user_id' in session

def require_auth():
    if not check_auth():
        return redirect(url_for('login'))
    return None

def general_auth():
    auth_redirect = require_auth()
    if auth_redirect:
        return auth_redirect

@app.route('/')
def decision():
    if check_auth():
        user_role = get_current_user_role()
        if user_role == 'Vendor':
            return redirect(url_for('vendor_dashboard'))
        elif user_role == 'Employee':
            return redirect(url_for('employee_dashboard'))
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('signup_selection'))

@app.route('/signup_selection')
def signup_selection():
    return render_template('signup_selection.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')        
        password = request.form.get('password')

        if not all([email, first_name, last_name, password]):
            flash('All fields are required', 'error')
            return render_template('signup.html')
        
        user_id, message = create_user(email, first_name, last_name, password)

        if user_id:
            session['user_id'] = user_id
            session['email'] = email
            session['first_name'] = first_name

            flash('Account created successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash(message, 'error')
            return render_template('signup.html')
        
    return render_template('signup.html')


#making sure only vendors can sign up as vendors is tricky, we have two options:
#make a secret vendor code (which is what this does)
#make a portal for admin/employee that has to approve vendors (i think this is doing too much)

@app.route('/signup/vendor', methods=['GET', 'POST'])
def vendor_signup():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        vendor_code = request.form.get('vendor_code') 

        if not all([email, first_name, last_name, password, vendor_code]):
            flash('All fields are required')
            return render_template('vendor_signup.html')
        
        if vendor_code != "12345": #we can change this
            flash('Imposter! You are not a vendor!')
            return render_template('vendor_signup.html')
        
        user_id, message = create_user(email, first_name, last_name, password, role='Vendor')

        if user_id:
            session['user_id'] = user_id
            session['email'] = email
            session['first_name'] = first_name
            flash('Vendor successfully created!')
            return redirect(url_for('vendor_dashboard'))
        else:
            flash(message, 'error')
            return render_template('vendor_signup.html')
        
    return render_template('vendor_signup.html')


#same options here, to start i will go with the secret code
@app.route('/signup/employee', methods=['GET', 'POST'])
def employee_signup():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        employee_code = request.form.get('employee_code') 

        if not all([email, first_name, last_name, password, employee_code]):
            flash('All fields are required')
            return render_template('employee_signup.html')
        
        if employee_code != "12345": #again, we can change this
            flash('Imposter! You are not an employee!')
            return render_template('employee_signup.html')
        
        user_id, message = create_user(email, first_name, last_name, password, role='Employee')

        if user_id:
            session['user_id'] = user_id
            session['email'] = email
            session['first_name'] = first_name
            flash('Employee successfully created!')
            return redirect(url_for('employee_dashboard'))
        else:
            flash(message, 'error')
            return render_template('employee_signup.html')
        
    return render_template('employee_signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = authenticate_user(email, password)
        if user:
            session['user_id'] = user['user_id']
            session['email'] = user['email']
            session['first_name'] = user['first_name']
            flash('Logged in successfully')


            user_role = get_user_role(user['user_id'])
            if user_role == 'Vendor':
                return redirect(url_for('vendor_dashboard'))
            elif user_role == 'Employee':
                return redirect(url_for('employee_dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid credentials')
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('signup_selection'))


@app.route('/home')
@require_role('Customer')
def home():

    user_id = session.get('user_id')


    con = get_db_connection()
    cursor = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("SELECT first_name FROM Users WHERE user_id = %s", (user_id,))
    

    name = cursor.fetchone()

    Hello = "Hello, " + name[0]
    
    # use STRING_AGG to combine multiple authors into a single string
    cursor.execute("""        
        SELECT b.book_id, b.title, b.price, b.image_id, STRING_AGG(a.author_name, ', ') as author_names
        FROM Book b
        JOIN BookAuthors ba ON b.book_id = ba.book_id
        JOIN Author a ON ba.author_id = a.author_id
        WHERE b.price > 10 AND b.price < 20
        GROUP BY b.book_id
        ORDER BY b.price ASC
    """)

    books_under_20 = cursor.fetchall()

    cursor.execute("""        
        SELECT b.book_id, b.title, b.price, b.image_id, STRING_AGG(a.author_name, ', ') as author_names
        FROM Book b
        JOIN BookAuthors ba ON b.book_id = ba.book_id
        JOIN Author a ON ba.author_id = a.author_id
        WHERE b.price < 10
        GROUP BY b.book_id
        ORDER BY b.price ASC
    """)

    books_under_10 = cursor.fetchall()

    cursor.close()
    con.close()

    if get_current_user_role() == 'Vendor':
        return render_template('vendorHome.html', books_under_10 = books_under_10, books_under_20 = books_under_20, Hello=Hello)
    else:
        return render_template('home.html', books_under_10 = books_under_10, books_under_20 = books_under_20, Hello=Hello)

#this is similar to a React component, it will be used across the webiste
#when a user clicks on a book, this will flash
@app.route('/book/<int:book_id>')
@require_role('Customer')
def book_detail(book_id):


    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT 
            b.book_id, b.title, b.price, b.image_id, b.short_description,
            STRING_AGG(DISTINCT a.author_name, ', ') as author_names,
            STRING_AGG(DISTINCT c.category_name, ', ') as category_names
        FROM Book b
        LEFT JOIN BookAuthors ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        LEFT JOIN BookCategories bc ON b.book_id = bc.book_id
        LEFT JOIN Category c ON bc.category_id = c.category_id
        WHERE b.book_id = %s
        GROUP BY b.book_id
    """, (book_id,))

    book = cur.fetchone()
    cur.close()
    con.close()

    if not book:
        flash('Book not found')
        return redirect(url_for('home'))
    
    return render_template('book_detail.html', book=book)

@app.route('/add_to_cart/<int:book_id>', methods=['POST'])
@require_role('Customer')
def add_to_cart(book_id):

    user_id = session['user_id']
    quantity = int(request.form.get('quantity', 1))

    con = get_db_connection()
    cur = con.cursor()

    try:
        #check if item is in cart
        cur.execute("SELECT quantity FROM Cart WHERE user_id = %s AND book_id = %s", 
                      (user_id, book_id))
        existing = cur.fetchone()

        if existing:
            new_quantity = existing[0] + quantity
            cur.execute("UPDATE Cart SET quantity = %s WHERE user_id = %s AND book_id = %s",
                          (new_quantity, user_id, book_id))
        else:
            #add new book to cart
            cur.execute("INSERT INTO Cart (user_id, book_id, quantity) VALUES (%s, %s, %s)",
                          (user_id, book_id, quantity))
        con.commit()
        cur.execute("SELECT title FROM Book WHERE book_id = %s", (book_id,))
        title_result = cur.fetchone()
        if title_result:
            title = title_result[0]
            flash(f'{title} added to cart!')
        else:
            flash('Book added to cart!')
    
    except Exception as e:
        con.rollback()
        flash('Error adding to cart', 'error')
    finally:
        cur.close()
        con.close()

    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/cart')
@require_role('Customer')
def view_cart():

    user_id = session['user_id']
    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # update command using the new DB schema
    cur.execute("""
        SELECT
            c.cart_id,
            c.quantity,
            b.book_id,
            b.title,
            b.price,
            b.image_id,
            (c.quantity * b.price) as item_total,
            STRING_AGG(a.author_name, ', ') as author_names
        FROM Cart c
        JOIN Book b ON c.book_id = b.book_id
        LEFT JOIN BookAuthors ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE c.user_id = %s
        GROUP BY c.cart_id, b.book_id
        ORDER BY c.added_at DESC
    """, (user_id,))

    cart_items = cur.fetchall()

    total = sum(item['item_total'] for item in cart_items)
    cur.close()
    con.close()

    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/cart/update', methods=['POST'])
@require_role('Customer')
def update_cart_quantity():
    cart_id = request.form.get('cart_id')
    action = request.form.get('action')

    if not cart_id or not action:
        flash('Invalid request')
        return redirect(url_for('view_cart'))
    
    con = get_db_connection()
    cur = con.cursor()

    try:
        cur.execute("SELECT quantity FROM Cart WHERE cart_id = %s", (cart_id,))
        result = cur.fetchone()

        if not result:
            flash('Cart item not found')
            return redirect(url_for('view_cart'))
        current_quantity = result[0]

        if action == 'increase':
            new_quantity = current_quantity + 1
        elif action == 'decrease':
            #just to make sure it cant go negative
            new_quantity = max(1, current_quantity - 1)
        else:
            flash('Invalid action')
            return redirect(url_for('view_cart'))
        
        cur.execute("UPDATE Cart SET quantity = %s WHERE cart_id = %s", (new_quantity, cart_id))
        con.commit()

    except Exception as e:
        con.rollback()
        flash('Error updating cart')
    finally:
        cur.close()
        con.close()
    
    return redirect(url_for('view_cart'))

@app.route('/cart/remove', methods=['POST'])
@require_role('Customer')
def remove_from_cart():
    cart_id = request.form.get('cart_id')

    if not cart_id:
        flash('Invalid request')
        return redirect(url_for('view_cart'))
    
    con = get_db_connection()
    cur = con.cursor()

    try:
        cur.execute("DELETE FROM Cart WHERE cart_id = %s", (cart_id,))
        con.commit()
    
    except Exception as e:
        con.rollback()
        flash('Error removing item from cart')
    finally:
        cur.close()
        con.close()

    return redirect(url_for('view_cart'))

@app.route('/search', methods=['GET', 'POST'])
@require_role('Customer')
def search():
    books = []
    query = ''
    search_type = ''
    if request.method == 'POST':
        if 'search_by_title_author' in request.form:
            query = request.form.get('query', '').strip()
            search_type = 'Title/Author'
            if query:
                con = get_db_connection()
                cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

                # search by title or author name, case insensitive, partial matches (LIKE query), or STRING_AGG for multiple authors
                cur.execute("""
                    SELECT b.book_id, b.title, b.price, b.image_id, b.short_description, STRING_AGG(a.author_name, ', ') as author_names
                    FROM Book b
                    JOIN BookAuthors ba ON b.book_id = ba.book_id
                    JOIN Author a ON ba.author_id = a.author_id
                    GROUP BY b.book_id
                    HAVING LOWER(b.title) LIKE %s OR LOWER(STRING_AGG(a.author_name, ', ')) LIKE %s
                    ORDER BY b.title ASC
                """, (f'%{query.lower()}%', f'%{query.lower()}%'))

                books = cur.fetchall()
                cur.close()
                con.close()
            else:
                flash('Please enter a search term', 'error')
        elif 'search_by_category' in request.form:
            query = request.form.get('category_query', '').strip()
            search_type = 'Category'
            if query:
                con = get_db_connection()
                cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
                # query for searching by category
                cur.execute("""
                    SELECT b.book_id, b.title, b.price, b.image_id, b.short_description, STRING_AGG(a.author_name, ', ') as author_names
                    FROM Book b
                    LEFT JOIN BookAuthors ba ON b.book_id = ba.book_id
                    LEFT JOIN Author a     ON ba.author_id = a.author_id
                    JOIN BookCategories bc ON b.book_id = bc.book_id
                    JOIN Category c ON bc.category_id = c.category_id
                    WHERE LOWER(c.category_name) LIKE %s
                    GROUP BY b.book_id
                    ORDER BY b.title ASC
                """, (f'%{query.lower()}%',))
                books = cur.fetchall()
                cur.close()
                con.close()
            else:
                flash('Please enter a search term for Category.', 'error')

    return render_template('searchbooks.html', books=books, query=query, search_type=search_type)


#dashboards:

@app.route('/vendor/dashboard')
@require_role('Vendor')
def vendor_dashboard():
    user_id = session['user_id']
    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT b.book_id, b.title, b.price, b.image_id, a.author_name, c.category_name
        FROM Book b
        JOIN Author a ON b.author_id = a.author_id
        JOIN Category c ON b.category_id = c.category_id
        WHERE b.uploaded_by = %s
        ORDER BY b.book_id DESC
    """, (user_id,))

    books = cur.fetchall()
    cur.close()
    con.close()

    return render_template('vendor_dashboard.html', books=books)

@app.route('/employee/dashboard')
@require_role('Employee')
def employee_dashboard():
    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT b.book_id, b.title, b.price, b.image_id, a.author_name, c.category_name, 
               u.first_name as uploaded_by_name
        FROM Book b
        JOIN Author a ON b.author_id = a.author_id
        JOIN Category c ON b.category_id = c.category_id
        LEFT JOIN Users u ON b.uploaded_by = u.user_id
        ORDER BY b.book_id DESC
    """)

    books = cur.fetchall()
    cur.close()
    con.close()

    return render_template('employee_dashboard.html', books=books)



#upload processes:
@app.route('/upload_book', methods=['GET', 'POST'])
@require_role('Vendor')
def upload_book():
    user_role = get_current_user_role()

    if request.method == 'POST':
        title = request.form.get('title')
        author_name_str = request.form.get('author_name', '')
        category_name_str = request.form.get('category_name', '')
        price = request.form.get('price')
        short_description = request.form.get('short_description')

        author_names = [name.strip() for name in author_name_str.split(',') if name.strip()]
        category_names = [name.strip() for name in category_name_str.split(',') if name.strip()]

        book_image = request.files.get('book_image')
        image_id = 'default_book' #if no image uploaded, go to default
        #TODO add a default image in static

        #once again i had to consult ChatGPT for help
        if book_image and book_image.filename != '' and allowed_file(book_image.filename):
            filename = secure_filename(book_image.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

            #make sure the path exists, if this is ur first time cloning, it will not
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            book_image.save(image_path)

            image_id = os.path.splitext(unique_filename)[0]

        if not all([title, author_names, category_names, price]):
            flash("All fields except image are required, ")
            return render_template('upload_book.html',user_role=user_role)
        
        try:
            price = int(price)
            if price <= 0:
                flash('Price must be a positive number')
                return render_template('upload_book.html', user_role=user_role)
        except ValueError:
            flash('Price is invalid')
            return render_template('upload_book.html',user_role=user_role)
        
        user_id = session['user_id']
        success, message = add_book_to_database(title, author_names, category_names, price, image_id, user_id, short_description)

        if success:
            flash('Book uploaded!')
            if user_role == 'Employee':
                return redirect(url_for('employee_dashboard'))
            else:
                return redirect(url_for('vendor_dashboard'))
        else:
            flash(f'Error uploading book: {message}')

    return render_template('upload_book.html', user_role=user_role)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
@require_role('Vendor')
def delete_book(book_id):
    user_id = session['user_id']
    user_role = get_current_user_role()

    success, message = delete_book_from_database(book_id, user_id, user_role)

    if success:
        flash("Book deleted!")
    else:
        flash("Book failed to delete!")

    if user_role == 'Employee':
        return redirect(url_for('employee_dashboard'))
    else:
        return redirect(url_for('vendor_dashboard'))
    
#TODO: Add categories in database.py
@app.route('/api/categories')
@require_role('Vendor')
def get_categories():
    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT category_id, category_name FROM Category ORDER BY category_name")
    categories = cur.fetchall()

    cur.close()
    con.close()

    # this is for the dropdown on the upload books page
    # im so fr i had no clue how to do this i had to ask chat
    return  {'categories': [dict(cat) for cat in categories]}

@app.route('/api/authors')
@require_role('Vendor')
def get_authors():
    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT author_id, author_name FROM Author ORDER BY author_name")
    authors = cur.fetchall()

    cur.close()
    con.close()

    #same as above
    return  {'categories': [dict(author) for author in authors]}
        
@app.route('/about')
@require_role('Customer')
def about():
    return render_template('about.html')


@app.route('/catalog', methods=['POST', 'GET']) 
@require_role('Customer')
def display_books():
    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)


    sort_by = request.form.get('sort') or request.args.get('sort', 'title')
    valid_sorts = {
        'title': 'b.title',
        'author_names': 'author_names', 
        'price': 'b.price',
        'category_names': 'category_names'
    }
    if sort_by not in valid_sorts:
        sort_by = 'title'
    
    # Use parameterized query to prevent SQL injection
    # updated command to reflect new DB schema
    sort_column = valid_sorts[sort_by]
    cur.execute(f"""
        SELECT 
            b.book_id,
            b.title, 
            b.price, 
            b.image_id,  
            STRING_AGG(DISTINCT a.author_name, ', ') AS author_names, 
            STRING_AGG(DISTINCT c.category_name, ', ') AS category_names
        FROM Book b
        LEFT JOIN BookAuthors ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        LEFT JOIN BookCategories bc ON b.book_id = bc.book_id
        LEFT JOIN Category c ON bc.category_id = c.category_id
        GROUP BY b.book_id
        ORDER BY {sort_column} ASC
    """)

        
    books = cur.fetchall()
    cur.close()
    con.close()
    return render_template('catalog.html', all_books = books, sort_by = sort_by)
    

@app.errorhandler(404)
def page_not_found(e):
    # Handles "Page Not Found" errors.
    return render_template(
        'error.html',
        error_code="404",
        error_title="Page Not Found",
        error_message="Sorry, the page you are looking for does not exist or has been moved."
    ), 404

@app.errorhandler(500)
def internal_server_error(e):
    # Handles "Internal Server Error" when the code crashes.
    return render_template(
        'error.html',
        error_code="500",
        error_title="Internal Server Error",
        error_message="We're sorry, something went wrong on our end. We've been notified and are looking into it."
    ), 500
@app.route('/checkout', methods=['GET', 'POST'])
@require_role('Customer')
def checkout():
    user_id = session.get('user_id')

    if request.method == 'POST':
        success, message = process_checkout_in_database(user_id)
        if success:
            flash(message, 'success')
            return redirect(url_for('home'))
        else:
            flash(f"An error occurred during checkout: {message}", 'error')
            return redirect(url_for('view_cart'))

    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT c.quantity, b.title, b.price, (c.quantity * b.price) as item_total
        FROM Cart c JOIN Book b ON c.book_id = b.book_id WHERE c.user_id = %s
    """, (user_id,))
    cart_items = cur.fetchall()
    cur.close()
    con.close()

    if not cart_items:
        flash("Your cart is empty.", "info")
        return redirect(url_for('view_cart'))

    total = sum(item['item_total'] for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/support', methods=['GET', 'POST'])
@require_role('Customer')
def support():
    user_id = session.get('user_id')
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        con = get_db_connection()
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            if not subject or not message:
                flash('Both subject and mess are required.','error')
                return render_template('support.html', subject=subject, message=message)
            cur.execute(
            """
            INSERT INTO SupportTicket (user_id, subject, message)
            VALUES (%s, %s, %s)
            """,
            (user_id, subject, message)
            )
            con.commit()
            flash("Your support ticket has been sent!","success")
        except Exception as e:
            con.rollback()
            flash('Error submitting ticket. Please try again.', 'error')

        finally:
            cur.close()
            con.close()
        # refresh page so user cannot resubmit the same form
        return redirect(url_for('support'))
    return render_template('support.html')

if __name__ == '__main__':
    start_db()

    app.run(debug=True)