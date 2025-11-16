"""
Admin Dashboard - Technical Manager Interface
Implements system monitoring, user management, and API testing
"""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit,
    QTabWidget, QLineEdit, QComboBox, QProgressBar, QFrame,
    QGridLayout, QScrollArea, QMessageBox, QSplitter,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
from datetime import datetime, timedelta
import requests
import json
import traceback
from database.db_manager import fetch_all, fetch_one, execute_query
from core.logger import logger

class APITestWorker(QThread):
    """Worker thread for API testing"""
    test_completed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.apis_to_test = {
            'GROQ AI': 'https://api.groq.com/openai/v1/chat/completions',
            'Plaid Sandbox': 'https://sandbox.plaid.com',
            'Currency API': 'https://api.exchangerate-api.com/v4/latest/USD'
        }
    
    def run(self):
        results = {}
        for api_name, url in self.apis_to_test.items():
            try:
                if 'groq' in url.lower():
                    # Test GROQ API with a simple request
                    response = requests.post(url, 
                        headers={'Authorization': 'Bearer demo_key'},
                        json={'model': 'llama2-70b-4096', 'messages': [{'role': 'user', 'content': 'test'}]},
                        timeout=10)
                    results[api_name] = {
                        'status': 'OK' if response.status_code in [200, 401] else 'ERROR',
                        'response_time': response.elapsed.total_seconds(),
                        'status_code': response.status_code
                    }
                else:
                    # Test other APIs
                    response = requests.get(url, timeout=10)
                    results[api_name] = {
                        'status': 'OK' if response.status_code == 200 else 'ERROR',
                        'response_time': response.elapsed.total_seconds(),
                        'status_code': response.status_code
                    }
            except Exception as e:
                results[api_name] = {
                    'status': 'ERROR',
                    'response_time': 0,
                    'error': str(e)
                }
        
        self.test_completed.emit(results)

