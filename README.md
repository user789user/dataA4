# **Features implemented**

## **Checklist of stuff that is working:**

### 1. User and Role Management
- [x] Superadmin can create a user
- [x] Superadmin can change a user's department id
- [x] Superadmin can delete a user

### 2. Data Access Control
- [x] Department admin can view or edit data in their department
- [x] User can view data in their department

### 3. Views and Queries for Department-Specific Data
- [x] Views and queries filtered by department for department admins and users:
  - [x] Department table views
  - [x] Dependent views
  - [x] Dept_location views
  - [x] Employee views
  - [x] Project views
  - [x] Works_on views

### 4. Authentication and Authorization
- [x] Log in and log out
- [x] Session data according to user role and department

### 5. User Interface with Role-Based Display
- [x] Create a dashboard
    - [x] Super Admins can view all departments
    - [x] Super Admins can view all users
    - [x] Super Admins have full access.   
- [x] Base.html with links based on role

---

# Project Name: A4 Database Management System  
1. **Overview**  
   This project is a Flask-based web application that interacts with a PostgreSQL
   database to manage and display data related to employees, departments, and
   projects. It is designed with role-based access control (RBAC) to ensure that
   different users have appropriate permissions based on their roles.

2. **Requirements**
   - **Operating System**: Windows, macOS, or Linux
   - **Python**: Version 3.8 or higher
   - **PostgreSQL**: Version 11 or higher
   - **Required Python Libraries**:
     - Flask
     - psycopg2
     - Werkzeug

3. **File Structure**
    ```plaintext
    project/
    |
    ├── app.py          # Main application script
    ├── config.py       # Database configuration file
    ├── init_db.sql     # Database initialization script
    ├── templates/      # HTML template directory
    |   ├── base.html
    |   ├── test_query.html
    |   └── ...
    └── README.md       # Project documentation
    ```

4. **Setup instructions**  
   1). **Install Dependencies**  
    Run the following command to install required libraries:
      ```plaintext
      pip install flask psycopg2 werkzeug
      ```

   2). **Initialize the Database**  
      - Open PostgreSQL CLI:
        ```plaintext
        psql -U postgres
        ```
      - Create or Recreate the Database:
        ```plaintext
        DROP DATABASE IF EXISTS app_company_a4;
        CREATE DATABASE app_company_a4;
        \c app_company_a4;
        ```
      - Run the `init_db.sql` script:
        ```plaintext
        (eg.\i path/to/init_db.sql)
        ```

   3). **Configure the Project**  
      Edit the `config.py` file to set the correct database connection details:
      ```python
      DATABASE_CONFIG = {
          "dbname": "app_company_a4",
          "user": "your_username",
          "password": "your_password",
          "host": "localhost",
          "port": "5432"
      }
      ```

   4). **Run the Application**  
      Start the Flask application:
      ```plaintext
      python app.py
      ```
      Navigate to:
      ```plaintext
      http://127.0.0.1:5000
      ```
   5). **Use exist admin/user to login to test the any above task**  
    The following accounts are pre-created for testing purposes:  

    | Role        | Username      | Password           |
    |-------------|---------------|--------------------|
    | superadmin  | superadmin    | superkey     |
    | admin       | admin         | adminkey           |
    | user        | user          | userkey            |       
        
5. **Notes**  
   1). The `init_db.sql` script ensures that the required database and tables are created before running the application.
   2). Make sure the PostgreSQL username and password in `config.py` match the credentials on your system.
   3). After running the application, you can directly access the system's functionalities via the browser without needing additional setup or testing scripts.

---
## **Developer Information**
- **Group name**: Project 5  
- **Team members**: Daniela, Charles, Yin

