from datetime import datetime                                                                                        # TO WORK WITH DATE AND TIME
import random                                                                                                        #TO generate random  values 
import json                                                                                                          #json data
import sqlite3                                                                                                       #to connect and work with sqlite darabase
from urllib import response                                                                                          #
import requests                                                                                                      #to send HTTP request and get data from APIs
import smtplib                                                                                                       # to send emails using SMPT
from email.message import EmailMessage                                                                               #to create email messages
import os                                                                                                            # to work with environment variables,files and floders
import base64                                                                                                        #to encode and decode data using base644
import mimetypes                                                                                                     #to identify the type of a file
from werkzeug.utils import secure_filename                                                                           #to safely handels uploads files name

from flask import (                                                                                                  #to use Flask function
    Flask,
    render_template, 
    request,
    redirect,                                                                                                        
    session,
    flash,
    url_for
)
from flask_mail import Mail,Message                                                                                               #to send emails from flsk
from math import ceil                                                                                                             #to round a number upward mainy used for panination
from dotenv import load_dotenv                                                                                                    #to load variables from the .env files
from groq import Groq                                                                                                             #to connect with groq ai api
from openai import OpenAI                                                                                                         #to use  open ai api  such as open route

# ----------------------------
# Flask App
# ----------------------------

app = Flask(__name__)             #Create the flask application
app.secret_key = "agrotech123"    #used to securely manages flask session

# ----------------------------
# Load Environment Variables
# ----------------------------

load_dotenv()

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)
print("GROQ KEY:", bool(os.getenv("GROQ_API_KEY")))
print("OPENROUTER KEY:", bool(os.getenv("OPENROUTER_API_KEY")))

#----------------------------
#for mail
#----------------------------

app.config["MAIL_SERVER"] = "smtp.gmail.com"        #Sets Gmails SMTP server 
app.config["MAIL_PORT"] = 587                       #Sets the port for the SMTP server
app.config["MAIL_USE_TLS"] = True                   #Enables secures TLS connection 
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")   #gets the username from .env files
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")   #get the password from .env files
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")  #sets default sender emails 

mail = Mail(app)      #initialize flask mails
# ----------------------------
# Upload Folder
# ----------------------------

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")               #create the path for uploads files 

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER                                    #Store the upload floder path in flask configuration

os.makedirs(UPLOAD_FOLDER, exist_ok=True)                                      #create the upload  if it does not exist

# ----------------------------
# Database Connection
# ----------------------------

def connect():                                                                  #Defines a database connection function

    conn = sqlite3.connect("agriculture.db")                                   #connects to the sqlite database file named "agriculture.db"
    conn.row_factory = sqlite3.Row                                             #Allows database rows to be accessed like dictionaries, enabling column access by name

    return conn                                                                #return the database connection 

# ----------------------------
# Home
# ----------------------------

@app.route("/")                                                                 #defines the home pages route
def home():

    return render_template("home1.html")                                       #display home page function

# ----------------------------
# About
# ----------------------------

@app.route("/about")
def about():

    return render_template("about.html")


# ----------------------------
# Farmer
# ----------------------------


