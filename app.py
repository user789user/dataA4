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
def index():
    session.pop('_flashes', None)
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

    # Fetch all department IDs to populate the dropdown
    cursor.execute("SELECT dnumber FROM Department")
    all_dnumbers = [row[0] for row in cursor.fetchall()]

    if request.method == 'POST':
        # Fetch form data
        role_id = request.form['role_id']
        department_id = request.form.get('department_id')  # Allow None for Super Admin

        # Convert empty string to None
        if department_id == "":
            department_id = None

        # Update user details in the database
        cursor.execute("""
            UPDATE users
            SET role_id = %s, department_id = %s
            WHERE id = %s
        """, (role_id, department_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        flash("User updated successfully!", "update_success")
        return redirect(url_for('view_users'))

    # Fetch user details for the given user_id
    cursor.execute("SELECT id, username, role_id, department_id FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        flash("User not found!", "user_not_found_error")
        return redirect(url_for('view_users'))

    return render_template('update_user.html', user=user, all_dnumbers=all_dnumbers)


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
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all department IDs to populate the dropdown
    cursor.execute("SELECT dnumber FROM Department")
    all_dnumbers = [row[0] for row in cursor.fetchall()]  # Convert to a list

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        role_id = request.form['roleid']
        department_id = request.form.get('departmentid')  # Optional

        # Convert empty string to None
        if department_id == "":
            department_id = None

        try:
            cursor.execute(
                "INSERT INTO Users (username, password_hash, role_id, department_id) VALUES (%s, %s, %s, %s)",
                (username, hashed_password, role_id, department_id)
            )
            conn.commit()
            flash('User created successfully!', 'create')
        except Exception as e:
            conn.rollback()
            flash(f"Error creating user: {e}", 'error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('view_users'))

    # Pass `all_dnumbers` to the template
    cursor.close()
    conn.close()
    return render_template('register.html', all_dnumbers=all_dnumbers)


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
@superadmin_required
def add_department():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all SSNs from Employee table
    cursor.execute("SELECT SSN FROM Employee")
    employee_ssns = [row[0] for row in cursor.fetchall()]  # Convert to a list of SSNs

    if request.method == 'POST':
        dname = request.form['dname']
        dnumber = request.form['dnumber']
        mgr_ssn = request.form['mgr_ssn']

        try:
            cursor.execute(
                "INSERT INTO Department (Dname, Dnumber, Mgr_ssn) VALUES (%s, %s, %s)",
                (dname, dnumber, mgr_ssn)
            )
            conn.commit()
            flash("Department added successfully!", "success")
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Failed to add department. Ensure the Department Number and Manager SSN are valid and unique.",
                  "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('view_departments'))

    cursor.close()
    conn.close()
    return render_template('add_department.html', employee_ssns=employee_ssns)


@app.route('/departments/update/<int:dnumber>', methods=('GET', 'POST'))
@superadmin_required
def update_department(dnumber):
    """
    Update department details. Only accessible by Super Admin.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all SSNs from Employee table
    cursor.execute("SELECT SSN FROM Employee")
    employee_ssns = [row[0] for row in cursor.fetchall()]  # Convert to a list of SSNs

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

    if not department:
        flash("Department not found!", "error")
        return redirect(url_for('view_departments'))

    cursor.close()
    conn.close()

    return render_template('update_department.html', department=department, employee_ssns=employee_ssns)


@app.route('/departments/delete/<int:dnumber>', methods=('POST',))
@superadmin_required
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
            cursor.execute(
                "SELECT Fname, Minit, Lname, SSN, Address, Sex, Salary, Super_ssn, Dno, Bdate, Empdate FROM Employee")
        elif role_id in [2, 3]:  # Department Admin&user
            cursor.execute(
                "SELECT Fname, Minit, Lname, SSN, Address, Sex, Salary, Super_ssn, Dno, Bdate, Empdate FROM Employee WHERE Dno = %s",
                (department_id,))
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

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT dnumber FROM Department""")
    all_dnumbers = [row[0] for row in cursor.fetchall()]

    if role_id not in [1, 2]:
        flash("Access denied. Only Admins and Super Admins can add employees.", "add_employee_error")
        return redirect(url_for('view_employees'))

    if request.method == 'POST':
        fname = request.form['fname']
        minit = request.form.get('minit', None)
        lname = request.form['lname']
        ssn = request.form['ssn']
        address = request.form['address']
        sex = request.form.get('sex', None)
        salary = request.form['salary']
        super_ssn = request.form.get('super_ssn', None)
        dno = request.form['dno']

        if role_id == 2 and int(dno) != department_id:
            flash("You can only add employees to your department.", "add_employee_2_error")
            return redirect(url_for('view_employees'))

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

    cursor.close()
    conn.close()
    return render_template('add_employee.html', all_dnumbers=all_dnumbers)


@app.route('/employees/update/<ssn>', methods=('GET', 'POST'))
@login_required
def update_employee(ssn):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch employee details for the given SSN
    cursor.execute("""
        SELECT Fname, Minit, Lname, SSN, Address, Sex, Salary, Super_ssn, Dno, Bdate, Empdate
        FROM Employee
        WHERE SSN = %s
    """, (str(ssn),))  # Ensure SSN is passed as a string

    employee = cursor.fetchone()

    cursor.execute("""SELECT dnumber FROM Department""")
    all_dnumbers = [row[0] for row in cursor.fetchall()]

    if request.method == 'POST':
        # Fetch data from the form
        fname = request.form['fname']
        minit = request.form['minit']
        lname = request.form['lname']
        address = request.form['address']
        sex = request.form['sex']
        salary = request.form['salary']
        super_ssn = request.form['super_ssn']
        dno = request.form['dno']

        # Update employee details in the database
        cursor.execute("""
            UPDATE Employee
            SET Fname = %s, Minit = %s, Lname = %s, Address = %s, Sex = %s, Salary = %s, Super_ssn = %s, Dno = %s
            WHERE SSN = %s
        """, (fname, minit, lname, address, sex, salary, super_ssn, dno, ssn))
        conn.commit()

        flash("Employee updated successfully!", "update_employee_success")
        return redirect(url_for('view_employees'))

    if not employee:
        flash("Employee not found!", "update_employee_error")
        return redirect(url_for('view_employees'))
    cursor.close()
    conn.close()
    return render_template('update_employee.html', employee=employee, all_dnumbers=all_dnumbers)


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
        flash(f"Employee {ssn} deleted successfully!", "delete_employee_success")
    except psycopg2.Error as e:
        conn.rollback()
        flash("Failed to delete employee. Please try again.", "delete_employee_error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('view_employees'))


###############################################changes above###########################################################

# Route to view all projects
@app.route('/projects')
@login_required
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

        conn = get_db_connection()
        cursor = conn.cursor()

        # if the user isn't a superadmin - they are restricted to only adding projects to their own department
        if session['department_id'] == None:
            cursor.execute("INSERT INTO Project (Pname, Pnumber, Plocation, Dnum) VALUES (%s, %s, %s, %s)", (
                pname, pnumber, plocation, dnum))
            conn.commit()
        else:     
            #if the project has the same dept as the user, allow the user to add it
            if dnum == session['department_id']:
                cursor.execute("UPDATE Project SET Pname = %s, Plocation = %s, Dnum = %s WHERE Pnumber = %s",
                       (pname, plocation, dnum, pnumber))
                conn.commit()
            else:
                conn.rollback()
                flash("Failed to update project - the project is not in the correct department.", "update_project_error")

        cursor.close()
        conn.close()
        return redirect(url_for('view_projects'))

    return render_template('add_project.html')


# Route to update a project
@app.route('/projects/update/<int:pnumber>', methods=('GET', 'POST'))
@superadmin_or_admin_required
def update_project(pnumber):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        pname = request.form['pname']
        plocation = request.form['plocation']
        dnum = request.form['dnum']

        if session['department_id'] == None:
            cursor.execute("UPDATE Project SET Pname = %s, Plocation = %s, Dnum = %s WHERE Pnumber = %s",
                       (pname, plocation, dnum, pnumber))
            conn.commit()
        else:
            cursor.execute("SELECT FROM Project, Department WHERE Pnumber = %s AND Dnumber = %s AND Dnum = Dnumber", 
                       (pnumber, session['department_id']))
            project = cursor.fetchall()

            #if the project has the same dept, allow the user to update it
            if project:
                cursor.execute("UPDATE Project SET Pname = %s, Plocation = %s, Dnum = %s WHERE Pnumber = %s",
                       (pname, plocation, dnum, pnumber))
                conn.commit()
            else:
                conn.rollback()
                flash("Failed to update project - the project is not in the correct department.", "update_project_error")
        
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
@superadmin_or_admin_required
def delete_project(pnumber):
    conn = get_db_connection()
    cursor = conn.cursor()

    if session['department_id'] == None:
        cursor.execute("DELETE FROM Project WHERE Pnumber = %s", (pnumber,))
        conn.commit()
    else: 
        cursor.execute("SELECT FROM Project, Department WHERE Pnumber = %s AND Dnumber = %s AND Dnum = Dnumber", 
                       (pnumber, session['department_id']))
        project = cursor.fetchall()
        if project:
            cursor.execute("DELETE FROM Project WHERE Pnumber = %s", (pnumber,))
            conn.commit()
        else: 
            conn.rollback()
            flash("Failed to delete project - the project is not in the correct department.", "delete_project_error")

    cursor.close()
    conn.close()
    return redirect(url_for('view_projects'))

# View works On
###
### **** SHOULD WORKSON VIEW BE DEPENDENT ON DEPARTMENT OF EMPLOYEE OR DEPARTMENT OF PROJECT *****
###
@app.route('/worksOn')
@login_required
def view_worksOn():
    conn = get_db_connection()
    cursor = conn.cursor()
    if session['department_id'] != None:
        dnum = session['department_id']
        cursor.execute("SELECT Essn, Pno, Hours FROM Works_On, Project WHERE Pno=Pnumber And Dnum = %s",(dnum,))
        worksOn = cursor.fetchall()
    else:
        cursor.execute("SELECT Essn, Pno, Hours FROM Works_On")
        worksOn = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_worksOn.html', worksOn=worksOn)
    
# Add works On    
@app.route('/worksOn/add', methods=('GET', 'POST'))
@superadmin_or_admin_required
def add_worksOn():
    if request.method == 'POST':
        Essn = request.form['essn']
        Pno = request.form['pnum']
        Hours = request.form['Hours']
        
        if session['department_id'] != None:
            conn=get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Dnum FROM Project WHERE Pnumber=%s",(Pno,))
            Dno = cursor.fetchone()
            if(Dno[0] != session['department_id']):
                flash("You can only assign work to employees within your own department.")
                return redirect(url_for('view_worksOn'))
            cursor.close()
            conn.close()
        conn=get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Works_On (Essn, Pno, Hours) VALUES (%s, %s, %s)", (Essn, Pno, Hours,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_worksOn'))
    return render_template('add_worksOn.html')
       
# Update Works On
# Add check for admin department        
@app.route('/worksOn/update/<string:ssn>/<int:pnumber>', methods=('GET', 'POST'))
@superadmin_or_admin_required
def update_worksOn(ssn, pnumber):
    conn = get_db_connection()
    cursor = conn.cursor() 
    if request.method == 'POST':
        Hours = request.form['Hours']
        if session['department_id'] != None:
            cursor.execute("SELECT Dnum FROM Project WHERE Pnumber=%s",(pnumber,))
            Dno = cursor.fetchone()
            if(Dno[0] != session['department_id']):
                flash("You can only update work to projects within your department.")
                return redirect(url_for('view_worksOn'))
        cursor.execute("UPDATE Works_On SET Hours = %s WHERE Pno=%s And Essn=%s", (Hours,pnumber,ssn))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_worksOn'))
    cursor.execute("SELECT Essn, Pno, Hours FROM Works_On WHERE Essn = %s and Pno = %s",(ssn,pnumber,))
    worksOn = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('update_worksOn.html',worksOn=worksOn)               

# Delete Works On
@app.route('/worksOn/delete/<string:ssn>/<int:pnumber>', methods=('GET', 'POST'))
@superadmin_or_admin_required
def delete_worksOn(ssn, pnumber):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if session['department_id'] == None:
        cursor.execute("DELETE FROM Works_On WHERE Pno=%s And Essn=%s", (pnumber, ssn,))
    else:
        cursor.execute("SELECT FROM Works_On, Project WHERE Pno=%s And Essn=%s And Essn=SSN And Dno=%s",(pnumber,ssn,session['department_id']))
        worksOn = cursor.fetchall()
        if worksOn:
            cursor.execute("DELETE FROM Works_On WHERE Pno=%s And Essn=%s", (pnumber,ssn))
        else:
            conn.rollback()
            flash("Failed to delete works on - incorrect department")
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_worksOn'))

#Dependents

@app.route('/dependents')
@login_required
def view_dependents():
    conn = get_db_connection()
    cursor = conn.cursor()
    if session['department_id'] != None:
        dnum = session['department_id']
        cursor.execute("SELECT Essn, Dependent_name, d.Sex, d.Bdate, Relationship FROM Dependent d, Employee E WHERE Essn=SSN and Dno=%s",(dnum,))
        dependents = cursor.fetchall()
    else:
        cursor.execute("SELECT Essn, Dependent_name, Sex, Bdate, Relationship FROM Dependent")
        dependents = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_dependents.html', dependents=dependents)

@app.route('/dependents/add', methods=('GET', 'POST'))
@superadmin_or_admin_required
def add_dependent():
    if request.method == 'POST':
        Essn = request.form['SSN']
        Dependent_name = request.form['Dependent_Name']
        Sex = request.form['Sex']
        Bdate = request.form['Birthday']
        Relationship = request.form['Relationship']
        if session['department_id'] != None:
            conn=get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Dno FROM Employee WHERE SSN=%s",(Essn,))
            Dno = cursor.fetchone()
            if(Dno[0] != session['department_id']):
                flash("You can only add dependents for your own department.")
                return redirect(url_for('view_dependents'))
            cursor.close()
            conn.close()
        conn=get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Dependent VALUES (%s, %s, %s, %s, %s)",(Essn, Dependent_name, Sex, Bdate, Relationship))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_dependents'))
    return render_template('add_dependent.html')

@app.route('/dependents/update/<string:ssn>/<string:depName>', methods=('GET', 'POST'))
@superadmin_or_admin_required
def update_dependents(ssn,depName):
    conn = get_db_connection()
    cursor = conn.cursor()
    if session['department_id'] != None:
            cursor.execute("SELECT Dno FROM Employee WHERE SSN=%s",(ssn,))
            Dno = cursor.fetchone()
            if(Dno[0] != session['department_id']):
                return redirect(url_for('view_dependents'))
    if request.method == 'POST':
        Sex= request.form['Sex']
        Bdate = request.form['Birthday']
        Relationship = request.form['Relationship']
        cursor.execute("UPDATE Dependent SET Sex = %s, Bdate = %s, Relationship = %s WHERE Essn = %s and Dependent_name = %s", (Sex,Bdate,Relationship,ssn,depName))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_dependents'))
    cursor.execute("SELECT Essn, Dependent_name, Sex, Bdate, Relationship FROM Dependent WHERE Essn = %s and Dependent_name = %s",(ssn,depName,))
    dependent = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('update_dependents.html',dependent=dependent)

@app.route('/dependents/delete/<string:ssn>/<string:depName>', methods=('GET', 'POST'))
@superadmin_or_admin_required
def delete_dependents(ssn, depName):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if session['department_id'] == None:
        cursor.execute("DELETE FROM Dependent WHERE Dependent_name=%s And Essn=%s", (depName, ssn,))
    else:
        cursor.execute("SELECT FROM Employee WHERE Essn=%s And Dno=%s",ssn,session['department_id'])
        department = cursor.fetchall()
        if department:
            cursor.execute("DELETE FROM Dependent WHERE Dependent_name=%s And Essn=%s", (depName,ssn))
        else:
            conn.rollback()
            flash("Failed to delete works on - incorrect department")
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_dependents'))


#department location views

# Route to view all locations
@app.route('/locations')
@login_required
def view_locations():
    conn = get_db_connection()
    cursor = conn.cursor()

    if session['department_id'] != None:
        dnumber = session['department_id']
        try:
            cursor.execute("CREATE VIEW LocationsByDept AS SELECT Dnumber, Dlocation FROM Dept_location WHERE Dnumber=%s", (dnumber,))
            conn.commit()
        except psycopg2.errors.DuplicateTable:
            conn.rollback()
            cursor.execute("DROP VIEW LocationsByDept")
            cursor.execute("CREATE VIEW LocationsByDept AS SELECT Dnumber, Dlocation FROM Dept_location WHERE Dnumber=%s", (dnumber,))
            conn.commit()

        cursor.execute("SELECT * FROM LocationsByDept")
        locations = cursor.fetchall()

    else: 
        cursor.execute("SELECT Dnumber, Dlocation FROM Dept_location")
        locations = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('view_locations.html', locations=locations)


# Route to add a new department location
@app.route('/locations/add', methods=('GET', 'POST'))
@superadmin_or_admin_required
def add_location():
    if request.method == 'POST':
        dnumber = request.form['dnumber']
        dlocation = request.form['dlocation']

        conn = get_db_connection()
        cursor = conn.cursor()

        if session['department id'] == None:
            cursor.execute("INSERT INTO Dept_location (Dnumber, Dlocation) VALUES (%s, %s)", (dnumber, dlocation))
            conn.commit()
        else:
            cursor.execute("SELECT FROM Dept_location AS DL, Department AS D WHERE DL.Dnumber = %s AND D.Dnumber = %s AND DL.Dnumber = D.Dnumber", 
                       (dnumber, session['department_id']))
            location = cursor.fetchall()
            if location:
                cursor.execute("INSERT INTO Dept_location (Dnumber, Dlocation) VALUES (%s, %s)", (dnumber, dlocation))
                conn.commit()
            else:
                conn.rollback()
                flash("Failed to insert - the department location is not in the correct department.", "add_location_error")

        cursor.close()
        conn.close()
        return redirect(url_for('view_locations'))

    return render_template('add_location.html')


# Route to update a location
@app.route('/location/update/<int:dnumber>/<dlocation>', methods=('GET', 'POST'))
@superadmin_or_admin_required
def update_location(dnumber, dlocation):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        dnumbernew = request.form['dnumber']
        dlocationnew = request.form['dlocation']

        if session['department_id'] == None:
            cursor.execute("UPDATE Dept_location SET Dlocation = %s, Dnumber = %s WHERE Dnumber = %s AND Dlocation = %s",
                       (dlocationnew, dnumbernew, dnumber, dlocation))
            conn.commit()
        else:
            cursor.execute("SELECT FROM Dept_location AS DL, Department AS D WHERE DL.Dnumber = %s AND D.Dnumber = %s AND DL.Dnumber = D.Dnumber", 
                       (dnumber, session['department_id']))
            location = cursor.fetchall()

            #if the location has the same dept, allow the user to update it
            if location:
                cursor.execute("UPDATE Dept_location SET Dlocation = %s AND Dnumber = %s WHERE Dnumber = %s AND Dlocation = %s",
                       (dlocation, dnumber, dnumber, dlocation))
                conn.commit()
            else:
                conn.rollback()
                flash("Failed to update - the department location is not in the correct department.", "update_location_error")
        
        cursor.close()
        conn.close()
        return redirect(url_for('view_locations'))

    cursor.execute(
        "SELECT Dnumber, Dlocation FROM Dept_location WHERE Dnumber = %s AND Dlocation = %s", (dnumber, dlocation))
    location = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('update_location.html', dept_location=location)


# Route to delete a project
@app.route('/locations/delete/<int:dnumber>/<dlocation>', methods=('POST',))
@superadmin_or_admin_required
def delete_location(dnumber, dlocation):
    conn = get_db_connection()
    cursor = conn.cursor()

    if session['department_id'] == None:
        cursor.execute("DELETE FROM Dept_location WHERE Dnumber = %s AND Dlocation = %s", (dnumber, dlocation))
        conn.commit()
    else: 
        cursor.execute("SELECT FROM Dept_location AS DL, Department AS D WHERE DL.Dnumber = %s AND D.Dnumber = %s AND DL.Dnumber = D.Dnumber", 
                       (dnumber, session['department_id']))
        location = cursor.fetchall()
        if location:
            cursor.execute("DELETE FROM Dept_location WHERE Dnumber = %sAND Dlocation = %s", (dnumber, dlocation))
            conn.commit()
        else: 
            conn.rollback()
            flash("Failed to delete - the department location is not in the correct department.", "delete_location_error")

    cursor.close()
    conn.close()
    return redirect(url_for('view_locations'))


# keep for backup page
@app.route('/testing')
def testing():
    return render_template('testing.html')


if __name__ == "__main__":
    app.run(debug=True)
