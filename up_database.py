import sqlite3

conn = sqlite3.connect("agriculture.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE sensor_record ADD COLUMN start_time TEXT")
cursor.execute("ALTER TABLE sensor_record ADD COLUMN end_time TEXT")
cursor.execute("ALTER TABLE sensor_record ADD COLUMN duration TEXT")

conn.commit()
conn.close()

print("Database Updated Successfully")