@app.route("/farmers")
def farmers():

    page = request.args.get("page", 1, type=int)                      #gates the current panination  page number

    if page < 1:                                                     #prevents negative or zero page numbers by setting the page to 1 if it is less than 1
        page = 1

    per_page = 10                                                  # Defines the number of records to display per page, set to 10 in this case.

    search = request.args.get("search", "")                        # Retrieves the search query from the request's query parameters. If no search query is provided, it defaults to an empty string.
    village = request.args.get("village", "")                       # Retrieves the village filter from the request's query parameters. If no village filter is provided, it defaults to an empty string.
    sort = request.args.get("sort", "new")                          # Retrieves the sorting option from the request's query parameters. If no sorting option is provided, it defaults to "new".

    conn = connect()                                                # Establishes a connection to the database 
    cursor = conn.cursor()                                          # Creates a cursor object for executing SQL queries

    # Base Query
    where = " WHERE 1=1 "                                          # Initializes the WHERE clause
    params = []                                                    # Initializes the list of parameters for the SQL query

    if search:                                                     # Checks if a search query is provided
        where += " AND name LIKE ? "                               # Adds a condition to the WHERE clause to filter farmers by name using a LIKE operator
        params.append(f"%{search}%")                               # Appends the search query to the list of parameters, using wildcards for partial matching

    if village:                                                   # Checks if a village filter is provided
        where += " AND village LIKE ? "                           # Adds a condition to the WHERE clause to filter farmers by village using a LIKE operator
        params.append(f"%{village}%")                             # Appends the village filter to the list of parameters, using wildcards for partial matching

    # Total Records
    cursor.execute(                                              # Executes the COUNT query to get the total number of records
        "SELECT COUNT(*) FROM farmers" + where,                  # The query to count the total number of farmers based on the WHERE clause
        params
    )

    total = cursor.fetchone()[0]                                 # Retrieves the total count of records from the query result

    total_pages = max(1, ceil(total / per_page))                 # Calculates the total number of pages based on the total records and records per page, ensuring at least one page exists

    if page > total_pages:                                       # Ensures that the current page number does not exceed the total number of pages. If it does, it sets the current page to the last page.
        page = total_pages

    offset = (page - 1) * per_page                               # Calculates the offset for the SQL query based on the current page number and records per page. This determines where to start fetching records for the current page.

    # Sorting
    order = " ORDER BY id DESC "                                # Initializes the ORDER BY clause for sorting the records. By default, it sorts by ID in descending order (newest first).

    if sort == "old":                                           # Checks if the sorting option is set to "old" (oldest first)
        order = " ORDER BY id ASC "

    elif sort == "az":                                         # Checks if the sorting option is set to "az" (alphabetical order A-Z)
        order = " ORDER BY name ASC "

    elif sort == "za":                                        # Checks if the sorting option is set to "za" (alphabetical order Z-A)
        order = " ORDER BY name DESC "

    # Final Query
    query = (                                                  # Constructs the final SQL query by combining the base query, WHERE clause, ORDER BY clause, and LIMIT/OFFSET for pagination.
        "SELECT * FROM farmers"
        + where
        + order
        + " LIMIT ? OFFSET ?"
    )

    final_params = params + [per_page, offset]                 # Combines the parameters for the WHERE clause with the LIMIT and OFFSET values for pagination.

    cursor.execute(query, final_params)                         # Executes the final SQL query with the combined parameters to fetch the farmer records for the current page.

    farmers = cursor.fetchall()                                  # Retrieves all the farmer records returned by the query and stores them in the `farmers` variable.

    conn.close()                                                # Closes the database connection to free up resources.

    return render_template(                                     # Renders the "farmers.html" template and passes the necessary data for display, including the list of farmers, current page number, and total pages for pagination.
        "farmers.html",
        farmers=farmers,
        page=page,
        total_pages=total_pages
    )
# ----------------------------
# Farmer Profile
# ----------------------------

@app.route("/farmer_profile/<int:id>")                                   #Defines a route for displaying the profile of a specific farmer based on their ID. The <int:id> part indicates that the route expects an integer parameter named id.
def farmer_profile(id):                                                  # Defines the function to handle the farmer profile route.

    if "username" not in session:                                        # Checks if the user is logged in by verifying if "username" exists in the session. If not, it redirects the user to the login page.
        return redirect("/login")

    conn = connect()                                                     # Establishes a connection to the database.

    farmer = conn.execute(                                               # Executes a SQL query to fetch the details of the farmer with the specified ID from the "farmers" table. The query uses a parameterized statement to prevent SQL injection.
        "SELECT * FROM farmers WHERE id=?",                              
        (id,)
    ).fetchone()                                                        # Retrieves the first row of the result set, which contains the farmer's details, and stores it in the `farmer` variable.

    conn.close()

    return render_template(
        "farmer_profile.html",                                            # Renders the "farmer_profile.html" template and passes the farmer's details to it for display.
        farmer=farmer
    )
    

