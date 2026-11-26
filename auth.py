from typing import Any

from fastapi import Depends, HTTPException, Request, status


def current_user(request: Request) -> dict[str, Any]:
    user = request.session.get("user")
    if not isinstance(user, dict) or user.get("role") not in {"admin", "student"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in to continue.",
        )
    return user


def require_admin(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access is required.",
        )
    return user


def require_student(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    if user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access is required.",
        )
    return user
