import sqlite3
conn = sqlite3.connect("agriculture.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS farmers(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT,
      mobile TEXT,
      village TEXT,
      username TEXT,
      password TEXT
)
  """)


cursor.execute("""
CREATE TABLE IF NOT EXISTS crop(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name TEXT,
    season TEXT
 )
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sensor_record(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature REAL,
    humidity REAL,
    soil_moisture REAL,
    motor_status TEXT,
    irrigation_status TEXT,
    date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS irrigation_schedule(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name TEXT,
    water_time TEXT,
    duration TEXT,
    status TEXT
)
""")

conn.commit()
conn.close()

print("Database Created Successfully")