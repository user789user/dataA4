from flask import Flask, request, session, redirect, url_for, render_template, flash, jsonify
from functools import wraps
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config.from_pyfile('config.py')


def get_db_connection():
    conn = psycopg2.connect(**app.config['DATABASE_CONFIG'])
    return conn


# Middleware
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role_id FROM Users WHERE id = %s", (session['user_id'],))
        role = cursor.fetchone()
        cursor.close()
        conn.close()

        if role and role[0] != 2:
            flash("Access restricted to department admins.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role_id FROM Users WHERE id = %s", (session['user_id'],))
        role = cursor.fetchone()
        cursor.close()
        conn.close()

        if role and role[0] != 1:
            flash("Access restricted to superadmins.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
@login_required
def index():
    return render_template('login.html', username=session.get('username'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.password_hash, u.role_id, u.department_id, 
                   COALESCE(d.dname, 'All Departments') AS dname
            FROM Users u
            LEFT JOIN Department d ON u.department_id = d.dnumber
            WHERE u.username = %s
        """, (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            session['role_id'] = user[2]
            session['department_id'] = user[3]
            session['department_name'] = user[4]
            flash('Login successful!', 'success')
            return redirect(url_for('base'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/base')
@login_required
def base():
    role_id = session['role_id']
    return render_template('base.html', role_id=role_id)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
@superadmin_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        role_id = request.form['roleid']
        department_id = request.form.get('departmentid') or None  # Convert empty string to None

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Users (username, password_hash, role_id, department_id) VALUES (%s, %s, %s, %s)",
                (username, hashed_password, role_id, department_id))
            conn.commit()
            flash('User created successfully!', 'create')
        except Exception as e:
            flash(f"Error creating user: {e}", 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/deleteuser', methods=['GET', 'POST'])
@superadmin_required
def deleteuser():
    if request.method == 'POST':
        user_id = request.form['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Users WHERE id = %s", (user_id,))
            conn.commit()
            flash('User deleted successfully!', 'deleteuser')
        except Exception as e:
            flash(f"Error deleting user: {e}", 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return render_template('deleteuser.html')

# Route to view all departments
@app.route('/viewdepartments')
def viewdepartments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Dnumber, Dname, Mgr_ssn FROM Department")
    departments = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('viewdepartments.html', departments=departments)


@app.route('/departments/add', methods=('GET', 'POST'))
def add_department():
    if request.method == 'POST':
        dname = request.form['dname']
        dnumber = request.form['dnumber']
        mgr_ssn = request.form['mgr_ssn']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Department (Dname, Dnumber, Mgr_ssn) VALUES (%s, %s, %s)",
            (dname, dnumber, mgr_ssn)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('viewdepartments'))

    return render_template('add_department.html')


# Route to update a department
@app.route('/departments/update/<int:dnumber>', methods=('GET', 'POST'))
def update_department(dnumber):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        dname = request.form['dname']
        mgr_ssn = request.form['mgr_ssn']

        cursor.execute("UPDATE Department SET Dname = %s, Mgr_ssn = %s WHERE Dnumber = %s",
                       (dname, mgr_ssn, dnumber))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('viewdepartments'))

    cursor.execute(
        "SELECT Dnumber, Dname, Mgr_ssn FROM Department WHERE Dnumber = %s", (dnumber,))
    department = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('update_department.html', department=department)

# Route to delete a department


@app.route('/departments/delete/<int:dnumber>', methods=('POST',))
def delete_department(dnumber):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Department WHERE Dnumber = %s", (dnumber,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('viewdepartments'))


# Route to view all projects
@app.route('/projects')
def view_projects():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Pnumber, Pname, Plocation, Dnum FROM Project")
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('projects.html', projects=projects)

# Route to add a new project


@app.route('/projects/add', methods=('GET', 'POST'))
def add_project():
    if request.method == 'POST':
        pname = request.form['pname']
        pnumber = request.form['pnumber']
        plocation = request.form['plocation']
        dnum = request.form['dnum']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Project (Pname, Pnumber, Plocation, Dnum) VALUES (%s, %s, %s, %s)", (
                pname, pnumber, plocation, dnum)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_projects'))

    return render_template('add_project.html')


# Route to update a project
@app.route('/projects/update/<int:pnumber>', methods=('GET', 'POST'))
def update_project(pnumber):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        pname = request.form['pname']
        plocation = request.form['plocation']
        dnum = request.form['dnum']

        cursor.execute("UPDATE Project SET Pname = %s, Plocation = %s, Dnum = %s WHERE Pnumber = %s",
                       (pname, plocation, dnum, pnumber))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_projects'))

    cursor.execute(
        "SELECT Pnumber, Pname, Plocation, Dnum FROM Project WHERE Pnumber = %s", (pnumber,))
    project = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('update_project.html', project=project)

# Route to delete a project


@app.route('/projects/delete/<int:pnumber>', methods=('POST',))
def delete_project(pnumber):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Project WHERE Pnumber = %s", (pnumber,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_projects'))


@app.route('/joined_data')
def view_joined_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Example SQL join query to fetch data from Employee, Department, and Project tables
    cursor.execute("""
        SELECT e.Fname, e.Lname, e.Salary, d.Dname, p.Pname, p.Plocation
        FROM Employee e
        JOIN Department d ON e.Dno = d.Dnumber
        JOIN Project p ON d.Dnumber = p.Dnum
        ORDER BY e.Lname, e.Fname;
    """)

    joined_data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('joined_data.html', joined_data=joined_data)


if __name__ == "__main__":
    app.run(debug=True)
