import sqlite3

def view_database():
    # Connect to the database
    conn = sqlite3.connect('./instance/users.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tables in the database:")
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        print("-" * 50)
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Get table contents
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        print("\nData:")
        for row in rows:
            print(f"  {row}")
    
    conn.close()

if __name__ == "__main__":
    view_database() 