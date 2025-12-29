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
from core.maintenance_mode import get_maintenance_mode
from core.system_diagnostics import get_diagnostics
from core.workos_auth import get_workos_authenticator

class APITestWorker(QThread):
    """Worker thread for API testing"""
    test_completed = pyqtSignal(dict)
    test_progress = pyqtSignal(str, dict)  # Signal for individual test completion
    
    def __init__(self, api_name=None):
        super().__init__()
        self.api_name = api_name  # If None, test all; otherwise test specific API
        self.apis_to_test = {
            'GROQ AI': {
                'url': 'https://api.groq.com/openai/v1/chat/completions',
                'method': 'POST',
                'headers': {'Authorization': 'Bearer demo_key', 'Content-Type': 'application/json'},
                'data': {'model': 'llama2-70b-4096', 'messages': [{'role': 'user', 'content': 'test'}]}
            },
            'Plaid Sandbox': {
                'url': 'https://sandbox.plaid.com',
                'method': 'GET',
                'headers': {},
                'data': None
            },
            'Currency API': {
                'url': 'https://api.exchangerate.host/latest',
                'method': 'GET',
                'headers': {},
                'data': {'base': 'USD'}  # Parameters for the API
            }
        }
    
    def run(self):
        results = {}
        apis_to_test = {self.api_name: self.apis_to_test[self.api_name]} if self.api_name else self.apis_to_test
        
        for api_name, config in apis_to_test.items():
            start_time = __import__('time').time()
            try:
                url = config['url']
                method = config['method']
                headers = config['headers']
                data = config['data']
                
                if method == 'POST':
                    response = requests.post(url, headers=headers, json=data, timeout=10)
                else:
                    # For GET requests, use params if data is provided (for currency API)
                    params = data if data else None
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                
                elapsed_ms = (__import__('time').time() - start_time) * 1000
                
                # Determine success based on status code
                is_success = response.status_code in [200, 201] or (api_name == 'GROQ AI' and response.status_code == 401)
                
                result = {
                    'status': 'Success' if is_success else 'Fail',
                    'response_time': elapsed_ms,
                    'status_code': response.status_code,
                    'details': f"Status Code: {response.status_code}"
                }
                
                if not is_success:
                    result['details'] = f"Status Code: {response.status_code} - Request failed"
                
                results[api_name] = result
                
                # Emit progress for individual test completion
                self.test_progress.emit(api_name, result)
                
            except requests.exceptions.Timeout:
                elapsed_ms = (__import__('time').time() - start_time) * 1000
                results[api_name] = {
                    'status': 'Fail',
                    'response_time': elapsed_ms,
                    'details': 'Timeout: Request exceeded 10 seconds'
                }
                self.test_progress.emit(api_name, results[api_name])
                
            except requests.exceptions.ConnectionError:
                elapsed_ms = (__import__('time').time() - start_time) * 1000
                results[api_name] = {
                    'status': 'Fail',
                    'response_time': elapsed_ms,
                    'details': 'Connection Error: Unable to reach server'
                }
                self.test_progress.emit(api_name, results[api_name])
                
            except Exception as e:
                elapsed_ms = (__import__('time').time() - start_time) * 1000
                error_msg = str(e)[:100]  # Limit error message length
                results[api_name] = {
                    'status': 'Fail',
                    'response_time': elapsed_ms,
                    'details': f'Error: {error_msg}'
                }
                self.test_progress.emit(api_name, results[api_name])
        
        self.test_completed.emit(results)

