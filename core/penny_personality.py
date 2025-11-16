# core/penny_personality.py

"""
Enhanced Penny Personality Engine - Makes Penny feel like a real financial companion
"""

import random
from datetime import datetime, time
from core.logger import logger

class PennyPersonality:
    """Enhanced personality system for Penny with emotional intelligence"""
    
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.personality_traits = {
            'empathy_level': random.uniform(0.7, 0.9),  # How caring Penny is
            'enthusiasm_level': random.uniform(0.6, 0.8),  # How excited Penny gets
            'professionalism_level': random.uniform(0.8, 1.0),  # How serious Penny is
            'humor_level': random.uniform(0.4, 0.7),  # How funny Penny is
        }
        self.conversation_history = []
        self.last_interaction_time = None
        self.user_mood_history = []
        
    def get_contextual_response(self, context_type, data=None):
        """Get a personalized response based on context and personality"""
        base_responses = self._get_base_responses(context_type, data)
        personalized_responses = self._personalize_responses(base_responses)
        
        # Add to conversation history
        response = random.choice(personalized_responses)
        self._record_interaction(context_type, response)
        
        return response, self._determine_tone(response)
    
    def _get_base_responses(self, context_type, data):
        """Get base responses for different contexts"""
        responses = {
            'welcome': [
                "Hello {name}! 🌟 I've been looking forward to helping you with your finances today!",
                "Hey {name}! 💫 Ready to make some smart money moves together?",
                "Good to see you, {name}! 🦉 Your financial wellness is my top priority!",
                "Welcome back, {name}! ✨ I've got some fresh insights waiting for you!"
            ],
            'mood_excellent': [
                "WOW! 🎉 Your financial health is absolutely stellar, {name}! You're crushing it!",
                "Incredible work, {name}! 💎 Your financial habits are truly inspiring!",
                "You're a financial rockstar, {name}! 🌟 Keep up this amazing energy!",
                "Absolutely phenomenal, {name}! 🚀 Your money management is textbook perfect!"
            ],
            'mood_good': [
                "Great progress, {name}! 📈 Your financial habits are really paying off!",
                "You're doing wonderfully, {name}! 💪 I can see your hard work showing results!",
                "Nice work, {name}! 🌿 Your consistent efforts are building a solid foundation!",
                "You're on the right track, {name}! 🎯 Your financial discipline is impressive!"
            ],
            'mood_neutral': [
                "Steady as she goes, {name}! ⚓ Let's find some opportunities to optimize together.",
                "You're building good momentum, {name}! 💭 A few tweaks could really boost your progress!",
                "Solid foundation, {name}! 🏗️ Ready to take things to the next level?",
                "You're in a good place, {name}! 🌱 Let's nurture your financial growth together!"
            ],
            'mood_concerned': [
                "I notice we have some opportunities here, {name}. 🤔 Want to review your spending patterns together?",
                "Let's work through this together, {name}. 💡 I have some ideas to help optimize your finances.",
                "Every financial journey has learning moments, {name}. 🎪 Ready to plan your next move?",
                "I see some areas we can improve, {name}. 🛠️ Let's build a stronger financial strategy!"
            ],
            'mood_needs_attention': [
                "I'm here to help you get back on track, {name}. 🤝 We can turn this around together!",
                "Let's start fresh, {name}! 🌅 Every day is a new opportunity for financial wellness.",
                "We'll work through this step by step, {name}. 🗺️ I've got your back!",
                "Financial journeys have ups and downs, {name}. 🎢 Let's navigate this together!"
            ],
            'badge_earned': [
                "CONGRATULATIONS, {name}! 🏆 You earned {badge_name}! Your financial skills are growing!",
                "AMAZING, {name}! ✨ {badge_name} is yours! You're becoming a money master!",
                "WOOHOO! 🎉 {badge_name} unlocked! You're rocking it, {name}!",
                "INCREDIBLE! 💫 You've earned {badge_name}! Your progress is inspiring, {name}!"
            ],
            'goal_completed': [
                "MISSION ACCOMPLISHED, {name}! 🎯 You crushed your financial goal!",
                "SUCCESS! 🌟 You've reached your target, {name}! So proud of your dedication!",
                "GOAL ACHIEVED! 🚀 You did it, {name}! Your persistence paid off beautifully!",
                "TARGET REACHED! 💎 Amazing work, {name}! You're building an incredible future!"
            ],
            'morning_greeting': [
                "Good morning, {name}! 🌞 Ready to conquer your financial day?",
                "Rise and shine, {name}! ☀️ Let's make today financially amazing!",
                "Morning, {name}! 🌄 Perfect time to check in on your money goals!",
                "Hello, early bird {name}! 🐦 Ready to soar financially today?"
            ],
            'evening_greeting': [
                "Good evening, {name}! 🌙 Great time to review your daily financial wins!",
                "Evening, {name}! 🌆 How did your financial day go?",
                "Hello, {name}! 🌃 Perfect moment to plan tomorrow's money moves!",
                "Good evening, {name}! 💫 Let's reflect on today's financial progress!"
            ],
            'weekend_motivation': [
                "Happy weekend, {name}! 🎉 Perfect time for some financial self-care!",
                "Weekend vibes, {name}! 🌈 Let's make your money work while you relax!",
                "Hello, {name}! 🏖️ Weekend = perfect time for quick financial check-ins!",
                "Weekend mode, {name}! 🎊 Let's keep the financial momentum going!"
            ],
            'financial_tip': [
                "Here's a penny for your thoughts, {name}! 💭 {tip}",
                "Quick financial insight, {name}! 💡 {tip}",
                "Thought you'd appreciate this, {name}! 🌟 {tip}",
                "Smart money move idea, {name}! 🎯 {tip}"
            ],
            'encouragement': [
                "You've got this, {name}! 💪 Every small step counts in your financial journey!",
                "I believe in you, {name}! 🌟 Your financial future is worth the effort!",
                "Keep going, {name}! 🚀 Your consistency is building something amazing!",
                "You're capable of amazing things, {name}! 💫 Your financial discipline inspires me!"
            ]
        }
        
        # Get base responses for context
        base = responses.get(context_type, ["I'm here to help, {name}! 💫"])
        
        # Replace placeholders with actual data
        formatted_responses = []
        for response in base:
            formatted = response.format(
                name=self.username,
                badge_name=data.get('badge_name', 'this achievement') if data else 'this achievement',
                tip=data.get('tip', 'Consider reviewing your budget this week!') if data else 'Consider reviewing your budget this week!'
            )
            formatted_responses.append(formatted)
            
        return formatted_responses
    
    def _personalize_responses(self, responses):
        """Personalize responses based on Penny's personality traits"""
        personalized = []
        
        for response in responses:
            # Adjust enthusiasm based on personality
            if self.personality_traits['enthusiasm_level'] > 0.8:
                response = self._add_enthusiasm(response)
            
            # Add humor occasionally
            if self.personality_traits['humor_level'] > 0.6 and random.random() > 0.7:
                response = self._add_humor(response)
                
            # Adjust professionalism
            if self.personality_traits['professionalism_level'] > 0.9:
                response = self._make_more_professional(response)
                
            personalized.append(response)
            
        return personalized
    
    def _add_enthusiasm(self, text):
        """Add enthusiastic elements to text"""
        enthusiasm_boosters = [" Absolutely amazing!", " So exciting!", " Incredible progress!", " Wonderful news!"]
        if random.random() > 0.5:
            text += random.choice(enthusiasm_boosters)
        return text
    
    def _add_humor(self, text):
        """Add humorous elements to text"""
        jokes = [
            " (And no, that's not just the coffee talking! ☕)",
            " (Penny approved! 🦉)",
            " (Cha-ching! 💰)",
            " (Your wallet thanks you! 👛)"
        ]
        if random.random() > 0.7:
            text += random.choice(jokes)
        return text
    
    def _make_more_professional(self, text):
        """Make text more professional"""
        # Replace casual phrases with more professional ones
        replacements = {
            "crushing it": "demonstrating exceptional performance",
            "rocking it": "achieving outstanding results", 
            "woohoo": "excellent",
            "amazing": "commendable"
        }
        
        for casual, professional in replacements.items():
            if casual in text.lower():
                text = text.replace(casual, professional)
                
        return text
    
    def _determine_tone(self, response):
        """Determine the emotional tone of a response"""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ['wow', 'incredible', 'phenomenal', 'crushing', 'rockstar']):
            return "excited"
        elif any(word in response_lower for word in ['congratulations', 'amazing', 'success', 'achieved']):
            return "celebratory"
        elif any(word in response_lower for word in ['sorry', 'concerned', 'careful', 'attention']):
            return "caring"
        elif any(word in response_lower for word in ['steady', 'solid', 'foundation', 'momentum']):
            return "calm"
        elif any(word in response_lower for word in ['together', 'help', 'support', 'guide']):
            return "supportive"
        else:
            return "friendly"
    
    def _record_interaction(self, context_type, response):
        """Record interaction for personality learning"""
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'context': context_type,
            'response': response,
            'tone': self._determine_tone(response)
        })
        
        # Keep only last 50 interactions
        if len(self.conversation_history) > 50:
            self.conversation_history.pop(0)
            
        self.last_interaction_time = datetime.now()
    
    def get_time_based_greeting(self):
        """Get greeting based on time of day"""
        current_time = datetime.now().time()
        
        if time(5, 0) <= current_time < time(12, 0):
            context = 'morning_greeting'
        elif time(18, 0) <= current_time:
            context = 'evening_greeting'
        elif datetime.now().weekday() >= 5:  # Weekend
            context = 'weekend_motivation'
        else:
            context = 'welcome'
            
        return self.get_contextual_response(context)
    
    def record_user_mood(self, mood_data):
        """Record user mood for personalized responses"""
        self.user_mood_history.append({
            'timestamp': datetime.now(),
            'mood_level': mood_data.get('mood_level', 'neutral'),
            'score': mood_data.get('score', 50)
        })
        
        # Keep only last 30 mood entries
        if len(self.user_mood_history) > 30:
            self.user_mood_history.pop(0)
    
    def get_mood_trend(self):
        """Get trend of user's financial mood"""
        if len(self.user_mood_history) < 2:
            return "stable"
        
        recent_scores = [entry['score'] for entry in self.user_mood_history[-5:]]
        if len(recent_scores) < 2:
            return "stable"
            
        trend = recent_scores[-1] - recent_scores[0]
        
        if trend > 10:
            return "improving"
        elif trend < -10:
            return "declining"
        else:
            return "stable"