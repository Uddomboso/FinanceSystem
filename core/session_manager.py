"""
Session Management for PennyWise
Handles token storage in memory and SQLite with lifetime management
"""

import sqlite3
import os
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from core.config import Config
from database.db_manager import connect_db, execute_query, fetch_one, fetch_all


class SessionManager:
    """Manages user sessions with token storage and lifetime handling"""
    
    def __init__(self):
        self.memory_sessions: Dict[str, Dict[str, Any]] = {}
        self.driver = Config.SESSION_DRIVER
        self.lifetime_minutes = Config.SESSION_LIFETIME
        self.encrypt = Config.SESSION_ENCRYPT
        self._ensure_sessions_table()
        self._cleanup_expired_sessions()
    
    def _ensure_sessions_table(self):
        """Create sessions table if it doesn't exist"""
        try:
            execute_query("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    token TEXT NOT NULL,
                    user_info TEXT,
                    role TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """, commit=True)
            
            # Create index for faster lookups
            execute_query("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
                ON sessions(user_id)
            """)
            
            execute_query("""
                CREATE INDEX IF NOT EXISTS idx_sessions_expires_at 
                ON sessions(expires_at)
            """)
        except Exception as e:
            print(f"Error creating sessions table: {e}")
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions from database"""
        try:
            execute_query("""
                DELETE FROM sessions 
                WHERE expires_at < datetime('now')
            """, commit=True)
        except Exception as e:
            print(f"Error cleaning up expired sessions: {e}")
    
    def create_session(self, user_id: int, token: str, user_info: Dict[str, Any], role: str) -> str:
        """Create a new session and return session ID"""
        session_id = f"session_{user_id}_{int(time.time())}"
        expires_at = datetime.now() + timedelta(minutes=self.lifetime_minutes)
        
        session_data = {
            'user_id': user_id,
            'token': token,
            'user_info': user_info,
            'role': role,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat()
        }
        
        # Store in memory if driver is memory or for short-lived sessions
        if self.driver == 'memory' or self.lifetime_minutes < 60:
            self.memory_sessions[session_id] = session_data
        
        # Always store in database for persistence
        try:
            execute_query("""
                INSERT INTO sessions (session_id, user_id, token, user_info, role, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                token,
                json.dumps(user_info),
                role,
                expires_at.isoformat()
            ), commit=True)
        except Exception as e:
            print(f"Error storing session in database: {e}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data by session ID"""
        # Check memory first
        if session_id in self.memory_sessions:
            session = self.memory_sessions[session_id]
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.now() < expires_at:
                return session
            else:
                # Expired, remove from memory
                del self.memory_sessions[session_id]
        
        # Check database
        try:
            result = fetch_one("""
                SELECT * FROM sessions 
                WHERE session_id = ? AND expires_at > datetime('now')
            """, (session_id,))
            
            if result:
                session = {
                    'user_id': result['user_id'],
                    'token': result['token'],
                    'user_info': json.loads(result['user_info']) if result['user_info'] else {},
                    'role': result['role'],
                    'created_at': result['created_at'],
                    'expires_at': result['expires_at']
                }
                return session
        except Exception as e:
            print(f"Error retrieving session from database: {e}")
        
        return None
    
    def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get the most recent active session for a user"""
        try:
            result = fetch_one("""
                SELECT * FROM sessions 
                WHERE user_id = ? AND expires_at > datetime('now')
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            if result:
                return {
                    'session_id': result['session_id'],
                    'user_id': result['user_id'],
                    'token': result['token'],
                    'user_info': json.loads(result['user_info']) if result['user_info'] else {},
                    'role': result['role'],
                    'created_at': result['created_at'],
                    'expires_at': result['expires_at']
                }
        except Exception as e:
            print(f"Error retrieving user session: {e}")
        
        return None
    
    def delete_session(self, session_id: str):
        """Delete a session by ID"""
        # Remove from memory
        if session_id in self.memory_sessions:
            del self.memory_sessions[session_id]
        
        # Remove from database
        try:
            execute_query("""
                DELETE FROM sessions WHERE session_id = ?
            """, (session_id,), commit=True)
        except Exception as e:
            print(f"Error deleting session: {e}")
    
    def delete_user_sessions(self, user_id: int):
        """Delete all sessions for a user (logout)"""
        # Remove from memory
        to_remove = [sid for sid, sess in self.memory_sessions.items() 
                    if sess['user_id'] == user_id]
        for sid in to_remove:
            del self.memory_sessions[sid]
        
        # Remove from database
        try:
            execute_query("""
                DELETE FROM sessions WHERE user_id = ?
            """, (user_id,), commit=True)
        except Exception as e:
            print(f"Error deleting user sessions: {e}")
    
    def is_session_valid(self, session_id: str) -> bool:
        """Check if a session is still valid"""
        session = self.get_session(session_id)
        return session is not None


# Global session manager instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

