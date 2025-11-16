#!/usr/bin/env python3
"""
Simple Admin Dashboard for Screenshots
Just needs to look good, not fully functional
"""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit,
    QTabWidget, QLineEdit, QComboBox, QProgressBar, QFrame,
    QGridLayout, QScrollArea, QMessageBox, QSplitter,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
from datetime import datetime, timedelta

class SimpleAdminDashboard(QMainWindow):
    """Simple Admin Dashboard for Screenshots"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PennyWise Admin Dashboard")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet("""
            QMainWindow {
                background: #f9f7f5;
            }
            QTabWidget::pane {
                border: 1px solid #e0d3cc;
                background: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #e8d2c4;
                color: #704b3b;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #d6733a;
                color: white;
            }
            QPushButton {
                background: #d6733a;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #b45131;
            }
            QTableWidget {
                gridline-color: #e0d3cc;
                background: white;
                alternate-background-color: #f9f7f5;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        
        self.setup_ui()
        self.populate_with_demo_data()
    
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
        self.statusBar().showMessage("Admin Dashboard Ready - Demo Mode")
    
    def create_header(self):
        """Create dashboard header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #d6733a, stop:1 #b45131);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        layout = QHBoxLayout(header_frame)
        
        # Title
        title = QLabel("PennyWise Admin Dashboard")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # User info
        user_info = QLabel("Technical Manager - Demo Mode")
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
        
        refresh_btn = QPushButton("Refresh Logs")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #10B981;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        
        clear_btn = QPushButton("Clear Logs")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #EF4444;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #DC2626;
            }
        """)
        
        # Log level filter
        level_label = QLabel("Filter Level:")
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["All", "INFO", "WARNING", "ERROR", "DEBUG"])
        
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
        
        self.tab_widget.addTab(logs_widget, "System Logs")
    
    def create_user_stats_tab(self):
        """Create user statistics tab"""
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)
        
        # Stats overview
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0d3cc;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        stats_layout = QGridLayout(stats_frame)
        
        # Create stat cards
        self.total_users_label = self.create_stat_card("Total Users", "1,247", "#3B82F6")
        self.monthly_signups_label = self.create_stat_card("This Month", "89", "#10B981")
        self.active_users_label = self.create_stat_card("Active Users", "892", "#F59E0B")
        self.new_today_label = self.create_stat_card("New Today", "12", "#8B5CF6")
        
        stats_layout.addWidget(self.total_users_label, 0, 0)
        stats_layout.addWidget(self.monthly_signups_label, 0, 1)
        stats_layout.addWidget(self.active_users_label, 0, 2)
        stats_layout.addWidget(self.new_today_label, 0, 3)
        
        layout.addWidget(stats_frame)
        
        # User signup trends
        trends_frame = QFrame()
        trends_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0d3cc;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        trends_layout = QVBoxLayout(trends_frame)
        
        trends_title = QLabel("User Signup Trends (Last 12 Months)")
        trends_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        trends_layout.addWidget(trends_title)
        
        # Simple bar chart representation
        self.trends_display = QTextEdit()
        self.trends_display.setMaximumHeight(200)
        self.trends_display.setReadOnly(True)
        trends_layout.addWidget(self.trends_display)
        
        layout.addWidget(trends_frame)
        
        self.tab_widget.addTab(stats_widget, "User Statistics")
    
    def create_api_testing_tab(self):
        """Create API testing tab"""
        api_widget = QWidget()
        layout = QVBoxLayout(api_widget)
        
        # Test controls
        controls_layout = QHBoxLayout()
        
        test_btn = QPushButton("Test All APIs")
        test_btn.setStyleSheet("""
            QPushButton {
                background: #8B5CF6;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #7C3AED;
            }
        """)
        
        self.test_progress = QProgressBar()
        self.test_progress.setValue(75)
        self.test_progress.setVisible(True)
        
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
        
        self.tab_widget.addTab(api_widget, "API Testing")
    
    def create_user_search_tab(self):
        """Create user search tab"""
        search_widget = QWidget()
        layout = QVBoxLayout(search_widget)
        
        # Search controls
        search_layout = QHBoxLayout()
        
        search_label = QLabel("Search Users:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter username, email, or user ID...")
        
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 10px 20px;
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
        
        self.tab_widget.addTab(search_widget, "User Search")
    
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
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        return card
    
    def populate_with_demo_data(self):
        """Populate with demo data for screenshots"""
        
        # Populate system logs
        demo_logs = [
            ("2024-01-15 10:30:15", "INFO", "User_123", "Login", "User successfully logged in"),
            ("2024-01-15 10:25:42", "INFO", "User_456", "Transaction", "Added new expense: $25.50"),
            ("2024-01-15 10:20:18", "WARNING", "System", "API", "Plaid API response time slow: 2.3s"),
            ("2024-01-15 10:15:33", "INFO", "User_789", "Badge", "Earned badge: Smart Saver"),
            ("2024-01-15 10:10:07", "ERROR", "System", "Database", "Connection timeout to external service"),
            ("2024-01-15 10:05:22", "INFO", "User_321", "Goal", "Completed savings goal: Emergency Fund"),
            ("2024-01-15 10:00:15", "DEBUG", "System", "Cache", "Cleared user session cache"),
            ("2024-01-15 09:55:41", "INFO", "User_654", "Mood", "Financial mood improved: Good"),
            ("2024-01-15 09:50:12", "WARNING", "User_987", "Budget", "Approaching monthly budget limit"),
            ("2024-01-15 09:45:28", "INFO", "System", "Backup", "Daily backup completed successfully")
        ]
        
        self.logs_table.setRowCount(len(demo_logs))
        for row, log in enumerate(demo_logs):
            self.logs_table.setItem(row, 0, QTableWidgetItem(log[0]))
            self.logs_table.setItem(row, 1, QTableWidgetItem(log[1]))
            self.logs_table.setItem(row, 2, QTableWidgetItem(log[2]))
            self.logs_table.setItem(row, 3, QTableWidgetItem(log[3]))
            self.logs_table.setItem(row, 4, QTableWidgetItem(log[4]))
            
            # Color code by level
            if log[1] == "ERROR":
                for col in range(5):
                    self.logs_table.item(row, col).setBackground(QColor(248, 215, 218))
            elif log[1] == "WARNING":
                for col in range(5):
                    self.logs_table.item(row, col).setBackground(QColor(255, 243, 205))
        
        # Populate trends display
        trends_text = """Monthly User Signups:
        
2023-02: ████████████████████ 156
2023-03: ████████████████████████ 189
2023-04: ████████████████████████████ 234
2023-05: ████████████████████████████████ 267
2023-06: ████████████████████████████████████ 298
2023-07: ████████████████████████████████████████ 312
2023-08: ████████████████████████████████████████████ 345
2023-09: ████████████████████████████████████████████████ 378
2023-10: ████████████████████████████████████████████████████ 401
2023-11: ████████████████████████████████████████████████████████ 423
2023-12: ████████████████████████████████████████████████████████████ 445
2024-01: ████████████████████████████████████████████████████████████████ 467"""
        
        self.trends_display.setText(trends_text)
        
        # Populate API test results
        api_results = [
            ("GROQ AI API", "OK", "0.45s", "Status Code: 200"),
            ("Plaid Sandbox", "OK", "1.23s", "Status Code: 200"),
            ("Currency API", "OK", "0.78s", "Status Code: 200"),
            ("Database", "OK", "0.12s", "Connection: Active"),
            ("Cache Service", "WARNING", "2.15s", "Response time slow"),
            ("Email Service", "OK", "0.89s", "Status Code: 200")
        ]
        
        self.api_results_table.setRowCount(len(api_results))
        for row, result in enumerate(api_results):
            self.api_results_table.setItem(row, 0, QTableWidgetItem(result[0]))
            
            status_item = QTableWidgetItem(result[1])
            if result[1] == "OK":
                status_item.setBackground(QColor(212, 237, 218))
            else:
                status_item.setBackground(QColor(255, 243, 205))
            
            self.api_results_table.setItem(row, 1, status_item)
            self.api_results_table.setItem(row, 2, QTableWidgetItem(result[2]))
            self.api_results_table.setItem(row, 3, QTableWidgetItem(result[3]))
        
        # Populate user search results
        demo_users = [
            ("1001", "john_doe", "john@example.com", "End User", "2023-01-15", "2024-01-15 09:30"),
            ("1002", "jane_smith", "jane@example.com", "End User", "2023-02-20", "2024-01-14 16:45"),
            ("1003", "admin_user", "admin@pennywise.com", "Admin", "2023-01-01", "2024-01-15 10:15"),
            ("1004", "sarah_wilson", "sarah@example.com", "End User", "2023-03-10", "2024-01-13 14:22"),
            ("1005", "mike_brown", "mike@example.com", "End User", "2023-04-05", "2024-01-12 11:30"),
            ("1006", "lisa_davis", "lisa@example.com", "End User", "2023-05-18", "2024-01-11 08:45"),
            ("1007", "tech_manager", "tech@pennywise.com", "Technical Manager", "2023-01-01", "2024-01-15 10:00"),
            ("1008", "general_manager", "gm@pennywise.com", "General Manager", "2023-01-01", "2024-01-15 09:45")
        ]
        
        self.users_table.setRowCount(len(demo_users))
        for row, user in enumerate(demo_users):
            for col, data in enumerate(user):
                self.users_table.setItem(row, col, QTableWidgetItem(data))

def main():
    """Run the simple admin dashboard"""
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create admin dashboard
    admin_dash = SimpleAdminDashboard()
    admin_dash.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