class AdminDashboard(QMainWindow):
    """Admin Dashboard for Technical Managers"""
    
    def __init__(self, user_id, username):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.api_worker = None
        self.diagnostics_worker = None
        self.maintenance_mode = get_maintenance_mode()
        self.diagnostics = get_diagnostics()
        
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
        self.create_user_stats_tab()
        self.create_api_testing_tab()
        self.create_system_controls_tab()
        self.create_diagnostics_tab()
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
        self.total_users_label = self.create_stat_card("Total Users", "0", "#007bff")
        self.monthly_signups_label = self.create_stat_card("This Month", "0", "#28a745")
        self.active_users_label = self.create_stat_card("Active Users", "0", "#ffc107")
        self.new_today_label = self.create_stat_card("New Today", "0", "#17a2b8")
        
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
        layout.setSpacing(15)
        
        # Test controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        test_all_btn = QPushButton("🧪 Test All APIs")
        test_all_btn.clicked.connect(self.test_all_apis)
        test_all_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background: #cccccc;
            }
        """)
        
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        self.test_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #6f42c1;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #6f42c1;
            }
        """)
        
        controls_layout.addWidget(test_all_btn)
        controls_layout.addWidget(self.test_progress)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # API test results table
        self.api_results_table = QTableWidget()
        self.api_results_table.setColumnCount(4)
        self.api_results_table.setHorizontalHeaderLabels([
            "API Name", "Status", "Response Time (ms)", "Details"
        ])
        self.api_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.api_results_table.setAlternatingRowColors(True)
        self.api_results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.api_results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.api_results_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background: white;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        # Initialize table with API names
        self.api_names = ['GROQ AI', 'Plaid Sandbox', 'Currency API']
        self.api_results_table.setRowCount(len(self.api_names))
        for row, api_name in enumerate(self.api_names):
            self.api_results_table.setItem(row, 0, QTableWidgetItem(api_name))
            self.api_results_table.setItem(row, 1, QTableWidgetItem("Not Tested"))
            self.api_results_table.setItem(row, 2, QTableWidgetItem("-"))
            self.api_results_table.setItem(row, 3, QTableWidgetItem("Click 'Test All APIs' to run tests"))
            
            # Make API name clickable for individual testing
            name_item = self.api_results_table.item(row, 0)
            name_item.setForeground(QColor(0, 102, 204))
            name_item.setToolTip("Click to test this API individually")
        
        # Connect double-click to test individual API
        self.api_results_table.cellDoubleClicked.connect(self.test_individual_api)
        
        layout.addWidget(self.api_results_table)
        
        # Status label
        self.api_status_label = QLabel("Ready to test APIs")
        self.api_status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        layout.addWidget(self.api_status_label)
        
        self.tab_widget.addTab(api_widget, "🔌 API Testing")
    
    def create_system_controls_tab(self):
        """Create system controls tab (maintenance mode, WorkOS health)"""
        controls_widget = QWidget()
        layout = QVBoxLayout(controls_widget)
        layout.setSpacing(20)
        
        # Emergency Shutdown Section
        shutdown_frame = QFrame()
        shutdown_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #dc3545;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        shutdown_layout = QVBoxLayout(shutdown_frame)
        
        shutdown_title = QLabel("🚨 Emergency Shutdown / Maintenance Mode")
        shutdown_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        shutdown_title.setStyleSheet("color: #dc3545;")
        shutdown_layout.addWidget(shutdown_title)
        
        shutdown_desc = QLabel(
            "When enabled, all end users will see a maintenance screen. "
            "Admins can still access the dashboard."
        )
        shutdown_desc.setWordWrap(True)
        shutdown_desc.setStyleSheet("color: #666; margin: 10px 0;")
        shutdown_layout.addWidget(shutdown_desc)
        
        # Maintenance mode status
        status_layout = QHBoxLayout()
        status_label = QLabel("Current Status:")
        status_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.maintenance_status_label = QLabel()
        self.maintenance_status_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.maintenance_status_label)
        status_layout.addStretch()
        shutdown_layout.addLayout(status_layout)
        
        # Toggle buttons
        button_layout = QHBoxLayout()
        self.enable_maintenance_btn = QPushButton("Enable Maintenance Mode")
        self.enable_maintenance_btn.clicked.connect(self.enable_maintenance_mode)
        self.enable_maintenance_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #c82333;
            }
            QPushButton:disabled {
                background: #cccccc;
            }
        """)
        
        self.disable_maintenance_btn = QPushButton("Disable Maintenance Mode")
        self.disable_maintenance_btn.clicked.connect(self.disable_maintenance_mode)
        self.disable_maintenance_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #218838;
            }
            QPushButton:disabled {
                background: #cccccc;
            }
        """)
        
        button_layout.addWidget(self.enable_maintenance_btn)
        button_layout.addWidget(self.disable_maintenance_btn)
        button_layout.addStretch()
        shutdown_layout.addLayout(button_layout)
        
        # Update status after buttons are created
        self.update_maintenance_status()
        
        layout.addWidget(shutdown_frame)
        
        # WorkOS Health Check Section
        workos_frame = QFrame()
        workos_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        workos_layout = QVBoxLayout(workos_frame)
        
        workos_title = QLabel("🔐 WorkOS Auth Service Health")
        workos_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        workos_layout.addWidget(workos_title)
        
        workos_desc = QLabel(
            "Check WorkOS API connectivity and configuration without performing OAuth."
        )
        workos_desc.setWordWrap(True)
        workos_desc.setStyleSheet("color: #666; margin: 10px 0;")
        workos_layout.addWidget(workos_desc)
        
        # WorkOS status display
        self.workos_status_label = QLabel("Click 'Check WorkOS Status' to test")
        self.workos_status_label.setStyleSheet("color: #6c757d; font-style: italic; padding: 10px;")
        workos_layout.addWidget(self.workos_status_label)
        
        # Check button
        check_workos_btn = QPushButton("Check WorkOS Status")
        check_workos_btn.clicked.connect(self.check_workos_health)
        check_workos_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        workos_layout.addWidget(check_workos_btn)
        
        layout.addWidget(workos_frame)
        layout.addStretch()
        
        self.tab_widget.addTab(controls_widget, "⚙️ System Controls")
    
    def create_diagnostics_tab(self):
        """Create system diagnostics tab"""
        diag_widget = QWidget()
        layout = QVBoxLayout(diag_widget)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("🔍 System Diagnostics")
        header_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(header_label)
        
        desc_label = QLabel(
            "Diagnostic checks to help identify if issues are external (services, internet) "
            "or internal (database, threads, UI)."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # Run diagnostics button
        run_diag_btn = QPushButton("🔄 Run All Diagnostics")
        run_diag_btn.clicked.connect(self.run_diagnostics)
        run_diag_btn.setStyleSheet("""
            QPushButton {
                background: #6f42c1;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #5a32a3;
            }
        """)
        layout.addWidget(run_diag_btn)
        
        # Diagnostics results display
        self.diagnostics_table = QTableWidget()
        self.diagnostics_table.setColumnCount(3)
        self.diagnostics_table.setHorizontalHeaderLabels([
            "Check", "Status", "Details"
        ])
        self.diagnostics_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.diagnostics_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.diagnostics_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.diagnostics_table.setAlternatingRowColors(True)
        self.diagnostics_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.diagnostics_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background: white;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.diagnostics_table)
        
        # Last exception display
        exception_frame = QFrame()
        exception_frame.setStyleSheet("""
            QFrame {
                background: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        exception_layout = QVBoxLayout(exception_frame)
        
        exception_title = QLabel("⚠️ Last Uncaught Exception")
        exception_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        exception_layout.addWidget(exception_title)
        
        self.exception_label = QLabel("No exceptions recorded")
        self.exception_label.setWordWrap(True)
        self.exception_label.setStyleSheet("color: #856404;")
        exception_layout.addWidget(self.exception_label)
        
        layout.addWidget(exception_frame)
        
        self.tab_widget.addTab(diag_widget, "🔬 Diagnostics")
    
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
        self.load_user_statistics()
        self.load_user_search_results()
        self.update_maintenance_status()
    
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
            QMessageBox.warning(self, "Test in Progress", "API tests are already running. Please wait.")
            return
        
        # Reset table
        for row in range(self.api_results_table.rowCount()):
            self.api_results_table.setItem(row, 1, QTableWidgetItem("Testing..."))
            self.api_results_table.setItem(row, 2, QTableWidgetItem("-"))
            self.api_results_table.setItem(row, 3, QTableWidgetItem("Running test..."))
            self.api_results_table.item(row, 1).setBackground(QColor(255, 255, 255))
        
        self.test_progress.setVisible(True)
        self.test_progress.setRange(0, 0)  # Indeterminate progress
        self.api_status_label.setText("Testing all APIs...")
        self.api_status_label.setStyleSheet("color: #6f42c1; font-weight: bold;")
        
        self.api_worker = APITestWorker()
        self.api_worker.test_completed.connect(self.on_api_test_completed)
        self.api_worker.test_progress.connect(self.on_api_test_progress)
        self.api_worker.start()
    
    def test_individual_api(self, row, col):
        """Test individual API when row is double-clicked"""
        if col != 0:  # Only trigger on API name column
            return
        
        if self.api_worker and self.api_worker.isRunning():
            QMessageBox.warning(self, "Test in Progress", "API tests are already running. Please wait.")
            return
        
        api_name = self.api_results_table.item(row, 0).text()
        
        # Update row to show testing
        self.api_results_table.setItem(row, 1, QTableWidgetItem("Testing..."))
        self.api_results_table.setItem(row, 2, QTableWidgetItem("-"))
        self.api_results_table.setItem(row, 3, QTableWidgetItem("Running test..."))
        self.api_results_table.item(row, 1).setBackground(QColor(255, 255, 255))
        
        self.test_progress.setVisible(True)
        self.test_progress.setRange(0, 0)
        self.api_status_label.setText(f"Testing {api_name}...")
        self.api_status_label.setStyleSheet("color: #6f42c1; font-weight: bold;")
        
        self.api_worker = APITestWorker(api_name=api_name)
        self.api_worker.test_completed.connect(self.on_api_test_completed)
        self.api_worker.test_progress.connect(self.on_api_test_progress)
        self.api_worker.start()
    
    def on_api_test_progress(self, api_name, result):
        """Handle individual API test completion (real-time updates)"""
        # Find row for this API
        for row in range(self.api_results_table.rowCount()):
            if self.api_results_table.item(row, 0).text() == api_name:
                # Update status
                status_item = QTableWidgetItem(result['status'])
                if result['status'] == 'Success':
                    status_item.setBackground(QColor(212, 237, 218))  # Light green
                    status_item.setForeground(QColor(0, 100, 0))
                else:
                    status_item.setBackground(QColor(248, 215, 218))  # Light red
                    status_item.setForeground(QColor(139, 0, 0))
                
                self.api_results_table.setItem(row, 1, status_item)
                
                # Update response time (in milliseconds)
                response_time_ms = result.get('response_time', 0)
                self.api_results_table.setItem(row, 2, QTableWidgetItem(f"{response_time_ms:.2f}"))
                
                # Update details
                details = result.get('details', 'No details available')
                self.api_results_table.setItem(row, 3, QTableWidgetItem(details))
                break
    
    def on_api_test_completed(self, results):
        """Handle API test completion"""
        self.test_progress.setVisible(False)
        
        # Update all results
        for api_name, result in results.items():
            for row in range(self.api_results_table.rowCount()):
                if self.api_results_table.item(row, 0).text() == api_name:
                    # Update status
                    status_item = QTableWidgetItem(result['status'])
                    if result['status'] == 'Success':
                        status_item.setBackground(QColor(212, 237, 218))  # Light green
                        status_item.setForeground(QColor(0, 100, 0))
                    else:
                        status_item.setBackground(QColor(248, 215, 218))  # Light red
                        status_item.setForeground(QColor(139, 0, 0))
                    
                    self.api_results_table.setItem(row, 1, status_item)
                    
                    # Update response time (in milliseconds)
                    response_time_ms = result.get('response_time', 0)
                    self.api_results_table.setItem(row, 2, QTableWidgetItem(f"{response_time_ms:.2f}"))
                    
                    # Update details
                    details = result.get('details', 'No details available')
                    self.api_results_table.setItem(row, 3, QTableWidgetItem(details))
                    break
        
        # Count successes (results are dicts, so .get() is fine)
        success_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get('status') == 'Success')
        total_count = len(results)
        
        self.api_status_label.setText(f"Testing completed: {success_count}/{total_count} APIs successful")
        if success_count == total_count:
            self.api_status_label.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.api_status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        
        self.statusBar().showMessage(f"API testing completed: {success_count}/{total_count} successful")
    
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
    
    def update_maintenance_status(self):
        """Update the maintenance mode status display"""
        is_enabled = self.maintenance_mode.is_enabled()
        if is_enabled:
            self.maintenance_status_label.setText("ENABLED")
            self.maintenance_status_label.setStyleSheet("color: #dc3545;")
            self.enable_maintenance_btn.setEnabled(False)
            self.disable_maintenance_btn.setEnabled(True)
        else:
            self.maintenance_status_label.setText("DISABLED")
            self.maintenance_status_label.setStyleSheet("color: #28a745;")
            self.enable_maintenance_btn.setEnabled(True)
            self.disable_maintenance_btn.setEnabled(False)
    
    def enable_maintenance_mode(self):
        """Enable maintenance mode"""
        reply = QMessageBox.question(
            self,
            "Enable Maintenance Mode",
            "This will block all end users from accessing PennyWise.\n\n"
            "Admins will still be able to access the dashboard.\n\n"
            "Are you sure you want to enable maintenance mode?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.maintenance_mode.enable():
                self.update_maintenance_status()
                QMessageBox.information(
                    self,
                    "Maintenance Mode Enabled",
                    "Maintenance mode has been enabled. End users will now see the maintenance screen."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to enable maintenance mode. Check logs for details."
                )
    
    def disable_maintenance_mode(self):
        """Disable maintenance mode"""
        if self.maintenance_mode.disable():
            self.update_maintenance_status()
            QMessageBox.information(
                self,
                "Maintenance Mode Disabled",
                "Maintenance mode has been disabled. End users can now access PennyWise normally."
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Failed to disable maintenance mode. Check logs for details."
            )
    
    def check_workos_health(self):
        """Check WorkOS API health"""
        self.workos_status_label.setText("Checking WorkOS status...")
        self.workos_status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        
        # Run check in a thread to avoid blocking UI
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self._perform_workos_check)
    
    def _perform_workos_check(self):
        """Perform the actual WorkOS health check"""
        try:
            result = self.diagnostics.check_workos_health()
            
            status = result['status']
            details = result['details']
            response_time = result.get('response_time_ms', 0)
            
            if status == 'healthy':
                status_text = f"✅ HEALTHY - {details}"
                if response_time > 0:
                    status_text += f" (Response time: {response_time:.2f}ms)"
                self.workos_status_label.setText(status_text)
                self.workos_status_label.setStyleSheet("color: #28a745; font-weight: bold; padding: 10px;")
            elif status == 'degraded':
                status_text = f"⚠️ DEGRADED - {details}"
                if response_time > 0:
                    status_text += f" (Response time: {response_time:.2f}ms)"
                self.workos_status_label.setText(status_text)
                self.workos_status_label.setStyleSheet("color: #ffc107; font-weight: bold; padding: 10px;")
            else:  # unreachable
                status_text = f"❌ UNREACHABLE - {details}"
                self.workos_status_label.setText(status_text)
                self.workos_status_label.setStyleSheet("color: #dc3545; font-weight: bold; padding: 10px;")
                
        except Exception as e:
            self.workos_status_label.setText(f"❌ Error checking WorkOS: {str(e)[:200]}")
            self.workos_status_label.setStyleSheet("color: #dc3545; font-weight: bold; padding: 10px;")
    
    def run_diagnostics(self):
        """Run all diagnostic checks"""
        self.diagnostics_table.setRowCount(0)
        self.diagnostics_table.setRowCount(6)  # 5 checks + header
        
        # Show loading state
        loading_item = QTableWidgetItem("Running diagnostics...")
        self.diagnostics_table.setItem(0, 0, loading_item)
        
        # Run diagnostics in background
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self._perform_diagnostics)
    
    def _perform_diagnostics(self):
        """Perform all diagnostic checks"""
        try:
            results = self.diagnostics.run_all_checks()
            
            row = 0
            
            # External checks
            external_label = QTableWidgetItem("External Services")
            external_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.diagnostics_table.setItem(row, 0, external_label)
            row += 1
            
            # WorkOS
            workos_result = results['external']['workos']
            self._add_diagnostic_row(row, "WorkOS API", workos_result)
            row += 1
            
            # Internet
            internet_result = results['external']['internet']
            self._add_diagnostic_row(row, "Internet Connectivity", internet_result)
            row += 1
            
            # Internal checks
            internal_label = QTableWidgetItem("Internal Systems")
            internal_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.diagnostics_table.setItem(row, 0, internal_label)
            row += 1
            
            # Database
            db_result = results['internal']['database']
            self._add_diagnostic_row(row, "Database", db_result)
            row += 1
            
            # Threads
            thread_result = results['internal']['threads']
            self._add_diagnostic_row(row, "Background Threads", thread_result)
            row += 1
            
            # UI
            ui_result = results['internal']['ui']
            self._add_diagnostic_row(row, "UI Event Loop", ui_result)
            
            # Last exception
            last_exception = results.get('last_exception')
            if last_exception:
                exception_text = (
                    f"Type: {last_exception['exception_type']}\n"
                    f"Message: {last_exception['message']}\n"
                    f"Time: {last_exception.get('timestamp', 'Unknown')}"
                )
                self.exception_label.setText(exception_text)
            else:
                self.exception_label.setText("No exceptions recorded")
            
            self.statusBar().showMessage("Diagnostics completed")
            
        except Exception as e:
            QMessageBox.warning(self, "Diagnostics Error", f"Failed to run diagnostics: {str(e)}")
    
    def _add_diagnostic_row(self, row, check_name, result):
        """Add a diagnostic result row to the table"""
        # Check name
        name_item = QTableWidgetItem(check_name)
        self.diagnostics_table.setItem(row, 0, name_item)
        
        # Status
        status = result.get('status', 'unknown')
        status_item = QTableWidgetItem(status.upper())
        
        if status == 'healthy':
            status_item.setBackground(QColor(212, 237, 218))  # Light green
            status_item.setForeground(QColor(0, 100, 0))
        elif status == 'degraded':
            status_item.setBackground(QColor(255, 243, 205))  # Light yellow
            status_item.setForeground(QColor(133, 100, 4))
        else:  # unreachable
            status_item.setBackground(QColor(248, 215, 218))  # Light red
            status_item.setForeground(QColor(139, 0, 0))
        
        self.diagnostics_table.setItem(row, 1, status_item)
        
        # Details
        details = result.get('details', 'No details available')
        response_time = result.get('response_time_ms')
        if response_time is not None:
            details += f" ({response_time:.2f}ms)"
        
        details_item = QTableWidgetItem(details)
        self.diagnostics_table.setItem(row, 2, details_item)

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






