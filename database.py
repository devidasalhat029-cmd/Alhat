import sqlite3

conn = sqlite3.connect("agriculture.db")
cursor = conn.cursor()

# -------------------------
# Farmers
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS farmers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mobile TEXT NOT NULL,
    village TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    photo TEXT DEFAULT 'default.png'
)
""")

# -------------------------
# Crop
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS crop(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name TEXT,
    season TEXT
)
""")

# -------------------------
# Sensor Record
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS sensor_record(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature TEXT,
    humidity TEXT,
    soil_moisture TEXT,
    moisture TEXT,
    motor_status TEXT,
    irrigation_status TEXT,
    start_time TEXT,
    end_time TEXT,
    duration TEXT,
    date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# -------------------------
# Irrigation Schedule
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS irrigation_schedule(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name TEXT,
    water_time TEXT,
    duration TEXT,
    status TEXT
)
""")

# -------------------------
# Feedback
# -------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    rating INTEGER,
    experience TEXT,
    message TEXT,
    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("✅ Database Created Successfully")