class AdminDashboard(QMainWindow):
    """Admin Dashboard for Technical Managers"""
    
    def __init__(self, user_id, username):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.api_worker = None
        
        self.setWindowTitle(f"Admin Dashboard - {username}")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet("""
            QMainWindow {
                background: #f8f9fa;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background: white;
            }
            QTabBar::tab {
                background: #e9ecef;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #007bff;
                color: white;
            }
        """)
        
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        """Setup the admin dashboard interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tab widget for different admin functions
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_system_logs_tab()
        self.create_user_stats_tab()
        self.create_api_testing_tab()
        self.create_user_search_tab()
        
        # Status bar
        self.statusBar().showMessage("Admin Dashboard Ready")
    
    def create_header(self):
        """Create dashboard header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #007bff, stop:1 #0056b3);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout(header_frame)
        
        # Title
        title = QLabel("🔧 Admin Dashboard")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # User info
        user_info = QLabel(f"Welcome, {self.username}")
        user_info.setFont(QFont("Segoe UI", 14))
        user_info.setStyleSheet("color: white;")
        layout.addWidget(user_info)
        
        return header_frame
    
    def create_system_logs_tab(self):
        """Create system logs monitoring tab"""
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh Logs")
        refresh_btn.clicked.connect(self.refresh_system_logs)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        
        clear_btn = QPushButton("🗑️ Clear Logs")
        clear_btn.clicked.connect(self.clear_system_logs)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c82333;
            }
        """)
        
        # Log level filter
        level_label = QLabel("Filter Level:")
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["All", "INFO", "WARNING", "ERROR", "DEBUG"])
        self.log_level_combo.currentTextChanged.connect(self.filter_logs)
        
        controls_layout.addWidget(refresh_btn)
        controls_layout.addWidget(clear_btn)
        controls_layout.addWidget(level_label)
        controls_layout.addWidget(self.log_level_combo)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels([
            "Timestamp", "Level", "User", "Action", "Details"
        ])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.logs_table)
        
        self.tab_widget.addTab(logs_widget, "📊 System Logs")
    
    def create_user_stats_tab(self):
        """Create user statistics tab"""
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)
        
        # Stats overview
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        stats_layout = QGridLayout(stats_frame)
        
        # Create stat cards
        self.total_users_label = self.create_stat_card("👥 Total Users", "0", "#007bff")
        self.monthly_signups_label = self.create_stat_card("📈 This Month", "0", "#28a745")
        self.active_users_label = self.create_stat_card("🟢 Active Users", "0", "#ffc107")
        self.new_today_label = self.create_stat_card("✨ New Today", "0", "#17a2b8")
        
        stats_layout.addWidget(self.total_users_label, 0, 0)
        stats_layout.addWidget(self.monthly_signups_label, 0, 1)
        stats_layout.addWidget(self.active_users_label, 0, 2)
        stats_layout.addWidget(self.new_today_label, 0, 3)
        
        layout.addWidget(stats_frame)
        
        # User signup trends (simplified chart representation)
        trends_frame = QFrame()
        trends_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        trends_layout = QVBoxLayout(trends_frame)
        
        trends_title = QLabel("📊 User Signup Trends (Last 12 Months)")
        trends_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        trends_layout.addWidget(trends_title)
        
        # Simple bar chart representation
        self.trends_display = QTextEdit()
        self.trends_display.setMaximumHeight(200)
        self.trends_display.setReadOnly(True)
        trends_layout.addWidget(self.trends_display)
        
        layout.addWidget(trends_frame)
        
        self.tab_widget.addTab(stats_widget, "👥 User Statistics")
    
    def create_api_testing_tab(self):
        """Create API testing tab"""
        api_widget = QWidget()
        layout = QVBoxLayout(api_widget)
        
        # Test controls
        controls_layout = QHBoxLayout()
        
        test_btn = QPushButton("🧪 Test All APIs")
        test_btn.clicked.connect(self.test_all_apis)
        test_btn.setStyleSheet("""
            QPushButton {
                background: #6f42c1;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #5a32a3;
            }
        """)
        
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        
        controls_layout.addWidget(test_btn)
        controls_layout.addWidget(self.test_progress)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # API test results
        self.api_results_table = QTableWidget()
        self.api_results_table.setColumnCount(4)
        self.api_results_table.setHorizontalHeaderLabels([
            "API Name", "Status", "Response Time", "Details"
        ])
        self.api_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.api_results_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.api_results_table)
        
        self.tab_widget.addTab(api_widget, "🔌 API Testing")
    
    def create_user_search_tab(self):
        """Create user search tab"""
        search_widget = QWidget()
        layout = QVBoxLayout(search_widget)
        
        # Search controls
        search_layout = QHBoxLayout()
        
        search_label = QLabel("🔍 Search Users:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter username, email, or user ID...")
        self.search_input.returnPressed.connect(self.search_users)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_users)
        search_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # User results table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels([
            "User ID", "Username", "Email", "Role", "Created", "Last Login"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.users_table)
        
        self.tab_widget.addTab(search_widget, "👤 User Search")
    
    def create_stat_card(self, title, value, color):
        """Create a statistics card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {color};
                color: white;
                border-radius: 10px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName("stat_value")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        return card
    
    def load_initial_data(self):
        """Load initial data for all tabs"""
        self.refresh_system_logs()
        self.load_user_statistics()
        self.load_user_search_results()
    
    def refresh_system_logs(self):
        """Refresh system logs from database"""
        try:
            # Get logs from database
            logs = fetch_all("""
                SELECT timestamp, level, user_id, action, details
                FROM system_logs 
                ORDER BY timestamp DESC 
                LIMIT 100
            """)
            
            self.logs_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                self.logs_table.setItem(row, 0, QTableWidgetItem(str(log['timestamp'])))
                self.logs_table.setItem(row, 1, QTableWidgetItem(log['action'] or 'N/A'))
                self.logs_table.setItem(row, 2, QTableWidgetItem(str(log['user_id']) if log['user_id'] else 'System'))
                self.logs_table.setItem(row, 3, QTableWidgetItem(log['action'] or 'N/A'))
                self.logs_table.setItem(row, 4, QTableWidgetItem(log['details'] or 'N/A'))
                
                # Color code by level
                if log['action'] and 'error' in log['action'].lower():
                    for col in range(5):
                        self.logs_table.item(row, col).setBackground(QColor(255, 245, 245))
            
            self.statusBar().showMessage(f"Loaded {len(logs)} log entries")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load logs: {str(e)}")
    
    def clear_system_logs(self):
        """Clear system logs"""
        reply = QMessageBox.question(self, "Clear Logs", 
                                   "Are you sure you want to clear all system logs?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                execute_query("DELETE FROM system_logs", commit=True)
                self.refresh_system_logs()
                QMessageBox.information(self, "Success", "System logs cleared successfully")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear logs: {str(e)}")
    
    def filter_logs(self, level):
        """Filter logs by level"""
        # This would implement filtering logic
        self.refresh_system_logs()
    
    def load_user_statistics(self):
        """Load user statistics"""
        try:
            # Total users
            total_users = fetch_one("SELECT COUNT(*) as count FROM users")
            self.total_users_label.findChild(QLabel, "stat_value").setText(str(total_users['count']))
            
            # Monthly signups
            monthly_signups = fetch_one("""
                SELECT COUNT(*) as count FROM users 
                WHERE created_at >= date('now', '-30 days')
            """)
            self.monthly_signups_label.findChild(QLabel, "stat_value").setText(str(monthly_signups['count']))
            
            # Active users (logged in last 7 days)
            active_users = fetch_one("""
                SELECT COUNT(*) as count FROM users 
                WHERE last_login >= date('now', '-7 days')
            """)
            self.active_users_label.findChild(QLabel, "stat_value").setText(str(active_users['count']))
            
            # New today
            new_today = fetch_one("""
                SELECT COUNT(*) as count FROM users 
                WHERE date(created_at) = date('now')
            """)
            self.new_today_label.findChild(QLabel, "stat_value").setText(str(new_today['count']))
            
            # Generate trends display
            self.generate_trends_display()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load user statistics: {str(e)}")
    
    def generate_trends_display(self):
        """Generate user signup trends display"""
        try:
            # Get monthly signup data
            trends_data = fetch_all("""
                SELECT strftime('%Y-%m', created_at) as month,
                       COUNT(*) as signups
                FROM users 
                WHERE created_at >= date('now', '-12 months')
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY month
            """)
            
            # Create simple text-based chart
            chart_text = "Monthly User Signups:\n\n"
            max_signups = max([row['signups'] for row in trends_data]) if trends_data else 1
            
            for trend in trends_data:
                month = trend['month']
                signups = trend['signups']
                bar_length = int((signups / max_signups) * 20)
                bar = "█" * bar_length
                chart_text += f"{month}: {bar} {signups}\n"
            
            self.trends_display.setText(chart_text)
            
        except Exception as e:
            self.trends_display.setText(f"Error loading trends: {str(e)}")
    
    def test_all_apis(self):
        """Test all integrated APIs"""
        if self.api_worker and self.api_worker.isRunning():
            return
        
        self.test_progress.setVisible(True)
        self.test_progress.setRange(0, 0)  # Indeterminate progress
        
        self.api_worker = APITestWorker()
        self.api_worker.test_completed.connect(self.on_api_test_completed)
        self.api_worker.start()
    
    def on_api_test_completed(self, results):
        """Handle API test completion"""
        self.test_progress.setVisible(False)
        
        self.api_results_table.setRowCount(len(results))
        
        for row, (api_name, result) in enumerate(results.items()):
            self.api_results_table.setItem(row, 0, QTableWidgetItem(api_name))
            
            status_item = QTableWidgetItem(result['status'])
            if result['status'] == 'OK':
                status_item.setBackground(QColor(212, 237, 218))  # Light green
            else:
                status_item.setBackground(QColor(248, 215, 218))  # Light red
            
            self.api_results_table.setItem(row, 1, status_item)
            self.api_results_table.setItem(row, 2, QTableWidgetItem(f"{result['response_time']:.2f}s"))
            
            details = f"Status Code: {result.get('status_code', 'N/A')}"
            if 'error' in result:
                details += f" | Error: {result['error']}"
            
            self.api_results_table.setItem(row, 3, QTableWidgetItem(details))
        
        self.statusBar().showMessage("API testing completed")
    
    def search_users(self):
        """Search for users"""
        query = self.search_input.text().strip()
        if not query:
            self.load_user_search_results()
            return
        
        try:
            users = fetch_all("""
                SELECT user_id, username, email, role, created_at, last_login
                FROM users 
                WHERE username LIKE ? OR email LIKE ? OR user_id = ?
                ORDER BY created_at DESC
            """, (f"%{query}%", f"%{query}%", query))
            
            self.display_search_results(users)
            
        except Exception as e:
            QMessageBox.warning(self, "Search Error", f"Failed to search users: {str(e)}")
    
    def load_user_search_results(self):
        """Load all users for search results"""
        try:
            users = fetch_all("""
                SELECT user_id, username, email, role, created_at, last_login
                FROM users 
                ORDER BY created_at DESC
                LIMIT 50
            """)
            
            self.display_search_results(users)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load users: {str(e)}")
    
    def display_search_results(self, users):
        """Display user search results"""
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['user_id'])))
            self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))
            self.users_table.setItem(row, 2, QTableWidgetItem(user['email']))
            self.users_table.setItem(row, 3, QTableWidgetItem(user['role']))
            self.users_table.setItem(row, 4, QTableWidgetItem(str(user['created_at'])))
            self.users_table.setItem(row, 5, QTableWidgetItem(str(user['last_login']) if user['last_login'] else 'Never'))
        
        self.statusBar().showMessage(f"Found {len(users)} users")

def main():
    """Test the admin dashboard"""
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create admin dashboard
    admin_dash = AdminDashboard(1, "Admin User")
    admin_dash.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())






