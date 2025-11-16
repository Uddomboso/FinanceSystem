# PennyWise v2.0

<div align="center">

![PennyWise Logo](logopng.png)

**Your Intelligent Financial Companion**

*A modern, AI-powered personal finance management application built with PyQt5*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15.9-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## About PennyWise

**PennyWise** is a comprehensive personal finance management application that combines modern UI design with intelligent AI assistance. Built with PyQt5, it provides users with a beautiful, intuitive interface to manage their finances, track spending, set budgets, and receive personalized financial advice from **Penny** - your friendly AI financial companion.

### What Makes PennyWise Special?

- **AI-Powered Insights**: Get personalized financial advice powered by GROQ AI
- **Bank Integration**: Connect your bank accounts securely via Plaid API (11,000+ banks supported)
- **Real-Time Tracking**: Monitor your finances with live transaction updates and balance syncing
- **Modern UI**: Beautiful, responsive interface with dark/light themes
- **Multi-Account Support**: Manage checking, savings, and investment accounts
- **Budget Management**: Category-based budgeting with visual progress tracking
- **Smart Notifications**: Stay on top of commitments, budgets, and financial goals
- **Multi-Currency**: Support for multiple currencies with real-time conversion

---

## API Key Storage

AI and API keys are stored securely in a `.env` file located in the root directory of the project. The application uses the `python-dotenv` package to load these environment variables.

**Location**: `.env` file in the project root directory

