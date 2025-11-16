# PennyWise Application Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PENNYWISE v2.0 APPLICATION                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   LOGIN UI      │    │  MAIN DASHBOARD │    │  SETTINGS    │ │
│  │                 │    │                 │    │              │ │
│  │ • Authentication│    │ • Financial     │    │ • Themes     │ │
│  │ • User Signup   │    │   Overview      │    │ • Currency   │ │
│  │ • Password      │    │ • Penny AI     │    │ • Language   │ │
│  │   Management    │    │ • Transactions  │    │ • Notifications│ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           │                       │                       │     │
│           └───────────────────────┼───────────────────────┘     │
│                                   │                             │
│  ┌─────────────────────────────────┼─────────────────────────────┐ │
│  │            CORE SERVICES LAYER  │                             │ │
│  │                                 │                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │
│  │  │   PENNY     │  │   PLAID     │  │  COMMITMENT │          │ │
│  │  │   AI BRAIN  │  │   API       │  │  MANAGER    │          │ │
│  │  │             │  │             │  │             │          │ │
│  │  │ • Personality│  │ • Bank      │  │ • Recurring │          │ │
│  │  │ • Emotional │  │   Connection│  │   Payments  │          │ │
│  │  │   Intelligence│  │ • Real-time │  │ • Due Date  │          │ │
│  │  │ • Context   │  │   Sync      │  │   Tracking  │          │ │
│  │  │   Awareness │  │ • Transaction│  │ • Auto-pay  │          │ │
│  │  │ • GROQ API  │  │   Import    │  │   Processing│          │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │
│  │  │   THEME     │  │   CURRENCY  │  │   BUDGET    │          │ │
│  │  │   MANAGER   │  │   CONVERTER │  │   SYSTEM    │          │ │
│  │  │             │  │             │  │             │          │ │
│  │  │ • Dark/Light│  │ • Multi-    │  │ • Category  │          │ │
│  │  │   Modes     │  │   Currency  │  │   Budgets   │          │ │
│  │  │ • Custom    │  │   Support   │  │ • Progress  │          │ │
│  │  │   Colors    │  │ • Real-time │  │   Tracking  │          │ │
│  │  │ • Responsive│  │   Rates     │  │ • Alerts    │          │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                   │                             │
│  ┌─────────────────────────────────┼─────────────────────────────┐ │
│  │            DATA LAYER           │                             │ │
│  │                                 │                             │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │                SQLITE DATABASE                         │ │ │
│  │  │                                                         │ │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ │ │
│  │  │  │    USERS    │  │ TRANSACTIONS│  │  CATEGORIES │    │ │ │
│  │  │  │             │  │             │  │             │    │ │ │
│  │  │  │ • user_id   │  │ • amount    │  │ • name      │    │ │ │
│  │  │  │ • email     │  │ • type      │  │ • color     │    │ │ │
│  │  │  │ • username  │  │ • date      │  │ • budget    │    │ │ │
│  │  │  │ • password  │  │ • category  │  │ • user_id   │    │ │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘    │ │ │
│  │  │                                                         │ │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ │ │
│  │  │  │   ACCOUNTS  │  │  SETTINGS   │  │ COMMITMENTS │    │ │ │
│  │  │  │             │  │             │  │             │    │ │ │
│  │  │  │ • bank_name │  │ • dark_mode │  │ • amount    │    │ │ │
│  │  │  │ • type      │  │ • currency  │  │ • due_day   │    │ │ │
│  │  │  │ • balance   │  │ • language  │  │ • is_paid   │    │ │ │
│  │  │  │ • plaid_id  │  │ • theme     │  │ • category  │    │ │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘    │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL INTEGRATIONS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐                    ┌─────────────────────┐ │
│  │   GROQ AI API   │                    │   PLAID API         │ │
│  │                 │                    │                     │ │
│  │ • Financial     │                    │ • Bank Connections  │ │
│  │   Advice        │                    │ • Transaction Data  │ │
│  │ • Personalized │                    │ • Account Balances  │ │
│  │   Tips          │                    │ • Real-time Sync    │ │
│  │ • Context       │                    │ • 11,000+ Banks     │ │
│  │   Awareness     │                    │                     │ │
│  └─────────────────┘                    └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components Breakdown

### 🎨 **UI Layer Components**
- **Login Window** (`ui/login_window.py`) - 431 lines
- **Main Dashboard** (`ui/dashboard_main.py`) - 2,461 lines  
- **User Dashboard** (`ui/dashboard_user.py`) - 773 lines
- **Enhanced Penny Widget** (`ui/components/enhanced_penny_widget.py`) - 408 lines
- **Settings Window** - Complete customization system

### 🧠 **AI & Intelligence**
- **Penny Personality Engine** - Emotional intelligence system
- **GROQ API Integration** - Fast AI responses
- **Context-Aware Prompts** - Personalized recommendations
- **Mood-Based Responses** - Adapts to user financial state

### 🏦 **Financial Features**
- **Multi-Account Management** - Checking, savings, investment
- **Transaction Tracking** - Real-time categorization
- **Budget Management** - Category-based with visual progress
- **Commitment Tracking** - Recurring payment management
- **Currency Support** - Multi-currency with real-time conversion

### 🔒 **Security & Data**
- **SQLite Database** - 15+ tables with proper relationships
- **Password Hashing** - bcrypt encryption
- **Secure API Calls** - Encrypted communication
- **Data Validation** - Input sanitization and validation

## Screenshot Recommendations

### 📸 **Suggested Screenshots for Presentation**

1. **Main Dashboard View**
   - File: `ui/dashboard_main.py` (lines 1-100)
   - Shows: Modern UI with financial overview cards, Penny AI widget, navigation sidebar

2. **Penny AI Assistant**
   - File: `ui/components/enhanced_penny_widget.py` (lines 1-50)
   - Shows: AI personality system, emotional intelligence features

3. **Bank Integration**
   - File: `ui/bank_connect_window.py` (lines 1-50)
   - Shows: Plaid integration interface, secure bank connection flow

4. **Settings & Customization**
   - File: `ui/settings_window.py` (if exists) or settings implementation
   - Shows: Theme selection, currency options, user preferences

5. **Database Schema**
   - File: `database/schema.sql` (lines 1-50)
   - Shows: Well-structured database design with proper relationships

6. **AI Integration Code**
   - File: `core/penny_personality.py` (lines 1-50)
   - Shows: Sophisticated AI personality system implementation

7. **Financial Data Management**
   - File: `core/commitment_manager.py` (if exists)
   - Shows: Advanced financial logic and data processing

8. **Modern UI Components**
   - File: `ui/components/penny_avatar.py` (lines 1-50)
   - Shows: Custom UI components and modern design patterns






