"""
Enhanced AI service layer for PennyWise with circuit breaker and robust error handling
Penny - Your friendly financial AI companion
"""

import time
import requests
import json
import re
from datetime import datetime, timedelta
from core.config import Config
from core.logger import logger
from core.ai_insights_cache import AIInsightsCache

class PennyBrain:
    """Enhanced AI service with circuit breaker and robust error handling"""

    def __init__(self):
        self.failures = 0
        self.circuit_open = False
        self.circuit_opened_at = None
        self.max_failures = 3
        self.circuit_timeout = 300  # 5 minutes
        self.cache = None
        self.monitor = None

    def set_monitor(self, monitor):
        """Set the monitor instance (called after both are initialized)"""
        self.monitor = monitor
        logger.info("✅ AIMonitor connected to PennyBrain")

    def set_monitor(self, monitor):
        """Set the monitor instance (called after both are initialized)"""
        self.monitor = monitor

    def get_financial_tip(self, user_id, financial_context=None):
        """Get a financial tip with enhanced reliability"""
        start_time = time.time()
        cache_hit = False

        # Initialize cache if needed
        if self.cache is None:
            self.cache = AIInsightsCache(user_id)

        # Check circuit breaker
        if self.circuit_open:
            if self._should_try_recovery():
                logger.info("🔄 Attempting circuit recovery")
                self.circuit_open = False
                self.failures = 0
            else:
                logger.warning("⏸️  Circuit open - using cached response")
                return self._get_cached_fallback(user_id, financial_context)

        # Try to get cached insight first
        if financial_context:
            cached_insight, tone = self.cache.get_cached_insight(financial_context)
            if cached_insight:
                logger.info("💾 Using cached AI insight")
                cache_hit = True
                response_time = (time.time() - start_time) * 1000  # ms
                if self.monitor:
                    self.monitor.record_request(success=True, cache_hit=True, response_time=response_time)
                return cached_insight, tone

        try:
            # Make API call
            tip, tone = self._call_ai_api(user_id, financial_context)

            # Record successful request
            response_time = (time.time() - start_time) * 1000  # ms
            if self.monitor:
                self.monitor.record_request(success=True, cache_hit=False, response_time=response_time)

            # Reset failure count on success
            self.failures = 0
            self.circuit_open = False

            # Cache the successful response
            if financial_context and tip:
                self.cache.cache_insight(financial_context, tip, tone)

            logger.info(f"✅ Penny tip generated successfully for user {user_id}")
            return tip, tone

        except Exception as e:
            # Record failed request
            response_time = (time.time() - start_time) * 1000  # ms
            if self.monitor:
                self.monitor.record_request(success=False, cache_hit=False, response_time=response_time)

            self.failures += 1
            logger.error(f"❌ Penny API call failed ({self.failures}/{self.max_failures}): {e}")

            # Open circuit if too many failures
            if self.failures >= self.max_failures:
                self.circuit_open = True
                self.circuit_opened_at = datetime.now()
                logger.warning("🔴 Circuit breaker opened due to repeated failures")

            # Return fallback
            return self._get_fallback_tip(user_id), "friendly"

    def _call_ai_api(self, user_id, financial_context=None):
        """Make API call to AI service with enhanced error handling"""

        if Config.DEMO_MODE:
            return self._get_demo_tip(user_id), "friendly"

        # Prepare context-aware prompt
        prompt = self._build_contextual_prompt(financial_context)

        headers = {
            "Authorization": f"Bearer {Config.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 120,
            "temperature": 0.7,
            "top_p": 0.9
        }

        try:
            response = requests.post(
                Config.GROQ_API_URL,
                headers=headers,
                json=data,
                timeout=15
            )
            response.raise_for_status()

            result = response.json()

            if "choices" not in result or not result["choices"]:
                raise ValueError("No choices in API response")

            raw_tip = result["choices"][0]["message"]["content"].strip()

            # Parse and clean the response
            tip, tone = self._parse_ai_response(raw_tip)

            return tip, tone

        except requests.exceptions.Timeout:
            raise Exception("Penny API timeout - service unavailable")
        except requests.exceptions.ConnectionError:
            raise Exception("Penny API connection error - network issue")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise Exception("Penny API rate limit exceeded")
            elif e.response.status_code >= 500:
                raise Exception("Penny API server error")
            else:
                raise Exception(f"Penny API HTTP error: {e.response.status_code}")
        except json.JSONDecodeError:
            raise Exception("Penny API returned invalid JSON")
        except Exception as e:
            raise Exception(f"Penny API unexpected error: {str(e)}")

    def _build_contextual_prompt(self, financial_context):
        """Build context-aware prompt for better AI responses"""
        base_prompt = "Give me a helpful, practical money tip for this week."

        if not financial_context:
            return base_prompt

        # Add context to prompt
        context_parts = []

        if financial_context.get('budget_status', 0) > 0:
            context_parts.append("I'm currently over budget in some categories")

        if financial_context.get('top_categories'):
            top_cats = financial_context['top_categories'][:3]
            context_parts.append(f"My main spending is on {', '.join(top_cats)}")

        if context_parts:
            context_str = " Context: " + ". ".join(context_parts) + "."
            return base_prompt + context_str

        return base_prompt

    def _get_system_prompt(self):
        """Get the system prompt for Penny's personality"""
        return """You are Penny, a friendly and empathetic financial assistant for PennyWise. 
        Your name is Penny. You're warm, encouraging, and genuinely care about helping people with their finances.
        Give short, practical, and encouraging money tips (1-2 sentences max). 
        Be human-like, warm, and focus on actionable advice.
        Always speak in first person as Penny.
        Tone should be: friendly, encouraging, and practical.
        Always respond in a complete sentence. Never use markdown or lists."""

    def _parse_ai_response(self, raw_response):
        """Parse and clean AI response"""
        # Remove quotes and markdown if present
        cleaned = re.sub(r'["*]', '', raw_response).strip()

        # Ensure it sounds like Penny
        if not cleaned.startswith(('I ', 'Hey', 'As ', 'Let')):
            # Add Penny's voice if missing
            penny_intros = [
                "I suggest ",
                "As Penny, I think ",
                "From my experience, ",
                "I've noticed that "
            ]
            import random
            cleaned = random.choice(penny_intros) + cleaned.lower()

        # Detect tone from content
        tone = self._detect_tone(cleaned)

        # Ensure it's a complete sentence
        if not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'

        return cleaned, tone

    def _detect_tone(self, text):
        """Detect tone from text content"""
        text_lower = text.lower()

        positive_words = ['great', 'excellent', 'awesome', 'amazing', 'congratulations', 'well done', 'proud']
        encouraging_words = ['try', 'consider', 'suggest', 'recommend', 'helpful', 'boost', 'together']
        warning_words = ['careful', 'avoid', 'warning', 'caution', 'danger', 'watch out']

        if any(word in text_lower for word in positive_words):
            return "positive"
        elif any(word in text_lower for word in warning_words):
            return "warning"
        elif any(word in text_lower for word in encouraging_words):
            return "encouraging"
        else:
            return "friendly"

    def _should_try_recovery(self):
        """Check if we should try to recover from circuit open state"""
        if not self.circuit_opened_at:
            return True

        time_since_open = (datetime.now() - self.circuit_opened_at).total_seconds()
        return time_since_open >= self.circuit_timeout

    def _get_cached_fallback(self, user_id, financial_context):
        """Get fallback from cache when circuit is open"""
        if financial_context:
            cached, tone = self.cache.get_cached_insight(financial_context, max_age_hours=168)  # 1 week
            if cached:
                return cached, tone

        return self._get_fallback_tip(user_id), "friendly"

    def _get_fallback_tip(self, user_id):
        """Get a fallback tip when AI is unavailable"""
        penny_fallbacks = [
            "I suggest reviewing your weekly spending to spot saving opportunities!",
            "As Penny, I recommend setting up automatic transfers to savings on payday.",
            "From my experience, small daily savings habits lead to big financial wins!",
            "Let's review your subscriptions together - you might find some you don't need.",
            "I've found that cooking at home more often really helps save on food expenses."
        ]

        # Use user_id to deterministically select a fallback
        import hashlib
        tip_index = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16) % len(penny_fallbacks)
        return penny_fallbacks[tip_index]

    def _get_demo_tip(self, user_id):
        """Get demo tip for demo mode"""
        penny_demo_tips = [
            "I suggest setting a weekly spending limit to track expenses better!",
            "As Penny, I recommend reviewing subscriptions - you might find unused ones.",
            "Let's try rounding up purchases and saving the difference automatically!",
            "From my experience, setting aside small amounts daily builds a solid emergency fund.",
            "I recommend reviewing your budget weekly to stay on track with financial goals."
        ]
        import hashlib
        tip_index = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16) % len(penny_demo_tips)
        return penny_demo_tips[tip_index]

    def get_service_status(self):
        """Get current service status"""
        return {
            "circuit_open": self.circuit_open,
            "failure_count": self.failures,
            "max_failures": self.max_failures,
            "circuit_opened_at": self.circuit_opened_at,
            "in_demo_mode": Config.DEMO_MODE
        }

# Global instance
penny_brain = PennyBrain()