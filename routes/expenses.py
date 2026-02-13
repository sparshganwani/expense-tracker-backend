from flask import Blueprint, request, jsonify
from models import db, Expense, Category
from datetime import datetime
from sqlalchemy import extract, func

bp = Blueprint('expenses', __name__)

@bp.route('/<int:user_id>', methods=['GET'])
def get_expenses(user_id):
    """Get all expenses for a user"""
    try:
        expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
        return jsonify([expense.to_dict() for expense in expenses]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['POST'])
def add_expense():
    """Add a new expense"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'category_id', 'amount', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Parse date
        expense_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Create new expense
        new_expense = Expense(
            user_id=data['user_id'],
            category_id=data['category_id'],
            amount=float(data['amount']),
            description=data.get('description', ''),
            date=expense_date
        )
        
        db.session.add(new_expense)
        db.session.commit()
        
        return jsonify(new_expense.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """Update an existing expense"""
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404
        
        data = request.get_json()
        
        if 'amount' in data:
            expense.amount = float(data['amount'])
        if 'description' in data:
            expense.description = data['description']
        if 'date' in data:
            expense.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'category_id' in data:
            expense.category_id = data['category_id']
        
        db.session.commit()
        return jsonify(expense.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404
        
        db.session.delete(expense)
        db.session.commit()
        return jsonify({'message': 'Expense deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/by-category/<int:user_id>/<int:category_id>', methods=['GET'])
def get_expenses_by_category(user_id, category_id):
    """Get all expenses for a specific category with monthly totals"""
    try:
        # Get all expenses for this category
        expenses = Expense.query.filter_by(
            user_id=user_id,
            category_id=category_id
        ).order_by(Expense.date.desc()).all()
        
        # Calculate monthly totals for chart
        monthly_totals = db.session.query(
            extract('year', Expense.date).label('year'),
            extract('month', Expense.date).label('month'),
            func.sum(Expense.amount).label('total')
        ).filter_by(
            user_id=user_id,
            category_id=category_id
        ).group_by('year', 'month').order_by('year', 'month').all()
        
        chart_data = [
            {
                'date': f"{int(year)}-{int(month):02d}",
                'total': float(total)
            }
            for year, month, total in monthly_totals
        ]
        
        return jsonify({
            'expenses': [expense.to_dict() for expense in expenses],
            'chart_data': chart_data
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/monthly-summary/<int:user_id>/<int:year>/<int:month>', methods=['GET'])
def get_monthly_summary(user_id, year, month):
    """Get expense summary for a specific month"""
    try:
        # Get expenses for the month grouped by category
        summary = db.session.query(
            Category.id,
            Category.name,
            Category.monthly_budget,
            func.sum(Expense.amount).label('total_spent')
        ).join(Expense).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month
        ).group_by(Category.id, Category.name, Category.monthly_budget).all()
        
        result = []
        for cat_id, cat_name, budget, spent in summary:
            result.append({
                'category_id': cat_id,
                'category_name': cat_name,
                'monthly_budget': budget,
                'total_spent': float(spent),
                'percentage_used': (float(spent) / budget * 100) if budget else None
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500