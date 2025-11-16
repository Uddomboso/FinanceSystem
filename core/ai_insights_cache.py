"""
AI insights caching system for PennyWise v2
"""

import hashlib
import json
from datetime import datetime, timedelta
from database.db_manager import execute_query, fetch_all, fetch_one
from core.config import Config
from core.logger import logger

class AIInsightsCache:
    """Cache AI insights to reduce API calls and improve performance"""
    
    def __init__(self, user_id):
        self.user_id = user_id
    
    def get_cached_insight(self, context_data, max_age_hours=24):
        """Get cached AI insight if available and fresh"""
        context_hash = self._generate_context_hash(context_data)
        
        cached = fetch_one("""
            SELECT insight_text, tone, created_at 
            FROM ai_insights 
            WHERE user_id = ? AND context_hash = ?
            ORDER BY created_at DESC LIMIT 1
        """, (self.user_id, context_hash))
        
        if cached:
            cache_age = datetime.now() - datetime.fromisoformat(cached['created_at'])
            if cache_age < timedelta(hours=max_age_hours):
                logger.info(f"Using cached AI insight for user {self.user_id}")
                return cached['insight_text'], cached['tone']
        
        return None, None
    
    def cache_insight(self, context_data, insight_text, tone='neutral'):
        """Cache a new AI insight"""
        context_hash = self._generate_context_hash(context_data)
        
        try:
            execute_query("""
                INSERT OR REPLACE INTO ai_insights 
                (user_id, insight_text, tone, context_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (self.user_id, insight_text, tone, context_hash, datetime.now()), commit=True)
            
            logger.info(f"Cached AI insight for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache AI insight: {e}")
            return False
    
    def _generate_context_hash(self, context_data):
        """Generate hash for context data to use as cache key"""
        if isinstance(context_data, dict):
            context_str = json.dumps(context_data, sort_keys=True)
        else:
            context_str = str(context_data)
        
        return hashlib.md5(context_str.encode()).hexdigest()
    
    def get_recent_insights(self, limit=5):
        """Get recent AI insights for this user"""
        return fetch_all("""
            SELECT insight_text, tone, created_at
            FROM ai_insights
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (self.user_id, limit))
    
    def clear_old_insights(self, days_old=30):
        """Clear insights older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
        
        execute_query("""
            DELETE FROM ai_insights 
            WHERE user_id = ? AND created_at < ?
        """, (self.user_id, cutoff_date), commit=True)
        
        logger.info(f"Cleared old AI insights for user {self.user_id}")

def get_cached_ai_tip(user_id, financial_context=None):
    """Get cached AI tip with financial context"""
    cache = AIInsightsCache(user_id)
    
    # Create context from financial data
    if financial_context is None:
        financial_context = _get_financial_context(user_id)
    
    # Try to get cached insight
    cached_insight, tone = cache.get_cached_insight(financial_context)
    
    if cached_insight:
        return cached_insight
    
    return None

def _get_financial_context(user_id):
    """Get financial context for cache key generation"""
    # Get recent spending summary
    recent_spending = fetch_all("""
        SELECT c.category_name, SUM(t.amount) as total
        FROM transactions t
        JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = ? AND t.transaction_type = 'expense'
        AND t.date >= date('now', '-30 days')
        GROUP BY c.category_name
        ORDER BY total DESC
        LIMIT 5
    """, (user_id,))
    
    # Get budget status
    budget_status = fetch_all("""
        SELECT category_name, budget_amount,
               COALESCE((SELECT SUM(amount) FROM transactions 
                        WHERE category_id = c.category_id 
                        AND transaction_type = 'expense'), 0) as spent
        FROM categories c
        WHERE user_id = ? AND budget_amount IS NOT NULL
    """, (user_id,))
    
    context = {
        'top_categories': [cat['category_name'] for cat in recent_spending],
        'budget_status': len([b for b in budget_status if b['spent'] > b['budget_amount']]),
        'total_categories': len(recent_spending)
    }
    
    return context