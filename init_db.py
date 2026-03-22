import sqlite3

conn = sqlite3.connect("database.db")

conn.execute('''
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT,
    role TEXT)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS jobs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    employer TEXT)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS applications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    job_id INTEGER,
    resume TEXT,
    parsed_text TEXT,
    status TEXT DEFAULT 'Applied',
    interview_date TEXT)
''')

conn.commit()
conn.close()

print("Database Ready ")