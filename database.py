# This file does ALL DB Management
# Add, Remove, Roles, UserAuth (not all of it) is contained in this file
# please god DO NOT CHANGE ANYTHING if you do not know what is going on
# Every other file is dependent on EVERY function in here
# if someone changes something and it messes up processes in auth.py or app.py, I will find you :)
# if you do make changes, branch first, do NOT commit to main

import os
import psycopg2
import psycopg2.extras
import json
import requests
import random

from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_PORT = os.environ.get('DB_PORT', '5432')



def initialize_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        database='postgres'
    )
    cursor = conn.cursor()

    cursor.close()
    conn.close()

def drop_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DROP TABLE IF EXISTS Transactions CASCADE')
    cursor.execute('DROP TABLE IF EXISTS Inventory CASCADE')
    cursor.execute('DROP TABLE IF EXISTS Book CASCADE')
    cursor.execute('DROP TABLE IF EXISTS Author CASCADE')
    cursor.execute('DROP TABLE IF EXISTS Category CASCADE')
    cursor.execute('DROP TABLE IF EXISTS Customers CASCADE')
    cursor.execute('DROP TABLE IF EXISTS BookAuthors CASCADE')
    cursor.execute('DROP TABLE IF EXISTS BookCategories CASCADE')
    cursor.execute('DROP TABLE IF EXISTS SupportTicket CASCADE')
    print("Successfully dropped all tables.")
    
    conn.commit()
    cursor.close()
    conn.close()

def get_db_connection():
    conn = None
    conn = psycopg2.connect(
    host=DB_HOST,
    database='dejiji_db',
    user=DB_USER,
    password=DB_PASS,
    port=DB_PORT
    )
    # only want for debug purposes
    # print('Successfully connected to the database.')
    return conn

