from xmlrpc import client
from datetime import datetime
import random
import json
from click import prompt
from flask import Flask, render_template, request, redirect, session
import requests          # Request for Wether Api
import sqlite3
from groq import Groq
from os import path
from dotenv import load_dotenv
import os
load_dotenv()


app = Flask(__name__)
app.secret_key = "agrotech123"
import os

print(os.path.abspath("agriculture.db"))                                                                                                                                                                                                       
# Database Connection
def connect():
    conn = sqlite3.connect("agriculture.db")
    conn.row_factory = sqlite3.Row
    return conn
# Home Page
@app.route('/')
def home():
    return render_template('home.html')


@app.route("/farmer")
def farmer_profile():

    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM farmers WHERE username=?",
        (session["username"],)
    )

    farmer = cur.fetchone()

    conn.close()

    return render_template(
        "farmer.html",
        farmer=farmer
    )

@app.route("/edit_profile", methods=["GET","POST"])
def edit_profile():

    if "username" not in session:
        return redirect("/edit_profile")

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    if request.method == "POST":

        name = request.form["name"]
        mobile = request.form["mobile"]
        village = request.form["village"]

        cur.execute("""
        UPDATE farmers
        SET name=?, mobile=?, village=?
        WHERE username=?
        """,
        (name, mobile, village, session["username"]))

        conn.commit()
        conn.close()

        return redirect("/farmer")


    cur.execute(
        "SELECT * FROM farmers WHERE username=?",
        (session["username"],)
    )

    farmer = cur.fetchone()

    conn.close()

    return render_template(
        "edit_profile.html",
        farmer=farmer
    )
# Register
@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        mobile = request.form['mobile']
        village = request.form['village']
        username = request.form['username']
        password = request.form['password']

        conn = connect()

        conn.execute("""
        INSERT INTO farmers
        (name,mobile,village,username,password)
        VALUES(?,?,?,?,?)
        """,(name,mobile,village,username,password))

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = connect()

        user = conn.execute("""
        SELECT * FROM farmers
        WHERE username=? AND password=?
        """,(username,password)).fetchone()

        conn.close()

        if user:
            session['username'] = user['username']
            return redirect('/farmer')

        else:
            return "Invalid Username or Password"

    return render_template('login.html')

@app.route("/motor/on")
def motor_on():

    session["motor_status"] = True

    return redirect("/dashboard")


@app.route("/motor/off")
def motor_off():

    session["motor_status"] = False

    return redirect("/dashboard")    


# Dashboard
@app.route('/dashboard')
def dashboard():

    if 'username' not in session:
        return redirect('/login')

    conn = connect()

    total_farmers = conn.execute(
        "SELECT COUNT(*) FROM farmers"
    ).fetchone()[0]

    total_crops = conn.execute(
        "SELECT COUNT(*) FROM crop"
    ).fetchone()[0]

    conn.close()

    # Demo Weather Data
    weather = {
        "temp": 28,
        "humidity": 65,
        "wind": 12,
        "condition": "Sunny"
    }

    if 'motor_status' not in session:
        session['motor_status'] = False

    return render_template(
        "dashboard.html",
        username=session['username'],
        farmers_name=session['username'],
        farmers_email="farmer@gmail.com",
        total_farmers=total_farmers,
        total_crops=total_crops,
        weather=weather,
        motor_status=session['motor_status'],
        temperature=28,
        humidity=65,
        moisture=45,
        city="Hingoli",
        wind="12 km/h"
    )


 # Replace only the search route in your existing app.py

@app.route('/search', methods=['GET', 'POST'])
def search():

    records = []

    if request.method == "POST":

        search = request.form['search']

        conn = connect()

        records = conn.execute("""
        SELECT * FROM crop
        WHERE crop_name LIKE ?
        OR season LIKE ?
        """, ('%' + search + '%', '%' + search + '%')).fetchall()

        conn.close()

    return render_template("serch_page.html", records=records)


# Crop Management (Read)
@app.route('/crop')
def crop():

    if 'username' not in session:
        return redirect('/login')

    conn = connect()
    data = conn.execute("SELECT * FROM crop").fetchall()
    conn.close()

    return render_template("crop.html", data=data)


# Create
@app.route('/add_crop', methods=['POST'])
def add_crop():

    crop_name = request.form['crop_name']
    season = request.form['season']

    conn = connect()

    conn.execute(
        "INSERT INTO crop(crop_name,season) VALUES(?,?)",
        (crop_name, season)
    )

    conn.commit()
    conn.close()

    return redirect('/crop')


