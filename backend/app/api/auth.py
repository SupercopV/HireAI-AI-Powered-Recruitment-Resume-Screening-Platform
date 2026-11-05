from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import verify_password, hash_password, create_access_token
from app.core.rbac import get_current_user
from app.database.session import get_db
from app.models.user import User, Organization, UserRole
from app.models.audit import AuditLog
from app.schemas.auth import LoginRequest, RegisterRequest, Token, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated"
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    # Log successful login
    audit = AuditLog(
        user_id=user.id,
        user_email=user.email,
        user_role=user.role.value,
        action="USER_LOGIN",
        resource_type="auth",
        resource_id=str(user.id),
        details={"email": user.email, "role": user.role.value}
    )
    db.add(audit)
    db.commit()

    org_name = user.organization.name if user.organization else None
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        organization_id=user.organization_id,
        organization_name=org_name
    )


@router.post("/register", response_model=UserResponse)
def register(reg_data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == reg_data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    org_id = None
    if reg_data.organization_name:
        client_code = (reg_data.client_code or reg_data.organization_name[:4].upper()).replace(" ", "_")
        org = db.query(Organization).filter(Organization.client_code == client_code).first()
        if not org:
            org = Organization(
                name=reg_data.organization_name,
                org_type="client" if reg_data.role == UserRole.CLIENT_HIRING_MANAGER else "staffing_agency",
                client_code=client_code
            )
            db.add(org)
            db.flush()
        org_id = org.id

    hashed = hash_password(reg_data.password)
    user = User(
        email=reg_data.email.lower(),
        hashed_password=hashed,
        full_name=reg_data.full_name,
        role=reg_data.role,
        organization_id=org_id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

