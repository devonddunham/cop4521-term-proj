# Bookstore Platform

A web-based bookstore platform built with Flask and PostgreSQL, featuring role-based access control, parallel processing capabilities, and inventory management.

## Features

- **User Roles & Authentication**

  - Customer: Browse products, manage cart, place orders
  - Vendor: List products, manage inventory, track sales 
  - Employee: Process orders, update inventory, customer service
  - Admin: Full system access and configuration

- **Core Functionality**
  - Product catalog with search and filtering
  - Shopping cart and secure checkout
  - Order tracking and management
  - Inventory management

## Tech Stack

- **Backend**: Python/Flask
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login, Flask-Security

## Libraries
  bcrypt, blinker, cachelib, certifi, charset-normalizer, click, dotenv, Flask, Flask-Session, gunicorn, idna, itsdangerous, Jinja2, MarkupSafe, msgspec, packaging, psycopg2, python-dotenv, requests, urllib3, Werkzeug, Json, secrets 

## Distribution of Work
  Ethan:
  ### Ivan: Added the search by category, connected the cart page to checkout and made it calculate the total, and created the support page on the customer end along with the table. Anywhere in those functions I modified the html files to make those features work
  Isa: fixed the mult_authors table/with ethan, collaborated with ethan to make VMS, intial db set up (if table exits), fixed cart/inventory, made about page, did vendor/employee implementation of the customer service side
  ### Devon: Added search by title or author. added the new schema for multiple authors or categories. Added the feature to populate from a json file. In collab worked to create the html files
   ### Joshua: Added the catalog/browse books with the search funtion(title,author,price). Going through the htmls pages to get them to look better and work together. Helped Isa with the about page. 
  Jack:
