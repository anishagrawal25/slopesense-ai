"""
Authentication and User Access Management Endpoints.
Implements Registration Approval Workflow (Citizens auto-approved, Volunteers approved by Authority, Authorities approved by Admin).
"""
from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.core.security import (
    verify_password, get_password_hash, create_access_token, get_current_user, require_roles
)
from backend.core.config import settings
from backend.models.user import User
from backend.models.system import AuditLog
from backend.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse, UserStatusUpdateRequest
)

router = APIRouter()

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    - Citizens: auto-approved.
    - Volunteers: pending approval by District Authority.
    - Authorities: pending approval by State Super Admin.
    """
    # Check password match if confirm_password provided
    if payload.confirm_password and payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    # Check if email exists
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered."
        )

    # Check phone number if provided
    if payload.phone_number:
        phone_existing = db.query(User).filter(User.phone_number == payload.phone_number).first()
        if phone_existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mobile phone number is already registered."
            )

    role = payload.role.lower()
    if role not in ("citizen", "volunteer", "authority", "admin"):
        role = "citizen"

    # Approval Status Logic
    if role == "citizen":
        approval_status = "approved"
    else:
        approval_status = "pending"

    user = User(
        full_name=payload.full_name,
        email=payload.email.lower(),
        phone_number=payload.phone_number,
        password_hash=get_password_hash(payload.password),
        role=role,
        state=payload.state or "Assam",
        district=payload.district or "Dima Hasao",
        village_area=payload.village_area,
        status=approval_status,
        is_active=True,
        latitude=payload.latitude or 25.1718,
        longitude=payload.longitude or 93.1230
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit = AuditLog(
        user_id=user.id,
        action="USER_REGISTERED",
        entity_type="USER",
        entity_id=user.id,
        details=f"User registered with role '{role}', approval status: '{approval_status}'"
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Registration successful" if approval_status == "approved" else "Registration submitted. Pending authority approval.",
        "user_id": user.id,
        "status": approval_status,
        "role": role
    }

@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user credentials and issue JWT session token."""
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact your system administrator."
        )

    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    audit = AuditLog(
        user_id=user.id,
        action="USER_LOGIN",
        entity_type="USER",
        entity_id=user.id,
        details=f"User logged in from role {user.role} (Status: {user.status})"
    )
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile of authenticated user."""
    return UserResponse.from_orm(current_user)

@router.get("/pending-users", response_model=List[UserResponse])
def get_pending_users(
    role_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["authority", "admin"]))
):
    """
    Retrieve pending volunteer/authority registrations.
    Authorities can view pending volunteers; Admins can view all pending users.
    """
    query = db.query(User).filter(User.status == "pending")
    if current_user.role == "authority":
        query = query.filter(User.role == "volunteer")
    elif role_filter:
        query = query.filter(User.role == role_filter)

    users = query.order_by(desc(User.created_at)).all()
    return [UserResponse.from_orm(u) for u in users]

@router.post("/users/{id}/approve", response_model=dict)
def approve_user_registration(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["authority", "admin"]))
):
    """Approve a pending volunteer or authority user registration."""
    target_user = db.query(User).filter(User.id == id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.role == "authority" and target_user.role != "volunteer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorities can only approve volunteer accounts."
        )

    target_user.status = "approved"
    db.commit()

    audit = AuditLog(
        user_id=current_user.id,
        action="USER_APPROVED",
        entity_type="USER",
        entity_id=target_user.id,
        details=f"User {target_user.full_name} ({target_user.role}) approved by {current_user.full_name}"
    )
    db.add(audit)
    db.commit()

    return {"message": f"User {target_user.full_name} has been approved successfully.", "status": "approved"}

@router.post("/users/{id}/reject", response_model=dict)
def reject_user_registration(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["authority", "admin"]))
):
    """Reject a pending user registration."""
    target_user = db.query(User).filter(User.id == id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.status = "rejected"
    db.commit()

    audit = AuditLog(
        user_id=current_user.id,
        action="USER_REJECTED",
        entity_type="USER",
        entity_id=target_user.id,
        details=f"User {target_user.full_name} rejected by {current_user.full_name}"
    )
    db.add(audit)
    db.commit()

    return {"message": f"User {target_user.full_name} has been rejected.", "status": "rejected"}

@router.get("/users", response_model=List[UserResponse])
def list_all_users(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "authority"]))
):
    """List all registered users across the platform."""
    query = db.query(User).order_by(desc(User.created_at))
    if role:
        query = query.filter(User.role == role)
    users = query.all()
    return [UserResponse.from_orm(u) for u in users]
