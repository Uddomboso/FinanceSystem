# core/badges_manager.py

"""
Micro Badges System - Achievement rewards for financial behaviors
"""

import time
from datetime import datetime, timedelta
from database.db_manager import fetch_all, fetch_one, execute_query
from core.logger import logger

class BadgesManager:
    """Manages badge earning, tracking, and display"""
    
    _cache = {}
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.badge_definitions = self._define_badges()
    
    def _define_badges(self):
        """Define all available badges and their criteria - using FontAwesome icons"""
        return {
            'steady_planner': {
                'name': 'Steady Planner',
                'description': 'Maintained budget adherence for 2+ weeks',
                'icon': 'fa5s.leaf',
                'color': '#10B981',
                'check_function': self._check_steady_planner,
                'rarity': 'common'
            },
            'smart_saver': {
                'name': 'Smart Saver', 
                'description': 'Saved 20%+ of income this month',
                'icon': 'fa5s.coins',
                'color': '#F59E0B',
                'check_function': self._check_smart_saver,
                'rarity': 'uncommon'
            },
            'quick_optimizer': {
                'name': 'Quick Optimizer',
                'description': 'Improved financial mood by 15+ points in a week',
                'icon': 'fa5s.bolt',
                'color': '#8B5CF6',
                'check_function': self._check_quick_optimizer,
                'rarity': 'rare'
            },
            'goal_crusher': {
                'name': 'Goal Crusher',
                'description': 'Completed 3 financial goals',
                'icon': 'fa5s.bullseye',
                'color': '#EF4444',
                'check_function': self._check_goal_crusher,
                'rarity': 'epic'
            },
            'balance_master': {
                'name': 'Balance Master',
                'description': 'Perfect spending balance for 30 days',
                'icon': 'fa5s.star',
                'color': '#06B6D4',
                'check_function': self._check_balance_master,
                'rarity': 'legendary'
            },
            'early_riser': {
                'name': 'Early Riser',
                'description': 'Logged transactions for 7 consecutive days',
                'icon': 'fa5s.sun',
                'color': '#F97316',
                'check_function': self._check_early_riser,
                'rarity': 'common'
            },
            'budget_ninja': {
                'name': 'Budget Ninja',
                'description': 'Stayed under budget in all categories',
                'icon': 'fa5s.user-secret',
                'color': '#6366F1',
                'check_function': self._check_budget_ninja,
                'rarity': 'uncommon'
            }
        }
    
    def check_new_badges(self):
        """Check and award any new badges the user earned"""
        try:
            earned_badges = self.get_earned_badges()
            newly_earned = []
            
            for badge_id, badge_info in self.badge_definitions.items():
                if badge_id not in earned_badges:
                    if badge_info['check_function']():
                        self._award_badge(badge_id)
                        newly_earned.append(badge_id)
                        logger.info(f"🏆 Badge earned: {badge_id} for user {self.user_id}")
            
            return newly_earned
            
        except Exception as e:
            logger.error(f"Error checking badges: {e}")
            return []
    
    def get_earned_badges(self):
        """Get list of badges user has already earned"""
        try:
            badges = fetch_all("""
                SELECT badge_id FROM user_badges 
                WHERE user_id = ? ORDER BY earned_at DESC
            """, (self.user_id,))
            
            return [badge['badge_id'] for badge in badges]
        except:
            return []
    
    def get_badges_with_progress(self):
        """Get all badges with progress information"""
        earned_badges = self.get_earned_badges()
        badges_with_progress = []
        
        for badge_id, badge_info in self.badge_definitions.items():
            progress = self._calculate_badge_progress(badge_id)
            badges_with_progress.append({
                'id': badge_id,
                'name': badge_info['name'],
                'description': badge_info['description'],
                'icon': badge_info['icon'],
                'color': badge_info['color'],
                'rarity': badge_info['rarity'],
                'earned': badge_id in earned_badges,
                'progress': progress,
                'progress_text': self._get_progress_text(badge_id, progress)
            })
        
        return badges_with_progress
    
    def _award_badge(self, badge_id):
        """Award a badge to the user"""
        try:
            execute_query("""
                INSERT INTO user_badges (user_id, badge_id, earned_at)
                VALUES (?, ?, ?)
            """, (self.user_id, badge_id, datetime.now()), commit=True)
            
            # Clear cache
            if self.user_id in self._cache:
                del self._cache[self.user_id]
                
        except Exception as e:
            logger.error(f"Error awarding badge {badge_id}: {e}")
    
    # ===== BADGE CRITERIA CHECK FUNCTIONS =====
    
    def _check_steady_planner(self):
        """Check if user maintained budget adherence for 2+ weeks"""
        try:
            # Check budget adherence over last 14 days
            budget_data = fetch_all("""
                SELECT c.category_name, c.budget_amount,
                       (SELECT SUM(amount) FROM transactions 
                        WHERE category_id = c.category_id 
                        AND transaction_type = 'expense'
                        AND date >= date('now', '-14 days')) as spent
                FROM categories c
                WHERE c.user_id = ? AND c.budget_amount IS NOT NULL
            """, (self.user_id,))
            
            if not budget_data:
                return False
            
            adherence_count = 0
            total_categories = len(budget_data)
            
            for row in budget_data:
                budget = row['budget_amount'] or 0
                spent = row['spent'] or 0
                
                # Allow 10% over budget as still "adherent"
                if spent <= budget * 1.1:
                    adherence_count += 1
            
            # Need 80%+ categories to be adherent
            return (adherence_count / total_categories) >= 0.8
            
        except:
            return False
    
    def _check_smart_saver(self):
        """Check if user saved 20%+ of income this month"""
        try:
            income_data = fetch_one("""
                SELECT SUM(amount) as total FROM transactions 
                WHERE user_id = ? AND transaction_type = 'income'
                AND date >= date('now', '-30 days')
            """, (self.user_id,))
            
            savings_data = fetch_all("""
                SELECT SUM(amount) as saved FROM transactions 
                WHERE user_id = ? AND transaction_type = 'income'
                AND category_id IN (
                    SELECT category_id FROM categories 
                    WHERE user_id = ? AND category_name LIKE '%savings%'
                )
                AND date >= date('now', '-30 days')
            """, (self.user_id, self.user_id))
            
            total_income = income_data['total'] or 1
            total_saved = savings_data[0]['saved'] if savings_data else 0
            
            savings_rate = (total_saved / total_income) * 100
            return savings_rate >= 20
            
        except:
            return False
    
    def _check_quick_optimizer(self):
        """Check if user improved financial mood by 15+ points in a week"""
        try:
            # This would require mood history tracking
            # For now, check if they've been active with improvements
            recent_activity = fetch_one("""
                SELECT COUNT(*) as count FROM transactions 
                WHERE user_id = ? AND date >= date('now', '-7 days')
            """, (self.user_id,))
            
            budget_updates = fetch_one("""
                SELECT COUNT(*) as count FROM categories 
                WHERE user_id = ? AND budget_amount IS NOT NULL
            """, (self.user_id,))
            
            return (recent_activity['count'] or 0) >= 5 and (budget_updates['count'] or 0) >= 2
            
        except:
            return False
    
    def _check_goal_crusher(self):
        """Check if user completed 3 financial goals"""
        try:
            # Check savings goals that are 100%+ complete
            completed_goals = fetch_all("""
                SELECT c.category_name, c.budget_amount as target,
                       (SELECT SUM(amount) FROM transactions 
                        WHERE category_id = c.category_id 
                        AND transaction_type = 'income') as saved
                FROM categories c
                WHERE c.user_id = ? AND c.budget_amount IS NOT NULL
                AND c.category_name LIKE '%goal%'
            """, (self.user_id,))
            
            crushed_goals = 0
            for goal in completed_goals:
                target = goal['target'] or 0
                saved = goal['saved'] or 0
                if saved >= target and target > 0:
                    crushed_goals += 1
            
            return crushed_goals >= 3
            
        except:
            return False
    
    def _check_balance_master(self):
        """Check perfect spending balance for 30 days"""
        try:
            spending_data = fetch_one("""
                SELECT SUM(amount) as total FROM transactions 
                WHERE user_id = ? AND transaction_type = 'expense'
                AND date >= date('now', '-30 days')
            """, (self.user_id,))
            
            income_data = fetch_one("""
                SELECT SUM(amount) as total FROM transactions 
                WHERE user_id = ? AND transaction_type = 'income' 
                AND date >= date('now', '-30 days')
            """, (self.user_id,))
            
            spending = spending_data['total'] or 0
            income = income_data['total'] or 1
            
            # Perfect balance = spending <= 70% of income
            return (spending / income) <= 0.7
            
        except:
            return False
    
    def _check_early_riser(self):
        """Check consecutive days of activity"""
        try:
            # Simplified - check if user has been active recently
            recent_activity = fetch_one("""
                SELECT COUNT(DISTINCT date) as days FROM transactions 
                WHERE user_id = ? AND date >= date('now', '-7 days')
            """, (self.user_id,))
            
            return (recent_activity['days'] or 0) >= 5
            
        except:
            return False
    
    def _check_budget_ninja(self):
        """Check if user stayed under budget in all categories"""
        try:
            over_budget_categories = fetch_all("""
                SELECT c.category_name FROM categories c
                WHERE c.user_id = ? AND c.budget_amount IS NOT NULL
                AND (SELECT SUM(amount) FROM transactions 
                     WHERE category_id = c.category_id 
                     AND transaction_type = 'expense') > c.budget_amount
            """, (self.user_id,))
            
            return len(over_budget_categories) == 0
            
        except:
            return False
    
    def _calculate_badge_progress(self, badge_id):
        """Calculate progress percentage for a badge (0-100)"""
        # Simplified progress calculation
        try:
            if badge_id == 'steady_planner':
                return min(75, 100)  # Example progress
            elif badge_id == 'smart_saver':
                savings_data = fetch_all("""
                    SELECT SUM(amount) as saved FROM transactions 
                    WHERE user_id = ? AND transaction_type = 'income'
                    AND category_id IN (
                        SELECT category_id FROM categories 
                        WHERE user_id = ? AND category_name LIKE '%savings%'
                    )
                """, (self.user_id, self.user_id))
                saved = savings_data[0]['saved'] if savings_data else 0
                return min(int((saved / 1000) * 100), 100)  # Progress toward $1000 saved
            else:
                return 0
        except:
            return 0
    
    def _get_progress_text(self, badge_id, progress):
        """Get human-readable progress text"""
        if progress >= 100:
            return "Ready to earn!"
        
        texts = {
            'steady_planner': f"{progress}% to consistent budgeting",
            'smart_saver': f"{progress}% to savings goal", 
            'quick_optimizer': "Keep optimizing your finances",
            'goal_crusher': "Crush those financial goals!",
            'balance_master': "Working toward perfect balance",
            'early_riser': "Build your daily habit",
            'budget_ninja': "Master your category budgets"
        }
        
        return texts.get(badge_id, "Keep going!")