**How it works**:
1. The `.env` file is loaded by `core/config.py` using `load_dotenv()` from the `python-dotenv` package
2. API keys are accessed via `os.getenv()` calls in the `Config` class
3. The `.env` file should never be committed to version control (it's in `.gitignore`)

**Example `.env` file structure**:
```env
GROQ_API_KEY=your_groq_api_key_here
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_BASE_URL=https://sandbox.plaid.com
```

**Security Notes**:
- The `.env` file is excluded from version control
- Keys are never hardcoded in the source code
- The application falls back to demo mode if keys are not provided
- All API communications are encrypted over HTTPS

---

## Key Features

### Penny AI Assistant
- **Emotional Intelligence**: Penny adapts to your financial mood and provides context-aware advice
- **Personality System**: Engaging, friendly AI companion that learns your spending patterns
- **Smart Suggestions**: Receive personalized tips based on your financial behavior
- **Circuit Breaker**: Robust error handling ensures reliable AI responses

### Financial Management
- **Transaction Tracking**: Automatic categorization and manual transaction entry
- **Budget System**: Set category-based budgets with visual progress indicators
- **Commitment Tracker**: Manage recurring payments and bills with due date reminders
- **Savings Goals**: Set and track savings goals with progress visualization
- **Transfer Management**: Easy transfers between accounts with Plaid integration

### Bank Integration
- **Plaid API**: Secure connection to 11,000+ financial institutions
- **Real-Time Sync**: Automatic transaction and balance updates
- **Multi-Account Support**: Manage multiple accounts from different banks
- **Demo Mode**: Test the application without real bank connections

### User Experience
- **Modern Dashboard**: Clean, intuitive interface with customizable layouts
- **Theme Support**: Light and dark modes with custom color schemes
- **Responsive Design**: Adapts to different screen sizes
- **Tutorial System**: Built-in onboarding for new users
- **Badge System**: Gamification elements to encourage good financial habits

### Analytics & Reports
- **Financial Overview**: Comprehensive dashboard with key metrics
- **Charts & Visualizations**: Interactive charts for spending analysis
- **Mood Meter**: Track your financial wellness over time
- **Export Functionality**: Export your financial data for external analysis

---

## Completed Features

### Core Functionality
- User authentication system with secure password hashing (bcrypt)
- Login and signup windows with validation
- Main dashboard with financial overview
- SQLite database with 15+ tables and proper relationships
- Database migration system for schema updates

### AI Features
- Penny AI assistant with personality system
- GROQ API integration for financial advice
- Context-aware AI responses based on user financial state
- Emotional intelligence system that adapts to user mood
- AI insights caching for performance
- Circuit breaker pattern for error handling
- AI monitoring and logging system

### Financial Management
- Transaction entry and management
- Automatic transaction categorization
- Manual transaction editing and deletion
- Transaction search and filtering
- Budget creation and management by category
- Budget progress tracking with visual indicators
- Commitment/recurring payment tracker
- Savings goals with progress visualization
- Account balance tracking
- Multi-account support (checking, savings, investment)
- Transfer management between accounts
- Plaid integration for real-time bank sync

### Bank Integration
- Plaid API integration for 11,000+ banks
- Secure bank account connection flow
- Real-time transaction synchronization
- Account balance updates
- Multi-institution support
- Demo mode with mock data
- Plaid Link web interface integration

### User Interface
- Modern dashboard with navigation sidebar
- Custom title bar with window controls
- Light and dark theme support
- Theme manager with custom color schemes
- Responsive layout system
- Custom UI components (cards, badges, metrics, progress bars)
- Enhanced Penny widget with animations
- Mood meter visualization
- Badge system for achievements
- Tutorial system for onboarding
- Settings window with comprehensive options
- Category manager
- Budget window
- Reports page
- Charts and visualizations
- Admin dashboard
- Transaction form with validation
- Transfer form
- Commitment form
- Savings goal manager

### Data & Analytics
- Financial metrics calculation
- Spending analysis
- Category-based reporting
- Export functionality
- Financial mood calculation
- Savings tracking
- Salary checking system

### Security & Data Management
- Password encryption with bcrypt
- Secure API key storage in environment variables
- Input validation and sanitization
- SQLite database with proper relationships
- Data export capabilities
- Logging system for debugging

---

## Planned Features / To-Do

### Enhanced Features
- Mobile application (iOS/Android)
- Cloud synchronization across devices
- Web application version
- Advanced investment tracking and portfolio management
- Credit score integration
- Bill reminder notifications system
- Receipt scanning and OCR integration
- Automatic recurring transaction detection
- Financial goal templates
- Debt payoff calculator and tracker
- Net worth tracking over time
- Tax preparation assistance
- Multi-language support (currently English only)
- Advanced reporting with PDF export
- Email notifications for important events
- SMS alerts for low balances
- Budget forecasting and predictions
- Financial health score
- Spending pattern analysis with ML
- Custom category icons and colors
- Transaction attachments (receipts, notes)
- Split transactions across categories
- Recurring transaction templates
- Financial calendar view
- Year-end financial summary
- Integration with more financial services
- Two-factor authentication
- Biometric login support
- Data backup and restore functionality
- Family/shared account support
- Financial advisor integration
- Automated savings rules
- Spending limit alerts
- Merchant-specific tracking
- Financial education content
- Goal-based savings recommendations

### Technical Improvements
- Unit test coverage
- Integration testing
- Performance optimization
- Database query optimization
- UI/UX improvements based on user feedback
- Accessibility improvements (screen reader support)
- Internationalization (i18n) framework
- API rate limiting improvements
- Enhanced error handling
- Better offline mode support
- Data encryption at rest
- Audit logging for sensitive operations
- Automated database backups
- Migration to newer PyQt version
- Docker containerization
- CI/CD pipeline setup
- Documentation improvements
- API documentation
- Developer guide

---

## Technology Stack

### **Frontend**
- **PyQt5** - Modern desktop application framework
- **QtAwesome** - Icon library for beautiful UI elements
- **Custom Components** - Reusable UI widgets and animations

### **Backend**
- **Python 3.8+** - Core programming language
- **SQLite** - Lightweight, embedded database
- **Flask** - Web server for Plaid Link integration

### **AI & APIs**
- **GROQ API** - Fast AI inference for financial advice
- **Plaid API** - Secure bank account integration
- **OpenAI-Compatible** - Flexible AI integration

### **Security**
- **bcrypt** - Password hashing and encryption
- **Environment Variables** - Secure API key management
- **Input Validation** - Comprehensive data sanitization

---

## Getting Started

### **Prerequisites**

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher** ([Download Python](https://www.python.org/downloads/))
- **pip** (Python package manager - usually included with Python)
- **Git** (for cloning the repository)

### **Installation Steps**

#### **1. Clone the Repository**

```bash
git clone https://github.com/yourusername/PennyWise.git
cd PennyWise
```

#### **2. Create a Virtual Environment** (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### **3. Install Dependencies**

```bash
pip install PyQt5==5.15.9
pip install PyQtWebEngine
pip install Flask
pip install python-dotenv==1.0.0
pip install requests==2.31.0
pip install bcrypt==4.0.1
pip install qtawesome
pip install typing_extensions
```

**Or install all at once:**
```bash
pip install PyQt5==5.15.9 PyQtWebEngine Flask python-dotenv==1.0.0 requests==2.31.0 bcrypt==4.0.1 qtawesome typing_extensions
```

#### **4. Configure Environment Variables**

Create a `.env` file in the root directory:

```env
# AI Configuration (Optional - app works in demo mode without this)
GROQ_API_KEY=your_groq_api_key_here

# Plaid Configuration (Optional - app works in demo mode without this)
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_BASE_URL=https://sandbox.plaid.com
```

**Note:** The application can run in **Demo Mode** without API keys, using mock data for testing purposes.

#### **5. Initialize the Database**

The database will be automatically created on first run. If you need to manually initialize:

```bash
python -c "from database.db_manager import initialize_db; initialize_db()"
```

#### **6. Run the Application**

**Windows:**
```bash
python main.py
```

**macOS/Linux:**
```bash
python3 main.py
```

Or directly:
```bash
python app_main.py
```

---

## Configuration

### **Demo Mode vs. Live Mode**

PennyWise can run in two modes:

#### **Demo Mode** (Default)
- Works without API keys
- Uses mock financial data
- Perfect for testing and development
- All features available except real bank connections

#### **Live Mode**
- Requires GROQ API key for AI features
- Requires Plaid credentials for bank integration
- Connects to real financial institutions
- Full production functionality

The application automatically detects which mode to use based on your `.env` configuration.

### **Getting API Keys**

#### **GROQ API Key** (For AI Features)
1. Visit [GROQ Console](https://console.groq.com/)
2. Sign up or log in
3. Create an API key
4. Add it to your `.env` file

#### **Plaid API Credentials** (For Bank Integration)
1. Visit [Plaid Dashboard](https://dashboard.plaid.com/)
2. Sign up for a free account
3. Get your `client_id` and `secret` from the dashboard
4. Add them to your `.env` file
5. Use sandbox mode for testing, production for live accounts

---

## Project Structure

```
PennyWise/
│
├── ai/                      # AI service layer
│   └── penny_brain.py      # Penny AI brain implementation
│
├── assets/                  # Static assets
│   └── styles/             # Stylesheets and themes
│
├── core/                    # Core business logic
│   ├── config.py           # Configuration management
│   ├── plaid_api.py        # Plaid API integration
│   ├── budget.py           # Budget management
│   ├── transactions.py     # Transaction handling
│   ├── commitment_manager.py  # Recurring payments
│   ├── penny_personality.py   # AI personality system
│   └── ...
│
├── database/                # Database layer
│   ├── db_manager.py       # Database operations
│   ├── schema.sql          # Database schema
│   └── migrations/         # Database migrations
│
├── ui/                      # User interface
│   ├── dashboard_main.py   # Main dashboard (4,915 lines)
│   ├── login_window.py     # Login/signup
│   ├── settings_window.py  # User settings
│   ├── components/         # Reusable UI components
│   │   ├── enhanced_penny_widget.py
│   │   ├── badges_widget.py
│   │   ├── mood_meter.py
│   │   └── ...
│   └── ...
│
├── app_main.py             # Application entry point
├── main.py                 # Main launcher
├── .env                    # Environment variables (create this)
└── ABOUT.md               # This file
```

---

## Usage Guide

### **First Launch**

1. **Start the Application**: Run `python main.py`
2. **Create Account**: Sign up with a username, email, and password
3. **Login**: Use your credentials to access the dashboard
4. **Tutorial**: Follow the built-in tutorial to learn the interface

### **Connecting Your Bank** (Optional)

1. Navigate to **Settings** → **Bank Connections**
2. Click **Connect Bank Account**
3. Select your bank from the list (11,000+ supported)
4. Authenticate with your bank credentials
5. Accounts will sync automatically

### **Key Features to Try**

- **Dashboard**: View your financial overview at a glance
- **Chat with Penny**: Ask financial questions and get AI-powered advice
- **Add Transactions**: Manually add or import transactions
- **Set Budgets**: Create category-based budgets
- **Track Commitments**: Manage recurring bills and payments
- **View Reports**: Analyze your spending patterns
- **Customize Theme**: Switch between light/dark modes

---

## Security & Privacy

- **Password Encryption**: All passwords are hashed using bcrypt
- **Secure API Calls**: All external API communications are encrypted
- **Local Database**: Your financial data is stored locally in SQLite
- **No Data Sharing**: Your data never leaves your machine (except for API calls you authorize)
- **Environment Variables**: API keys are stored securely in `.env` (never commit this file)

---

## Troubleshooting

### **Common Issues**

#### **Application Won't Start**
- Ensure Python 3.8+ is installed: `python --version`
- Check all dependencies are installed: `pip list`
- Verify virtual environment is activated

#### **Database Errors**
- Delete `pennywise.db` and let it recreate on next launch
- Check file permissions in the project directory

#### **Plaid Connection Issues**
- Verify your Plaid credentials in `.env`
- Check you're using the correct environment (sandbox vs. production)
- Ensure your firewall allows connections to Plaid servers

#### **AI Features Not Working**
- Verify GROQ_API_KEY is set in `.env`
- Check your internet connection
- The app will work in demo mode if API key is missing

#### **UI Rendering Issues**
- Update PyQt5: `pip install --upgrade PyQt5`
- Check your display scaling settings
- Try running with different DPI settings

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### **Development Setup**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- **Plaid** - For secure bank account integration
- **GROQ** - For fast AI inference
- **PyQt5** - For the excellent GUI framework
- **QtAwesome** - For beautiful icons

---

## Support

For questions, issues, or feature requests, please open an issue on GitHub.

---

<div align="center">

**Made for better financial management**

*PennyWise v2.0 - Your Intelligent Financial Companion*

</div>

