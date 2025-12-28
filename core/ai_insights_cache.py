"""
AI insights caching system for PennyWise v2
"""

import hashlib
import json
import time
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
    # Get total spending for threshold calculation
    total_spending_row = fetch_one("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ? AND transaction_type = 'expense'
        AND date >= date('now', '-30 days')
    """, (user_id,))
    total_spending = total_spending_row['total'] or 0
    
    # Get recent spending summary with amounts
    recent_spending = fetch_all("""
        SELECT c.category_name, SUM(t.amount) as total
        FROM transactions t
        JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = ? AND t.transaction_type = 'expense'
        AND t.date >= date('now', '-30 days')
        GROUP BY c.category_name
        ORDER BY total DESC
    """, (user_id,))
    
    # Filter out micro-expenses: must be > 5% of total OR amount > 2
    MIN_AMOUNT = 2.0
    MIN_PERCENT = 0.05  # 5%
    min_threshold = max(MIN_AMOUNT, total_spending * MIN_PERCENT) if total_spending > 0 else MIN_AMOUNT
    
    significant_categories = [
        cat for cat in recent_spending 
        if cat['total'] and cat['total'] >= min_threshold
    ]
    
    # Limit to top 5 significant categories
    top_categories = [cat['category_name'] for cat in significant_categories[:5]]
    
    # Get unpaid commitments (priority items - always included)
    unpaid_commitments = fetch_all("""
        SELECT c.category_name, cc.amount
        FROM category_commitments cc
        JOIN categories c ON cc.category_id = c.category_id
        WHERE cc.user_id = ? AND COALESCE(cc.is_paid, 0) = 0
        ORDER BY cc.amount DESC
    """, (user_id,))
    
    commitment_categories = [c['category_name'] for c in unpaid_commitments]
    
    # Get budget status
    budget_status = fetch_all("""
        SELECT category_name, budget_amount,
               COALESCE((SELECT SUM(amount) FROM transactions 
                        WHERE category_id = c.category_id 
                        AND transaction_type = 'expense'), 0) as spent
        FROM categories c
        WHERE user_id = ? AND budget_amount IS NOT NULL
    """, (user_id,))
    
    # Build prioritized category list: commitments first, then significant spending
    # Remove duplicates (commitments might also appear in spending)
    all_categories = []
    seen = set()
    for cat in commitment_categories:
        if cat not in seen:
            all_categories.append(cat)
            seen.add(cat)
    for cat in top_categories:
        if cat not in seen:
            all_categories.append(cat)
            seen.add(cat)
    
    context = {
        'user_id': user_id,
        'top_categories': all_categories[:5],  # Limit to 5 total
        'commitment_categories': commitment_categories,
        'budget_status': len([b for b in budget_status if b['spent'] > b['budget_amount']]),
        'total_categories': len(significant_categories),
        'unpaid_commitment_count': len(unpaid_commitments)
    }
    
    # #region agent log
    try:
        with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"A","location":"ai_insights_cache.py:_get_financial_context","message":"Category filtering and prioritization","data":{"total_spending":total_spending,"min_threshold":min_threshold,"significant_count":len(significant_categories),"commitment_count":len(commitment_categories),"final_categories":all_categories[:5],"commitment_categories":commitment_categories},"timestamp":int(time.time()*1000)}) + '\n')
    except: pass
    # #endregion
    
    return context