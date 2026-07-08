from flask import Flask, render_template, request, redirect, session
import sqlite3

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

    return render_template(
        "dashboard.html",
        total_farmers=total_farmers,
        total_crops=total_crops,
        username=session['user']
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

        elif action == "stop":
            session['motor_status'] = False

    return render_template(
        "motor.html",
        status=session['motor_status']
    )
# Records
@app.route('/records')
def records():

    if 'user' not in session:
        return redirect('/login')

    return render_template('records.html')


#irrigation
@app.route('/irrigation')
def irrigation():

    if 'user' not in session:
        return redirect('/login')

    return render_template('irrigation.html')


 #delet quary
"""@app.route('/delete/<int:id') 
def delete_records(id):
    conn= get_db ()
    #first check it is exits
    farmer=conn.execute('SELECR * from Farmer WHERE id=?,' (id,)).fetchone()
    if farmer is none:
        Flash("Farmer is not found","danger")
        conn.close()
        return redirect(url_for('farmer_page'))
    conn.execute('DELETE FROM farmer WHERE id =?',(id))
    conn.commit()
    conn.close()
    flash("farmer deleted succesfully","success")
    return redirect(url_for('farmer_page'))"""


#update data

# Analytics
@app.route('/analytics')
def analytics():

    if 'user' not in session:
        return redirect('/login')

    return render_template('analytics.html')

# Logout
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"),404


if __name__ == "__main__":
    app.run(debug=True)