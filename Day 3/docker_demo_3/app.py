## Stretch: connect to a PostgreSQL container and write to a table.

import psycopg2
from datetime import datetime
import time

##connect to database with retries (since the database container may not be ready when this app starts)
try:
    conn = psycopg2.connect(
        host='host.docker.internal',
        user='postgres',
        password='password',
        database='postgres'
    )
    cursor = conn.cursor()
    print("Connected to database")

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Table 'logs' ready.")

    # Insert row with current timestamp
    log_message = f"Hello docker time is {datetime.now()}"
    cursor.execute(
        f"INSERT INTO logs (message) VALUES ('{log_message}')"
    )
    conn.commit()
    print(f"Inserted: {log_message}")

    # Show all rows
    cursor.execute("SELECT * FROM logs ORDER BY created_at DESC")
    rows = cursor.fetchall()
    print("Recent logs:")
    for row in rows:
        print(f"  ID:[{row[0]}] Message:[{row[1]}] Created At:[{row[2]}]")

    cursor.close()
    conn.close()
    print("Database connection closed.")

except Exception as e:
    print(f"Error connecting to database: {e}")