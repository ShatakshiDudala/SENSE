import hashlib
import sqlite3
import streamlit as st
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database file path
AUTH_DB_PATH = "sense_auth.db"

def create_auth_database():
    """Create authentication database and tables"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'manager', 'operator')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Create default admin user if not exists
        admin_password_hash = hash_password("admin123")
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', ("admin", admin_password_hash, "admin"))
        
        # Create default manager user
        manager_password_hash = hash_password("manager123")
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', ("manager", manager_password_hash, "manager"))
        
        # Create default operator user
        operator_password_hash = hash_password("operator123")
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', ("operator", operator_password_hash, "operator"))
        
        conn.commit()
        conn.close()
        
        logger.info("Authentication database created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating auth database: {e}")
        return False

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

def authenticate_user(username, password):
    """Authenticate user credentials"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, password_hash, role, is_active
            FROM users
            WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        
        if result:
            user_id, password_hash, role, is_active = result
            
            if not is_active:
                logger.warning(f"Inactive user attempted login: {username}")
                conn.close()
                return False
            
            if verify_password(password, password_hash):
                # Update last login time
                cursor.execute('''
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (user_id,))
                
                conn.commit()
                conn.close()
                
                logger.info(f"Successful login: {username} ({role})")
                return True
            else:
                logger.warning(f"Invalid password for user: {username}")
        else:
            logger.warning(f"User not found: {username}")
        
        conn.close()
        return False
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False

def get_user_role(username):
    """Get user role by username"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role
            FROM users
            WHERE username = ? AND is_active = TRUE
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
        
    except Exception as e:
        logger.error(f"Error getting user role: {e}")
        return None

def get_user_info(username):
    """Get complete user information"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, role, created_at, last_login, is_active
            FROM users
            WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'role': result[2],
                'created_at': result[3],
                'last_login': result[4],
                'is_active': result[5]
            }
        return None
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return None

def create_user(username, password, role):
    """Create new user"""
    try:
        if role not in ['admin', 'manager', 'operator']:
            logger.error(f"Invalid role: {role}")
            return False
        
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute('''
            SELECT username FROM users WHERE username = ?
        ''', (username,))
        
        if cursor.fetchone():
            logger.warning(f"Username already exists: {username}")
            conn.close()
            return False
        
        # Create new user
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', (username, password_hash, role))
        
        conn.commit()
        conn.close()
        
        logger.info(f"User created successfully: {username} ({role})")
        return True
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False

def update_user_role(username, new_role):
    """Update user role"""
    try:
        if new_role not in ['admin', 'manager', 'operator']:
            logger.error(f"Invalid role: {new_role}")
            return False
        
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET role = ?
            WHERE username = ?
        ''', (new_role, username))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            logger.info(f"Role updated for user {username}: {new_role}")
            return True
        else:
            conn.close()
            logger.warning(f"User not found for role update: {username}")
            return False
        
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        return False

def deactivate_user(username):
    """Deactivate user account"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET is_active = FALSE
            WHERE username = ?
        ''', (username,))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            logger.info(f"User deactivated: {username}")
            return True
        else:
            conn.close()
            logger.warning(f"User not found for deactivation: {username}")
            return False
        
    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        return False

def activate_user(username):
    """Activate user account"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET is_active = TRUE
            WHERE username = ?
        ''', (username,))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            logger.info(f"User activated: {username}")
            return True
        else:
            conn.close()
            logger.warning(f"User not found for activation: {username}")
            return False
        
    except Exception as e:
        logger.error(f"Error activating user: {e}")
        return False

def change_password(username, old_password, new_password):
    """Change user password"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        # Verify old password
        cursor.execute('''
            SELECT password_hash
            FROM users
            WHERE username = ? AND is_active = TRUE
        ''', (username,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            logger.warning(f"User not found for password change: {username}")
            return False
        
        if not verify_password(old_password, result[0]):
            conn.close()
            logger.warning(f"Invalid old password for user: {username}")
            return False
        
        # Update password
        new_password_hash = hash_password(new_password)
        cursor.execute('''
            UPDATE users
            SET password_hash = ?
            WHERE username = ?
        ''', (new_password_hash, username))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Password changed successfully for user: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return False

def get_all_users():
    """Get all users (admin only)"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, role, created_at, last_login, is_active
            FROM users
            ORDER BY created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        users = []
        for result in results:
            users.append({
                'username': result[0],
                'role': result[1],
                'created_at': result[2],
                'last_login': result[3],
                'is_active': result[4]
            })
        
        return users
        
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

def get_user_stats():
    """Get user statistics"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Active users
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = TRUE')
        active_users = cursor.fetchone()[0]
        
        # Users by role
        cursor.execute('''
            SELECT role, COUNT(*) 
            FROM users 
            WHERE is_active = TRUE 
            GROUP BY role
        ''')
        role_counts = dict(cursor.fetchall())
        
        # Recent logins (last 7 days)
        cursor.execute('''
            SELECT COUNT(*) 
            FROM users 
            WHERE last_login >= datetime('now', '-7 days')
        ''')
        recent_logins = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'role_counts': role_counts,
            'recent_logins': recent_logins
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {}

def check_permission(username, required_role):
    """Check if user has required permission level"""
    role_hierarchy = {
        'operator': 1,
        'manager': 2,
        'admin': 3
    }
    
    user_role = get_user_role(username)
    
    if not user_role:
        return False
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def log_user_activity(username, activity, details=""):
    """Log user activity"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        # Create activity log table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                activity TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO user_activity_log (username, activity, details)
            VALUES (?, ?, ?)
        ''', (username, activity, details))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")
        return False

def get_user_activity_log(username=None, limit=100):
    """Get user activity log"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        if username:
            cursor.execute('''
                SELECT username, activity, details, timestamp
                FROM user_activity_log
                WHERE username = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (username, limit))
        else:
            cursor.execute('''
                SELECT username, activity, details, timestamp
                FROM user_activity_log
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        activities = []
        for result in results:
            activities.append({
                'username': result[0],
                'activity': result[1],
                'details': result[2],
                'timestamp': result[3]
            })
        
        return activities
        
    except Exception as e:
        logger.error(f"Error getting activity log: {e}")
        return []

# Initialize authentication database
def initialize_auth():
    """Initialize authentication system"""
    try:
        success = create_auth_database()
        if success:
            logger.info("Authentication system initialized successfully")
        return success
    except Exception as e:
        logger.error(f"Failed to initialize authentication system: {e}")
        return False

# Initialize when module is imported
if __name__ == "__main__":
    initialize_auth()
else:
    # Auto-initialize when imported
    initialize_auth()