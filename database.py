import sqlite3

conn = sqlite3.connect("database.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    location TEXT,
    status TEXT
)
""")

# Default users
try:
    conn.execute("INSERT INTO users (username,password,role) VALUES ('admin','admin123','admin')")
    conn.execute("INSERT INTO users (username,password,role) VALUES ('staff','staff123','staff')")
except:
    pass

conn.commit()
conn.close()

print("Database Ready")