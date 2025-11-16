from database.db_manager import fetch_all, execute_query

class SavingsGoalTracker:
    def __init__(self, user_id):
        self.user_id = user_id
    
    def update_savings_progress(self):
        """Use 'Savings' categories as goals"""
        savings_cats = fetch_all("""
            SELECT c.category_id, c.category_name, c.budget_amount as target,
                   COALESCE((
                       SELECT SUM(t.amount) 
                       FROM transactions t 
                       WHERE t.category_id = c.category_id 
                         AND t.transaction_type = 'income'
                   ), 0) as saved
            FROM categories c
            WHERE c.user_id = ? AND c.category_name LIKE '%savings%'
        """, (self.user_id,))
        
        updates = 0
        for goal in savings_cats:
            if goal["target"] and goal["saved"] >= goal["target"]:
                self._notify_goal_completed(goal["category_name"])
                updates += 1
        return updates
    
    def _notify_goal_completed(self, goal_name):
        execute_query("""
            INSERT INTO notifications (user_id, content, notification_type)
            VALUES (?, ?, 'savings')
        """, (self.user_id, f"🎉 Savings goal '{goal_name}' completed!"), commit=True)

def track_savings_goals(user_id):
    tracker = SavingsGoalTracker(user_id)
    return tracker.update_savings_progress()