#----------------------------
#For edit farmer profile
#----------------------------
@app.route("/edit_farmer/<int:id>", methods=["GET","POST"])              #Defines a route for editing the profile of a specific farmer based on their ID. The <int:id> part indicates that the route expects an integer parameter named id. The methods=["GET","POST"] part specifies that this route can handle both GET and POST requests.
def edit_farmer(id):

    conn = connect()                                                    # Establishes a connection to the database.
    cursor = conn.cursor()                                              # Creates a cursor object for executing SQL queries.


    if request.method == "POST":                                       # Checks if the request method is POST, indicating that the form has been submitted for updating the farmer's profile.

        name = request.form["name"]                                    # Retrieves the updated name from the submitted form data.
        mobile = request.form["mobile"]                                # Retrieves the updated mobile number from the submitted form data.
        village = request.form["village"]                             # Retrieves the updated village from the submitted form data.
        username = request.form["username"]                           # Retrieves the updated username from the submitted form data.


        cursor.execute(                                               # Executes a SQL query to fetch the current photo filename of the farmer with the specified ID from the "farmers" table. This is done to retain the old photo if no new photo is uploaded.
            "SELECT photo FROM farmers WHERE id=?",
            (id,)
        )

        old_photo = cursor.fetchone()[0]                                # Retrieves the current photo filename from the query result and stores it in the `old_photo` variable.


        photo = request.files["photo"]                                # Retrieves the uploaded photo file from the submitted form data.


        if photo and photo.filename != "":                             # Checks if a new photo file has been uploaded (i.e., the file exists and has a filename). If so, it processes the new photo.

            filename = secure_filename(photo.filename)                 # Sanitizes the uploaded photo's filename to ensure it is safe for use in the filesystem.

            photo.save(                                                  # Saves the uploaded photo file to the specified upload folder on the server, using the sanitized filename. The file is saved in the "static/uploads/" directory.
                "static/uploads/" + filename
            )

        else:                                                        # If no new photo is uploaded, it retains the old photo filename for the farmer's profile.

            filename = old_photo



        cursor.execute("""
        UPDATE farmers                                             ## Executes a SQL query to update the farmer's profile information in the "farmers" table. The query uses parameterized statements to prevent SQL injection. It updates the name, mobile number, village, username, and photo filename for the farmer with the specified ID.
        SET name=?,
            mobile=?,
            village=?,
            username=?,
            photo=?
        WHERE id=?
        """,
        (
            name,
            mobile,
            village,                                                      
            username,
            filename,
            id
        ))


        conn.commit()                                       # Commits the changes made to the database, ensuring that the updated farmer profile information is saved permanently.
        conn.close()                                         # Closes the database connection to free up resources.


        return redirect("/farmers")                               # Redirects the user to the "/farmers" page after successfully updating the farmer's profile.



    cursor.execute(
        "SELECT * FROM farmers WHERE id=?",                    # Executes a SQL query to fetch the details of the farmer with the specified ID from the "farmers" table. This is done to populate the edit form with the current information of the farmer.
        (id,)
    )

    farmer = cursor.fetchone()                               # Retrieves the first row of the result set, which contains the farmer's details, and stores it in the `farmer` variable.

    conn.close()                                            # Closes the database connection to free up resources.


    return render_template(                                   # Renders the "edit_profile.html" template and passes the farmer's details to it for display in the edit form.
        "edit_profile.html",
        farmer=farmer
    )
# ----------------------------
# DElETe
# ----------------------------
@app.route("/delete_farmer/<int:id>")                             #Defines a route for deleting a specific farmer based on their ID. The <int:id> part indicates that the route expects an integer parameter named id.
def delete_farmer(id):

    if "username" not in session:                                # Checks if the user is logged in by verifying if "username" exists in the session. If not, it redirects the user to the login page.
        return redirect("/login")                                             

    conn = connect()

    conn.execute(
        "DELETE FROM farmers WHERE id=?",                          # Executes a SQL query to delete the farmer with the specified ID from the "farmers" table. The query uses a parameterized statement to prevent SQL injection.
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/farmers")

# ----------------------------
# Add farmer 
# ----------------------------
@app.route("/add_farmer", methods=["GET", "POST"])                  #Defines a route for adding a new farmer to the system. The methods=["GET", "POST"] part specifies that this route can handle both GET and POST requests.
def add_farmer():

    if "username" not in session:                                 # Checks if the user is logged in by verifying if "username" exists in the session. If not, it redirects the user to the login page.
        return redirect("/login")

    if request.method == "POST":                                   # Checks if the request method is POST, indicating that the form has been submitted for adding a new farmer.

        name = request.form["name"]           # Retrieves the name of the new farmer from the submitted form data.
        mobile = request.form["mobile"]# Retrieves the mobile number of the new farmer from the submitted form data.
        village = request.form["village"]# Retrieves the village of the new farmer from the submitted form data.
        username = request.form["username"]# Retrieves the username of the new farmer from the submitted form data.
        password = request.form["password"]# Retrieves the password of the new farmer from the submitted form data.

        filename = "default.png"           # Sets a default filename for the farmer's photo in case no photo is uploaded.

        photo = request.files.get("photo")       # Retrieves the uploaded photo file from the submitted form data. If no photo is uploaded, it will be None.

        if photo and photo.filename != "":             # Checks if a new photo file has been uploaded (i.e., the file exists and has a filename). If so, it processes the new photo.
            filename = secure_filename(photo.filename)        # Sanitizes the uploaded photo's filename to ensure it is safe for use in the filesystem.
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))           # Saves the uploaded photo file to the specified upload folder on the server, using the sanitized filename. The file is saved in the "static/uploads/" directory.

        conn = connect()

        conn.execute("""
        INSERT INTO farmers                                                    # Executes a SQL query to insert a new farmer's information into the "farmers" table. The query uses parameterized statements to prevent SQL injection. It inserts the name, mobile number, village, username, password, and photo filename for the new farmer.
        (name, mobile, village, username, password, photo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, mobile, village, username, password, filename))

        conn.commit()
        conn.close()

        return redirect("/farmers")

    return render_template("add_farmer.html")                                  # Renders the "add_farmer.html" template, which contains the form for adding a new farmer. This is displayed when the request method is GET (i.e., when the user navigates to the add farmer page).

# ----------------------------
# Register
# ----------------------------

@app.route("/register", methods=["GET", "POST"])                            #Defines a route for user registration. The methods=["GET", "POST"] part specifies that this route can handle both GET and POST requests.
def register():

    if request.method == "POST":                                              # Checks if the request method is POST, indicating that the registration form has been submitted.

        name = request.form["name"]                                          # Retrieves the name of the user from the submitted form data.,mobile = request.form["mobile"]                                          # Retrieves the mobile number of the user from the submitted form data.
        mobile = request.form["mobile"]
        village = request.form["village"]
        username = request.form["username"]
        password = request.form["password"]

        # Photo
        photo = request.files["photo"]             # Retrieves the uploaded photo file from the submitted form data. If no photo is uploaded, it will be None.

        filename = "default.png"                # Sets a default filename for the user's photo in case no photo is uploaded.

        if photo and photo.filename != "":              # Checks if a new photo file has been uploaded (i.e., the file exists and has a filename). If so, it processes the new photo.
            filename = secure_filename(photo.filename)              # Sanitizes the uploaded photo's filename to ensure it is safe for use in the filesystem.
            photo.save(os.path.join("static/uploads", filename))             # Saves the uploaded photo file to the specified upload folder on the server, using the sanitized filename. The file is saved in the "static/uploads/" directory.

        conn = connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM farmers WHERE username = ?", (username,))                     # Executes a SQL query to check if the provided username already exists in the "farmers" table. The query uses a parameterized statement to prevent SQL injection.
        user = cursor.fetchone()

        if user:                              # If a user with the provided username already exists in the database, it means the username is taken. In this case, the function closes the database connection and returns a message indicating that the username already exists and prompts the user to choose another username.
            conn.close()                    # Closes the database connection to free up resources.
            return "Username already exists! Please choose another username."          

        cursor.execute("""                                    
        INSERT INTO farmers
        (name, mobile, village, username, password, photo)
        VALUES (?, ?, ?, ?, ?, ?)                                       # Executes a SQL query to insert the new user's information into the "farmers" table. The query uses parameterized statements to prevent SQL injection. It inserts the name, mobile number, village, username, password, and photo filename for the new user.
        """, (name, mobile, village, username, password, filename))           

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")



# ----------------------------
# Login
# ----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = connect()

        cursor = conn.cursor()
        user = cursor.execute("""
        SELECT * FROM farmers
        WHERE username=? AND password=?
        """,
        (username, password)).fetchone()

        conn.close()

        if user:

            session["username"] = user["username"]

            return redirect("/dashboard")

        else:

            flash("Invalid Username or Password", "danger")

    return render_template("login.html")


# ----------------------------
# Motor ON
# ----------------------------

@app.route("/motor/on")
def motor_on():

    session["motor_status"] = True

    return redirect("/dashboard")


# ----------------------------
# Motor OFF
# ----------------------------

@app.route("/motor/off")
def motor_off():

    session["motor_status"] = False

    return redirect("/dashboard")

# ----------------------------
# Dashboard
# ----------------------------

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/login")

    conn = connect()

    total_farmers = conn.execute(
        "SELECT COUNT(*) FROM farmers"
    ).fetchone()[0]

    total_crops = conn.execute(
        "SELECT COUNT(*) FROM crop"
    ).fetchone()[0]

    conn.close()

    # Motor status
    if "motor_status" not in session:
        session["motor_status"] = False

    # Dashboard weather data
    weather = {
        "temp": 28,
        "humidity": 65,
        "wind": 12,
        "condition": "Sunny"
    }

    return render_template(

        "dashboard.html",

        username=session["username"],

        total_farmers=total_farmers,

        total_crops=total_crops,

        weather=weather,

        motor_status=session["motor_status"],

        temperature=28,

        humidity=65,

        moisture=45,

        city="Hingoli",

        wind="12 km/h"
    )
# ----------------------------
# AI CROP INFORMATION
# ----------------------------

@app.route("/crop_ai", methods=["GET", "POST"])
def crop_ai():

    if "username" not in session:
        return redirect("/login")

    crop_info = None
    crop_name = ""
    image_url = None

    if request.method == "POST":

        crop_name = request.form.get("crop_name", "").strip()

        if crop_name:

            prompt = f"""
You are an expert agricultural advisor.

Give accurate and practical information about this crop:
{crop_name}

Return ONLY valid JSON.

Use exactly these keys:

crop_name
season
sowing_time
harvesting_time
temperature
soil
water_requirement
irrigation
fertilizer
growth_duration
common_pests
common_diseases
farming_tips

Rules:
- Give simple information suitable for Indian farmers.
- Keep each value short but useful.
- Do not use markdown.
- Do not use json.
"""

            try:

                # =========================
                # AI INFORMATION
                # =========================

                response = groq_client.chat.completions.create(

                    model="llama-3.1-8b-instant",

                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    temperature=0.3,
                    max_tokens=1000
                )

                ai_text = response.choices[0].message.content.strip()

                ai_text = ai_text.replace("json", "")
                ai_text = ai_text.replace("```", "")
                ai_text = ai_text.strip()

                crop_info = json.loads(ai_text)


                # =========================
                # AUTOMATIC CROP IMAGE
                # =========================

                try:

                    search_name = crop_info.get(
                        "crop_name",
                        crop_name
                    )

                    image_api = (
                        "https://commons.wikimedia.org/"
                        "w/api.php"
                    )

                    image_params = {

                        "action": "query",

                        "generator": "search",

                        "gsrsearch":
                            f"{search_name} crop agriculture",

                        "gsrnamespace": 6,

                        "gsrlimit": 5,

                        "prop": "imageinfo",

                        "iiprop": "url",

                        "format": "json"
                    }

                    image_response = requests.get(
                        image_api,
                        params=image_params,
                        headers={
                            "User-Agent":
                            "AgroMonitor/1.0"
                        },
                        timeout=10
                    )

                    image_data = image_response.json()

                    pages = image_data.get(
                        "query",
                        {}
                    ).get(
                        "pages",
                        {}
                    )

                    if pages:

                        first_page = next(
                            iter(pages.values())
                        )

                        image_info = first_page.get(
                            "imageinfo",
                            []
                        )

                        if image_info:

                            image_url = image_info[0].get(
                                "url"
                            )

                except Exception as image_error:

                    print(
                        "CROP IMAGE ERROR:",
                        image_error
                    )

                    image_url = None


            except Exception as ai_error:

                print(
                    "AI CROP ERROR:",
                    ai_error
                )

                crop_info = {

                    "error":
                    "AI service is temporarily unavailable. Please try again."
                }


    return render_template(

        "crop_ai.html",

        crop_info=crop_info,

        crop_name=crop_name,

        image_url=image_url
    )
# ----------------------------
# Weather
# ----------------------------

@app.route("/weather")
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

    return render_template(
        "weather.html",
        weather=weather_data
    )


# ----------------------------
# Motor Control
# ----------------------------

@app.route("/motor", methods=["GET", "POST"])
def motor():

    conn = connect()

    if request.method == "POST":

        action = request.form["action"]

        moisture = f"{random.randint(40,80)}%"
        temperature = f"{random.randint(25,35)}°C"
        humidity = f"{random.randint(50,90)}%"

        if action == "start":

            session["motor_status"] = True
            session["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn.execute("""
            INSERT INTO sensor_record
            (
                moisture,
                temperature,
                humidity,
                motor_status,
                irrigation_status,
                start_time
            )
            VALUES(?,?,?,?,?,?)
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

                conn.execute("""
                INSERT INTO sensor_record
                (
                    moisture,
                    temperature,
                    humidity,
                    motor_status,
                    irrigation_status,
                    start_time,
                    end_time,
                    duration
                )
                VALUES(?,?,?,?,?,?,?,?)
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
# ----------------------------
# Live Farm
# ----------------------------

@app.route("/live_farm")
def live_farm():

    if "username" not in session:
        return redirect("/login")

    return render_template(
        "live_farm.html",
        status=session.get("motor_status", False)
    )


# ----------------------------
# Records
# ----------------------------

@app.route("/records")
def records():

    if "username" not in session:
        return redirect("/login")

    conn = connect()

    records = conn.execute("""
        SELECT *
        FROM sensor_record
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "records.html",
        records=records
    )


# ----------------------------
# Delete Record
# ----------------------------

@app.route("/delete_record/<int:id>")
def delete_record(id):

    if "username" not in session:
        return redirect("/login")

    conn = connect()

    conn.execute(
        "DELETE FROM sensor_record WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Record Deleted Successfully!", "success")

    return redirect("/records")


# ----------------------------
# Remove Record (Analytics)
# ----------------------------

@app.route("/clean_record/<int:record_id>")
def clean_record(record_id):

    if "username" not in session:
        return redirect("/login")

    conn = connect()

    conn.execute(
        "DELETE FROM sensor_record WHERE id = ?",
        (record_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("analytics"))
# ----------------------------
# Irrigation
# ----------------------------

@app.route("/irrigation", methods=["GET", "POST"])
def irrigation():

    if "username" not in session:
        return redirect("/login")

    conn = connect()

    if request.method == "POST":

        crop_name = request.form["crop_name"]
        water_time = request.form["water_time"]
        duration = request.form["duration"]

        conn.execute("""
        INSERT INTO irrigation_schedule
        (crop_name, water_time, duration, status)
        VALUES(?,?,?,?)
        """,
        (
            crop_name,
            water_time,
            duration,
            "Scheduled"
        ))

        conn.commit()

    records = conn.execute("""
        SELECT *
        FROM irrigation_schedule
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "irrigation.html",
        records=records
    )


# ----------------------------
# Edit Irrigation
# ----------------------------

@app.route("/edit_irrigation/<int:id>", methods=["GET","POST"])
def edit_irrigation(id):

    conn = connect()

    if request.method == "POST":

        crop_name = request.form["crop_name"]
        water_time = request.form["water_time"]
        duration = request.form["duration"]

        conn.execute("""
        UPDATE irrigation_schedule
        SET crop_name=?,
            water_time=?,
            duration=?
        WHERE id=?
        """,
        (
            crop_name,
            water_time,
            duration,
            id
        ))

        conn.commit()
        conn.close()

        flash("Schedule Updated Successfully!", "success")

        return redirect("/irrigation")

    data = conn.execute(
        "SELECT * FROM irrigation_schedule WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template(
        "edit_irrigation.html",
        data=data
    )


# ----------------------------
# Delete Irrigation
# ----------------------------

@app.route("/delete_irrigation/<int:id>")
def delete_irrigation(id):

    conn = connect()

    conn.execute(
        "DELETE FROM irrigation_schedule WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Schedule Deleted Successfully!", "success")
    return redirect("/irrigation")

# -------------------------
# MOTOR ANALYTICS
# ----------------------------

@app.route("/analytics")
def analytics():

    if "username" not in session:
        return redirect("/login")

    conn = connect()

    rows = conn.execute("""
        SELECT
            id,
            motor_status,
            start_time,
            end_time,
            duration
        FROM sensor_record
        WHERE start_time IS NOT NULL
        ORDER BY id ASC
    """).fetchall()

    conn.close()

    # ----------------------------
    # Calculate ON / OFF time
    # ----------------------------

    total_on_seconds = 0
    total_off_seconds = 0

    on_count = 0
    off_count = 0

    motor_events = []

    for row in rows:

        status = row["motor_status"]

        if status == "ON":
            on_count += 1
        elif status == "OFF":
            off_count += 1

        try:

            # ON record
            if status == "ON" and row["start_time"]:

                time_value = datetime.strptime(
                    row["start_time"],
                    "%Y-%m-%d %H:%M:%S"
                )

                motor_events.append({
                    "status": "ON",
                    "time": time_value
                })

            # OFF record
            elif status == "OFF":

                time_value = None

                if row["end_time"]:

                    time_value = datetime.strptime(
                        row["end_time"],
                        "%Y-%m-%d %H:%M:%S"
                    )

                elif row["start_time"]:

                    time_value = datetime.strptime(
                        row["start_time"],
                        "%Y-%m-%d %H:%M:%S"
                    )

                if time_value:

                    motor_events.append({
                        "status": "OFF",
                        "time": time_value
                    })

        except Exception as e:

            print("Time Error:", e)


    # ----------------------------
    # Sort events by time
    # ----------------------------

    motor_events.sort(
        key=lambda x: x["time"]
    )


    # ----------------------------
    # Calculate duration between events
    # ----------------------------

    for i in range(len(motor_events) - 1):

        current = motor_events[i]

        next_event = motor_events[i + 1]

        difference = (
            next_event["time"]
            - current["time"]
        ).total_seconds()

        if difference < 0:
            difference = 0

        if current["status"] == "ON":

            total_on_seconds += difference

        elif current["status"] == "OFF":

            total_off_seconds += difference


    # ----------------------------
    # Format time
    # ----------------------------

    def format_time(seconds):

        seconds = int(seconds)

        hours = seconds // 3600

        minutes = (seconds % 3600) // 60

        secs = seconds % 60

        if hours > 0:

            return f"{hours} hr {minutes} min"

        elif minutes > 0:

            return f"{minutes} min {secs} sec"

        else:

            return f"{secs} sec"


    total_on_time = format_time(
        total_on_seconds
    )

    total_off_time = format_time(
        total_off_seconds
    )


    # ----------------------------
    # Graph values
    # ----------------------------

    graph_on_minutes = round(
        total_on_seconds / 60,
        2
    )

    graph_off_minutes = round(
        total_off_seconds / 60,
        2
    )


    print("ON TIME:", total_on_time)

    print("OFF TIME:", total_off_time)

    print("ON MINUTES:", graph_on_minutes)

    print("OFF MINUTES:", graph_off_minutes)


    return render_template(

        "analytics.html",

        records=rows,

        on_count=on_count,

        off_count=off_count,

        total_on_time=total_on_time,

        total_off_time=total_off_time,

        graph_on_minutes=graph_on_minutes,

        graph_off_minutes=graph_off_minutes

    )
# ----------------------------
# AI Tips
# ----------------------------

@app.route("/ai_tips")
def ai_tips():

    if "username" not in session:
        return redirect("/login")

    prompt = f"""
    You are an agriculture expert.

    Farmer: {session['username']}

    Give one useful and short farming tip.
    Keep it simple and practical.
    """

    try:

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=150
        )

        advice = response.choices[0].message.content

    except Exception as e:

        print("AI ERROR:", e)

        advice = "AI services not available"

    return render_template(
        "ai_tips.html",
        username=session["username"],
        advice=advice
    )# ----------------------------
# AI Assistant
# ----------------------------

@app.route("/ai_assistant", methods=["GET", "POST"])
def ai_assistant():

    if "username" not in session:
        return redirect("/login")

    # Chat history
    chat_history = session.get("ai_chat_history", [])

    if request.method == "POST":

        question = request.form.get("question", "").strip()

        if question:

            prompt = f"""
You are an intelligent Agriculture AI Assistant.

Farmer Name:
{session["username"]}

Farmer's Question:
{question}

Give a clear, practical and easy-to-understand answer.

Rules:
- Answer in simple language.
- Keep the answer useful for farming.
- Give steps when necessary.
- Do not make the answer unnecessarily long.
"""

            try:

                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful Agriculture AI Assistant."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=300
                )

                answer = response.choices[0].message.content

            except Exception as e:

                print("AI ASSISTANT ERROR:", e)

                answer = "AI Assistant is currently unavailable."

            # Save conversation
            chat_history.append({
                "question": question,
                "answer": answer
            })

            # Keep latest 20 conversations
            chat_history = chat_history[-20:]

            session["ai_chat_history"] = chat_history
            session.modified = True

    return render_template(
        "ai_assistant.html",
        username=session["username"],
        chat_history=chat_history
    )


# ----------------------------
# Clear AI Chat
# ----------------------------

@app.route("/clear_ai_chat")
def clear_ai_chat():

    if "username" not in session:
        return redirect("/login")

    session.pop("ai_chat_history", None)

    return redirect("/ai_assistant")
# ----------------------------
# Disease Detection
# ----------------------------

@app.route("/disease", methods=["GET", "POST"])
def disease():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        file = request.files.get("leaf")

        if not file or file.filename == "":
            flash("Please select an image.", "danger")
            return redirect("/disease")

        filename = secure_filename(file.filename)

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        file.save(filepath)

        prompt = """
You are an expert agricultural plant disease specialist.

Identify the crop automatically from the uploaded leaf image.

Supported crops include but are not limited to:
Tomato, Potato, Rice, Wheat, Cotton, Maize, Soybean,
Sugarcane, Chilli, Brinjal, Okra, Cucumber, Mango,
Banana, Grapes, Apple, Orange, Lemon, Papaya and Pomegranate.

Reply ONLY in this format:

Plant:
Status:
Disease:
Confidence:

Treatment:
- Point 1
- Point 2
- Point 3

Prevention:
- Point 1
- Point 2
- Point 3
"""

        with open(filepath, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        mime_type = mimetypes.guess_type(filepath)[0] or "image/jpeg"

        response = openrouter_client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=700
        )

        result = response.choices[0].message.content

        plant = ""
        status = ""
        disease_name = ""
        confidence = ""
        treatment = []
        prevention = []

        section = ""

        for line in result.splitlines():

            line = line.strip()

            if line.startswith("Plant:"):
                plant = line.replace("Plant:", "").strip()

            elif line.startswith("Status:"):
                status = line.replace("Status:", "").strip()

            elif line.startswith("Disease:"):
                disease_name = line.replace("Disease:", "").strip()

            elif line.startswith("Confidence:"):
                confidence = line.replace("Confidence:", "").strip()

            elif line.startswith("Treatment:"):
                section = "treatment"

            elif line.startswith("Prevention:"):
                section = "prevention"

            elif line.startswith("-"):

                if section == "treatment":
                    treatment.append(line.replace("-", "").strip())

                elif section == "prevention":
                    prevention.append(line.replace("-", "").strip())

        return render_template(
                    "result.html",
                    image=filename,
                    plant=plant,
                    status=status,
                    disease=disease_name,
                    confidence=confidence,
                    treatment=treatment,
                    prevention=prevention
)

    return render_template("disease.html")
# ----------------------------
# Contact
# ----------------------------
@app.route("/contact", methods=["GET", "POST"])
def contact():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        try:
            msg = EmailMessage()

            msg["Subject"] = f"Contact Message: {subject}"
            msg["From"] = os.getenv("MAIL_USERNAME")
            msg["To"] = os.getenv("CONTACT_EMAIL")
            msg["Reply-To"] = email

            msg.set_content(f"""
New Contact Message

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}
""")

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(
                    os.getenv("MAIL_USERNAME"),
                    os.getenv("MAIL_PASSWORD")
                )

                smtp.send_message(msg)

            return render_template(
                "contact.html",
                success="Message sent successfully! 💜"
            )

        except Exception as e:
            print("EMAIL ERROR:", e)

            return render_template(
                "contact.html",
                error="Message could not be sent. Please try again."
            )

    return render_template("contact.html")
# ----------------------------
# Feedback
# ----------------------------

@app.route("/feedback", methods=["GET","POST"])
def feedback():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]


        msg = Message(

            subject="🌱 New Agro Monitor Feedback",

            sender=os.getenv("MAIL_USERNAME"),

            recipients=[
                os.getenv("MAIL_USERNAME")
            ]

        )


        msg.body = f"""

        New Feedback Received

        Name:
        {name}


        Email:
        {email}


        Feedback:

        {message}


        -------------------
        Agro Monitor System
        """



        mail.send(msg)



        return render_template(
            "feedback_success.html",
            name=name
        )


    return render_template("feedback.html")
@app.route("/alerts")
def alerts():

    if "username" not in session:
        return redirect("/login")

    conn = connect()

    # Latest sensor record
    record = conn.execute("""
        SELECT
            id,
            moisture,
            temperature,
            humidity,
            motor_status,
            irrigation_status,
            date_time
        FROM sensor_record
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    alerts_list = []

    if record:

        moisture = record[1]
        temperature = record[2]
        humidity = record[3]
        motor_status = record[4]

        # -------------------------
        # Soil Moisture Alert
        # -------------------------

        try:
            moisture_value = float(moisture)

            if moisture_value < 30:

                alerts_list.append({
                    "type": "warning",
                    "icon": "🌱",
                    "title": "Low Soil Moisture",
                    "message": f"Soil moisture is {moisture_value}%. Irrigation may be required."
                })

        except (TypeError, ValueError):
            pass


        # -------------------------
        # Temperature Alert
        # -------------------------

        try:
            temperature_value = float(temperature)

            if temperature_value > 35:

                alerts_list.append({
                    "type": "danger",
                    "icon": "🌡️",
                    "title": "High Temperature",
                    "message": f"Temperature is {temperature_value}°C. Please monitor your crop."
                })

        except (TypeError, ValueError):
            pass


        # -------------------------
        # Humidity Alert
        # -------------------------

        try:
            humidity_value = float(humidity)

            if humidity_value < 30:

                alerts_list.append({
                    "type": "info",
                    "icon": "💧",
                    "title": "Low Humidity",
                    "message": f"Humidity is {humidity_value}%. Monitor crop conditions."
                })

        except (TypeError, ValueError):
            pass


        # -------------------------
        # Motor Alert
        # -------------------------

        if motor_status == "ON":

            alerts_list.append({
                "type": "motor",
                "icon": "⚙️",
                "title": "Motor is ON",
                "message": "The irrigation motor is currently running."
            })


    # -------------------------
    # System Normal
    # -------------------------

    if not alerts_list:

        alerts_list.append({
            "type": "success",
            "icon": "✅",
            "title": "System Normal",
            "message": "All monitored conditions are currently normal."
        })


    return render_template(
        "alerts.html",
        alerts=alerts_list,
        record=record
    )
# ----------------------------
# Logout
# ----------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged Out Successfully!", "success")

    return redirect("/")


# ----------------------------
# Run Application
# ----------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )