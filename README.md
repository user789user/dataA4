# Features implemented
## Checklist of stuff that is working:
- [x] Superadmin can create a user
- [X] Superadmin can change a user's department id
- [ ] Superadmin can delete a user
----------------------------------------------------------------------------------


# Project Name: A4 Database Management System
1. Overview
    This project is a Flask-based web application that interacts with a PostgreSQL
    database to manage and display data related to employees, departments, and
    projects. It is designed with role-based access control (RBAC) to ensure that
    different users have appropriate permissions based on their roles.
    
2. Requirements
- Operating System: Windows, macOS, or Linux
- Python: Version 3.8 or higher
- PostgreSQL: Version 11 or higher
- Required Python Libraries:
    a. Flask
    b. psycopg2
    c. Werkzeug
    
3. File Structure
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
**4. Setup instructions**
*** 1） Install Dependencies: ***
    ```plaintext
        pip install flask psycopg2 werkzeug
    ```
*** 2） Initialize the Database: ***
    - Open PostgreSQL CLI:
    ```plaintext
        （eg.psql -U postgres)
    ```

    - Create or Recreate the Database:
    ```plaintext
        DROP DATABASE IF EXISTS a4_db;
        CREATE DATABASE a4_db;
        \c a4_db;
    ```
    
    - Run the init_db.sql script:
    ```plaintext
        \i 
        (e.g. \i path/to/init_db.sql).
    ```
*** 3） Configure the Project: ***
    - Edit the config.py file to set the correct database connection details:
    ```plaintext
        DATABASE_CONFIG = {
            "dbname": "a4_db",          # Database name
            "user": "your_username",    # Your PostgreSQL username
            "password": "your_password",# Your PostgreSQL password
            "host": "localhost",        # Database host
            "port": "5432"              # Database port
        }
    ```
*** 4） Run the Application: ***
    - Start the Flask application by running the following command:
    ```plaintextpython app.py
        python app.py
    ```
    - Once running, open your browser and navigate to:
    ```plaintext
        http://127.0.0.1:5000
    ```
    You can now start interacting with the management system. The system provides
    role-based access to perform operations such as managing employees,
    departments,and projects based on the logged-in user's role.
    
*5. Notes*
    1）The init_db.sql script ensures that the required database and tables are
    created before running the application. If the database a4_db already exists,
    the script will skip its creation.
    2）Make sure the PostgreSQL username and password in config.py match the
    credentials on your system.
    3）After running the application, you can directly access the system's
    functionalities via the browser without needing additional setup or testing
    scripts.
------------------------------------------------------------------
# Developer Information
**Group name:** Project 5
**Team members:** Daniela, Charles, Yin.
