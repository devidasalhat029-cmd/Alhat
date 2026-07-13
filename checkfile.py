import sqlite3

conn = sqlite3.connect("agriculture.db")
cur = conn.cursor()

cur.execute("""
SELECT motor_status, COUNT(*)
FROM sensor_record
GROUP BY motor_status
""")

print(cur.fetchall())

conn.close()