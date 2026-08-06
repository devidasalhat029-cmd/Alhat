from datetime import datetime
import random
import sqlite3
import os
import requests

from werkzeug.utils import secure_filename

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    url_for
)

from flask_mail import Mail
from math import ceil
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
app.secret_key = "agrotech123"

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

# AI clients
groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
print("ENV FILE LOADED")
print("OPENWEATHER KEY:", bool(os.getenv("OPENWEATHER_API_KEY")))
print("GROQ KEY:", bool(os.getenv("GROQ_API_KEY")))
print("OPENROUTER KEY:", bool(os.getenv("OPENROUTER_API_KEY")))


# ============================================================
# MAIL CONFIGURATION
# ============================================================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

# ============================================================
# MAIL CONFIGURATION
# ============================================================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

mail = Mail(app)

# ============================================================
# UPLOAD FOLDER
# ============================================================

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "static",
    "uploads"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect():

    conn = sqlite3.connect("agriculture.db")

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# DATABASE TABLES
# ============================================================

def setup_tables():

    conn = connect()

    # --------------------------------------------------------
    # FARMERS
    # --------------------------------------------------------

    conn.execute("""
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


    # --------------------------------------------------------
    # CROP
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS crop(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            crop_name TEXT NOT NULL,

            crop_type TEXT,

            sowing_date TEXT
        )
    """)


    # --------------------------------------------------------
    # SENSOR RECORD
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_record(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            temperature TEXT,

            humidity TEXT,

            moisture TEXT,

            motor_status TEXT,

            irrigation_status TEXT,

            start_time TEXT,

            end_time TEXT,

            duration TEXT,

            date_time TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # --------------------------------------------------------
    # AUTOMATIC IRRIGATION
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS irrigation(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            farmer_id INTEGER,

            crop_name TEXT,

            moisture_threshold REAL,

            duration INTEGER,

            frequency INTEGER,

            auto_irrigation TEXT DEFAULT 'OFF'
        )
    """)


    conn.commit()

    conn.close()


setup_tables()


# ============================================================
# CREATE ADMIN ACCOUNT
# ============================================================

def create_admin():

    conn = connect()

    try:

        admin = conn.execute("""
            SELECT id
            FROM farmers
            WHERE username = ?
        """, (
            "admin",
        )).fetchone()


        if not admin:

            conn.execute("""
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

            conn.commit()

            print("Admin account created.")

        else:

            print("Admin account already exists.")


    except sqlite3.OperationalError as e:

        print("Admin error:", e)


    finally:

        conn.close()


create_admin()


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "home1.html"
    )


# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        conn = connect()

        user = conn.execute("""
            SELECT *
            FROM farmers
            WHERE username = ?
            AND password = ?
        """, (
            username,
            password
        )).fetchone()

        conn.close()


        if user:

            # Store session
            session["username"] = user["username"]

            session["role"] = user["role"]

            session["farmer_id"] = user["id"]


            # -----------------------------
            # ADMIN
            # -----------------------------

            if user["role"] == "admin":

                return redirect(
                    url_for("admin_dashboard")
                )


            # -----------------------------
            # FARMER
            # -----------------------------

            return redirect(
                url_for("farmer_dashboard")
            )


        flash(
            "Invalid username or password!",
            "danger"
        )

        return redirect(
            url_for("login")
        )


    return render_template(
        "login.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        village = request.form.get(
            "village",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        # Validation
        if (
            not name
            or not mobile
            or not village
            or not username
            or not password
        ):

            return render_template(
                "register.html",
                error="Please fill all fields."
            )


        # Photo
        photo = request.files.get(
            "photo"
        )

        filename = "default.png"


        if photo and photo.filename:

            filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )


        conn = connect()


        try:

            conn.execute("""
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
                name,
                mobile,
                village,
                username,
                password,
                "farmer",
                filename
            ))

            conn.commit()


        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "register.html",
                error="Username already exists."
            )


        conn.close()


        flash(
            "Registration successful! Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin_dashboard")
def admin_dashboard():

    if "username" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("role") != "admin":

        flash(
            "Access denied! Admin only.",
            "danger"
        )

        return redirect(
            url_for("farmer_dashboard")
        )


    conn = connect()


    # Total farmers
    total_farmers = conn.execute("""
        SELECT COUNT(*)
        FROM farmers
        WHERE role = 'farmer'
    """).fetchone()[0]


    # Total crops
    total_crops = conn.execute("""
        SELECT COUNT(*)
        FROM crop
    """).fetchone()[0]


    # Total sensor records
    total_records = conn.execute("""
        SELECT COUNT(*)
        FROM sensor_record
    """).fetchone()[0]


    # Motor ON count
    motor_on_count = conn.execute("""
        SELECT COUNT(*)
        FROM sensor_record
        WHERE motor_status = 'ON'
    """).fetchone()[0]


    conn.close()


    return render_template(
        "admin_dashboard.html",

        total_farmers=total_farmers,

        total_crops=total_crops,

        total_records=total_records,

        motor_on_count=motor_on_count
    )


# ============================================================
# FARMER DASHBOARD
# ============================================================

@app.route("/farmer_dashboard")
def farmer_dashboard():

    if "username" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("role") != "farmer":

        return redirect(
            url_for("admin_dashboard")
        )


    farmer_id = session.get(
        "farmer_id"
    )


    conn = connect()


    farmer = conn.execute("""
        SELECT *
        FROM farmers
        WHERE id = ?
    """, (
        farmer_id,
    )).fetchone()


    latest_record = conn.execute("""
        SELECT *
        FROM sensor_record
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()


    irrigation = conn.execute("""
        SELECT *
        FROM irrigation
        WHERE farmer_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (
        farmer_id,
    )).fetchone()


    conn.close()


    return render_template(
        "farmer_dashboard.html",

        farmer=farmer,

        latest_record=latest_record,

        irrigation=irrigation
    )


# ============================================================
# FARMERS LIST - ADMIN ONLY
# ============================================================

@app.route("/farmers")
def farmers():

    if "username" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("role") != "admin":

        flash(
            "Only Admin can access Farmer Management.",
            "danger"
        )

        return redirect(
            url_for("farmer_dashboard")
        )


    page = request.args.get(
        "page",
        1,
        type=int
    )


    if page < 1:

        page = 1


    per_page = 10


    search = request.args.get(
        "search",
        ""
    ).strip()


    village = request.args.get(
        "village",
        ""
    ).strip()


    sort = request.args.get(
        "sort",
        "new"
    )


    conn = connect()


    where = """
        WHERE role = 'farmer'
    """

    params = []


    # Search
    if search:

        where += """
            AND name LIKE ?
        """

        params.append(
            f"%{search}%"
        )


    # Village
    if village:

        where += """
            AND village LIKE ?
        """

        params.append(
            f"%{village}%"
        )


    # Count
    total = conn.execute(
        "SELECT COUNT(*) FROM farmers "
        + where,
        params
    ).fetchone()[0]


    total_pages = max(
        1,
        ceil(total / per_page)
    )


    if page > total_pages:

        page = total_pages


    offset = (
        page - 1
    ) * per_page


    # Sorting
    order = """
        ORDER BY id DESC
    """


    if sort == "old":

        order = """
            ORDER BY id ASC
        """


    elif sort == "az":

        order = """
            ORDER BY name ASC
        """


    elif sort == "za":

        order = """
            ORDER BY name DESC
        """


    # IMPORTANT:
    # LIMIT ? OFFSET ? मध्ये space आहे.
    query = (
        "SELECT * FROM farmers "
        + where
        + " "
        + order
        + " LIMIT ? OFFSET ?"
    )


    final_params = (
        params
        + [
            per_page,
            offset
        ]
    )


    farmers = conn.execute(
        query,
        final_params
    ).fetchall()


    conn.close()


    return render_template(
        "farmers.html",

        farmers=farmers,

        page=page,

        total_pages=total_pages,

        search=search,

        village=village,

        sort=sort
    )


# ============================================================
# FARMER PROFILE
# ============================================================

@app.route(
    "/farmer_profile/<int:id>"
)
def farmer_profile(id):

    if "username" not in session:

        return redirect(
            url_for("login")
        )


    # Farmer can view only own profile
    if session.get("role") == "farmer":

        if session.get("farmer_id") != id:

            flash(
                "You can access only your own profile.",
                "danger"
            )

            return redirect(
                url_for("farmer_dashboard")
            )


    conn = connect()


    farmer = conn.execute("""
        SELECT *
        FROM farmers
        WHERE id = ?
    """, (
        id,
    )).fetchone()


    conn.close()


    if not farmer:

        flash(
            "Farmer not found.",
            "danger"
        )

        if session.get("role") == "admin":

            return redirect(
                url_for("farmers")
            )

        return redirect(
            url_for("farmer_dashboard")
        )


    return render_template(
        "farmer_profile.html",
        farmer=farmer
    )


# ============================================================
# MY PROFILE
# ============================================================

@app.route("/my_profile")
def my_profile():

    if "username" not in session:

        return redirect(
            url_for("login")
        )


    farmer_id = session.get(
        "farmer_id"
    )


    conn = connect()


    farmer = conn.execute("""
        SELECT *
        FROM farmers
        WHERE id = ?
    """, (
        farmer_id,
    )).fetchone()


    conn.close()


    return render_template(
        "farmer_profile.html",
        farmer=farmer
    )




# ============================================================
# EDIT FARMER - ADMIN ONLY
# ============================================================

# ============================================================
# EDIT FARMER PROFILE
# ADMIN + FARMER
# ============================================================

@app.route(
    "/edit_farmer/<int:id>",
    methods=["GET", "POST"]
)
def edit_farmer(id):

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if "username" not in session:

        return redirect(
            url_for("login")
        )


    # --------------------------------------------------------
    # FARMER CAN EDIT ONLY OWN PROFILE
    # ADMIN CAN EDIT ANY FARMER
    # --------------------------------------------------------

    if session.get("role") == "farmer":

        if session.get("farmer_id") != id:

            flash(
                "You can edit only your own profile.",
                "danger"
            )

            return redirect(
                url_for("farmer_dashboard")
            )


    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    conn = connect()

    cursor = conn.cursor()


    # Get farmer
    cursor.execute("""
        SELECT *
        FROM farmers
        WHERE id = ?
    """, (
        id,
    ))

    farmer = cursor.fetchone()


    if not farmer:

        conn.close()

        flash(
            "Farmer not found!",
            "danger"
        )

        if session.get("role") == "admin":

            return redirect(
                url_for("farmers")
            )

        return redirect(
            url_for("farmer_dashboard")
        )


    # ========================================================
    # POST - UPDATE PROFILE
    # ========================================================

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        village = request.form.get(
            "village",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()


        # ----------------------------------------------------
        # OLD PHOTO
        # ----------------------------------------------------

        old_photo = farmer["photo"]


        # ----------------------------------------------------
        # NEW PHOTO
        # ----------------------------------------------------

        photo_file = request.files.get(
            "photo"
        )


        if (
            photo_file
            and photo_file.filename != ""
        ):

            filename = secure_filename(
                photo_file.filename
            )

            photo_file.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

        else:

            filename = old_photo


        # ----------------------------------------------------
        # UPDATE DATABASE
        # ----------------------------------------------------

        try:

            cursor.execute("""
                UPDATE farmers
                SET
                    name = ?,
                    mobile = ?,
                    village = ?,
                    username = ?,
                    photo = ?
                WHERE id = ?
            """, (
                name,
                mobile,
                village,
                username,
                filename,
                id
            ))


            conn.commit()


        except sqlite3.IntegrityError:

            conn.close()

            flash(
                "Username already exists!",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_farmer",
                    id=id
                )
            )


        conn.close()


        # ----------------------------------------------------
        # UPDATE SESSION USERNAME
        # ----------------------------------------------------

        session["username"] = username


        flash(
            "Profile updated successfully!",
            "success"
        )


        # ----------------------------------------------------
        # BACK TO PROFILE
        # ----------------------------------------------------

        return redirect(
            url_for(
                "farmer_profile",
                id=id
            )
        )


    # ========================================================
    # GET - SHOW EDIT PAGE
    # ========================================================

    conn.close()


    return render_template(
        "edit_profile.html",
        farmer=farmer
    )

# ============================================================
# DELETE FARMER - ADMIN ONLY
# ============================================================

@app.route("/delete_farmer/<int:id>")
def delete_farmer(id):

    if "username" not in session:

        return redirect("/login")


    if session.get("role") != "admin":

        flash(
            "Only Admin can delete farmers.",
            "danger"
        )

        return redirect("/farmer_dashboard")


    conn = connect()

    conn.execute("""
        DELETE FROM farmers
        WHERE id = ?
        AND role = 'farmer'
    """, (
        id,
    ))

    conn.commit()

    conn.close()


    flash(
        "Farmer deleted successfully!",
        "success"
    )

    return redirect("/farmers")


# ============================================================
# ADD FARMER - ADMIN ONLY
# ============================================================

@app.route(
    "/add_farmer",
    methods=["GET", "POST"]
)
def add_farmer():

    if "username" not in session:

        return redirect("/login")


    if session.get("role") != "admin":

        flash(
            "Only Admin can add farmers.",
            "danger"
        )

        return redirect("/farmer_dashboard")


    if request.method == "POST":

        name = request.form["name"]

        mobile = request.form["mobile"]

        village = request.form["village"]

        username = request.form["username"]

        password = request.form["password"]


        # Every farmer added here gets farmer role
        role = "farmer"


        # Photo
        photo = request.files.get(
            "photo"
        )

        filename = "default.png"


        if photo and photo.filename != "":

            filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )


        conn = connect()


        try:

            conn.execute("""
                INSERT INTO farmers
                (
                    name,
                    mobile,
                    village,
                    username,
                    password,
                    photo,
                    role
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                mobile,
                village,
                username,
                password,
                filename,
                role
            ))


            conn.commit()


            flash(
                "Farmer added successfully!",
                "success"
            )


        except sqlite3.IntegrityError:

            flash(
                "Username already exists!",
                "danger"
            )


        finally:

            conn.close()


        return redirect("/farmers")


    return render_template(
        "add_farmer.html"
    )


# ============================================================
# CREATE ADMIN ACCOUNT
# ============================================================
# Run this function ONCE if you need an admin account.
#
# Username: admin
# Password: admin123
#
# After creating the account, you can comment this function
# if you want.
# ============================================================

def create_admin():

    conn = connect()

    try:

        existing_admin = conn.execute("""
            SELECT id
            FROM farmers
            WHERE username = ?
        """, (
            "admin",
        )).fetchone()


        if not existing_admin:

            conn.execute("""
                INSERT INTO farmers
                (
                    name,
                    mobile,
                    village,
                    username,
                    password,
                    photo,
                    role
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "Admin",
                "0000000000",
                "Admin",
                "admin",
                "admin123",
                "default.png",
                "admin"
            ))

            conn.commit()

            print("Admin account created.")

        else:

            print("Admin account already exists.")


    except sqlite3.OperationalError as e:

        print(
            "Admin creation error:",
            e
        )


    finally:

        conn.close()


# Create admin account
create_admin()


# ----------------------------
# AI CROP INFORMATION
# ----------------------------

# =========================================================
# CROP MANAGEMENT
# =========================================================

@app.route("/crop", methods=["GET", "POST"])
def crop():

    crops = []

    # Saved crops
    try:
        conn = sqlite3.connect("agriculture.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM crop
            ORDER BY id DESC
        """)

        crops = cursor.fetchall()

        conn.close()

    except Exception as e:
        print("Crop DB Error:", e)


    crop_info = None
    crop_name = ""
    image_url = None


    # AI SEARCH
    if request.method == "POST":

        crop_name = request.form.get("crop_name", "").strip()

        if crop_name:

            try:

                prompt = f"""
You are an agriculture expert.

Give useful farming information about {crop_name}.

Return ONLY valid JSON in exactly this format:

{{
    "crop_name": "{crop_name}",
    "season": "...",
    "sowing_time": "...",
    "harvesting_time": "...",
    "temperature": "...",
    "soil": "...",
    "water_requirement": "...",
    "irrigation": "...",
    "fertilizer": "...",
    "growth_duration": "...",
    "common_pests": "...",
    "common_diseases": "...",
    "farming_tips": "..."
}}

Give practical and simple information.
"""


                response = groq_client.chat.completions.create(

                    model="llama-3.3-70b-versatile",

                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    temperature=0.3
                )


                ai_text = response.choices[0].message.content.strip()


                # Remove markdown JSON if AI adds it
                if ai_text.startswith(""):
                    ai_text = ai_text.replace("json", "")
                    ai_text = ai_text.replace("```", "")
                    ai_text = ai_text.strip()


                import json

                crop_info = json.loads(ai_text)


                # Simple crop image
                image_url = (
                    "https://images.unsplash.com/"
                    "photo-1497250681960-ef046c08a56e"
                    "?auto=format&fit=crop&w=900&q=80"
                )


            except Exception as e:

                print("AI CROP ERROR:", e)

                crop_info = {
                    "error": "AI information could not be generated right now."
                }


    return render_template(
        "crop_ai.html",
        crops=crops,
        crop_info=crop_info,
        crop_name=crop_name,
        image_url=image_url
    )


# =========================================================
# ADD CROP
# =========================================================

@app.route("/add_crop", methods=["GET", "POST"])
def add_crop():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        crop_name = request.form.get("crop_name", "").strip()
        crop_type = request.form.get("crop_type", "").strip()
        sowing_date = request.form.get("sowing_date", "").strip()

        if not crop_name:
            return render_template(
                "add_crop.html",
                error="Please enter crop name."
            )

        conn = sqlite3.connect("agriculture.db")

        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crop (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crop_name TEXT NOT NULL,
                crop_type TEXT,
                sowing_date TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO crop
            (crop_name, crop_type, sowing_date)
            VALUES (?, ?, ?)
        """, (
            crop_name,
            crop_type,
            sowing_date
        ))

        conn.commit()
        conn.close()

        return redirect("/crop")

    return render_template("add_crop.html")


# =========================================================
# EDIT CROP
# =========================================================

@app.route("/edit_crop/<int:id>", methods=["GET", "POST"])
def edit_crop(id):

    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("agriculture.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM crop
        WHERE id = ?
    """, (id,))

    crop_data = cursor.fetchone()

    if crop_data is None:

        conn.close()

        return "Crop not found", 404


    if request.method == "POST":

        crop_name = request.form.get(
            "crop_name", ""
        ).strip()

        crop_type = request.form.get(
            "crop_type", ""
        ).strip()

        sowing_date = request.form.get(
            "sowing_date", ""
        ).strip()


        cursor.execute("""
            UPDATE crop

            SET
                crop_name = ?,
                crop_type = ?,
                sowing_date = ?

            WHERE id = ?
        """, (
            crop_name,
            crop_type,
            sowing_date,
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/crop")


    conn.close()

    return render_template(
        "edit_crop.html",
        crop=crop_data
    )


# =========================================================
# DELETE CROP
# =========================================================

@app.route("/delete_crop/<int:id>")
def delete_crop(id):

    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("agriculture.db")

    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM crop
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/crop")
# ----------------------------
# Weather
# ----------------------------
@app.route("/weather", methods=["GET", "POST"])
def weather():

    city = request.form.get("city", "").strip() if request.method == "POST" else request.args.get("city", "Hingoli").strip()

    if not city:
        city = "Hingoli"

    api_key = os.getenv("OPENWEATHER_API_KEY")

    print("WEATHER CITY:", city)
    print("WEATHER KEY LOADED:", bool(api_key))

    if not api_key:
        return render_template(
            "weather.html",
            error="OpenWeather API key is not configured.",
            weather=None,
            forecast=[]
        )

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        print("WEATHER STATUS:", response.status_code)
        print("WEATHER RESPONSE:", response.text[:500])

        data = response.json()

        if response.status_code != 200:

            return render_template(
                "weather.html",
                error=data.get("message", "Weather data not found."),
                weather=None,
                forecast=[]
            )

        weather = {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "temp_min": round(data["main"]["temp_min"]),
            "temp_max": round(data["main"]["temp_max"]),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind": round(data["wind"]["speed"] * 3.6, 1),
            "wind_direction": data["wind"].get("deg", 0),
            "visibility": round(data.get("visibility", 0) / 1000, 1),
            "condition": data["weather"][0]["description"].title(),
            "icon": data["weather"][0]["icon"],
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"],
            "sunrise": datetime.fromtimestamp(
                data["sys"]["sunrise"]
            ).strftime("%I:%M %p"),
            "sunset": datetime.fromtimestamp(
                data["sys"]["sunset"]
            ).strftime("%I:%M %p"),
            "rain_chance": 0
        }

        return render_template(
            "weather.html",
            weather=weather,
            forecast=[],
            error=None
        )

    except Exception as e:

        print("WEATHER ERROR:", repr(e))

        return render_template(
            "weather.html",
            weather=None,
            forecast=[],
            error=str(e)
        )

# ----------------------------
# Motor Control
# ----------------------------

@app.route("/motor", methods=["GET", "POST"])
def motor():

    conn = connect()

    if request.method == "POST":

        action = request.form.get("action")

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
# ============================================================
#  IRRIGATION
# ============================================================
@app.route("/irrigation")
def irrigation():

    conn = sqlite3.connect("agriculture.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # =====================================================
    # LATEST SOIL MOISTURE
    # =====================================================

    cur.execute("""
        SELECT moisture
        FROM sensor_record
        WHERE moisture IS NOT NULL
          AND TRIM(moisture) != ''
        ORDER BY id DESC
        LIMIT 1
    """)

    moisture_row = cur.fetchone()

    if moisture_row:

        try:
            soil_moisture = float(moisture_row["moisture"])
        except:
            soil_moisture = 0

    else:
        soil_moisture = 0


    # =====================================================
    # ALL MOTOR ON EVENTS
    # =====================================================

    cur.execute("""
        SELECT id, motor_status, date_time
        FROM sensor_record
        WHERE UPPER(TRIM(motor_status)) = 'ON'
        ORDER BY id ASC
    """)

    motor_records = cur.fetchall()


    total_count = len(motor_records)

    morning_count = 0
    evening_count = 0


    # =====================================================
    # COUNT MORNING / EVENING
    # =====================================================

    for row in motor_records:

        date_value = row["date_time"]

        if not date_value:
            continue

        try:

            date_value = str(date_value).strip()

            dt = datetime.strptime(
                date_value,
                "%Y-%m-%d %H:%M:%S"
            )

            hour = dt.hour


            # 5 AM - 11:59 AM
            if 5 <= hour < 12:

                morning_count += 1


            # 5 PM - 11:59 PM
            elif 17 <= hour <= 23:

                evening_count += 1


        except Exception as e:

            print("Date parsing error:", date_value, e)


    # =====================================================
    # LATEST MOTOR STATUS
    # =====================================================

    cur.execute("""
        SELECT motor_status
        FROM sensor_record
        ORDER BY id DESC
        LIMIT 1
    """)

    motor_row = cur.fetchone()

    if motor_row and motor_row["motor_status"]:

        motor_status = str(
            motor_row["motor_status"]
        ).strip().upper()

    else:

        motor_status = "OFF"


    conn.close()


    return render_template(
        "irrigation.html",

        soil_moisture=soil_moisture,

        total_count=total_count,

        morning_count=morning_count,

        evening_count=evening_count,

        motor_status=motor_status
    )
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
    )
# ----------------------------
# AI Assistant
# ----------------------------

@app.route("/ai")
def ai():
    if "username" not in session:
        return redirect("/login")

    return render_template("ai.html")


@app.route("/ai_chat", methods=["POST"])
def ai_chat():

    if "username" not in session:
        return {"reply": "Please login first."}, 401

    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return {"reply": "Please enter a message."}

    try:

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """
You are AgroTech AI, an intelligent agricultural assistant.

Help farmers with:
- Crop management
- Crop diseases
- Irrigation
- Soil moisture
- Weather
- Fertilizer guidance
- Smart farming
- Farm monitoring

Give clear, simple and useful answers.
"""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.5
        )

        reply = response.choices[0].message.content

        return {"reply": reply}

    except Exception as e:

        print("AI ERROR:", e)

        return {
            "reply": "AI service is currently unavailable. Please check your API key and internet connection."
        }, 500
# ----------------------------
# Clear AI Chat
# ----------------------------

@app.route("/clear_ai_chat")
def clear_ai_chat():

    if "username" not in session:
        return redirect("/login")

    session.pop("ai_chat_history", None)

    return redirect("/ai")
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
# ============================================================
# AI DISEASE DETECTION
# ============================================================
# ============================================================
# AI DISEASE DETECTION
# ============================================================

@app.route("/ai_disease", methods=["GET", "POST"])
def ai_disease():

    if "username" not in session:
        return redirect(url_for("login"))

    result = None
    error = None

    if request.method == "POST":

        crop_name = request.form.get("crop_name", "").strip()
        symptoms = request.form.get("symptoms", "").strip()
        photo = request.files.get("leaf_image")

        # --------------------------------------------
        # VALIDATION
        # --------------------------------------------

        if not crop_name:
            error = "Please select a crop."

        elif not photo or photo.filename == "":
            error = "Please upload a leaf image."

        else:

            try:

                # ------------------------------------
                # SAVE IMAGE
                # ------------------------------------

                filename = secure_filename(photo.filename)

                filepath = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )

                photo.save(filepath)


                # ------------------------------------
                # AI PROMPT
                # ------------------------------------

                prompt = f"""
You are an agriculture assistant.

Crop: {crop_name}

Farmer observed symptoms:
{symptoms if symptoms else "No symptoms provided."}

Provide a preliminary crop-health analysis.

Give the answer in this format:

🌿 Crop:
{crop_name}

🦠 Possible Disease:
<disease name or Healthy>

📊 Confidence:
<Low / Medium / High>

🔍 Symptoms:
<short explanation>

原因 / Cause:
<short explanation>

💊 Suggested Care:
<basic safe care suggestion>

🛡️ Prevention:
<short prevention suggestion>

⚠️ Note:
This is an AI-based preliminary assessment and should not replace advice from an agricultural expert.
"""

                # ------------------------------------
                # OPENROUTER
                # ------------------------------------

                response = openrouter_client.chat.completions.create(

                    model="openai/gpt-4o-mini",

                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    temperature=0.2,

                    max_tokens=600
                )


                # ------------------------------------
                # GET RESULT
                # ------------------------------------

                result = response.choices[0].message.content


                if not result:

                    error = "AI returned an empty result."


            except Exception as e:

                print("================================")
                print("AI DISEASE ERROR:")
                print(str(e))
                print("================================")

                error = (
                    "AI analysis failed. "
                    "Please check your OpenRouter API key "
                    "and try again."
                )


    return render_template(
        "ai_disease.html",
        result=result,
        error=error
    )
# ----------------------------
# Logout
# ----------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged Out Successfully!", "success")

    return redirect("/")

@app.route("/check_sensor_table")
def check_sensor_table():

    conn = sqlite3.connect("agriculture.db")
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(sensor_record)")
    columns = cur.fetchall()

    conn.close()

    return "<pre>" + str(columns) + "</pre>"

# ----------------------------
# Run Application
# ----------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )