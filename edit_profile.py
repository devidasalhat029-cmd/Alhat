import sqlite3

conn = sqlite3.connect("agriculture.db")
cursor = conn.cursor()

cursor.execute("""
ALTER TABLE farmers
ADD COLUMN photo TEXT
""")

conn.commit()
conn.close()

print("Photo column added successfully")
