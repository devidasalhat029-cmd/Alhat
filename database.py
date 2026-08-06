import sqlite3


# =========================================================
# DATABASE CONNECTION
# =========================================================

conn = sqlite3.connect("agriculture.db")

cursor = conn.cursor()


# =========================================================
# FARMERS
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS farmers(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,

    mobile TEXT NOT NULL,

    village TEXT NOT NULL,

    username TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL,

    role TEXT DEFAULT 'farmer',

    photo TEXT DEFAULT 'default.png'

)
""")


# =========================================================
# CROP
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS crop(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    crop_name TEXT,

    season TEXT,

    crop_type TEXT,

    sowing_date TEXT

)
""")


# =========================================================
# CHECK EXISTING CROP COLUMNS
# =========================================================

cursor.execute("""
PRAGMA table_info(crop)
""")

crop_columns = [
    row[1]
    for row in cursor.fetchall()
]


# =========================================================
# ADD crop_type IF MISSING
# =========================================================

if "crop_type" not in crop_columns:

    cursor.execute("""
    ALTER TABLE crop
    ADD COLUMN crop_type TEXT
    """)


# =========================================================
# ADD sowing_date IF MISSING
# =========================================================

if "sowing_date" not in crop_columns:

    cursor.execute("""
    ALTER TABLE crop
    ADD COLUMN sowing_date TEXT
    """)


# =========================================================
# SENSOR RECORD
# =========================================================

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


# =========================================================
# IRRIGATION SCHEDULE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS irrigation_schedule(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    crop_name TEXT,

    water_time TEXT,

    duration TEXT,

    status TEXT

)
""")


# =========================================================
# FEEDBACK
# =========================================================

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


# =========================================================
# DEFAULT ADMIN
# =========================================================

cursor.execute(
    "SELECT * FROM farmers WHERE username=?",
    ("admin",)
)

admin = cursor.fetchone()


if admin is None:

    cursor.execute("""
    INSERT INTO farmers
    (
        name,
        mobile,
        village,
        username,
        password,
        role,
        photo
    )

    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (

        "Administrator",

        "9999999999",

        "Office",

        "admin",

        "admin123",

        "admin",

        "default.png"

    ))


# =========================================================
# SAVE DATABASE
# =========================================================

conn.commit()


# =========================================================
# CLOSE DATABASE
# =========================================================

conn.close()


print("✅ Database Created Successfully")
print("✅ Crop table checked successfully")
print("✅ crop_type and sowing_date columns checked")
print("✅ Admin account checked")