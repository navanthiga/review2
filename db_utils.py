# db_utils.py
import sqlite3
import hashlib
import datetime
import os
import json

def get_db_connection():
    """Create a connection to the SQLite database"""
    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect('data/learning_platform.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # Create activity_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity_type TEXT NOT NULL,
        activity_details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create videos_watched table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS videos_watched (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        completion_percentage REAL DEFAULT 0,
        last_watched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        watch_count INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create quiz_attempts table - Fix comment format
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        score INTEGER NOT NULL,
        max_score INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        question_data TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS code_challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        story TEXT NOT NULL,
        description TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        category TEXT NOT NULL,
        initial_code TEXT,
        solution_code TEXT,
        test_cases TEXT,
        hints TEXT,
        xp_reward INTEGER NOT NULL,
        badge_id TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        challenge_id INTEGER NOT NULL,
        completed BOOLEAN DEFAULT 0,
        attempts INTEGER DEFAULT 0,
        last_code TEXT,
        completed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (challenge_id) REFERENCES code_challenges (id),
        UNIQUE(user_id, challenge_id)
    )
    ''')
    
    # Commit the changes
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password, full_name=""):
    """Register a new user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hash_password(password)
    
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, full_name)
    
    )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # Username or email already exists
        success = False
    finally:
        conn.close()
    
    return success

def authenticate_user(username, password):
    """Check if username and password match"""
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hash_password(password)
    
    cursor.execute(
        "SELECT id, username, email, full_name FROM users WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    )
    user = cursor.fetchone()
    
    if user:
        # Update last login time
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.datetime.now(), user['id'])
        )
        conn.commit()
        
        # Log login activity
        log_activity(user['id'], "login")
    
    conn.close()
    return dict(user) if user else None

def log_activity(user_id, activity_type, activity_details=None):
    """Log user activity in the database with error handling"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Convert activity_details to string if it's not already
        if activity_details is not None and not isinstance(activity_details, str):
            try:
                # Try to convert to JSON string if it's a dict or list
                activity_details = json.dumps(activity_details)
            except:
                # If that fails, convert to string representation
                activity_details = str(activity_details)
        
        # Insert activity log
        cursor.execute(
            """
            INSERT INTO activity_logs (user_id, activity_type, activity_details, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, activity_type, activity_details, datetime.datetime.now().isoformat())
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        try:
            conn.close()
        except:
            pass
        return False

def log_video_watched(user_id, topic, completion_percentage=100):
    """Log when a user watches a video"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if this video was watched before
    cursor.execute(
        "SELECT id, watch_count FROM videos_watched WHERE user_id = ? AND topic = ?",
        (user_id, topic)
    )
    existing = cursor.fetchone()
    
    if existing:
        # Update existing record
        cursor.execute(
            """UPDATE videos_watched 
               SET completion_percentage = ?, last_watched = ?, watch_count = ? 
               WHERE id = ?""",
            (completion_percentage, datetime.datetime.now(), existing['watch_count'] + 1, existing['id'])
        )
    else:
        # Create new record
        cursor.execute(
            "INSERT INTO videos_watched (user_id, topic, completion_percentage) VALUES (?, ?, ?)",
            (user_id, topic, completion_percentage)
        )
    
    conn.commit()
    conn.close()
    
    # Log the activity
    details = {
        "topic": topic,
        "completion_percentage": completion_percentage
    }
    log_activity(user_id, "video_watched", details)

def log_quiz_attempt(user_id, topic, score, max_score, question_data):
    """Log quiz attempt details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if isinstance(question_data, dict) or isinstance(question_data, list):
        question_data = json.dumps(question_data)
    
    cursor.execute(
        """INSERT INTO quiz_attempts 
           (user_id, topic, score, max_score, question_data) 
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, topic, score, max_score, question_data)
    )
    
    conn.commit()
    conn.close()
    
    # Log the activity
    details = {
        "topic": topic,
        "score": score,
        "max_score": max_score
    }
    log_activity(user_id, "quiz_attempt", details)

def get_user_progress(user_id):
    """Get a summary of the user's learning progress"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get videos watched
    cursor.execute(
        "SELECT topic, completion_percentage, watch_count FROM videos_watched WHERE user_id = ?",
        (user_id,)
    )
    videos_watched = [dict(row) for row in cursor.fetchall()]
    
    # Get quiz performance
    cursor.execute(
        """SELECT topic, AVG(score * 100.0 / max_score) as avg_percentage, 
           COUNT(*) as attempt_count, MAX(score) as high_score
           FROM quiz_attempts 
           WHERE user_id = ? 
           GROUP BY topic""",
        (user_id,)
    )
    quiz_performance = [dict(row) for row in cursor.fetchall()]
    
    # Get recent activities
    cursor.execute(
        """SELECT activity_type, activity_details, timestamp 
           FROM activity_logs 
           WHERE user_id = ? 
           ORDER BY timestamp DESC LIMIT 10""",
        (user_id,)
    )
    recent_activities = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "videos_watched": videos_watched,
        "quiz_performance": quiz_performance,
        "recent_activities": recent_activities
    }
def init_chatbot_db():
    """Initialize database tables for the chatbot"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chatbot_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chatbot_user_time
            ON chatbot_interactions (user_id, timestamp)
        """)
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error initializing chatbot database: {e}")
        return False
    
# Add these new functions to db_utils.py

def get_user_stats(user_id):
    """Get comprehensive user statistics including XP and level"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate total XP from activities
    cursor.execute("""
        SELECT 
            COUNT(*) as total_activities,
            SUM(CASE 
                WHEN activity_type = 'challenge_completed' THEN json_extract(activity_details, '$.xp_reward')
                WHEN activity_type = 'daily_challenge_completed' THEN json_extract(activity_details, '$.xp_reward')
                ELSE 0 
            END) as total_xp
        FROM activity_logs
        WHERE user_id = ?
    """, (user_id,))
    
    stats = cursor.fetchone()
    
    if not stats:
        return {
            "level": 1,
            "xp": 0,
            "total_activities": 0,
            "badges": []
        }
    
    # Calculate level (1 level per 100 XP)
    level = 1 + (stats['total_xp'] or 0) // 100
    
    # Get earned badges
    cursor.execute("""
        SELECT json_extract(activity_details, '$.badge_id') as badge_id
        FROM activity_logs
        WHERE user_id = ? AND activity_type = 'badge_earned'
    """, (user_id,))
    
    badges = [row['badge_id'] for row in cursor.fetchall() if row['badge_id']]
    
    conn.close()
    
    return {
        "level": level,
        "xp": stats['total_xp'] or 0,
        "total_activities": stats['total_activities'] or 0,
        "badges": badges
    }

def get_user_challenges_progress(user_id):
    """Get all challenges progress for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            c.id, c.title, c.difficulty, c.category, c.xp_reward, c.badge_id,
            uc.completed, uc.attempts, uc.completed_at
        FROM code_challenges c
        LEFT JOIN user_challenges uc ON c.id = uc.challenge_id AND uc.user_id = ?
        ORDER BY c.difficulty, c.id
    """, (user_id,))
    
    challenges = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return challenges

def update_user_challenge(user_id, challenge_id, completed=False, code=None):
    """Update or create a user challenge record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if record exists
    cursor.execute("""
        SELECT id FROM user_challenges
        WHERE user_id = ? AND challenge_id = ?
    """, (user_id, challenge_id))
    
    existing = cursor.fetchone()
    
    if existing:
        # Update existing record
        cursor.execute("""
            UPDATE user_challenges
            SET attempts = attempts + 1,
                completed = ?,
                last_code = ?,
                completed_at = CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE completed_at END
            WHERE id = ?
        """, (completed, code, completed, existing['id']))
    else:
        # Create new record
        cursor.execute("""
            INSERT INTO user_challenges
            (user_id, challenge_id, completed, attempts, last_code, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            challenge_id,
            completed,
            1,  # first attempt
            code,
            datetime.datetime.now().isoformat() if completed else None
        ))
    
    conn.commit()
    conn.close()
    return True

def init_challenges_tables():
    """Initialize the challenge-specific tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create code_challenges table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                story TEXT NOT NULL,
                description TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                category TEXT NOT NULL,
                initial_code TEXT,
                solution_code TEXT,
                test_cases TEXT,
                hints TEXT,
                xp_reward INTEGER NOT NULL,
                badge_id TEXT
            )
        ''')
        
        # Create user_challenges table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                challenge_id INTEGER NOT NULL,
                completed BOOLEAN DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                last_code TEXT,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (challenge_id) REFERENCES code_challenges (id),
                UNIQUE(user_id, challenge_id)
            )
        ''')
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        return False
    finally:
        conn.close()

def migrate_challenges_tables():
    """Migrate existing tables if needed"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if test_cases column exists
        cursor.execute("PRAGMA table_info(code_challenges)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'test_cases' not in columns:
            print("Adding missing test_cases column...")
            cursor.execute("ALTER TABLE code_challenges ADD COLUMN test_cases TEXT")
            conn.commit()
            print("Migration complete!")
        return True
    except sqlite3.Error as e:
        print(f"Migration error: {e}")
        return False
    finally:
        conn.close()