import sqlite3

# Function to create the database and users table
def create_db():
    conn = sqlite3.connect('iot_dashboard.db')
    cursor = conn.cursor()
    
    # Create the users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfid_tag TEXT NOT NULL UNIQUE,
        temp_threshold REAL NOT NULL,
        light_threshold REAL NOT NULL
    );
    ''')
    conn.commit()
    conn.close()

# Run the create_db function to set up the database
create_db()
