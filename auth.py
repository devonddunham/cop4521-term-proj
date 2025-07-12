import bcrypt
import secrets
import string
from database import *
import psycopg2.extras 

"""
logic for this file (Ethan Anderson)
For end-users (customers) Sign-up: 
Email
Name (F/L)
Password

Create userID from: Trim first 5 letters from first name, append to string
Trim first “” “” “” “” “” last name, append to string
email address before the @, append to string
srand() or dev/urandom 5 random numbers, append to string

userID should look likeFirstName[::5]+LastName[::5]+Email[strip(@)::]+randomNumber(5 long)
use bcrypt() to hash password with a salt(userID) or just a static salt

ignore bad typos for comments (i have a concussion)
"""


#TODO: Add date requirement for session token


def generate_user_id(first_name, last_name, email):
    first_part = first_name[:5].lower()
    last_part = last_name[:5].lower()
    email_part = email.split('@')[0].lower()
    random_numbers = ''.join([str(secrets.randbelow(10)) for _ in range(5)])
    user_id = f"{first_part}{last_part}{email_part}{random_numbers}"

    return user_id

def hash_password(password, user_id):
    
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_user(email, first_name, last_name, password, role='Customer'):
    con = get_db_connection()
    cur = con.cursor()

    try:
        #first we wanna check to make sure user doesnt exist
        cur.execute("SELECT email FROM Users WHERE email = %s", (email,))
        if cur.fetchone():
            return None, "Email Exists"
        
        user_id = generate_user_id(first_name, last_name, email)

        #make sure user_id is unique
        cur.execute("SELECT user_id FROM Users WHERE user_id = %s", (user_id,))
        while cur.fetchone():
            user_id = generate_user_id(first_name, last_name, email)
            cur.execute("SELECT user_id FROM Users WHERE user_id = %s", (user_id,))

        #get the hash
        password_hash = hash_password(password, user_id)

        cur.execute("""
            INSERT INTO Users (user_id, email, first_name, last_name, password_hash, role)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, email, first_name, last_name, password_hash, role))

        con.commit()
        cur.close()
        con.close()

        if not assign_user_role(user_id, role):
            print("Error assigning role")

        return user_id, "User creation was successful!"

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        return None, f"Error creating user: {str(e)}"
    
def authenticate_user(email, password):
    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cur.execute('SELECT user_id, email, first_name, last_name, password_hash, role FROM Users WHERE email = %s', (email,))

        user = cur.fetchone()
        cur.close()
        con.close()

        if user and verify_password(password, user['password_hash']):
            return dict(user)
        return None
    
    except Exception as e:
        cur.close()
        con.close()
        return None