import sqlite3
import json
import os
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth_db.sqlite3")

def get_db_connection():
    """Returns a connection to the SQLite database with dictionary rows."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite_db():
    """Initializes the SQLite tables if they do not exist."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    height TEXT DEFAULT 'N/A',
                    weight TEXT DEFAULT 'N/A',
                    bmi TEXT DEFAULT 'N/A'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER NOT NULL,
                    user_email TEXT NOT NULL,
                    title TEXT NOT NULL,
                    messages TEXT NOT NULL,
                    PRIMARY KEY (user_email, id),
                    FOREIGN KEY (user_email) REFERENCES users (email) ON DELETE CASCADE
                )
            """)
        print("[SUCCESS] SQLite database tables initialized successfully.")
    finally:
        conn.close()

def get_user_by_email(email: str):
    """Fetches a complete user dict including their sessions from the database."""
    conn = get_db_connection()
    try:
        user_row = conn.execute(
            "SELECT email, username, password, height, weight, bmi FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        
        if not user_row:
            return None
            
        session_rows = conn.execute(
            "SELECT id, title, messages FROM sessions WHERE user_email = ? ORDER BY id DESC",
            (email,)
        ).fetchall()
        
        sessions = []
        for s in session_rows:
            try:
                messages_list = json.loads(s["messages"])
            except Exception:
                messages_list = []
                
            sessions.append({
                "id": s["id"],
                "title": s["title"],
                "messages": messages_list
            })
            
        return {
            "username": user_row["username"],
            "email": user_row["email"],
            "password": user_row["password"],
            "height": user_row["height"],
            "weight": user_row["weight"],
            "bmi": user_row["bmi"],
            "sessions": sessions
        }
    finally:
        conn.close()

def create_user_db(username, email, password, height="N/A", weight="N/A", bmi="N/A", sessions=None):
    """Creates a new user record and their default or provided sessions."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO users (email, username, password, height, weight, bmi) VALUES (?, ?, ?, ?, ?, ?)",
                (email, username, password, height, weight, bmi)
            )
            
            if not sessions:
                sessions = [{
                    "id": int(time.time() * 1000),
                    "title": "New Chat",
                    "messages": []
                }]
                
            for session in sessions:
                conn.execute(
                    "INSERT INTO sessions (id, user_email, title, messages) VALUES (?, ?, ?, ?)",
                    (session["id"], email, session["title"], json.dumps(session.get("messages", [])))
                )
        return get_user_by_email(email)
    finally:
        conn.close()

def update_user_db(email, username=None, password=None, height=None, weight=None, bmi=None, sessions=None):
    """Updates user information and/or overwrites session history atomically."""
    conn = get_db_connection()
    try:
        with conn:
            # 1. Update user fields if provided
            update_fields = []
            params = []
            if username is not None:
                update_fields.append("username = ?")
                params.append(username)
            if password is not None:
                update_fields.append("password = ?")
                params.append(password)
            if height is not None:
                update_fields.append("height = ?")
                params.append(height)
            if weight is not None:
                update_fields.append("weight = ?")
                params.append(weight)
            if bmi is not None:
                update_fields.append("bmi = ?")
                params.append(bmi)
                
            if update_fields:
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE email = ?"
                params.append(email)
                conn.execute(query, tuple(params))
                
            # 2. Overwrite sessions if provided
            if sessions is not None:
                # Delete existing sessions
                conn.execute("DELETE FROM sessions WHERE user_email = ?", (email,))
                # Insert new sessions list
                for session in sessions:
                    conn.execute(
                        "INSERT INTO sessions (id, user_email, title, messages) VALUES (?, ?, ?, ?)",
                        (session["id"], email, session["title"], json.dumps(session.get("messages", [])))
                    )
        return get_user_by_email(email)
    finally:
        conn.close()