def create_tables_roles():

    conn = None
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('CREATE TABLE IF NOT EXISTS Users (' +
                   'user_id VARCHAR(50) PRIMARY KEY, ' +
                   'email VARCHAR(100) UNIQUE NOT NULL, ' +
                   'first_name VARCHAR(50) NOT NULL, ' +
                   'last_name VARCHAR(50) NOT NULL, ' +
                   'password_hash VARCHAR(255) NOT NULL, ' +
                   'role VARCHAR(20) NOT NULL DEFAULT \'Customer\', ' +
                   'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    

    cursor.execute('CREATE TABLE IF NOT EXISTS Category (category_id INT PRIMARY KEY, category_name VARCHAR(100))')
    cursor.execute('CREATE TABLE IF NOT EXISTS Author (author_id INT PRIMARY KEY, author_name VARCHAR(100))')

    cursor.execute('CREATE TABLE IF NOT EXISTS Users (' +
                   'user_id VARCHAR(50) PRIMARY KEY, ' +
                   'email VARCHAR(100) UNIQUE NOT NULL, ' +
                   'first_name VARCHAR(50) NOT NULL, ' +
                   'last_name VARCHAR(50) NOT NULL, ' +
                   'password_hash VARCHAR(255) NOT NULL, ' +
                   'role VARCHAR(20) NOT NULL DEFAULT \'Customer\', ' +
                   'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')

    cursor.execute('CREATE TABLE IF NOT EXISTS Book (' +
                'book_id INT PRIMARY KEY, ' +
                'title VARCHAR(100), ' +
                'price INT, ' +
                'image_id VARCHAR(100), ' +
                'short_description TEXT, ' +
                'uploaded_by VARCHAR(50) REFERENCES Users(user_id))')

    cursor.execute('CREATE TABLE IF NOT EXISTS BookAuthors (' +
                   'book_id INT REFERENCES Book(book_id) ON DELETE CASCADE, ' +
                   'author_id INT REFERENCES Author(author_id) ON DELETE CASCADE, ' +
                   'PRIMARY KEY (book_id, author_id))')
    
    cursor.execute('CREATE TABLE IF NOT EXISTS BookCategories (' +
                   'book_id INT REFERENCES Book(book_id) ON DELETE CASCADE, ' +
                   'category_id INT REFERENCES Category(category_id) ON DELETE CASCADE, ' +
                   'PRIMARY KEY (book_id, category_id))')

    cursor.execute('CREATE TABLE IF NOT EXISTS Customers (' +
                   'customer_id INT PRIMARY KEY, ' +
                   'customer_name VARCHAR(100))')

    cursor.execute('CREATE TABLE IF NOT EXISTS Inventory (book_id INT PRIMARY KEY, Quantity INTEGER, FOREIGN KEY(book_id) REFERENCES Book(book_id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS Transactions (' +
                'transaction_id SERIAL PRIMARY KEY, ' +    #entered 'Serial' for increasing counter
                'transaction_total INT, ' + 
                'transaction_date DATE, ' + 
                'customer_id INT, ' +
                'book_id INT, ' +
                'FOREIGN KEY(customer_id) REFERENCES Customers(customer_id), ' +
                'FOREIGN KEY(book_id) REFERENCES Book(book_id))')
    
    cursor.execute('CREATE TABLE IF NOT EXISTS Cart (' +
               'cart_id SERIAL PRIMARY KEY, ' +
               'user_id VARCHAR(50) REFERENCES Users(user_id), ' +
               'book_id INT REFERENCES Book(book_id), ' +
               'quantity INT DEFAULT 1, ' +
               'added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, ' +
               'UNIQUE(user_id, book_id))')
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS SupportTicket (
            ticket_id   SERIAL PRIMARY KEY,
            user_id     VARCHAR(50) REFERENCES Users(user_id),
            subject     VARCHAR(150)      NOT NULL,
            message     TEXT              NOT NULL,
            status      VARCHAR(20)       NOT NULL DEFAULT 'Open',
            created_at  TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")

    
    #create role customer
    cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'Customer'")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute('CREATE ROLE "Customer"')
    cursor.execute('GRANT SELECT ON Category, Author, Book, Inventory TO "Customer"')
    cursor.execute('GRANT SELECT (transaction_total, transaction_date) ON Transactions TO "Customer"')


    #conditionally create role of employee
    cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'Employee'")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute('CREATE ROLE "Employee"')
    cursor.execute('GRANT INSERT, UPDATE, DELETE ON Customers TO "Employee"')
    cursor.execute('GRANT INSERT, UPDATE, DELETE ON Inventory TO "Employee"')
    cursor.execute('GRANT INSERT, UPDATE, DELETE ON Transactions TO "Employee"') #when employee checks out customer, new data is entered into table about transaction?
    

    #create role of vendor
    cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'Vendor'")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute('CREATE ROLE "Vendor"')


    cursor.execute('GRANT INSERT, UPDATE, DELETE ON Inventory TO "Vendor"')
    cursor.execute('GRANT INSERT, UPDATE, DELETE ON Book TO "Vendor"')
    cursor.execute('GRANT INSERT, UPDATE, DELETE ON Author TO "Vendor"')
    cursor.execute('GRANT INSERT, UPDATE, DELETE ON Category TO "Vendor"')

    print("Successfully initialized database")

    conn.commit()
    cursor.close()
    conn.close()



def assign_user_role(user_id, role):
    con = get_db_connection()
    cur = con.cursor()

    try:
        pg_username = f"user_{user_id.lower().replace('-', '_')}"

        try:
            cur.execute(f'CREATE USER "{pg_username}" WITH PASSWORD %s', (user_id,))
        except psycopg2.errors.DuplicateObject:
            pass

        cur.execute(f'GRANT "{role}" TO "{pg_username}"')

        con.commit()
        return True
    
    except Exception as e:
        print(f"Error assigning role: {e}")
        con.rollback()
        return False
    finally:
        cur.close()
        con.close()

def get_user_role(user_id):
    con = get_db_connection()
    cur = con.cursor()

    try:
        cur.execute("SELECT role FROM Users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error gettin user role: {e}")
        return None
    finally:
        cur.close()
        con.close()

def check_user_permission(user_id, required_role):
    user_role = get_user_role(user_id)
    if not user_role:
        return False
    
    roles = {'Customer': 1, 'Vendor': 2, 'Employee': 3, 'Admin': 4}

    user_level = roles.get(user_role, 0 )
    required_level = roles.get(required_role, 0)

    return user_level >= required_level

# for adding books, categories etc.
def get_or_create_author(author_name):
    con = get_db_connection()
    cur = con.cursor()

    try:
        cur.execute("SELECT author_id FROM Author WHERE LOWER(author_name) = LOWER(%s)", (author_name,))
        result = cur.fetchone()

        if result:
            return result[0]

        cur.execute("SELECT COALESCE(MAX(author_id), 0) + 1 FROM Author")
        new_author_id = cur.fetchone()[0]

        cur.execute("INSERT INTO Author (author_id, author_name) VALUES (%s, %s)", (new_author_id, author_name))

        con.commit()
        return new_author_id
    
    except Exception as e:
        con.rollback()
        raise e
    
    finally:
        cur.close()
        con.close()



def get_or_create_category(category_name):
    con = get_db_connection()
    cur = con.cursor()

    try:
        cur.execute("SELECT category_id FROM Category WHERE LOWER(category_name) = LOWER(%s)", (category_name,))
        result = cur.fetchone()

        if result:
            return result[0]
        
        cur.execute("SELECT COALESCE(MAX(category_id), 0) + 1 FROM Category")
        new_category_id = cur.fetchone()[0]
        
        cur.execute("INSERT INTO Category (category_id, category_name) VALUES (%s, %s)", (new_category_id, category_name))

        con.commit()
        return new_category_id
    except Exception as e:
        con.rollback()
        raise e
    
    finally:
        cur.close()
        con.close()

def download_image_from_url(image_url, book_id, save_dir='static/images', default_image_id='default_book'):
    if not image_url:
        return default_image_id

    try:
        response = requests.get(image_url)
        response.raise_for_status()

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        image_id = f'{book_id}.jpeg'
        image_path = os.path.join(save_dir, image_id)
        with open(image_path, 'wb') as f:
            f.write(response.content)

        return book_id
    except Exception as e:
        print(f'Error downloading image: {e}')
        return default_image_id

# in comboination with multiple people made this function
def add_book_to_database(title, author_names, category_names, price, image_id, uploaded_by, short_description=None):
    con = get_db_connection()
    cur = con.cursor()

    try:
        cur.execute("SELECT COALESCE(MAX(book_id), 0) + 1 FROM Book")
        new_book_id = cur.fetchone()[0]

        if not image_id:
            image_id = 'default_book'

        cur.execute("INSERT INTO Book (book_id, title, price, image_id, uploaded_by, short_description) VALUES (%s, %s, %s, %s, %s, %s)", 
                    (new_book_id, title, price, image_id, uploaded_by, short_description))
        
        # in case there is multiple authors
        for author_name in author_names:
            author_id = get_or_create_author(author_name.strip())
            cur.execute("INSERT INTO BookAuthors (book_id, author_id) VALUES (%s, %s)", (new_book_id, author_id))

        # in case there is multiple categories
        for category_name in category_names:
            category_id = get_or_create_category(category_name.strip())
            cur.execute("INSERT INTO BookCategories (book_id, category_id) VALUES (%s, %s)", (new_book_id, category_id))

        cur.execute("INSERT INTO Inventory (book_id, Quantity) VALUES (%s, %s)", (new_book_id, 1))

        con.commit()
        return True, 'Booked added'
    
    except Exception as e:
        print(f"Error adding book: {e}")
        con.rollback()
        return False, str(e)
    finally:
        cur.close()
        con.close()

def delete_book_from_database(book_id, user_id, user_role):
    con = get_db_connection()
    cur = con.cursor()

    try:
        cur.execute("SELECT uploaded_by FROM Book WHERE book_id = %s", (book_id,))
        result = cur.fetchone()

        if not result:
            return False, "Book not found"
        
        uploaded_by = result[0]

        #Vendors can delete their own books not others
        if user_role == 'Vendor' and uploaded_by != user_id:
            return False
        
        cur.execute("DELETE FROM Inventory WHERE book_id = %s", (book_id,))
        cur.execute("DELETE FROM Cart WHERE book_id = %s", (book_id,))
        cur.execute("DELETE FROM Book WHERE book_id = %s", (book_id,))

        con.commit()
        return True
    
    except Exception as e:
        con.rollback()
        return False, str(e)
    finally:
        cur.close()
        con.close()
def process_checkout_in_database(user_id):
    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute("SELECT * FROM Cart JOIN Book ON Cart.book_id = Book.book_id WHERE user_id = %s", (user_id,))
        cart_items = cur.fetchall()

        if not cart_items:
            return False, "Your cart is empty. Cannot process checkout."

        total_price = sum(item['quantity'] * item['price'] for item in cart_items)

        #adding below
        cur.execute("SELECT customer_id FROM Customers INNER JOIN Users ON Customers.customer_name = (Users.first_name || ' ' || Users.last_name)")
        new_id = cur.fetchone()
        ### now new thing is transactions isn't working

        cur.execute(
            "INSERT INTO Transactions (transaction_total, transaction_date, customer_id) VALUES (%s, CURRENT_DATE, %s)",
            (total_price, new_id)  #changed user_id to new_id
        )

    #updating inventory here, test if user asks for more than stock, works
        for item in cart_items:
            bookId = item['book_id']
            quantity = item['quantity']
            cur.execute("SELECT Quantity FROM Inventory WHERE book_id=%s",(bookId,))
            inventory = cur.fetchone()['quantity']

            if inventory < quantity:
                return False, "We're sorry, we don't have enough in stock for your purchase"
            
            cur.execute("UPDATE Inventory SET Quantity = Quantity-%s WHERE book_id=%s", (quantity, bookId))

            cur.execute("SELECT Quantity FROM Inventory WHERE book_id=%s", (bookId,))
            new_inventory = cur.fetchone()['quantity']
            
            if new_inventory <= 0:
                # Remove book entirely when quantity reaches 0
                cur.execute("DELETE FROM Inventory WHERE book_id = %s", (bookId,))
                cur.execute("DELETE FROM Cart WHERE book_id = %s", (bookId,))
                cur.execute("DELETE FROM BookAuthors WHERE book_id = %s", (bookId,))
                cur.execute("DELETE FROM BookCategories WHERE book_id = %s", (bookId,))
                cur.execute("DELETE FROM Book WHERE book_id = %s", (bookId,))
        
        cur.execute("DELETE FROM Cart WHERE user_id = %s", (user_id,))

        con.commit()
        return True, "Order placed successfully!"

    except Exception as e:
        con.rollback()
        return False, str(e)
    finally:
        cur.close()
        con.close()

def get_all_categories():
    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT category_id, category_name FROM Category ORDER BY category_name")
    data = cur.fetchall()
    cur.close()
    con.close()
    return data

def get_all_authors():
    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT author_id, author_name FROM Author ORDER BY author_name")
    data = cur.fetchall()
    cur.close()
    con.close()
    return data


def pop_from_json(filepath='dejiji.books.json'):
    try:
        with open(filepath, 'r') as f:
            books_data = json.load(f)
    except Exception as e:
        print(f'Error loading JSON file: {e}')
        return

    con = get_db_connection()
    cur = con.cursor()
    
    # dummy user to be the uploader for first 25 books
    uploader_user_id = 'json_importer'
    cur.execute("SELECT user_id FROM Users WHERE user_id = %s", (uploader_user_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO Users (user_id, email, first_name, last_name, password_hash, role) VALUES (%s, %s, %s, %s, %s, %s)",
                    (uploader_user_id, 'importer@system.com', 'JSON', 'Importer', 'nohash', 'Admin'))
        con.commit()
    for book in books_data:
        try:
            book_id = book.get('_id')
            title = book.get('title')
            authors = book.get('authors', [])
            categories = book.get('categories', [])
            short_desc = book.get('shortDescription')
            image_url = book.get('thumbnailUrl')

            if not all([book_id, title, authors, categories]):
                continue

            # check if that book already exists
            cur.execute("SELECT book_id FROM Book WHERE book_id = %s", (book_id,))
            if cur.fetchone():
                continue
            price_rand = lambda: random.randint(5, 35)
            price = price_rand()
            image_id = download_image_from_url(image_url, book_id)
            # insert book with a default price of 20 and image_id as book_id for now
            cur.execute("INSERT INTO Book (book_id, title, price, image_id, uploaded_by, short_description) VALUES (%s, %s, %s, %s, %s, %s)",
                        (book_id, title, price, image_id, uploader_user_id, short_desc))

            # insert authors and link to book
            for author_name in authors:
                if author_name:
                    author_id = get_or_create_author(author_name)
                    cur.execute("INSERT INTO BookAuthors (book_id, author_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (book_id, author_id))

            # insert categories and link to book
            for cat_name in categories:
                if cat_name:
                    category_id = get_or_create_category(cat_name)
                    cur.execute("INSERT INTO BookCategories (book_id, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (book_id, category_id))
            
            quant_rand = lambda: random.randint(5, 20)
            quant = quant_rand()
            cur.execute("INSERT INTO Inventory (book_id, Quantity) VALUES (%s, %s) ON CONFLICT DO NOTHING", (book_id, quant))

        except Exception as e:
            print(f"Error processing book ID {book.get('_id')}: {e}")
            con.rollback()
        else:
            con.commit()
    print("Finished populating database from JSON.")
    cur.close()
    con.close()

def start_db():
    if input("Drop tables? y/n: ").lower() == 'y':
        drop_tables()
    initialize_db()
    create_tables_roles()
    if input("Populate database from dejiji.books.json? y/n: ").lower() == 'y':
        pop_from_json()

if __name__ == '__main__':
    start_db()


