import logging
import os
import secrets

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from auth import current_user, require_admin, require_student
from certificate import router as certificate_router
from course import router as course_router
from database import get_connection
from enroll import router as enrollment_router
from passwords import hash_password, verify_password
from staff import router as staff_router
from stnds import router as student_router

logger = logging.getLogger(__name__)
session_secret = os.getenv("SESSION_SECRET")
if not session_secret:
    session_secret = secrets.token_urlsafe(32)
    logger.warning("SESSION_SECRET is unset; active sessions will expire when the server restarts.")

app = FastAPI(title="Learn Flow Course Management")
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    same_site="lax",
    https_only=os.getenv("COOKIE_HTTPS_ONLY", "false").lower() == "true",
)
app.mount("/image", StaticFiles(directory="image"), name="image")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("index.html")


@app.get("/index.html")
def index_page():
    return FileResponse("index.html")


@app.get("/login.html")
def login_page():
    return FileResponse("login.html")


@app.get("/admin.html")
def admin_login_page():
    return FileResponse("admin.html")


@app.get("/student.html")
def student_login_page():
    return FileResponse("student.html")


@app.get("/admin/dashboard")
def admin_dashboard(_: dict = Depends(require_admin)):
    return FileResponse("admin-dashboard.html")


@app.get("/student/dashboard")
def student_dashboard(_: dict = Depends(require_student)):
    return FileResponse("student-dashboard.html")


@app.get("/course.html")
def course_page(_: dict = Depends(require_admin)):
    return FileResponse("course.html")


@app.get("/staff.html")
def staff_page(_: dict = Depends(require_admin)):
    return FileResponse("staff.html")


@app.get("/certificate.html")
def certificate_page(_: dict = Depends(require_admin)):
    return FileResponse("certificate.html")


@app.get("/enroll.html")
def enroll_page(_: dict = Depends(require_admin)):
    return FileResponse("enroll.html")


@app.get("/stnds.html")
def students_page(_: dict = Depends(require_admin)):
    return FileResponse("stnds.html")


@app.post("/admin")
def admin_login(
    request: Request,
    uname: str = Form(...),
    password: str = Form(...),
):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT uname, password FROM admininfo WHERE uname=%s", (uname,))
            account = cursor.fetchone()
            authenticated = False
            if account is not None:
                authenticated, needs_rehash = verify_password(password, account["password"] or "")
                if authenticated and needs_rehash:
                    cursor.execute(
                        "UPDATE admininfo SET password=%s WHERE uname=%s AND password=%s",
                        (hash_password(password), account["uname"], account["password"]),
                    )
                    connection.commit()
    finally:
        connection.close()

    if not authenticated:
        return RedirectResponse("/admin.html?error=invalid", status_code=303)

    request.session.clear()
    request.session["user"] = {"role": "admin", "username": account["uname"]}
    return RedirectResponse("/admin/dashboard", status_code=303)


@app.post("/student/login")
def student_login(
    request: Request,
    uname: str = Form(...),
    password: str = Form(...),
):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT stnd_id, stnd_name, uname, password FROM stndinfo WHERE uname=%s",
                (uname,),
            )
            account = cursor.fetchone()
            authenticated = False
            if account is not None:
                authenticated, needs_rehash = verify_password(password, account["password"] or "")
                if authenticated and needs_rehash:
                    cursor.execute(
                        "UPDATE stndinfo SET password=%s WHERE stnd_id=%s AND password=%s",
                        (hash_password(password), account["stnd_id"], account["password"]),
                    )
                    connection.commit()
    finally:
        connection.close()

    if not authenticated:
        return RedirectResponse("/student.html?error=invalid", status_code=303)

    request.session.clear()
    request.session["user"] = {
        "role": "student",
        "stnd_id": account["stnd_id"],
        "name": account["stnd_name"],
        "username": account["uname"],
    }
    return RedirectResponse("/student/dashboard", status_code=303)


@app.get("/auth/me")
def who_am_i(user: dict = Depends(current_user)):
    return user


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


app.include_router(course_router)
app.include_router(staff_router)
app.include_router(certificate_router)
app.include_router(student_router)
app.include_router(enrollment_router)
