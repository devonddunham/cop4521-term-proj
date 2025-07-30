# Bookstore Platform

A distributed web-based bookstore platform built with Flask, PostgreSQL, and Python featuring role-based access control, and inventory management.

## Features

- **User Roles & Authentication**
  - Customer: Browse products, manage cart, place orders, put complaints
  - Vendor: List products, manage inventory, track sales
  - Employee: Process orders, update inventory, customer service
  - Admin: Full system access and configuration

- **Core Functionality**
  - Product catalog with search and filtering
  - Shopping cart and checkout
  - Inventory management
    - Book upload and delete and modify for:
      - Vendor
        - Can only manage their uploaded books
      - Employee
        - Can manage any uploaded book
  - Customer service management
  - SSO with session tokens
    - Password hashing with bcrypt library

## Problem Solved
Our platform addresses the disconnect between book publishers/vendors, retail management, and customers in traditional bookstore operations.

Our platform allows vendors to upload and manage their own books, without having to go through a publisher or other regulations. A free-market for book selling.

## Description of Extra Features Beyond Proposal
- **Enhanced Security**: bcrypt password hashing, session tokens with TTL, file upload restrictions, SQL injection prevention
- **Real-Time Inventory Management**: Auto-stock removal when quantity reaches zero, vendor-specific book management
- **Multi-Author/Category Support**: Many-to-many relationships with dynamic creation and aggregated display
- **Advanced Search & Discovery**: search (title/author/category), catalog sorting, partial match support
- **Customer Service Integration**: Support ticket system with employee management interface and status tracking
- **Distribution**: Distributed deployment, environment configuration, automated database initialization

## Tech Stack

- **Backend**: Python/Flask
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS
- **Authentication**: Flask-Login, Flask-Security, Session Token, bcrypt Hashing

## Libraries
  bcrypt, blinker, cachelib, certifi, charset-normalizer, click, dotenv, Flask, Flask-Session, gunicorn, idna, itsdangerous, Jinja2, MarkupSafe, msgspec, packaging, psycopg2, python-dotenv, requests, urllib3, Werkzeug, Json, secrets

## Other Resources
  Book Json Source taken from:
  > https://github.com/dudeonthehorse/datasets/blob/master/amazon.books.json

## How To Run
Requirements:
PostgreSQL
.env including:
```
DB_NAME='dejiji_db'
DB_USER='db_user'
DB_PASS='db_user_password'
```
DB User must be a superuser.
.env is not required locally, unless it is first time setup.  

Python3.x

First create a Python Virtual Environment:
```bash
python3 -m venv .venv
```
And activate it:
```bash
source .venv/bin/activate
```
Then, execute the pre-build commands (from project root)
```bash
mkdir -p .static_backup && cp -a static/images/. .static_backup && pip install -r requirements.txt
```
Finally, use gunicorn to deploy the webapp
```bash
gunicorn app:app --bind 127.0.0.1:10000 --workers 5
```

Alternatively use this link to access the distributed version of the webapp at:
https://dejijibooks.store (Does not work on FSU WiFi)

## Distribution of Work
  #### Ethan:
  - created auth.py
    - Secure sign on with user auth
      - Password hashing with bcrypt
      - UserID creation
      - Session tokens with TTL
  - in database.py
    - All RBAC
      - created assign_user_role()
      - created get_user_role()
      - created check_user_permission()
      - Defined role and user tables
      - created get_or_create_author/category()
      - created book upload/delete logic/code
    - Created some tables for DB
  - in app.py
    - created role decorators
    - all auth/check auth
    - created decision (/) page
    - signup/login/logout for customers, vendors, and employees
    - home page
    - /book/<int:book_id> component
    - add to cart
      - update/remove
    - Dashboards for Vendor and Employee
    - /upload_book and /delete_book routes
    - categories and authors api
  - Distributed Component (with Isa)
    - Worked with Isa to deploy the webapp on a distributed VMS
    - Created init_deploy.py
  - Worked in conjunction on HTML with teammates
  - General debugging
  - Final README.md

  #### Ivan: 
  - Added the search by category
  - connected the cart page to checkout and made it calculate the total
  - and created the support page on the customer end along with the table. 
  - Anywhere in those functions I modified the html files to make those features work

  #### Isa:
  - fixed the mult_authors table/with ethan 
  - collaborated with ethan to make VMS
  - intial db set up (if table exits)
  - fixed cart/inventory
  -  made about page
  -  did vendor/employee implementation of the customer service side

  #### Devon: 
  - Added search by title or author
  - added the new schema for multiple authors or categories
  - Added the feature to populate from a json file
  - In collab worked to create the html files

  #### Joshua: 
  - Added the catalog/browse books with the search funtion(title,author,price).
  - Going through the htmls pages to get them to look better and work together.
  - Helped Isa with the about page. 


## For Sharanya
The Vendor and Employee auth codes are both: 12345
