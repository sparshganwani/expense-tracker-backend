from flask import Blueprint, request, jsonify
from models import db, User

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    """Register a new user after Firebase authentication"""
    try:
        data = request.get_json()
        
        required_fields = ['firebase_uid', 'email']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(firebase_uid=data['firebase_uid']).first()
        if existing_user:
            return jsonify(existing_user.to_dict()), 200
        
        # Create new user
        new_user = User(
            firebase_uid=data['firebase_uid'],
            email=data['email'],
            name=data.get('name', '')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify(new_user.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/user/<firebase_uid>', methods=['GET'])
def get_user(firebase_uid):
    """Get user by Firebase UID"""
    try:
        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500