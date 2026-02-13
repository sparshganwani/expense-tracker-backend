from flask import Blueprint, request, jsonify
from models import db, Category

bp = Blueprint('categories', __name__)

# Default categories to create for new users
DEFAULT_CATEGORIES = [
    'Groceries',
    'Health',
    'Entertainment',
    'Shopping',
    'Food & Dining',
    'Transportation',
    'Utilities',
    'Other'
]

@bp.route('/<int:user_id>', methods=['GET'])
def get_categories(user_id):
    """Get all categories for a user"""
    try:
        categories = Category.query.filter_by(user_id=user_id).all()
        return jsonify([category.to_dict() for category in categories]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['POST'])
def add_category():
    """Add a new category"""
    try:
        data = request.get_json()
        
        if 'user_id' not in data or 'name' not in data:
            return jsonify({'error': 'user_id and name are required'}), 400
        
        # Check if category already exists for this user
        existing = Category.query.filter_by(
            user_id=data['user_id'],
            name=data['name']
        ).first()
        
        if existing:
            return jsonify({'error': 'Category already exists'}), 400
        
        new_category = Category(
            user_id=data['user_id'],
            name=data['name'],
            is_default=False,
            monthly_budget=data.get('monthly_budget')
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        return jsonify(new_category.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update a category (mainly for budget)"""
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data and not category.is_default:
            category.name = data['name']
        
        if 'monthly_budget' in data:
            category.monthly_budget = data['monthly_budget']
        
        db.session.commit()
        return jsonify(category.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a custom category"""
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        if category.is_default:
            return jsonify({'error': 'Cannot delete default categories'}), 400
        
        db.session.delete(category)
        db.session.commit()
        return jsonify({'message': 'Category deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/initialize/<int:user_id>', methods=['POST'])
def initialize_default_categories(user_id):
    """Create default categories for a new user"""
    try:
        created_categories = []
        
        for cat_name in DEFAULT_CATEGORIES:
            # Check if it doesn't already exist
            existing = Category.query.filter_by(user_id=user_id, name=cat_name).first()
            if not existing:
                category = Category(
                    user_id=user_id,
                    name=cat_name,
                    is_default=True
                )
                db.session.add(category)
                created_categories.append(cat_name)
        
        db.session.commit()
        return jsonify({
            'message': f'Created {len(created_categories)} default categories',
            'categories': created_categories
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500