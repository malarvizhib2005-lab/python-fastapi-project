from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth import require_admin
from database import get_connection

router = APIRouter()


class CertificateInput(BaseModel):
    cert_id: int = Field(gt=0)
    course_id: int = Field(gt=0)
    course_name: str = Field(min_length=1, max_length=20)
    stnd_id: int = Field(gt=0)
    stnd_name: str = Field(min_length=1, max_length=20)
    description: str = Field(min_length=1, max_length=50)
    course_cd: str = Field(min_length=1, max_length=20)
    technology: str = Field(min_length=1, max_length=50)
    performs: str = Field(min_length=1, max_length=50)


CERTIFICATE_FIELDS = (
    "cert_id, course_id, course_name, stnd_id, stnd_name, "
    "description, course_cd, technology, performs"
)


@router.get("/certificate")
def get_certificates(_: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {CERTIFICATE_FIELDS} FROM certinfo ORDER BY cert_id"
            )
            return cursor.fetchall()
    finally:
        connection.close()


@router.post("/certificate", status_code=status.HTTP_201_CREATED)
def add_certificate(certificate: CertificateInput, _: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM courseinfo WHERE course_id=%s",
                (certificate.course_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Course not found")
            cursor.execute(
                "SELECT 1 FROM stndinfo WHERE stnd_id=%s",
                (certificate.stnd_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Student not found")
            cursor.execute(
                "SELECT 1 FROM certinfo WHERE cert_id=%s",
                (certificate.cert_id,),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Certificate ID already exists")

            cursor.execute(
                "INSERT INTO certinfo "
                "(cert_id, course_id, course_name, stnd_id, stnd_name, description, "
                "course_cd, technology, performs) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    certificate.cert_id,
                    certificate.course_id,
                    certificate.course_name,
                    certificate.stnd_id,
                    certificate.stnd_name,
                    certificate.description,
                    certificate.course_cd,
                    certificate.technology,
                    certificate.performs,
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Certificate added successfully", "cert_id": certificate.cert_id}


@router.put("/certificate/{cert_id}")
def update_certificate(
    cert_id: int,
    certificate: CertificateInput,
    _: dict = Depends(require_admin),
):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM courseinfo WHERE course_id=%s",
                (certificate.course_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Course not found")
            cursor.execute(
                "SELECT 1 FROM stndinfo WHERE stnd_id=%s",
                (certificate.stnd_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Student not found")
            cursor.execute(
                "UPDATE certinfo SET course_id=%s, course_name=%s, stnd_id=%s, "
                "stnd_name=%s, description=%s, course_cd=%s, technology=%s, "
                "performs=%s WHERE cert_id=%s",
                (
                    certificate.course_id,
                    certificate.course_name,
                    certificate.stnd_id,
                    certificate.stnd_name,
                    certificate.description,
                    certificate.course_cd,
                    certificate.technology,
                    certificate.performs,
                    cert_id,
                ),
            )
            if cursor.rowcount == 0:
                cursor.execute("SELECT 1 FROM certinfo WHERE cert_id=%s", (cert_id,))
                if cursor.fetchone() is None:
                    raise HTTPException(status_code=404, detail="Certificate not found")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Certificate updated successfully"}


@router.delete("/certificate/{cert_id}")
def delete_certificate(cert_id: int, _: dict = Depends(require_admin)):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM certinfo WHERE cert_id=%s", (cert_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Certificate not found")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {"message": "Certificate deleted successfully"}
