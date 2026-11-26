from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth import current_user, require_admin
from database import get_connection

router = APIRouter()


class StaffInput(BaseModel):
    staff_id: int = Field(gt=0)
    staff_name: str = Field(min_length=1, max_length=20)
    email: Optional[str] = Field(default=None, max_length=25)
    phno: Optional[int] = None
    specialization: str = Field(min_length=1, max_length=25)
    experiences: Optional[str] = Field(default=None, max_length=25)


STAFF_FIELDS = "staff_id, staff_name, email, phno, specialization, experiences"


@router.get("/staff")
def get_staff(_: dict = Depends(current_user)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT {STAFF_FIELDS} FROM staffinfo ORDER BY staff_id")
            return cursor.fetchall()
    finally:
        connection.close()


@router.get("/staff/{staff_id}")
def get_staff_member(staff_id: int, _: dict = Depends(current_user)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {STAFF_FIELDS} FROM staffinfo WHERE staff_id=%s",
                (staff_id,),
            )
            member = cursor.fetchone()
    finally:
        connection.close()

    if member is None:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return member


@router.post("/staff", status_code=status.HTTP_201_CREATED)
def add_staff(staff: StaffInput, _: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM staffinfo WHERE staff_id=%s", (staff.staff_id,))
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Staff ID already exists")

            cursor.execute(
                "INSERT INTO staffinfo "
                "(staff_id, staff_name, email, phno, specialization, experiences) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    staff.staff_id,
                    staff.staff_name,
                    staff.email,
                    staff.phno,
                    staff.specialization,
                    staff.experiences,
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Staff member added successfully", "staff_id": staff.staff_id}


@router.put("/staff/{staff_id}")
def update_staff(staff_id: int, staff: StaffInput, _: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE staffinfo SET staff_name=%s, email=%s, phno=%s, "
                "specialization=%s, experiences=%s WHERE staff_id=%s",
                (
                    staff.staff_name,
                    staff.email,
                    staff.phno,
                    staff.specialization,
                    staff.experiences,
                    staff_id,
                ),
            )
            if cursor.rowcount == 0:
                cursor.execute("SELECT 1 FROM staffinfo WHERE staff_id=%s", (staff_id,))
                if cursor.fetchone() is None:
                    raise HTTPException(status_code=404, detail="Staff member not found")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Staff member updated successfully"}


@router.delete("/staff/{staff_id}")
def delete_staff(staff_id: int, _: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM courseinfo WHERE staff_id=%s LIMIT 1",
                (staff_id,),
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail="A staff member assigned to a course cannot be deleted.",
                )
            cursor.execute("DELETE FROM staffinfo WHERE staff_id=%s", (staff_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Staff member not found")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Staff member deleted successfully"}
