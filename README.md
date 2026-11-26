# Learn Flow

Learn Flow is a FastAPI and MySQL course-management application with separate administrator and student workspaces.

## Run on Windows

From Command Prompt:

```bat
cd /d "D:\python fastapi project"
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
set DB_HOST=localhost
set DB_USER=root
set DB_NAME=coursedb
set DB_PASSWORD=your_mysql_password
set SESSION_SECRET=replace_with_a_long_random_value
python setup_database.py
python -m uvicorn main:app --reload
```

Replace the database password and session secret with your local values. Keep them out of source files. These `set` values apply to the current Command Prompt window.

Run `python setup_database.py` once before starting the server. It widens the existing password columns so migrated password hashes fit, and adds unique indexes for course IDs, staff IDs, student usernames, and one enrollment per student/course. It stops with an error if duplicate records would prevent those indexes. Your MySQL database must contain the existing `admininfo`, `courseinfo`, `staffinfo`, `stndinfo`, `enrollinfo`, and `certinfo` tables.

## Roles

- **Administrator:** use the admin account already in `admininfo`. The dashboard links to course, staff, certificate, and student CRUD pages. Enrollments are read-only for administrators.
- **Student:** use a student account in `stndinfo`. Students can view the catalog and instructor profiles, enroll in a course once, and see their own enrollments.
- **Public catalog:** the homepage reads courses from the MySQL `courseinfo` table.

The current database already contains the Python course (course ID 1), which references staff ID 1. The `staffinfo` table is currently empty. Add the real instructor through **Admin → Staff** using staff ID 1; the student course view will show the instructor when that profile exists. No instructor identity is fabricated.

Enrollment records are stored in `enrollinfo` with the signed-in student's ID, course ID, course price, status, and enrollment date. Payment is not processed by this application.
