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

    def get_financial_tip(self, user_id, financial_context=None):
        """Get a financial tip with enhanced reliability.

        Returns (tip_text, tone, payload_dict|None)
        """
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
                return cached_insight, tone, None

        try:
            # Make API call
            tip, tone, payload = self._call_ai_api(user_id, financial_context)

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
            return tip, tone, payload

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
            return self._get_fallback_tip(user_id), "friendly", None

    def _call_ai_api(self, user_id, financial_context=None):
        """Make API call to AI service with enhanced error handling"""

        if Config.DEMO_MODE:
            tip = self._get_demo_tip(user_id)
            return tip, "friendly", None

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
            tip, tone, payload = self._parse_ai_response(raw_tip)

            return tip, tone, payload

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

    def _parse_ai_response(self, raw_response):
        """Parse and clean AI response"""
        cleaned = raw_response.strip()

        payload = None
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            # Remove code fences or stray characters, then retry once
            cleaned_no_fences = re.sub(r"```(?:json)?|```", "", cleaned, flags=re.IGNORECASE).strip()
            try:
                payload = json.loads(cleaned_no_fences)
            except json.JSONDecodeError:
                payload = None

        if isinstance(payload, dict):
            coaching = payload.get('coaching', '').strip()
            action = payload.get('action_step', '').strip()
            challenge = payload.get('challenge_name', 'Daily Mission').strip()
            tip_text = f"{challenge}: {coaching}\nAction: {action}".strip()
            tone = payload.get('tone_hint') or self._detect_tone(tip_text)
            return tip_text, tone, payload

        # Fallback to legacy parsing
        cleaned = re.sub(r'["*]', '', cleaned).strip()
        if not cleaned.startswith(('I ', 'Hey', 'As ', 'Let')):
            penny_intros = [
                "I suggest ",
                "As Penny, I think ",
                "From my experience, ",
                "I've noticed that "
            ]
            import random
            cleaned = random.choice(penny_intros) + cleaned.lower()

        tone = self._detect_tone(cleaned)
        if not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'

        return cleaned, tone, None

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

    def generate_emotion_phrase(self, mood_label: str, context: dict, advice_mode: str = "standard") -> str:
        """Generate one short emotional framing sentence (no advice, max 12 words, lowercase).
        
        Args:
            mood_label: The mood level (excellent, good, neutral, concerned, needs_attention)
            context: Brief context summary dict
            
        Returns:
            Single lowercase sentence with emotional framing, no advice or numbers
        """
        # Hardcoded fallback phrases per mood
        fallback_phrases = {
            "excellent": "oh wow, you're really nailing this lately.",
            "good": "this is looking pretty solid right now.",
            "neutral": "things are steady, which is fine.",
            "concerned": "this is getting a bit tight, but it's manageable.",
            "needs_attention": "okay, we need to pay attention here."
        }
        
        # Check circuit breaker
        if self.circuit_open and not self._should_try_recovery():
            logger.warning("⏸️  Circuit open - using fallback emotion phrase")
            return fallback_phrases.get(mood_label, fallback_phrases["neutral"])
        
        if Config.DEMO_MODE:
            return fallback_phrases.get(mood_label, fallback_phrases["neutral"])
        
        try:
            # Build context summary for prompt
            context_summary = self._build_context_summary(context)
            
            mode_instruction = ""
            if advice_mode == "strict":
                mode_instruction = "Use direct acknowledgment, no softening."
            elif advice_mode == "supportive":
                mode_instruction = "Use gentle, reassuring tone. Acknowledge effort."
            elif advice_mode == "cautionary":
                mode_instruction = "Use balanced tone - acknowledge good state but note vigilance."
            
            prompt = f"""Generate ONE short emotional framing sentence (max 12 words, lowercase) for someone whose financial mood is: {mood_label}

Context: {context_summary}
{mode_instruction}

CRITICAL RULES:
- Output ONLY one sentence
- Lowercase only
- No advice, numbers, or solutions
- No explanations
- Casual, human tone (adjust based on mode instruction)
- Pure emotional response/acknowledgment
- No greeting, no markdown, no emojis

Example for 'concerned': "this is getting a bit tight, but it's manageable."
Example for 'excellent': "oh wow, you're really nailing this lately."

Response:"""
            
            headers = {
                "Authorization": f"Bearer {Config.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an emotional companion. Generate ONLY one short lowercase sentence with emotional framing. Never give advice, numbers, or solutions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 30,
                "temperature": 0.8,
                "top_p": 0.9
            }
            
            response = requests.post(
                Config.GROQ_API_URL,
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            if "choices" not in result or not result["choices"]:
                raise ValueError("No choices in API response")
            
            raw_phrase = result["choices"][0]["message"]["content"].strip()
            
            # Clean and validate response
            cleaned = raw_phrase.lower().strip()
            # Remove quotes, markdown, emojis
            cleaned = re.sub(r'["\'`*]', '', cleaned)
            cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'[^\w\s,.]', '', cleaned)  # Remove emojis and special chars except punctuation
            cleaned = cleaned.strip()
            
            # Ensure it's a single sentence, max ~12 words
            words = cleaned.split()
            if len(words) > 15:  # Allow a bit over for safety
                cleaned = ' '.join(words[:12]) + '.'
            
            # Validate it doesn't contain advice keywords
            advice_keywords = ['should', 'need to', 'must', 'recommend', 'suggest', 'try', 'consider', 'do this']
            if any(keyword in cleaned for keyword in advice_keywords):
                logger.warning("AI response contained advice keywords, using fallback")
                return fallback_phrases.get(mood_label, fallback_phrases["neutral"])
            
            if cleaned:
                # Ensure it ends with punctuation
                if not cleaned.endswith(('.', '!', '?')):
                    cleaned += '.'
                return cleaned
            
            return fallback_phrases.get(mood_label, fallback_phrases["neutral"])
            
        except Exception as e:
            logger.error(f"❌ Emotion phrase generation failed: {e}")
            self.failures += 1
            if self.failures >= self.max_failures:
                self.circuit_open = True
                self.circuit_opened_at = datetime.now()
            return fallback_phrases.get(mood_label, fallback_phrases["neutral"])
    
    def generate_financial_actions(self, context: dict, advice_mode: str = "standard") -> list[str]:
        """Generate 1-2 concrete financial actions (unemotional, practical, bullet points only).
        
        Args:
            context: Financial context dictionary
            advice_mode: Advice style mode ("standard", "strict", "supportive", "cautionary")
            
        Returns:
            List of 1-2 concrete action strings, no emotions or explanations
        """
        # Improved fallback rules with priority logic
        def get_fallback_actions():
            if not context:
                return ["prioritize essential bills", "pause non-essential spending"]
            
            # Priority 1: Unpaid commitments (highest priority)
            commitment_cats = context.get('commitment_categories', [])
            if commitment_cats:
                top_commitment = commitment_cats[0]
                return [f"pay {top_commitment} commitment first", "pause discretionary spending"]
            
            # Priority 2: Budget overruns
            budget_status = context.get('budget_status', 0)
            if budget_status > 0:
                over_budget_count = budget_status
                return [f"cut spending in {over_budget_count} over-budget categories", "reduce discretionary expenses"]
            
            # Priority 3: Top spending categories (only if significant)
            top_categories = context.get('top_categories', [])
            if top_categories:
                category = top_categories[0]
                return [f"reduce {category} spending", "review other top categories"]
            
            return ["prioritize essential bills", "pause non-essential spending"]
        
        # Check circuit breaker
        if self.circuit_open and not self._should_try_recovery():
            logger.warning("⏸️  Circuit open - using fallback financial actions")
            return get_fallback_actions()
        
        if Config.DEMO_MODE:
            return get_fallback_actions()
        
        try:
            # Build context summary
            context_summary = self._build_context_summary(context)
            
            mode_instruction = ""
            if advice_mode == "strict":
                mode_instruction = "Use direct, no-nonsense language. Focus on immediate priorities and tradeoffs."
            elif advice_mode == "supportive":
                mode_instruction = "Frame actions as manageable steps. Acknowledge constraints."
            elif advice_mode == "cautionary":
                mode_instruction = "Include one preventive action to maintain current good state."
            
            prompt = f"""Generate 1-2 concrete financial decisions (not generic advice).

Context: {context_summary}
{mode_instruction}

CRITICAL RULES:
- Output ONLY 1-2 specific financial decisions
- Each must be a concrete action (what to do, which bill, which category)
- REQUIRED: Include prioritization or tradeoff (e.g., "first", "instead of", "before")
- FORBIDDEN: Generic phrases like "review", "consider", "check", "think about"
- No emotions, greetings, or encouragement words
- No explanations or "why"
- No markdown formatting (no bullets, no dashes in output)
- Each action on its own line
- Must be immediately actionable

Good examples:
pay electricity bill first, skip gym membership this month
reduce dining out by 50%, increase grocery budget instead
transfer $200 to savings account before next paycheck

Bad examples (too generic):
review your spending
consider cutting expenses
think about your budget

Response:"""
            
            headers = {
                "Authorization": f"Bearer {Config.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a precise financial advisor. Generate ONLY 1-2 concrete financial decisions with prioritization. FORBIDDEN: generic verbs like 'review', 'consider', 'check'. REQUIRED: specific actions with tradeoffs or priorities. No emotions, explanations, or markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 60,
                "temperature": 0.5,
                "top_p": 0.9
            }
            
            response = requests.post(
                Config.GROQ_API_URL,
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            if "choices" not in result or not result["choices"]:
                raise ValueError("No choices in API response")
            
            raw_actions = result["choices"][0]["message"]["content"].strip()
            
            # Parse actions - split by newlines and clean
            lines = [line.strip() for line in raw_actions.split('\n') if line.strip()]
            actions = []
            
            for line in lines:
                # Remove markdown bullets, dashes, numbers
                cleaned = re.sub(r'^[\s]*[-*•]\s*', '', line)
                cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
                cleaned = re.sub(r'["\'`*]', '', cleaned)
                cleaned = cleaned.strip().lower()
                
                # Filter out explanation-like phrases and generic verbs
                if cleaned and len(cleaned) > 3:
                    # Skip generic verbs
                    generic_verbs = ['review', 'consider', 'check', 'think about', 'look at', 'examine', 'analyze']
                    if any(verb in cleaned for verb in generic_verbs):
                        continue  # Skip this action entirely
                    
                    # Skip if it looks like explanation/emotion
                    skip_patterns = ['because', 'this will', 'remember', 'keep in mind', 'don\'t forget']
                    if not any(pattern in cleaned for pattern in skip_patterns):
                        actions.append(cleaned)
            
            # Limit to 2 actions
            actions = actions[:2]
            
            if len(actions) >= 1:
                return actions
            
            return get_fallback_actions()
            
        except Exception as e:
            logger.error(f"❌ Financial actions generation failed: {e}")
            self.failures += 1
            if self.failures >= self.max_failures:
                self.circuit_open = True
                self.circuit_opened_at = datetime.now()
            return get_fallback_actions()
    
    def _build_context_summary(self, context: dict) -> str:
        """Build a brief text summary from context dict for prompts"""
        if not context:
            return "standard financial situation"
        
        parts = []
        
        # Prioritize commitments - always mention unpaid commitments first
        if 'commitment_categories' in context and context['commitment_categories']:
            commitment_count = len(context['commitment_categories'])
            if commitment_count > 0:
                # Show top 2 commitment categories
                top_commitments = ', '.join(context['commitment_categories'][:2])
                parts.append(f"unpaid commitments: {top_commitments}")
        
        # Then mention significant spending categories (excluding commitments already mentioned)
        if 'top_categories' in context and context['top_categories']:
            # Filter out commitment categories already mentioned
            commitment_cats = set(context.get('commitment_categories', []))
            spending_cats = [cat for cat in context['top_categories'][:3] if cat not in commitment_cats]
            if spending_cats:
                cats = ', '.join(spending_cats)
                parts.append(f"top spending: {cats}")
        
        if 'budget_status' in context:
            over_budget = context['budget_status']
            if over_budget > 0:
                parts.append(f"{over_budget} categories over budget")
        
        return ". ".join(parts) if parts else "standard financial situation"
    
    def _build_contextual_prompt(self, financial_context):
        """Build contextual prompt for financial tips (stub for existing code)"""
        if not financial_context:
            return "Generate a helpful financial tip."
        
        context_parts = []
        if 'top_categories' in financial_context:
            cats = ', '.join(financial_context['top_categories'][:3])
            context_parts.append(f"User's top spending categories: {cats}")
        if 'budget_status' in financial_context:
            over = financial_context['budget_status']
            if over > 0:
                context_parts.append(f"{over} categories are over budget")
        
        context_str = ". ".join(context_parts) if context_parts else "standard financial situation"
        return f"Given this context: {context_str}. Generate a helpful, friendly financial tip."
    
    def _get_system_prompt(self):
        """Get system prompt for financial tips (stub for existing code)"""
        return """You are Penny, a friendly financial AI companion. Generate helpful, practical financial tips that are encouraging and supportive. Keep responses concise and actionable."""

# Global instance
penny_brain = PennyBrain()