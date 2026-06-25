from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "agrotech123"

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

    return render_template('dashboard.html')

# Farmer Profile@app.route('/farmer')
@app.route('/farmer')
def farmer():

    if 'user' not in session:
        return redirect('/login')

    farmer = {
        "name": session['user']
    }

    return render_template('farmer.html', farmer=farmer)

# Crop Recommendation
@app.route('/crop')
def crop():

    if 'user' not in session:
        return redirect('/login')

    return render_template('crop.html')

# Weather Forecast
@app.route('/weather')
def weather():

    if 'user' not in session:
        return redirect('/login')

    return render_template('weather.html')

# Motor Control
@app.route('/motor')
def motor():

    if 'user' not in session:
        return redirect('/login')

    return render_template('motor.html')

# Records
@app.route('/record')
def record():

    if 'user' not in session:
        return redirect('/login')

    return render_template('records.html')

# Analytics
@app.route('/analysis')
def analysis():

    if 'user' not in session:
        return redirect('/login')

    return render_template('analysis.html')

# Logout
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)