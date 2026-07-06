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


conn.commit()
conn.close()

print("Database Created Successfully")