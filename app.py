
from xmlrpc import client
from datetime import datetime
import random
import json
from click import prompt
from flask import Flask, render_template, request, redirect, session,flash
import requests          # Request for Wether Api
import sqlite3
from groq import Groq
from os import path
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import os

load_dotenv()


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.secret_key = "agrotech123"

print(os.path.abspath("agriculture.db"))                                                                                                                                                                                                       
# Database Connection
def connect():
    conn = sqlite3.connect("agriculture.db")
    conn.row_factory = sqlite3.Row
    return conn
# Home Page
@app.route('/')
def home():
    return render_template('home1.html')
@app.route('/features')
def features():
    return render_template('features.html')



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
        return redirect("/login")

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    if request.method == "POST":

        name = request.form["name"]
        mobile = request.form["mobile"]
        village = request.form["village"]

        photo = request.files.get("photo")

        filename = None

        if photo and photo.filename:
            filename = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

            cur.execute("""
            UPDATE farmers
            SET name=?, mobile=?, village=?, photo=?
            WHERE username=?
            """,
            (name, mobile, village, filename, session["username"]))

        else:

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


    weather = {
        "temp": 28,
        "humidity": 65,
        "wind": 12,
        "condition": "Sunny"
    }


    if 'motor_status' not in session:
        session['motor_status'] = False


    # 🤖 AI Farmer Advice
    prompt = f"""
    Farmer name: {session['username']}

    Give a short farming advice for this farmer.
    Keep it simple and useful.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    ai_tip = response.choices[0].message.content


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
        wind="12 km/h",
        ai_tip=ai_tip
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

    API_KEY = os.getenv("API_KEY")   

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


    return f"Report Generated Successfully: {filename}"
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
        WHERE id=?
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

@app.route('/ai_advice')
def ai_advice():

    if 'username' not in session:
        return redirect('/login')


    temperature = 28
    humidity = 65
    moisture = 45


    prompt = f"""

You are an agriculture expert.

Farm Data:

Temperature:
{temperature} C

Humidity:
{humidity} %

Soil Moisture:
{moisture} %

Give simple farming advice.

"""


    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]

    )


    advice = response.choices[0].message.content


    return render_template(
        "ai_advice.html",
        username=session["username"],
        temperature=temperature,
        humidity=humidity,
        moisture=moisture,
        advice=advice
    )

@app.route('/ai_assistant', methods=['GET','POST'])
def ai_assistant():

    if 'username' not in session:
        return redirect('/login')


    answer = ""


    if request.method == "POST":


        question = request.form["question"]


        prompt = f"""

You are an Agriculture AI Assistant.

Farmer Name:
{session['username']}


Give simple and useful farming advice.

Help about:
- Crop selection
- Irrigation
- Fertilizer
- Weather
- Plant diseases
- Soil management


Farmer Question:

{question}

"""


        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[
                {
                    "role":"user",
                    "content":prompt
                }
            ]

        )


        answer = response.choices[0].message.content



    return render_template(

        "ai_assistant.html",

        answer=answer

    )
@app.route("/disease")
def disease():
    return render_template("disease.html")


@app.route("/predict_disease", methods=["POST"])
def predict_disease():

    file = request.files["image"]

    if file.filename == "":
        return "No file selected"

    filename = secure_filename(file.filename)

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(filepath)

    # Demo Prediction
    disease = "Tomato Early Blight"
    confidence = "98%"
    treatment = "Use recommended fungicide and remove infected leaves."

    return render_template(
    "predict_disease.html",
    image=filename,
    disease=disease,
    confidence=confidence,
    treatment=treatment
)
@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        subject = request.form["subject"]
        message = request.form["message"]

        conn = sqlite3.connect("agriculture.db")
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO contact(name,email,mobile,subject,message)
        VALUES(?,?,?,?,?)
        """,(name,email,mobile,subject,message))

        conn.commit()
        conn.close()

        flash("Message Sent Successfully!")
        return redirect("/contact")

    return render_template("contact.html")
@app.route("/feedback", methods=["GET", "POST"])
def feedback():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        rating = request.form["rating"]
        experience = request.form["experience"]
        message = request.form["message"]

        conn = sqlite3.connect("agriculture.db")
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO feedback
            (name,email,rating,experience,message)
            VALUES(?,?,?,?,?)
        """,
        (name,email,rating,experience,message))

        conn.commit()
        conn.close()

        flash("Feedback submitted successfully!", "success")

        return redirect("/feedback")

    return render_template("feedback.html")
@app.route("/feedback_dashboard")
def feedback_dashboard():

    conn = sqlite3.connect("agriculture.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM feedback 
        ORDER BY id DESC
    """)

    feedback = cur.fetchall()


    cur.execute("SELECT COUNT(*) FROM feedback")
    total = cur.fetchone()[0]


    cur.execute("SELECT AVG(rating) FROM feedback")
    avg = cur.fetchone()[0]

    if avg is None:
        avg = 0


    # Rating Count

    cur.execute("SELECT COUNT(*) FROM feedback WHERE rating=5")
    five = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM feedback WHERE rating=4")
    four = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM feedback WHERE rating=3")
    three = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM feedback WHERE rating=2")
    two = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM feedback WHERE rating=1")
    one = cur.fetchone()[0]


    conn.close()


    return render_template(
        "feedback_dashboard.html",
        feedback=feedback,
        total=total,
        avg=round(avg,1),
        five=five,
        four=four,
        three=three,
        two=two,
        one=one
    )
@app.route("/delete_feedback/<int:id>")
def delete_feedback(id):

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM feedback WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Feedback deleted successfully!")

    return redirect("/feedback_dashboard")
@app.errorhandler(404)
def page_not_found(e):
    return"404 -page not found"
404


if __name__ == "__main__":
    app.run(debug=True)