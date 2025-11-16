# ui/components/confetti.py

"""
Confetti Celebration Animation - Makes achievements feel magical!
"""

from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PyQt5.QtGui import QColor, QPainter, QPen
import random
import math

class ConfettiParticle(QLabel):
    """Individual confetti particle with physics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.velocity_y = random.uniform(5, 15)
        self.velocity_x = random.uniform(-3, 3)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-10, 10)
        self.gravity = 0.5
        self.wind = random.uniform(-0.2, 0.2)
        self.life = 100  # frames
        self.age = 0
        
        # Random confetti shape and color
        shapes = ['■', '●', '▲', '♦']
        colors = ['#EF4444', '#F59E0B', '#10B981', '#3B82F6', '#8B5CF6', '#EC4899']
        
        self.setText(random.choice(shapes))
        self.setStyleSheet(f"color: {random.choice(colors)}; font-size: 16px; background: transparent;")
        self.setAlignment(Qt.AlignCenter)
        
    def update_position(self):
        """Update particle position with physics"""
        self.velocity_y += self.gravity
        self.velocity_x += self.wind
        self.rotation += self.rotation_speed
        self.age += 1
        
        # Move particle
        new_x = self.x() + self.velocity_x
        new_y = self.y() + self.velocity_y
        
        self.move(int(new_x), int(new_y))
        self.setStyleSheet(self.styleSheet() + f" opacity: {1 - (self.age / self.life)};")
        
        return self.age < self.life and self.y() < self.parent().height()

class ConfettiCelebration(QWidget):
    """Full-screen confetti celebration effect"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Cover entire parent
        if parent:
            self.setGeometry(parent.rect())
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_particles)
        
    def start_celebration(self, duration=3000):
        """Start the confetti celebration"""
        self.create_particles(50)  # Create 50 particles
        self.timer.start(30)  # Update every 30ms
        
        # Stop after duration
        QTimer.singleShot(duration, self.stop_celebration)
        
    def create_particles(self, count):
        """Create confetti particles at random positions"""
        for _ in range(count):
            particle = ConfettiParticle(self)
            particle.move(
                random.randint(0, self.width()),
                random.randint(-100, 0)  # Start above the view
            )
            particle.show()
            self.particles.append(particle)
    
    def animate_particles(self):
        """Animate all particles"""
        alive_particles = []
        
        for particle in self.particles:
            if particle.update_position():
                alive_particles.append(particle)
            else:
                particle.deleteLater()
        
        self.particles = alive_particles
        
        # If all particles are gone, stop
        if not self.particles:
            self.stop_celebration()
    
    def stop_celebration(self):
        """Stop the celebration and clean up"""
        self.timer.stop()
        for particle in self.particles:
            particle.deleteLater()
        self.particles.clear()
        self.deleteLater()