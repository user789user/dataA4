from flask import Flask, request, session, redirect, url_for, render_template, flash, jsonify
from functools import wraps
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'my_random_key'
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
            flash("Please log in to access this page.", "login_erro")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role_id FROM Users WHERE id = %s", (session['user_id'],))
        role = cursor.fetchone()
        cursor.close()
        conn.close()

        if role and role[0] != 2:
            flash("Access restricted to department admins.", "privilege2_error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function

def superadmin_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cursor = conn.cursor()
        print(session['user_id'])
        cursor.execute("SELECT role_id FROM Users WHERE id = %s", (session['user_id'],))
        role = cursor.fetchone()
        cursor.close()
        conn.close()

        if role and (role[0] != 1 and role[0] != 2):
            flash("Access restricted to admins or superadmins.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "login_erro")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role_id FROM Users WHERE id = %s", (session['user_id'],))
        role = cursor.fetchone()
        cursor.close()
        conn.close()

        if role and role[0] != 1:
            flash("Access restricted to superadmins.", "privilege1_error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


#####################################################################################################################################
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
            flash('Login successful!', 'login_success')
            return redirect(url_for('base'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'logout')
    return redirect(url_for('login'))


@app.route('/base')
@login_required
def base():
    role_id = session['role_id']
    return render_template('base.html', role_id=role_id)


# user access below
@app.route('/view_users')
@superadmin_required
def view_users():
    """
    View all users. Only accessible by Super Admin.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role_id, department_id FROM users ORDER BY id ASC")
        users = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('view_users.html', users=users)
    except Exception as e:
        flash(f"Error fetching users: {e}", "view_users_error")
        return redirect(url_for('view_users'))


@app.route('/users/update/<int:user_id>', methods=('GET', 'POST'))
@superadmin_required
def update_user(user_id):
    """
    Update user details. Only accessible by Super Admin.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Fetch form data
        role_id = request.form['role_id']
        department_id = request.form.get('department_id')  # Allow None for Super Admin

        # Update user details in the database
        cursor.execute("""
            UPDATE users 
            SET role_id = %s, department_id = %s 
            WHERE id = %s
        """, (role_id, department_id if department_id else None, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        flash("User updated successfully!", "suser_update_uccess")
        return redirect(url_for('view_users'))

    # Fetch user details for the given user_id
    cursor.execute("SELECT id, username, role_id, department_id FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        flash("User not found!", "user_not_found_error")
        return redirect(url_for('view_users'))

    return render_template('update_user.html', user=user)


@app.route('/users/delete/<int:user_id>', methods=['POST'])
@superadmin_required
def delete_user(user_id):
    """
    Delete a user. Only accessible by Super Admin.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Execute the delete query
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        flash("User deleted successfully!", "user_delete_success")
    except Exception as e:
        flash(f"An error occurred while deleting the user: {e}", "user_delete_error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('view_users'))


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


# department below
@app.route('/view_departments', methods=['GET'])
@login_required
def view_departments():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check user role and department
    role_id = session.get('role_id')
    department_id = session.get('department_id')

    if role_id == 1:  # Super Admin
        cursor.execute("SELECT Dnumber, Dname, Mgr_ssn FROM Department")
    elif role_id in [2, 3]:  # Department Admin
        cursor.execute("SELECT Dnumber, Dname, Mgr_ssn FROM Department WHERE Dnumber = %s", (department_id,))
    else:
        # Normal users cannot access departments
        flash("Access denied. You do not have permission to view departments.", "view_department_error")
        cursor.close()
        conn.close()
        return redirect(url_for('base'))

    departments = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('view_departments.html', departments=departments)


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
        return redirect(url_for('view_departments'))

    return render_template('add_department.html')


@app.route('/departments/update/<int:dnumber>', methods=('GET', 'POST'))
@superadmin_required
def update_department(dnumber):
    """
    Update department details. Only accessible by Super Admin.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_dnumber = request.form['dnumber']
        dname = request.form['dname']
        mgr_ssn = request.form['mgr_ssn']

        try:
            cursor.execute("""
                UPDATE Department
                SET Dnumber = %s, Dname = %s, Mgr_ssn = %s
                WHERE Dnumber = %s
            """, (new_dnumber, dname, mgr_ssn, dnumber))
            conn.commit()
            flash("Department updated successfully!", "department_update_success")
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Failed to update department. The new Department ID might already exist.", "department_update_error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('view_departments'))

    cursor.execute(
        "SELECT Dnumber, Dname, Mgr_ssn FROM Department WHERE Dnumber = %s", (dnumber,))
    department = cursor.fetchone()
    cursor.close()
    conn.close()

    if not department:
        flash("Department not found!", "error")
        return redirect(url_for('view_departments'))

    return render_template('update_department.html', department=department)


@app.route('/departments/delete/<int:dnumber>', methods=('POST',))
def delete_department(dnumber):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Department WHERE Dnumber = %s", (dnumber,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_departments'))


# Employee below
@app.route('/view_employees', methods=['GET'])
@login_required
def view_employees():
    """
    View employees. Normal users can only view data, while admins and superadmins can perform actions.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    role_id = session.get('role_id')
    department_id = session.get('department_id')

    try:
        if role_id == 1:  # Super Admin
            cursor.execute("SELECT SSN, Fname, Minit, Lname, Address, Salary, Dno FROM Employee")
        elif role_id == 2:  # Department Admin
            cursor.execute("SELECT SSN, Fname, Minit, Lname, Address, Salary, Dno FROM Employee WHERE Dno = %s", (department_id,))
        elif role_id == 3:  # Normal User
            cursor.execute("SELECT SSN, Fname, Minit, Lname, Address, Salary, Dno FROM Employee WHERE Dno = %s", (department_id,))
        else:
            flash("Access denied. You do not have permission to view employees.", "view_employee_error")
            return redirect(url_for('base'))

        employees = cursor.fetchall()
    except psycopg2.Error as e:
        flash(f"An error occurred while fetching employees: {e}", "view_employee_fetch_error")
        employees = []
    finally:
        cursor.close()
        conn.close()

    return render_template('view_employees.html', employees=employees, role_id=role_id)


@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    """
    Add a new employee. Admins can only add employees to their department.
    """
    role_id = session.get('role_id')
    department_id = session.get('department_id')

    if role_id not in [1, 2]:
        flash("Access denied. Only Admins and Super Admins can add employees.", "add_employee_error")
        return redirect(url_for('view_employees'))

    if request.method == 'POST':
        fname = request.form['fname']
        minit = request.form.get['minit']
        lname = request.form['lname']
        ssn = request.form['ssn']
        address = request.form['address']
        sex = request.form['sex']
        salary = request.form['salary']
        super_ssn = request.form.get['super_ssn']
        dno = request.form['dno']

        if role_id == 2 and int(dno) != department_id:
            flash("You can only add employees to your department.", "add_employee_2_error")
            return redirect(url_for('view_employees'))

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Employee (Fname, Minit, Lname, SSN, Address, Sex, Salary, Super_ssn, Dno)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (fname, minit, lname, ssn, address, sex, salary, super_ssn, dno))
            conn.commit()
            flash("Employee added successfully!", "add_employee_success")
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Failed to add employee. Ensure the SSN and Department Number are valid and unique.",
                  "add_employee_3_error")
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('view_employees'))

    return render_template('add_employee.html')


@app.route('/employees/update/<ssn>', methods=('GET', 'POST'))
@login_required
def update_employee(ssn):
    """
    Update employee details.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Fetch data from the form
        fname = request.form['fname']
        lname = request.form['lname']
        address = request.form['address']
        salary = request.form['salary']
        dno = request.form['dno']

        # Update employee details in the database
        cursor.execute("""
            UPDATE Employee
            SET Fname = %s, Lname = %s, Address = %s, Salary = %s, Dno = %s
            WHERE SSN = %s
        """, (fname, lname, address, salary, dno, ssn))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Employee updated successfully!", "update_employee_success")
        return redirect(url_for('view_employees'))

    # Fetch employee details for the given SSN
    cursor.execute("""
        SELECT SSN, Fname, Lname, Address, Salary, Dno
        FROM Employee
        WHERE SSN = %s
    """, (str(ssn),))  # Ensure SSN is passed as a string
    employee = cursor.fetchone()
    cursor.close()
    conn.close()

    if not employee:
        flash("Employee not found!", "update_employee_error")
        return redirect(url_for('view_employees'))

    return render_template('update_employee.html', employee=employee)


@app.route('/employees/delete/<ssn>', methods=['POST'])
@login_required
def delete_employee(ssn):
    """
    Delete an employee. Only accessible to Super Admins and Admins within their department.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Ensure SSN is treated as a string
        cursor.execute("DELETE FROM Employee WHERE SSN = %s", (str(ssn),))
        conn.commit()
        flash("Employee deleted successfully!", "delete_employee_success")
    except psycopg2.Error as e:
        conn.rollback()
        flash("Failed to delete employee. Please try again.", "delete_employee_error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('view_employees'))

###################-----finish part above-------############################################################################################

# Route to view all projects
@app.route('/projects')
def view_projects():
    conn = get_db_connection()
    cursor = conn.cursor()

    if session['department_id'] != None:
        dnum = session['department_id']
        cursor.execute("SELECT Pnumber, Pname, Plocation, Dnum FROM Project WHERE Dnum=%s", (dnum, ))
        projects = cursor.fetchall()

    else: 
        cursor.execute("SELECT Pnumber, Pname, Plocation, Dnum FROM Project")
        projects = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('view_projects.html', projects=projects)


# Route to add a new project
@app.route('/projects/add', methods=('GET', 'POST'))
@superadmin_or_admin_required
def add_project():
    if request.method == 'POST':
        pname = request.form['pname']
        pnumber = request.form['pnum']
        plocation = request.form['plocation']
        dnum = request.form['dnum']

        # if the user isn't a superadmin - they are restricted to only adding projects to their own department
        if session['department_id'] != None:
            dnum = session['department_id']

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

    if session['department_id'] == None:
        cursor.execute("DELETE FROM Project WHERE Pnumber = %s", (pnumber,))
    else: 
        cursor.execute("SELECT FROM Project, Department WHERE Pnumber = %s AND Dnumber = %s AND Dnum = Dnumber", 
                       (pnumber, session['department_id']))
        project = cursor.fetchall()
        if project:
            cursor.execute("DELETE FROM Project WHERE Pnumber = %s", (pnumber,))
        else: 
            conn.rollback()
            flash("Failed to delete project - the project is not in the correct department.", "delete_project_error")

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_projects'))

@app.route('/worksOn')
def view_worksOn():
    conn = get_db_connection()
    cursor = conn.cursor()
    if session['department_id'] != None:
        dnum = session['department_id']
        cursor.execute("SELECT Essn, Pno, Hours FROM Works_On, Employee WHERE Essn=SSN And Dno = %s",(dnum,))
        worksOn = cursor.fetchall()
    else:
        cursor.execute("SELECT Essn, Pno, Hours FROM Works_On")
        worksOn = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_worksOn.html', worksOn=worksOn)
    
# keep for backup page
@app.route('/testing')
def testing():
    return render_template('testing.html')


if __name__ == "__main__":
    app.run(debug=True)
