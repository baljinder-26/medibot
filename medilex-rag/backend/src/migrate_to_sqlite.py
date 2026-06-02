import json
import os
import sqlite_db

JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth_db.json")

def run_migration():
    print("[START] Starting migration from JSON to SQLite...")
    
    # 1. Initialize SQLite Database Tables
    sqlite_db.init_sqlite_db()
    
    # 2. Check if JSON file exists
    if not os.path.exists(JSON_PATH):
        print(f"[WARN] No JSON database found at {JSON_PATH}. Database tables initialized empty.")
        return

    # 3. Read JSON data
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Error reading JSON database: {str(e)}")
        print("Please check if the JSON is corrupted. Attempting fallback parse...")
        # Since the file might be corrupted, let's log the error and stop.
        return

    # 4. De-duplicate users (prioritizing entries with sessions)
    unique_users = {}
    for user in raw_data.get("users", []):
        email = user.get("email")
        if not email:
            continue
        
        # Normalize email representation (strip whitespace, lowercase)
        email_clean = email.strip().lower()
        user["email"] = email_clean
        
        # If email not yet seen, or if new entry has active sessions while current stored one has none
        if email_clean not in unique_users:
            unique_users[email_clean] = user
        else:
            existing_sessions = unique_users[email_clean].get("sessions", [])
            new_sessions = user.get("sessions", [])
            if len(new_sessions) > len(existing_sessions):
                unique_users[email_clean] = user

    # 5. Insert into SQLite
    migrated_count = 0
    errors_count = 0
    
    for email, user in unique_users.items():
        try:
            # We check if user already exists in SQLite to avoid inserting duplicates on re-runs
            if sqlite_db.get_user_by_email(email):
                print(f"[SKIP] User {email} already exists in SQLite. Skipping.")
                continue
                
            sqlite_db.create_user_db(
                username=user.get("username"),
                email=email,
                password=user.get("password"),
                height=user.get("height", "N/A"),
                weight=user.get("weight", "N/A"),
                bmi=user.get("bmi", "N/A"),
                sessions=user.get("sessions", [])
            )
            print(f"[SUCCESS] Migrated user: {email} with {len(user.get('sessions', []))} sessions.")
            migrated_count += 1
        except Exception as ex:
            print(f"[ERROR] Failed to migrate user {email}: {str(ex)}")
            errors_count += 1

    print("\n[SUMMARY] Migration Summary:")
    print(f"   - Total unique users in JSON: {len(unique_users)}")
    print(f"   - Successfully migrated: {migrated_count}")
    print(f"   - Errors encountered: {errors_count}")

if __name__ == "__main__":
    run_migration()
