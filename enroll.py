from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth import current_user, require_student
from database import get_connection

router = APIRouter()


class EnrollmentInput(BaseModel):
    course_id: int = Field(gt=0)


ENROLLMENT_SELECT = (
    "SELECT e.enroll_id, e.stnd_id, s.stnd_name, s.email, "
    "e.course_id, c.course_name, e.amount, e.status, e.enroll_date "
    "FROM enrollinfo e "
    "JOIN stndinfo s ON s.stnd_id=e.stnd_id "
    "JOIN courseinfo c ON c.course_id=e.course_id"
)


@router.get("/enroll")
def get_enrollments(user: dict = Depends(current_user)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if user["role"] == "admin":
                cursor.execute(ENROLLMENT_SELECT + " ORDER BY e.enroll_date DESC, e.enroll_id DESC")
            else:
                cursor.execute(
                    ENROLLMENT_SELECT
                    + " WHERE e.stnd_id=%s ORDER BY e.enroll_date DESC, e.enroll_id DESC",
                    (user["stnd_id"],),
                )
            return cursor.fetchall()
    finally:
        connection.close()


@router.post("/enroll", status_code=status.HTTP_201_CREATED)
def enroll_student(
    enrollment: EnrollmentInput,
    user: dict = Depends(require_student),
):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT cost FROM courseinfo WHERE course_id=%s",
                (enrollment.course_id,),
            )
            course = cursor.fetchone()
            if course is None:
                raise HTTPException(status_code=404, detail="Course not found")

            cursor.execute(
                "SELECT enroll_id FROM enrollinfo WHERE stnd_id=%s AND course_id=%s",
                (user["stnd_id"], enrollment.course_id),
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail="You are already enrolled in this course.",
                )

            cursor.execute(
                "INSERT INTO enrollinfo "
                "(stnd_id, course_id, amount, payment_id, payment_method, status, "
                "enroll_date, payment_date) "
                "VALUES (%s, %s, %s, NULL, %s, %s, CURDATE(), NULL)",
                (
                    user["stnd_id"],
                    enrollment.course_id,
                    course["cost"] or 0,
                    "Not required",
                    "Enrolled",
                ),
            )
            enrollment_id = cursor.lastrowid
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {
        "message": "Enrollment saved successfully.",
        "enroll_id": enrollment_id,
    }
