# ui/components/enhanced_penny_widget.py

"""
Enhanced Penny Widget with Personality Integration
"""

import random
import json
from PyQt5.QtWidgets import (QFrame,QHBoxLayout,QVBoxLayout,QLabel,
                             QPushButton)
from PyQt5.QtCore import (Qt,QTimer,pyqtSignal,QPropertyAnimation,
                          QEasingCurve,QRect)
from PyQt5.QtGui import QFont
from core.penny_personality import PennyPersonality
from core.ai_suggestions import generate_penny_message
from core.ai_insights_cache import _get_financial_context
from .penny_avatar import PennyAvatar


class EnhancedPennyWidget(QFrame):
    """Enhanced Penny widget with personality and emotional intelligence"""

    # Signals
    message_updated = pyqtSignal(str,str)  # message, tone
    personality_ready = pyqtSignal(object)  # personality engine

    def __init__(self,user_id,username,parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.username = username

        # Initialize personality engine
        self.personality = PennyPersonality(user_id,username)
        self.personality_ready.emit(self.personality)

        self.current_tone = "friendly"
        self.message_history = []
        self.is_expanded = False
        self.user_mood_history = []
        self.last_mood_check = None

        self.setup_ui()
        self.apply_styling()
        self.setup_animations()
        self.setup_personality_timers()

    def setup_ui(self):
        """Setup enhanced Penny layout"""
        self.setProperty("class","penny_widget")
        self.setFixedHeight(120)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16,16,16,16)
        main_layout.setSpacing(20)

        # Left: Enhanced Avatar with emotional states
        self.avatar = PennyAvatar(size=80)
        main_layout.addWidget(self.avatar)

        # Right: Speech bubble and enhanced controls
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)

        # Speech bubble
        self.bubble_frame = QFrame()
        self.bubble_frame.setProperty("class","penny_bubble")
        self.bubble_frame.setFixedHeight(80)

        bubble_layout = QHBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(16,12,16,12)

        self.message_label = QLabel("💭 Getting to know you...")
        self.message_label.setWordWrap(True)
        
        # Theme-aware message text color
        from core.theme_manager import theme_manager
        from assets.styles.penny_colors import PennyColors
        p = PennyColors.get_palette(theme_manager.current_theme)
        self.message_label.setStyleSheet(f"color: {p['text_primary']}; font-size: 14px; line-height: 1.4;")
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        bubble_layout.addWidget(self.message_label)
        right_layout.addWidget(self.bubble_frame)

        # Refresh button
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        self.refresh_btn = QPushButton()
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.clicked.connect(self.request_new_tip)
        self.refresh_btn.setToolTip("Refresh for new advice")

        controls_layout.addStretch()
        controls_layout.addWidget(self.refresh_btn)

        right_layout.addLayout(controls_layout)
        main_layout.addLayout(right_layout)

        # Apply styling to enhanced buttons
        self.style_enhanced_buttons()

        # Accessibility features
        self.setFocusPolicy(Qt.StrongFocus)
        self.message_label.setAccessibleName("Penny's message")
        self.message_label.setAccessibleDescription("Financial companion advice and tips")

    def style_enhanced_buttons(self):
        """Apply consistent styling to refresh button with theme support"""
        from core.theme_manager import theme_manager
        from assets.styles.penny_colors import PennyColors
        p = PennyColors.get_palette(theme_manager.current_theme)
        
        try:
            import qtawesome as qta
            icon_color = p['text_secondary']
            refresh_icon = qta.icon('fa5s.sync-alt', color=icon_color)
            self.refresh_btn.setIcon(refresh_icon)
        except ImportError:
            # Fallback to text if qtawesome not available
            self.refresh_btn.setText("↻")
        
        if theme_manager.current_theme == "dark":
            # Dark mode: subtle button
            button_style = f"""
                QPushButton {{
                    background: rgba(19, 47, 58, 0.8);
                    border: 1px solid rgba(30, 122, 157, 0.3);
                    border-radius: 16px;
                    padding: 0px;
                    font-size: 14px;
                    color: {p['text_secondary']};
                }}
                QPushButton:hover {{
                    background: rgba(19, 47, 58, 1);
                    border-color: {p['ai_accent']};
                    color: {p['accent']};
                }}
                QPushButton:pressed {{
                    background: rgba(16, 42, 51, 1);
                }}
            """
        else:
            # Light mode: original style
            button_style = """
                QPushButton {
                    background: rgba(255, 255, 255, 0.9);
                    border: 1px solid rgba(0, 0, 0, 0.1);
                    border-radius: 16px;
                    padding: 0px;
                    font-size: 14px;
                    color: #6B7280;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 1);
                    border-color: rgba(37, 99, 235, 0.3);
                    color: #2563EB;
                }
                QPushButton:pressed {
                    background: rgba(240, 240, 240, 1);
                }
            """
        self.refresh_btn.setStyleSheet(button_style)

    def setup_personality_timers(self):
        """Setup timers for personality-based interactions"""
        # Time-based greeting
        self.greeting_timer = QTimer()
        self.greeting_timer.timeout.connect(self.send_time_based_greeting)
        self.greeting_timer.start(3600000)  # Check every hour

        # Proactive tips
        self.tip_timer = QTimer()
        self.tip_timer.timeout.connect(self.send_proactive_tip)
        self.tip_timer.start(1800000)  # Every 30 minutes (with randomness)

        # Send initial greeting
        QTimer.singleShot(2000,self.send_time_based_greeting)

    def send_time_based_greeting(self):
        """Send greeting based on time of day"""
        message,tone = self.personality.get_time_based_greeting()
        self.update_message(message,tone)

    def send_proactive_tip(self):
        """Send proactive financial tip (with randomness)"""
        if self.should_send_proactive_tip() and random.random() < 0.3:  # 30% chance
            # #region agent log
            try:
                with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"A","location":"enhanced_penny_widget.py:send_proactive_tip","message":"Proactive tip triggered","data":{"user_id":self.user_id},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion
            
            financial_context = _get_financial_context(self.user_id)
            result = generate_penny_message(financial_context)
            
            # Use expression for avatar visual display (not mood)
            expression = result.get('expression', 'neutral')
            # Keep tone mapping for backward compatibility with styling
            mood_to_tone = {
                'excellent': 'positive',
                'good': 'positive',
                'neutral': 'friendly',
                'concerned': 'warning',
                'needs_attention': 'alert'
            }
            tone = mood_to_tone.get(result['mood'], 'friendly')
            
            # #region agent log
            try:
                with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"A","location":"enhanced_penny_widget.py:send_proactive_tip","message":"New pipeline result","data":{"mood":result['mood'],"expression":expression,"tone":tone,"message_preview":result['message'][:50]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion
            
            self.update_message(result['message'], tone, expression)

    def should_send_proactive_tip(self):
        """Determine if we should send a proactive tip"""
        # Don't interrupt if user recently interacted
        if self.message_history:
            # Simple check - if last message was user-initiated, wait
            last_message = self.message_history[-1][0] if self.message_history else ""
            auto_messages = ["💭","Consider reviewing","Round up","Set a weekly","Review your","Small daily"]
            if not any(msg in last_message for msg in auto_messages):
                return False

        return True


    def track_mood_patterns(self):
        """Analyze mood patterns for better responses"""
        if len(self.user_mood_history) < 3:
            return "neutral"

        recent_moods = [mood.get('mood_level','neutral') for mood in self.user_mood_history[-3:]]

        # Simple pattern detection
        if all(mood == 'excellent' for mood in recent_moods):
            return "trending_positive"
        elif all(mood in ['concerned','needs_attention'] for mood in recent_moods):
            return "trending_concerned"

        return "stable"

    def update_message(self,message,tone="friendly",expression=None):
        """Enhanced message update with personality"""
        try:
            if not message or not isinstance(message,str):
                message = "I'm here to help with your financial journey! 💫"
                tone = "friendly"
                expression = "neutral"

            self.current_tone = tone
            self.message_history.append((message,tone))

            # Keep only last 15 messages
            if len(self.message_history) > 15:
                self.message_history.pop(0)

            # Animate message change
            if hasattr(self,'message_animation'):
                self.message_animation.setStartValue(0.3)
                self.message_animation.setEndValue(1.0)
                self.message_animation.start()

            self.message_label.setText(message)
            self.apply_tone_styling(tone)

            # Update avatar based on expression (not mood/tone)
            if hasattr(self,'avatar'):
                avatar_expression = expression if expression else tone
                self.avatar.update_emotional_state(avatar_expression)

            # Emit signal for other components
            self.message_updated.emit(message,tone)

            # Trigger bubble animation
            self.animate_bubble()

        except Exception as e:
            print(f"Error updating Penny message: {e}")
            # Fallback message
            self.message_label.setText("Hello! Ready to help with your finances! 💫")

    def celebrate_achievement(self,achievement_type,data=None):
        """Celebrate user achievements with personality"""
        if achievement_type == 'badge':
            message,tone = self.personality.get_contextual_response('badge_earned',data)
        elif achievement_type == 'goal':
            message,tone = self.personality.get_contextual_response('goal_completed',data)
        elif achievement_type == 'mood_improvement':
            message,tone = self.personality.get_contextual_response('mood_excellent',data)
        else:
            message,tone = self.personality.get_contextual_response('welcome')

        self.update_message(message,tone)

    def update_user_mood(self,mood_data):
        """Update Penny's responses based on user mood"""
        self.personality.record_user_mood(mood_data)
        self.user_mood_history.append(mood_data)

        # Keep mood history manageable
        if len(self.user_mood_history) > 10:
            self.user_mood_history.pop(0)

        mood_level = mood_data.get('mood_level','neutral')
        context_map = {
            'excellent': 'mood_excellent',
            'good': 'mood_good',
            'neutral': 'mood_neutral',
            'concerned': 'mood_concerned',
            'needs_attention': 'mood_needs_attention'
        }

        context = context_map.get(mood_level,'mood_neutral')
        message,tone = self.personality.get_contextual_response(context)
        self.update_message(message,tone)

    def apply_styling(self):
        """Apply Penny's special styling with theme support"""
        from core.theme_manager import theme_manager
        from assets.styles.penny_colors import PennyColors
        
        if theme_manager.current_theme == "dark":
            # Dark mode: subtle, muted penny area
            p = PennyColors.get_palette("dark")
            self.setStyleSheet(f"""
                QFrame[class="penny_widget"] {{
                    background: {p['ai_bg']};
                    border: 1px solid rgba(30, 122, 157, 0.3);
                    border-radius: 20px;
                }}
                QFrame[class="penny_bubble"] {{
                    background: {p['surface']};
                    border-left: 3px solid {p['ai_accent']};
                    border-radius: 12px;
                }}
            """)
        else:
            # Light mode: original bright colors
            self.setStyleSheet("""
                QFrame[class="penny_widget"] {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(254, 243, 199, 0.3), 
                        stop:1 rgba(253, 230, 138, 0.3));
                    border: 1px solid rgba(245, 158, 11, 0.2);
                    border-radius: 20px;
                }
                QFrame[class="penny_bubble"] {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #FEF3C7, stop:1 #FDE68A);
                    border-left: 4px solid #F59E0B;
                    border-radius: 12px;
                }
            """)

    def setup_animations(self):
        """Setup entrance and interaction animations"""
        # Bubble pulse animation
        self.bubble_animation = QPropertyAnimation(self.bubble_frame,b"geometry")
        self.bubble_animation.setDuration(800)
        self.bubble_animation.setEasingCurve(QEasingCurve.OutElastic)

        # Message fade animation
        self.message_animation = QPropertyAnimation(self.message_label,b"windowOpacity")
        self.message_animation.setDuration(400)
        self.message_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Entrance animation
        self.entrance_animation = QPropertyAnimation(self,b"windowOpacity")
        self.entrance_animation.setDuration(1000)
        self.entrance_animation.setStartValue(0.0)
        self.entrance_animation.setEndValue(1.0)
        self.entrance_animation.start()

    def apply_tone_styling(self,tone):
        """Apply tone-specific styling to the bubble with theme support"""
        from core.theme_manager import theme_manager
        from assets.styles.penny_colors import PennyColors
        
        if theme_manager.current_theme == "dark":
            # Dark mode: subtle tone colors with reduced contrast
            p = PennyColors.get_palette("dark")
            tone_colors_dark = {
                "friendly": (p['surface'], "#1e7a9d"),
                "positive": (p['surface'], "#2ba878"),
                "encouraging": (p['surface'], "#2596be"),
                "warning": (p['surface'], "#d89b3a"),
                "alert": (p['surface'], "#e57373"),
                "excited": (p['surface'], "#2596be"),
                "supportive": (p['surface'], "#2596be"),
                "calm": (p['surface'], "#2ba878")
            }
            
            bg_color, border_color = tone_colors_dark.get(tone, tone_colors_dark["friendly"])
            
            self.bubble_frame.setStyleSheet(f"""
                QFrame[class="penny_bubble"] {{
                    background: {bg_color};
                    border-left: 3px solid {border_color};
                    border-radius: 12px;
                }}
            """)
        else:
            # Light mode: original bright colors
            tone_colors = {
                "friendly": ("#FEF3C7","#FDE68A","#F59E0B"),
                "positive": ("#D1FAE5","#A7F3D0","#10B981"),
                "encouraging": ("#DBEAFE","#93C5FD","#2563EB"),
                "warning": ("#FEF3C7","#FDE68A","#F59E0B"),
                "alert": ("#FEE2E2","#FCA5A5","#DC2626"),
                "excited": ("#FEF3C7","#FDE68A","#F59E0B"),
                "supportive": ("#DBEAFE","#93C5FD","#2563EB"),
                "calm": ("#F0FDF4","#BBF7D0","#22C55E")
            }

            start_color,end_color,border_color = tone_colors.get(
                tone,tone_colors["friendly"]
            )

            self.bubble_frame.setStyleSheet(f"""
                QFrame[class="penny_bubble"] {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {start_color}, stop:1 {end_color});
                    border-left: 4px solid {border_color};
                    border-radius: 12px;
                }}
            """)

    def animate_bubble(self):
        """Animate the speech bubble for emphasis"""
        original_geometry = self.bubble_frame.geometry()

        # Create a gentle bounce effect
        self.bubble_animation.setStartValue(
            QRect(original_geometry.x() - 2,original_geometry.y() - 1,
                  original_geometry.width() + 4,original_geometry.height() + 2)
        )
        self.bubble_animation.setEndValue(original_geometry)
        self.bubble_animation.start()

    def toggle_history(self):
        """Toggle message history view"""
        print("📜 History button clicked - would show message history")
        # For now, cycle through last messages
        if self.message_history and len(self.message_history) > 1:
            # Show previous message
            prev_message,prev_tone = self.message_history[-2]
            self.update_message(prev_message,prev_tone)

    def request_new_tip(self):
        """Request a new AI tip"""
        # #region agent log
        try:
            with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"B","location":"enhanced_penny_widget.py:request_new_tip","message":"New tip requested","data":{"user_id":self.user_id},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
        
        self.update_message("💡 Let me think of something fresh for you...","friendly")

        # Use real AI service with delay
        QTimer.singleShot(1500,self._fetch_new_tip)

    def _fetch_new_tip(self):
        """Fetch new tip from generate_penny_message pipeline"""
        financial_context = _get_financial_context(self.user_id)
        result = generate_penny_message(financial_context)
        
        # Use expression for avatar visual display (not mood)
        expression = result.get('expression', 'neutral')
        # Keep tone mapping for backward compatibility with styling
        mood_to_tone = {
            'excellent': 'positive',
            'good': 'positive',
            'neutral': 'friendly',
            'concerned': 'warning',
            'needs_attention': 'alert'
        }
        tone = mood_to_tone.get(result['mood'], 'friendly')
        
        # #region agent log
        try:
            with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"B","location":"enhanced_penny_widget.py:_fetch_new_tip","message":"New pipeline result","data":{"mood":result['mood'],"expression":expression,"tone":tone,"message_preview":result['message'][:50]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
        
        self.update_message(result['message'], tone, expression)

    def get_current_message(self):
        """Get Penny's current message"""
        return self.message_label.text(),self.current_tone

    def clear_history(self):
        """Clear message history"""
        self.message_history.clear()
        self.update_message("💭 Hello! I'm Penny, your financial companion.","friendly")

    def get_contextual_tip(self,user_context=None):
        """Get tips based on user's current financial context"""
        if not user_context:
            return self.request_financial_tip()

        # Context-aware tip selection
        if user_context.get('overspending',False):
            message,tone = self.personality.get_contextual_response(
                'overspending_alert',user_context
            )
        elif user_context.get('savings_goal_met',False):
            message,tone = self.personality.get_contextual_response(
                'savings_success',user_context
            )
        elif user_context.get('budget_tight',False):
            message,tone = self.personality.get_contextual_response(
                'budget_help',user_context
            )
        else:
            return self.request_financial_tip()

        self.update_message(message,tone)

    def cleanup(self):
        """Clean up timers and resources"""
        if hasattr(self,'greeting_timer'):
            self.greeting_timer.stop()
        if hasattr(self,'tip_timer'):
            self.tip_timer.stop()