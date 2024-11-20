from flask import Flask, request, session, redirect, url_for, render_template, flash
from functools import wraps
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config.from_pyfile('config.py')


def get_db_connection():
    conn = psycopg2.connect(**app.config['DATABASE_CONFIG'])
    return conn


# Middleware: login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            user_id = session['user_id']
            
            cursor.execute("SELECT role_id FROM Users WHERE ID = %s", (user_id,))
            user_role = cursor.fetchone()

            if user_role[0] != 1:
                flash("Only superadmins can see this.", "error")
                return redirect(url_for("login"))

            cursor.close()
            conn.close()
                
        return f(*args, **kwargs)
    return decorated_function


@app.route('/register', methods=['GET', 'POST'])
@superadmin_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        role_id = request.form['roleid']
        department_id = request.form['departmentid']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Users (username, password_hash, role_id, department_id) VALUES (%s, %s, %s, %s)",
                           (username, hashed_password, role_id, department_id))
            conn.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration error: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/deleteuser', methods=['GET','POST'])
@superadmin_required
def deleteuser():
    if request.method == 'POST':
        username = request.form['username']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Users WHERE username = %s",(username,))
            conn.commit()
            #redirect somewhere else
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration error: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return render_template('deleteuser.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, password_hash FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()  # Clear all session data to log out
    flash('You have been logged out.')
    return redirect(url_for('index'))


@app.route('/user')
def show_user():
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You need to log in to view this page.')
        return redirect(url_for('login'))

    # Fetch only the logged-in user's data
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, role_id FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()  # Retrieve the row for the current user
    print(user[0])
    cursor.close()
    conn.close()

    # Pass the user data to the template
    return render_template('user.html', user=user)


@app.route('/')
@login_required
def index():
    username = session.get('username')
    return render_template('index.html', username=username)


if __name__ == "__main__":
    app.run(debug=True)
