from flask import Flask, jsonify
from flask_cors import CORS
from models import db
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration
database_url = os.getenv('DATABASE_URL', 'sqlite:///expense_tracker.db')
   # Fix for PostgreSQL URL from Render
   if database_url and database_url.startswith('postgres://'):
       database_url = database_url.replace('postgres://', 'postgresql://', 1)
   app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database
db.init_app(app)

# Import routes
from routes import expenses, categories, auth

# Register blueprints (routes)
app.register_blueprint(expenses.bp, url_prefix='/api/expenses')
app.register_blueprint(categories.bp, url_prefix='/api/categories')
app.register_blueprint(auth.bp, url_prefix='/api/auth')

# Test route
@app.route('/')
def home():
    return jsonify({'message': 'Expense Tracker API is running!'})

# Create tables
with app.app_context():
    db.create_all()
    print("Database tables created!")

if __name__ == '__main__':
    app.run(debug=True, port=5000)