# Update
@app.route('/edit_crop/<int:id>', methods=['GET','POST'])
def edit_crop(id):

    conn = connect()

    if request.method == 'POST':

        crop_name = request.form['crop_name']
        season = request.form['season']

        conn.execute(
            "UPDATE crop SET crop_name=?, season=? WHERE id=?",
            (crop_name, season, id)
        )

        conn.commit()
        conn.close()

        return redirect('/crop')

    crop = conn.execute(
        "SELECT * FROM crop WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template("edit_crop.html", crop=crop)


# Delete
@app.route('/delete_crop/<int:id>')
def delete_crop(id):

    conn = connect()

    conn.execute(
        "DELETE FROM crop WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/crop')


# Weather Forecast
@app.route('/weather')
def weather():

    API_KEY = os.getenv("My API_key")   

    city = "Hingoli"

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    response = requests.get(url)

    data = response.json()

    weather_data = {
        "city": data["name"],
        "temperature": round(data["main"]["temp"]),
        "humidity": data["main"]["humidity"],
        "wind": data["wind"]["speed"],
        "condition": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"]
    }

    return render_template("weather.html", weather=weather_data)

# Motor Control
@app.route("/motor", methods=["GET", "POST"])
def motor():

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    if request.method == "POST":

        action = request.form.get("action")

        moisture = f"{random.randint(40,80)}%"
        temperature = f"{random.randint(24,36)}°C"
        humidity = f"{random.randint(50,90)}%"

        if action == "start":

            session["motor_status"] = True
            session["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Save Motor ON record
            cur.execute("""
            INSERT INTO sensor_record
            (moisture, temperature, humidity, motor_status,
             irrigation_status, start_time)
            VALUES (?,?,?,?,?,?)
            """,
            (
                moisture,
                temperature,
                humidity,
                "ON",
                "Running",
                session["start_time"]
            ))

            conn.commit()

            conn.close()
            return redirect("/motor")

        elif action == "stop":

            session["motor_status"] = False

            if "start_time" in session:

                end = datetime.now()

                start = datetime.strptime(
                    session["start_time"],
                    "%Y-%m-%d %H:%M:%S"
                )

                duration = str(end - start)

                # Save Motor OFF record
                cur.execute("""
                INSERT INTO sensor_record
                (moisture, temperature, humidity, motor_status,
                 irrigation_status, start_time, end_time, duration)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    moisture,
                    temperature,
                    humidity,
                    "OFF",
                    "Completed",
                    session["start_time"],
                    end.strftime("%Y-%m-%d %H:%M:%S"),
                    duration
                ))

                conn.commit()

                session.pop("start_time", None)

            conn.close()
            return redirect("/motor")

    status = session.get("motor_status", False)

    conn.close()

    return render_template(
        "motor.html",
        status=status
    )
    
#live_farm
@app.route('/live_farm')
def livefarm():

    
    if 'username' not in session:
        return redirect('/login')

    return render_template(
        "live_farm.html",
        status=session.get('motor_status', False)
    )
# Records
@app.route('/records')
def record():

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM sensor_record ORDER BY id DESC")

    records = cur.fetchall()

    conn.close()

    return render_template("records.html", records=records)


#irrigation
@app.route('/irrigation', methods=['GET','POST'])
def irrigation():

    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    if request.method == "POST":

        crop_name = request.form["crop_name"]
        water_time = request.form["water_time"]
        duration = request.form["duration"]

        cur.execute("""
        INSERT INTO irrigation_schedule
        (crop_name, water_time, duration, status)
        VALUES(?,?,?,?)
        """,(crop_name, water_time, duration, "Scheduled"))

        conn.commit()

    cur.execute("SELECT * FROM irrigation_schedule ORDER BY id DESC")

    records = cur.fetchall()

    conn.close()

    return render_template("irrigation.html", records=records)

# Analytics
@app.route('/analytics')
def analytics():

    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    # Motor ON Count
    cur.execute("SELECT COUNT(*) FROM sensor_record WHERE motor_status='ON'")
    motor_on = cur.fetchone()[0]

    # Motor OFF Count
    cur.execute("SELECT COUNT(*) FROM sensor_record WHERE motor_status='OFF'")
    motor_off = cur.fetchone()[0]

    # Total Running Time
    cur.execute("""
        SELECT duration
        FROM sensor_record
        WHERE duration IS NOT NULL
    """)

    times = cur.fetchall()

    total_seconds = 0

    for t in times:
        try:
            h, m, s = t[0].split(":")
            total_seconds += int(h) * 3600 + int(m) * 60 + int(float(s))
        except:
            pass

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    total_time = f"{hours} Hr {minutes} Min {seconds} Sec"

    # Last 10 Records
    cur.execute("""
    SELECT duration
    FROM sensor_record
    WHERE motor_status='OFF'
    ORDER BY id
    """)

    rows = cur.fetchall()

    graph_labels = []
    graph_data = []

    count = 1

    for row in rows:
        if row[0]:
            try:
                h, m, s = row[0].split(":")
                seconds = int(h) * 3600 + int(m) * 60 + int(float(s))

                graph_labels.append(f"Run {count}")
                graph_data.append(seconds)

                count += 1
            except:
                pass
    cur.execute("""
        SELECT moisture,
               temperature,
               humidity,
               motor_status,
               irrigation_status,
               id
        FROM sensor_record
        ORDER BY id DESC
        LIMIT 10
    """)

    records = cur.fetchall()

    conn.close()

    return render_template(

    "analytics.html",
    motor_on=motor_on,
    motor_off=motor_off,
    total_time=total_time,
    records=records,
    graph_labels=json.dumps(graph_labels),
    graph_data=json.dumps(graph_data)
)

# Logout
@app.route('/logout')
def logout():

    
    session.clear()

    return redirect('/')
@app.route('/delete_record/<int:id>')
def delete_record(id):
    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM sensor_record WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect('/records')
@app.route('/delete_irrigation/<int:id>')
def delete_irrigation(id):

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM irrigation_schedule WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect('/irrigation')
@app.route('/edit_irrigation/<int:id>', methods=['GET', 'POST'])
def edit_irrigation(id):

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    if request.method == "POST":

        crop_name = request.form["crop_name"]
        water_time = request.form["water_time"]
        duration = request.form["duration"]

        cur.execute("""
        UPDATE irrigation_schedule
        SET crop_name=?,
            water_time=?,
            duration=?
        WHERE id=?w
        """,(crop_name, water_time, duration, id))

        conn.commit()
        conn.close()

        return redirect('/irrigation')

    cur.execute(
        "SELECT * FROM irrigation_schedule WHERE id=?",
        (id,)
    )

    data = cur.fetchone()

    conn.close()

    return render_template(
        "edit_irrigation.html",
        data=data
    )
@app.route("/remove_record/<int:id>")
def remove_record(id):
    conn = sqlite3.connect("agriculture.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM sensor_record WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/analytics")

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"),404


if __name__ == "__main__":
    app.run(debug=True)