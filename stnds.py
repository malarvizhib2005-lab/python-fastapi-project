from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth import require_admin
from database import get_connection
from passwords import hash_password

router = APIRouter()


class StudentInput(BaseModel):
    stnd_id: Optional[int] = Field(default=None, gt=0)
    stnd_name: str = Field(min_length=1, max_length=25)
    age: Optional[int] = Field(default=None, ge=1, le=120)
    gender: Optional[str] = Field(default=None, max_length=10)
    qualification: Optional[str] = Field(default=None, max_length=25)
    yop: Optional[str] = Field(default=None, max_length=20)
    college: Optional[str] = Field(default=None, max_length=25)
    address: Optional[str] = Field(default=None, max_length=25)
    city: Optional[str] = Field(default=None, max_length=20)
    state: Optional[str] = Field(default=None, max_length=20)
    uname: str = Field(min_length=1, max_length=20)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    email: Optional[str] = Field(default=None, max_length=25)
    phno: Optional[int] = None


STUDENT_FIELDS = (
    "stnd_id, stnd_name, age, gender, qualification, yop, college, address, "
    "city, state, uname, email, phno"
)


@router.get("/student")
def get_students(_: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT {STUDENT_FIELDS} FROM stndinfo ORDER BY stnd_id")
            return cursor.fetchall()
    finally:
        connection.close()


@router.get("/student/{stnd_id}")
def get_student(stnd_id: int, _: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {STUDENT_FIELDS} FROM stndinfo WHERE stnd_id=%s",
                (stnd_id,),
            )
            student = cursor.fetchone()
    finally:
        connection.close()

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("/student", status_code=status.HTTP_201_CREATED)
def add_student(student: StudentInput, _: dict = Depends(require_admin)):
    if not student.password:
        raise HTTPException(status_code=422, detail="A password is required for a new student.")

    fields = (
        "stnd_name, age, gender, qualification, yop, college, address, city, "
        "state, uname, password, email, phno"
    )
    values = (
        student.stnd_name,
        student.age,
        student.gender,
        student.qualification,
        student.yop,
        student.college,
        student.address,
        student.city,
        student.state,
        student.uname,
        hash_password(student.password),
        student.email,
        student.phno,
    )
    if student.stnd_id is not None:
        fields = "stnd_id, " + fields
        values = (student.stnd_id,) + values

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM stndinfo WHERE uname=%s",
                (student.uname,),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Username already exists")

            placeholders = ", ".join(["%s"] * len(values))
            cursor.execute(
                f"INSERT INTO stndinfo ({fields}) VALUES ({placeholders})",
                values,
            )
            new_id = student.stnd_id or cursor.lastrowid
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Student added successfully", "stnd_id": new_id}


@router.put("/student/{stnd_id}")
def update_student(
    stnd_id: int,
    student: StudentInput,
    _: dict = Depends(require_admin),
):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM stndinfo WHERE stnd_id=%s",
                (stnd_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Student not found")

            cursor.execute(
                "SELECT 1 FROM stndinfo WHERE uname=%s AND stnd_id<>%s",
                (student.uname, stnd_id),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Username already exists")

            fields = (
                "stnd_name=%s, age=%s, gender=%s, qualification=%s, yop=%s, "
                "college=%s, address=%s, city=%s, state=%s, uname=%s, email=%s, phno=%s"
            )
            values = (
                student.stnd_name,
                student.age,
                student.gender,
                student.qualification,
                student.yop,
                student.college,
                student.address,
                student.city,
                student.state,
                student.uname,
                student.email,
                student.phno,
            )
            if student.password:
                fields += ", password=%s"
                values += (hash_password(student.password),)
            cursor.execute(
                f"UPDATE stndinfo SET {fields} WHERE stnd_id=%s",
                values + (stnd_id,),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Student updated successfully"}


@router.delete("/student/{stnd_id}")
def delete_student(stnd_id: int, _: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM enrollinfo WHERE stnd_id=%s LIMIT 1",
                (stnd_id,),
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail="A student with enrollments cannot be deleted.",
                )
            cursor.execute("DELETE FROM stndinfo WHERE stnd_id=%s", (stnd_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Student not found")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Student deleted successfully"}
