"""
Demo mode management for PennyWise v2
"""

import json
import random
from datetime import datetime, timedelta
from database.db_manager import execute_query, fetch_all, fetch_one
from core.config import Config
from core.logger import logger

class DemoManager:
    """Manage demo data and scenarios"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.scenarios = {
            'healthy': self._create_healthy_spender_scenario,
            'needs_help': self._create_needs_help_scenario,
            'savings_challenge': self._create_savings_challenge_scenario
        }
    
    def seed_demo_data(self, scenario_type='healthy'):
        """Seed demo data for a specific scenario"""
        if scenario_type not in self.scenarios:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
        
        logger.info(f"Seeding demo data for scenario: {scenario_type}")
        
        # Clear existing demo data for this user
        self._clear_existing_demo_data()
        
        # Create scenario data
        scenario_data = self.scenarios[scenario_type]()
        
        # Save to cache
        self._cache_demo_data(scenario_type, scenario_data)
        
        # Apply to user's actual data
        self._apply_demo_data(scenario_data)
        
        logger.info(f"Demo data seeded successfully for scenario: {scenario_type}")
        return True
    
    def _create_healthy_spender_scenario(self):
        """Create data for a financially healthy user"""
        return {
            'accounts': [
                {
                    'bank_name': 'Demo Checking',
                    'account_type': 'salary',
                    'balance': 4500.00
                },
                {
                    'bank_name': 'Demo Savings', 
                    'account_type': 'savings',
                    'balance': 12000.00
                }
            ],
            'transactions': self._generate_healthy_transactions(),
            'budgets': [
                {'category_name': 'Groceries', 'budget_amount': 400.00, 'spent': 320.00},
                {'category_name': 'Entertainment', 'budget_amount': 150.00, 'spent': 120.00},
                {'category_name': 'Dining Out', 'budget_amount': 200.00, 'spent': 180.00},
                {'category_name': 'Transportation', 'budget_amount': 100.00, 'spent': 85.00}
            ],
            'commitments': [
                {'category_name': 'Rent', 'amount': 1200.00, 'is_paid': 1},
                {'category_name': 'Netflix', 'amount': 15.99, 'is_paid': 1}
            ]
        }
    
    def _create_needs_help_scenario(self):
        """Create data for a user who needs financial help"""
        return {
            'accounts': [
                {
                    'bank_name': 'Demo Checking',
                    'account_type': 'salary', 
                    'balance': 350.00
                },
                {
                    'bank_name': 'Demo Savings',
                    'account_type': 'savings',
                    'balance': 500.00
                }
            ],
            'transactions': self._generate_struggling_transactions(),
            'budgets': [
                {'category_name': 'Groceries', 'budget_amount': 300.00, 'spent': 350.00},
                {'category_name': 'Entertainment', 'budget_amount': 50.00, 'spent': 120.00},
                {'category_name': 'Dining Out', 'budget_amount': 100.00, 'spent': 250.00},
                {'category_name': 'Shopping', 'budget_amount': 100.00, 'spent': 300.00}
            ],
            'commitments': [
                {'category_name': 'Credit Card', 'amount': 150.00, 'is_paid': 0},
                {'category_name': 'Student Loan', 'amount': 200.00, 'is_paid': 0}
            ]
        }
    
    def _create_savings_challenge_scenario(self):
        """Create data for savings-focused user"""
        return {
            'accounts': [
                {
                    'bank_name': 'Demo Checking',
                    'account_type': 'salary',
                    'balance': 2800.00
                },
                {
                    'bank_name': 'Vacation Fund',
                    'account_type': 'savings', 
                    'balance': 2500.00
                },
                {
                    'bank_name': 'Emergency Fund',
                    'account_type': 'savings',
                    'balance': 5000.00
                }
            ],
            'transactions': self._generate_savings_transactions(),
            'budgets': [
                {'category_name': 'Groceries', 'budget_amount': 350.00, 'spent': 300.00},
                {'category_name': 'Entertainment', 'budget_amount': 75.00, 'spent': 60.00},
                {'category_name': 'Dining Out', 'budget_amount': 100.00, 'spent': 80.00},
                {'category_name': 'Savings', 'budget_amount': 500.00, 'spent': 500.00}
            ],
            'commitments': [
                {'category_name': 'Auto Savings', 'amount': 200.00, 'is_paid': 1},
                {'category_name': 'Investment', 'amount': 300.00, 'is_paid': 1}
            ]
        }
    
    def _generate_healthy_transactions(self):
        """Generate realistic transactions for healthy spender"""
        transactions = []
        base_date = datetime.now() - timedelta(days=30)
        
        # Income
        transactions.extend([
            {'date': (base_date + timedelta(days=0)).strftime('%Y-%m-%d'), 'amount': 2500.00, 'type': 'income', 'description': 'Salary', 'category': 'Income'},
            {'date': (base_date + timedelta(days=14)).strftime('%Y-%m-%d'), 'amount': 2500.00, 'type': 'income', 'description': 'Salary', 'category': 'Income'}
        ])
        
        # Expenses
        expense_pattern = [
            (85.00, 'Whole Foods', 'Groceries'),
            (45.00, 'Shell Gas', 'Transportation'),
            (65.00, 'Amazon', 'Shopping'),
            (35.00, 'Netflix & Spotify', 'Entertainment'),
            (28.00, 'Starbucks', 'Dining Out'),
            (42.00, 'CVS Pharmacy', 'Healthcare'),
            (120.00, 'Electric Bill', 'Bills'),
            (60.00, 'Internet Bill', 'Bills')
        ]
        
        for i, (amount, desc, category) in enumerate(expense_pattern):
            transactions.append({
                'date': (base_date + timedelta(days=3+i*4)).strftime('%Y-%m-%d'),
                'amount': amount,
                'type': 'expense',
                'description': desc,
                'category': category
            })
        
        return transactions
    
    def _generate_struggling_transactions(self):
        """Generate transactions for struggling user"""
        transactions = []
        base_date = datetime.now() - timedelta(days=30)
        
        # Income
        transactions.append({
            'date': (base_date + timedelta(days=0)).strftime('%Y-%m-%d'),
            'amount': 1800.00,
            'type': 'income', 
            'description': 'Salary',
            'category': 'Income'
        })
        
        # Expenses (overspending)
        struggling_expenses = [
            (120.00, 'Uber Eats', 'Dining Out'),
            (75.00, 'Online Shopping', 'Shopping'),
            (45.00, 'Movie Theater', 'Entertainment'),
            (200.00, 'Credit Card Payment', 'Bills'),
            (85.00, 'Groceries', 'Groceries'),
            (60.00, 'Gas', 'Transportation'),
            (35.00, 'Coffee Shop', 'Dining Out'),
            (90.00, 'Clothing Store', 'Shopping')
        ]
        
        for i, (amount, desc, category) in enumerate(struggling_expenses):
            transactions.append({
                'date': (base_date + timedelta(days=2+i*3)).strftime('%Y-%m-%d'),
                'amount': amount,
                'type': 'expense',
                'description': desc,
                'category': category
            })
        
        return transactions
    
    def _generate_savings_transactions(self):
        """Generate transactions for savings-focused user"""
        transactions = []
        base_date = datetime.now() - timedelta(days=30)
        
        # Income
        transactions.extend([
            {'date': (base_date + timedelta(days=0)).strftime('%Y-%m-%d'), 'amount': 2200.00, 'type': 'income', 'description': 'Salary', 'category': 'Income'},
            {'date': (base_date + timedelta(days=0)).strftime('%Y-%m-%d'), 'amount': 200.00, 'type': 'income', 'description': 'Auto Savings', 'category': 'Savings'},
            {'date': (base_date + timedelta(days=0)).strftime('%Y-%m-%d'), 'amount': 300.00, 'type': 'income', 'description': 'Investment', 'category': 'Savings'}
        ])
        
        # Conservative expenses
        savings_expenses = [
            (65.00, 'Grocery Store', 'Groceries'),
            (30.00, 'Gas Station', 'Transportation'),
            (25.00, 'Home Cooking Supplies', 'Groceries'),
            (40.00, 'Monthly Subscription', 'Entertainment'),
            (15.00, 'Coffee at Home', 'Dining Out'),
            (35.00, 'Utility Bill', 'Bills'),
            (50.00, 'Phone Bill', 'Bills')
        ]
        
        for i, (amount, desc, category) in enumerate(savings_expenses):
            transactions.append({
                'date': (base_date + timedelta(days=4+i*5)).strftime('%Y-%m-%d'),
                'amount': amount,
                'type': 'expense',
                'description': desc,
                'category': category
            })
        
        return transactions
    
    def _clear_existing_demo_data(self):
        """Clear existing demo data for this user"""
        # Clear transactions
        execute_query("DELETE FROM transactions WHERE user_id = ?", (self.user_id,), commit=True)
        
        # Clear accounts (except those with plaid tokens)
        execute_query("DELETE FROM accounts WHERE user_id = ? AND plaid_token IS NULL", (self.user_id,), commit=True)
        
        # Reset budgets
        execute_query("UPDATE categories SET budget_amount = NULL WHERE user_id = ?", (self.user_id,), commit=True)
        
        # Clear commitments
        execute_query("DELETE FROM category_commitments WHERE user_id = ?", (self.user_id,), commit=True)
    
    def _cache_demo_data(self, scenario_type, data):
        """Cache demo data for later use"""
        for data_type, data_content in data.items():
            execute_query("""
                INSERT INTO demo_data_cache (user_id, data_type, scenario_type, json_data)
                VALUES (?, ?, ?, ?)
            """, (self.user_id, data_type, scenario_type, json.dumps(data_content)), commit=True)
    
    def _apply_demo_data(self, data):
        """Apply demo data to user's actual data"""
        # Create accounts
        for account in data.get('accounts', []):
            execute_query("""
                INSERT INTO accounts (user_id, bank_name, account_type, currency)
                VALUES (?, ?, ?, 'USD')
            """, (self.user_id, account['bank_name'], account['account_type']), commit=True)
        
        # Create categories and set budgets
        for budget in data.get('budgets', []):
            # Get or create category
            category = fetch_one(
                "SELECT category_id FROM categories WHERE user_id = ? AND category_name = ?",
                (self.user_id, budget['category_name'])
            )
            
            if not category:
                execute_query("""
                    INSERT INTO categories (user_id, category_name)
                    VALUES (?, ?)
                """, (self.user_id, budget['category_name']), commit=True)
                category = fetch_one("SELECT last_insert_rowid() as category_id")
            
            # Set budget
            execute_query("""
                UPDATE categories SET budget_amount = ? 
                WHERE category_id = ?
            """, (budget['budget_amount'], category['category_id']), commit=True)
        
        # Add transactions
        for txn in data.get('transactions', []):
            # Get category ID
            category = fetch_one(
                "SELECT category_id FROM categories WHERE user_id = ? AND category_name = ?",
                (self.user_id, txn['category'])
            )
            category_id = category['category_id'] if category else None
            
            # Get account ID
            account = fetch_one(
                "SELECT account_id FROM accounts WHERE user_id = ? LIMIT 1",
                (self.user_id,)
            )
            account_id = account['account_id'] if account else None
            
            if account_id:
                execute_query("""
                    INSERT INTO transactions (user_id, account_id, category_id, amount, 
                                            transaction_type, description, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (self.user_id, account_id, category_id, txn['amount'], 
                      txn['type'], txn['description'], txn['date']), commit=True)
        
        # Add commitments
        for commitment in data.get('commitments', []):
            category = fetch_one(
                "SELECT category_id FROM categories WHERE user_id = ? AND category_name = ?",
                (self.user_id, commitment['category_name'])
            )
            
            if category:
                execute_query("""
                    INSERT INTO category_commitments (user_id, category_id, amount, is_paid)
                    VALUES (?, ?, ?, ?)
                """, (self.user_id, category['category_id'], commitment['amount'], commitment['is_paid']), commit=True)

def reset_demo_data(user_id):
    """Reset demo data for a user"""
    demo_manager = DemoManager(user_id)
    return demo_manager.seed_demo_data('healthy')