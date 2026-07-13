import sqlite3

conn = sqlite3.connect("agriculture.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE sensor_record ADD COLUMN moisture TEXT")

conn.commit()
conn.close()

print("Column added successfully")