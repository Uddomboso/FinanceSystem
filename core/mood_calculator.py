"""
Financial Mood Calculator - analyzes user data and returns mood score + message
"""

import time
import json
from datetime import datetime, date
from database.db_manager import fetch_all, fetch_one
from core.logger import logger

class MoodCalculator:
    """calculates financial mood based on user spending, savings, and habits"""
    
    _cache = {}  # {user_id: (timestamp, mood_data)}

    def __init__(self, user_id):
        self.user_id = user_id

    def calculate_overall_mood(self):
        """return cached result if recent else compute new"""
        try:
            cached = self._cache.get(self.user_id)
            if cached and time.time() - cached[0] < 60:
                return cached[1]

            # Check for danger signals FIRST - these override all positive factors
            overdue_count = self._count_overdue_commitments()
            unpaid_count = self._count_unpaid_commitments()
            
            # Force mood based on danger signals
            if overdue_count > 0:
                # Any overdue commitment → needs_attention
                mood_level = 'needs_attention'
                mood_score = 20  # Low score for needs_attention
                factors = {
                    'spending_health': 50,
                    'savings_progress': 50,
                    'budget_adherence': 50,
                    'goal_momentum': 50,
                    'overdue_commitments': overdue_count,
                    'unpaid_commitments': unpaid_count
                }
            elif unpaid_count >= 2:
                # Unpaid commitments >= 2 → concerned
                mood_level = 'concerned'
                mood_score = 35  # Low score for concerned
                factors = {
                    'spending_health': 50,
                    'savings_progress': 50,
                    'budget_adherence': 50,
                    'goal_momentum': 50,
                    'overdue_commitments': overdue_count,
                    'unpaid_commitments': unpaid_count
                }
            else:
                # No danger signals - calculate normal factors
                factors = {
                    'spending_health': self._calculate_spending_health(),
                    'savings_progress': self._calculate_savings_progress(),
                    'budget_adherence': self._calculate_budget_adherence(),
                    'goal_momentum': self._calculate_goal_momentum()
                }
                
                total_score = (
                    factors['spending_health'] * 0.35 +
                    factors['savings_progress'] * 0.30 +
                    factors['budget_adherence'] * 0.25 +
                    factors['goal_momentum'] * 0.10
                )
                mood_score = total_score
                mood_level = self._score_to_mood_level(total_score)
            
            # Calculate spending ratio for debug log
            try:
                recent_income = fetch_one("""
                    SELECT SUM(amount) as total FROM transactions 
                    WHERE user_id=? AND transaction_type='income' 
                    AND date >= date('now', '-30 days')
                """, (self.user_id,))
                recent_spending = fetch_one("""
                    SELECT SUM(amount) as total FROM transactions 
                    WHERE user_id=? AND transaction_type='expense' 
                    AND date >= date('now', '-30 days')
                """, (self.user_id,))
                income = (recent_income['total'] or 0) or 1
                spending = recent_spending['total'] or 0
                spend_ratio = spending / income
            except:
                spend_ratio = 0.0
            
            # #region agent log
            try:
                with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"A","location":"mood_calculator.py:calculate_overall_mood","message":"Mood calculation with commitment checks","data":{"unpaid_count":unpaid_count,"overdue_count":overdue_count,"spend_ratio":round(spend_ratio,2),"final_mood":mood_level,"mood_score":mood_score},"timestamp":int(time.time()*1000)}) + '\n')
            except: pass
            # #endregion

            mood_data = {
                'score': mood_score,
                'factors': factors,
                'mood_level': mood_level,
                'message': self._get_mood_message_by_level(mood_level)
            }

            self._cache[self.user_id] = (time.time(), mood_data)
            logger.info(f"🎭 mood calculated for user {self.user_id}: {mood_data['mood_level']} (unpaid: {unpaid_count}, overdue: {overdue_count})")
            return mood_data

        except Exception as e:
            logger.error(f"error calculating mood: {e}")
            return self._get_default_mood()

    def _calculate_spending_health(self):
        try:
            recent_income = fetch_one("""
                SELECT SUM(amount) as total FROM transactions 
                WHERE user_id=? AND transaction_type='income' 
                AND date >= date('now', '-30 days')
            """, (self.user_id,))
            recent_spending = fetch_one("""
                SELECT SUM(amount) as total FROM transactions 
                WHERE user_id=? AND transaction_type='expense' 
                AND date >= date('now', '-30 days')
            """, (self.user_id,))
            income = (recent_income['total'] or 0) or 1
            spending = recent_spending['total'] or 0
            ratio = spending / income
            if ratio <= 0.5: return 90
            elif ratio <= 0.7: return 85
            elif ratio <= 0.9: return 60
            else: return 30
        except: return 50

    def _calculate_savings_progress(self):
        try:
            rows = fetch_all("""
                SELECT c.budget_amount as target,
                       (SELECT SUM(amount) FROM transactions 
                        WHERE category_id=c.category_id 
                        AND transaction_type='income') as saved
                FROM categories c
                WHERE c.user_id=? AND c.category_name LIKE '%savings%'
            """, (self.user_id,))
            if not rows: return 40
            total_saved = sum((r['saved'] or 0) for r in rows)
            total_target = sum((r['target'] or 0) for r in rows)
            if total_target == 0: return 50
            ratio = total_saved / total_target
            if ratio >= 1: return 95
            elif ratio >= 0.8: return 85
            elif ratio >= 0.5: return 70
            elif ratio >= 0.2: return 55
            else: return 40
        except: return 50

    def _calculate_budget_adherence(self):
        try:
            rows = fetch_all("""
                SELECT c.budget_amount as budget,
                       (SELECT SUM(amount) FROM transactions 
                        WHERE category_id=c.category_id 
                        AND transaction_type='expense') as spent
                FROM categories c
                WHERE c.user_id=? AND c.budget_amount IS NOT NULL
            """, (self.user_id,))
            if not rows: return 50
            scores = []
            for r in rows:
                budget = (r['budget'] or 1)
                spent = (r['spent'] or 0)
                if spent <= budget * 0.8: scores.append(90)
                elif spent <= budget: scores.append(80)
                elif spent <= budget * 1.2: scores.append(50)
                else: scores.append(20)
            return sum(scores) / len(scores)
        except: return 50

    def _calculate_goal_momentum(self):
        try:
            res = fetch_one("""
                SELECT COUNT(*) as count FROM transactions 
                WHERE user_id=? AND date >= date('now', '-7 days')
            """, (self.user_id,))
            count = res['count'] or 0
            if count >= 10: return 80
            elif count >= 5: return 70
            elif count >= 2: return 60
            else: return 50
        except: return 50

    def _score_to_mood_level(self, score):
        if score >= 85: return "excellent"
        elif score >= 70: return "good"
        elif score >= 55: return "neutral"
        elif score >= 40: return "concerned"
        else: return "needs_attention"

    def _get_mood_message(self, score):
        mood = self._score_to_mood_level(score)
        return self._get_mood_message_by_level(mood)
    
    def _get_mood_message_by_level(self, mood_level):
        """Get mood message by mood level (used when mood is forced by commitments)"""
        import random
        messages = {
            "excellent": ["🎉 your finances are thriving! keep it up!"],
            "good": ["💪 solid progress — your habits are paying off!"],
            "neutral": ["💭 steady, but small tweaks could help!"],
            "concerned": ["🤔 let's review your spending this week."],
            "needs_attention": ["🆗 time to rebalance — penny can help!"]
        }
        return random.choice(messages.get(mood_level, messages["neutral"]))

    def _count_unpaid_commitments(self):
        """Count unpaid commitments"""
        try:
            result = fetch_one("""
                SELECT COUNT(*) as count
                FROM category_commitments
                WHERE user_id = ? AND COALESCE(is_paid, 0) = 0
            """, (self.user_id,))
            return result['count'] or 0
        except Exception as e:
            logger.error(f"error counting unpaid commitments: {e}")
            return 0

    def _count_overdue_commitments(self):
        """Count overdue commitments based on due_day"""
        try:
            today = date.today()
            commitments = fetch_all("""
                SELECT due_day
                FROM category_commitments
                WHERE user_id = ? AND COALESCE(is_paid, 0) = 0
            """, (self.user_id,))
            
            overdue_count = 0
            for commitment in commitments:
                due_day = commitment.get('due_day', 1)
                if not due_day or due_day < 1 or due_day > 31:
                    continue
                
                # Calculate most recent due date (same logic as notification_manager)
                current_month = today.month
                current_year = today.year
                
                # If today's day is past the due day, the commitment was due this month
                if today.day > due_day:
                    due_month = current_month
                    due_year = current_year
                else:
                    # Due last month
                    if current_month == 1:
                        due_month = 12
                        due_year = current_year - 1
                    else:
                        due_month = current_month - 1
                        due_year = current_year
                
                # Create due date (handle months with fewer days)
                try:
                    import calendar
                    last_day = calendar.monthrange(due_year, due_month)[1]
                    due_date = date(due_year, due_month, min(due_day, last_day))
                except ValueError:
                    continue
                
                # Check if overdue
                if due_date < today:
                    overdue_count += 1
            
            return overdue_count
        except Exception as e:
            logger.error(f"error counting overdue commitments: {e}")
            return 0

    def _get_default_mood(self):
        return {'score': 50, 'factors': {}, 'mood_level': 'neutral',
                'message': "💭 let's get started with your financial journey!"}
