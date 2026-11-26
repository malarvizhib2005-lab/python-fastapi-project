from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth import require_admin
from database import get_connection

router = APIRouter()


class CourseInput(BaseModel):
    course_id: int = Field(gt=0)
    course_name: str = Field(min_length=1, max_length=20)
    description: str = Field(min_length=1, max_length=50)
    technology: str = Field(min_length=1, max_length=50)
    course_duration: str = Field(min_length=1, max_length=20)
    staff_id: int = Field(gt=0)
    cost: float = Field(ge=0)
    course_st: Optional[date] = None
    course_ed: Optional[date] = None


def _course_values(course: CourseInput):
    return (
        course.course_name,
        course.description,
        course.technology,
        course.course_duration,
        course.staff_id,
        course.course_st,
        course.course_ed,
        course.cost,
    )


@router.get("/course")
def get_courses():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT course_id, course_name, description, technology, "
                "course_duration, staff_id, cost, course_st, course_ed "
                "FROM courseinfo ORDER BY course_id"
            )
            return cursor.fetchall()
    finally:
        connection.close()


@router.get("/course/{course_id}")
def get_course(course_id: int):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT course_id, course_name, description, technology, "
                "course_duration, staff_id, cost, course_st, course_ed "
                "FROM courseinfo WHERE course_id=%s",
                (course_id,),
            )
            course = cursor.fetchone()
    finally:
        connection.close()

    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/course", status_code=status.HTTP_201_CREATED)
def add_course(course: CourseInput, _: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM courseinfo WHERE course_id=%s",
                (course.course_id,),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Course ID already exists")

            cursor.execute(
                "SELECT 1 FROM staffinfo WHERE staff_id=%s",
                (course.staff_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=400, detail="Select an existing staff member")

            cursor.execute(
                "INSERT INTO courseinfo "
                "(course_id, course_name, description, technology, course_duration, "
                "staff_id, cost, course_st, course_ed) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (course.course_id, *_course_values(course)[0:5], course.cost,
                 course.course_st, course.course_ed),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Course added successfully", "course_id": course.course_id}


@router.put("/course/{course_id}")
def update_course(course_id: int, course: CourseInput, _: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM courseinfo WHERE course_id=%s",
                (course_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Course not found")

            cursor.execute(
                "SELECT 1 FROM staffinfo WHERE staff_id=%s",
                (course.staff_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=400, detail="Select an existing staff member")

            cursor.execute(
                "UPDATE courseinfo SET course_name=%s, description=%s, technology=%s, "
                "course_duration=%s, staff_id=%s, course_st=%s, course_ed=%s, cost=%s "
                "WHERE course_id=%s",
                (*_course_values(course), course_id),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Course updated successfully"}


@router.delete("/course/{course_id}")
def delete_course(course_id: int, _: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM enrollinfo WHERE course_id=%s LIMIT 1",
                (course_id,),
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail="A course with enrollments cannot be deleted.",
                )

            cursor.execute("DELETE FROM courseinfo WHERE course_id=%s", (course_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Course not found")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Course deleted successfully"}
