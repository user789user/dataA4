# **Features implemented**

## **Checklist of stuff that is working:**

### 1. User and Role Management
- [x] Superadmin can create a user
- [x] Superadmin can change a user's department id
- [ ] Superadmin can delete a user

### 2. Data Access Control
- [ ] Department admin can view or edit data in their department
- [ ] User can view data in their department

### 3. Views and Queries for Department-Specific Data
- [ ] Views and queries filtered by department for department admins and users:
  - [ ] Department table views
  - [ ] Dependent views
  - [ ] Dept_location views
  - [ ] Employee views
  - [ ] Project views
  - [ ] Works_on views

### 4. Authentication and Authorization
- [ ] Log in and log out
- [ ] Session data according to user role and department

### 5. User Interface with Role-Based Display
- [ ] Dashboard
- [ ] Base.html with links based on role

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
        DROP DATABASE IF EXISTS a4_db;
        CREATE DATABASE a4_db;
        \c a4_db;
        ```
      - Run the `init_db.sql` script:
        ```plaintext
        \i path/to/init_db.sql
        ```

   3). **Configure the Project**  
      Edit the `config.py` file to set the correct database connection details:
      ```python
      DATABASE_CONFIG = {
          "dbname": "a4_db",
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

5. **Notes**  
   1). The `init_db.sql` script ensures that the required database and tables are created before running the application.
   2). Make sure the PostgreSQL username and password in `config.py` match the credentials on your system.
   3). After running the application, you can directly access the system's functionalities via the browser without needing additional setup or testing scripts.

---
## **Developer Information**
- **Group name**: Project 5  
- **Team members**: Daniela, Charles, Yin
