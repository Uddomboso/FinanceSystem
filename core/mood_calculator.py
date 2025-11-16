"""
Financial Mood Calculator - analyzes user data and returns mood score + message
"""

import time
from datetime import datetime
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

            mood_data = {
                'score': total_score,
                'factors': factors,
                'mood_level': self._score_to_mood_level(total_score),
                'message': self._get_mood_message(total_score)
            }

            self._cache[self.user_id] = (time.time(), mood_data)
            logger.info(f"🎭 mood calculated for user {self.user_id}: {mood_data['mood_level']}")
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
        import random
        messages = {
            "excellent": ["🎉 your finances are thriving! keep it up!"],
            "good": ["💪 solid progress — your habits are paying off!"],
            "neutral": ["💭 steady, but small tweaks could help!"],
            "concerned": ["🤔 let's review your spending this week."],
            "needs_attention": ["🆗 time to rebalance — penny can help!"]
        }
        return random.choice(messages[mood])

    def _get_default_mood(self):
        return {'score': 50, 'factors': {}, 'mood_level': 'neutral',
                'message': "💭 let's get started with your financial journey!"}
