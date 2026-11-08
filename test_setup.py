import sqlite3 
import os

def main():
    db_path = "data/Chinook_Sqlite.sqlite"
    
    if not os.path.exists(db_path):
        print(f"Error: Could not find database at {db_path}")
        return

    # 1. Connect to the database file
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. Query the hidden SQLite system table that stores all table names
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    cursor.execute(query)
    
    tables = cursor.fetchall()
    
    print("Successfully connected! Here are the tables:")
    for table in tables:
        print(f"- {table[0]}")
        
    conn.close()

if __name__ == "__main__":
    main()