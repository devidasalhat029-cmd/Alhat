from xmlrpc import client
import random
from click import prompt
from flask import Flask, render_template, request, redirect, session
import sqlite3
from groq import Groq
from os import path



app = Flask(__name__)
app.secret_key = "agrotech123"
import os

print(os.path.abspath("agriculture.db"))                                                                                                                                                                                                       
# Database Connection
def connect():
    conn = sqlite3.connect("agriculture.db")
    conn.row_factory = sqlite3.Row
    return conn



@app.route('/farmer/<int:id>')
def farmer_profile(id):
    conn = connect()
    farmer = conn.execute("SELECT * FROM farmers WHERE id=?", (id,)).fetchone()
    conn.close()
    if farmer is None:
        return "Farmer not found", 404
    prompt = f"""
    Farmer's Name: {farmer['name']}     
    Farmer's Email: {farmer['username']}
    Please write a short and simple email to the farmer about the
    Automatic Agriculture Monitoring System.
    """

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="mixtral-8x7b-32768",
    )
    tip = response.choices[0].message.content
    return render_template('farmer_profile.html', farmer=farmer, tip=tip)

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

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
            session['user'] = user['name']
            return redirect('/dashboard')

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

    if 'user' not in session:
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
        username=session['user'],
        farmers_name=session['user'],
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

# Farmer Profile
@app.route('/farmer')
def farmer():

    if 'user' not in session:
        return redirect('/login')

    farmer = {
        "name": session['user']
    }

    return render_template('farmer.html', farmer=farmer)
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

    if 'user' not in session:
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

    if 'user' not in session:
        return redirect('/login')

    return render_template('weather.html')

# Motor Control
@app.route('/motor', methods=['GET', 'POST'])
def motor():

    if 'user' not in session:
        return redirect('/login')

    if 'motor_status' not in session:
        session['motor_status'] = False

    if request.method == "POST":

        action = request.form.get("action")

        if action == "start":
            session['motor_status'] = True
            motor = "ON"
            irrigation = "Running"

        elif action == "stop":
            session['motor_status'] = False
            motor = "OFF"
            irrigation = "Stopped"


        # Sensor Record Save
        conn = sqlite3.connect("agriculture.db")
        cur = conn.cursor()

        moisture = f"{random.randint(40,80)}%"
        temperature = f"{random.randint(24,36)}°C"
        humidity = f"{random.randint(50,90)}%"

        cur.execute("""
        INSERT INTO sensor_record
        (moisture, temperature, humidity, motor_status, irrigation_status)
        VALUES (?,?,?,?,?)
        """,
        (
           moisture,
           temperature,
           humidity,
           motor,
           irrigation
        ))
        conn.commit()
        conn.close()


    return render_template(
        "motor.html",
        status=session['motor_status']
    )
#live_farm
@app.route('/live_farm')
def livefarm():

    if 'user' not in session:
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

    if 'user' not in session:
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


#update data

# Analytics
@app.route('/analytics')
def analytics():

    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    # Motor ON Count
    cur.execute("SELECT COUNT(*) FROM sensor_record WHERE motor_status='ON'")
    motor_on = cur.fetchone()[0]

    # Motor OFF Count
    cur.execute("SELECT COUNT(*) FROM sensor_record WHERE motor_status='OFF'")
    motor_off = cur.fetchone()[0]

    # Last 10 Sensor Records
    cur.execute("""
        SELECT moisture,
               temperature,
               humidity,
               motor_status,
               irrigation_status
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
        records=records
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

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"),404


if __name__ == "__main__":
    app.run(debug=True)