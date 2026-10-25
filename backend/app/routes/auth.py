import os
import secrets
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..services.email_service import send_verification_email, send_account_verification_email
from ..security import canonical_role, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Enforces email uniqueness, strong password validation, bcrypt hashing,
    and dispatches an email verification link via Gmail SMTP.
    """
    existing_user = crud.get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{user_in.email}' already exists."
        )

    user = crud.create_user(db, user_in, email_verified=False)
    raw_token = crud.issue_email_verification_token(db, user, expires_in_hours=24)
    send_account_verification_email(user.email, user.name, raw_token)
    return user


@router.post("/login", response_model=schemas.LoginResponse)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user credentials, enforce email verification status,
    and return user profile upon success.
    """
    user = crud.get_user_by_email(db, login_data.email)
    if not user or not crud.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before signing in."
        )

    response = schemas.UserResponse.model_validate(user).model_dump()
    response["role"] = canonical_role(user.role)
    response["access_token"] = create_access_token(user.id)
    return response


@router.get("/verify-email", response_model=schemas.VerifyEmailResponse)
def verify_email_get(token: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Verify account email address using GET query parameter token.
    Validates expiration, verifies cryptographic hash, and marks email verified.
    """
    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is required."
        )

    success, message, user = crud.verify_email_token(db, token.strip())
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return schemas.VerifyEmailResponse(
        message=message,
        email=user.email if user else None,
        already_verified=False
    )


@router.post("/verify-email", response_model=schemas.VerifyEmailResponse)
def verify_email_post(
    token: Optional[str] = Query(None),
    payload: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """
    Verify account email address using POST (query param or JSON payload).
    """
    raw_token = token
    if not raw_token and payload and isinstance(payload, dict):
        raw_token = payload.get("token")

    if not raw_token or not str(raw_token).strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is required."
        )

    success, message, user = crud.verify_email_token(db, str(raw_token).strip())
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return schemas.VerifyEmailResponse(
        message=message,
        email=user.email if user else None,
        already_verified=False
    )


@router.post("/resend-verification", response_model=schemas.ResendVerificationResponse)
def resend_verification(req: schemas.ResendVerificationRequest, db: Session = Depends(get_db)):
    """
    Resend account verification link via Gmail SMTP with anti-abuse cooldown.
    Safe against user enumeration for non-existent emails.
    """
    user = crud.get_user_by_email(db, req.email)
    if not user:
        # Do not expose account existence
        return schemas.ResendVerificationResponse(
            message="If an account exists and requires verification, a verification email has been sent.",
            already_verified=False
        )

    if user.email_verified:
        return schemas.ResendVerificationResponse(
            message="This email address is already verified.",
            already_verified=True
        )

    if not crud.can_resend_verification(user, cooldown_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait 60 seconds before requesting another verification email."
        )

    raw_token = crud.issue_email_verification_token(db, user, expires_in_hours=24)
    send_account_verification_email(user.email, user.name, raw_token)

    return schemas.ResendVerificationResponse(
        message="A new verification link has been sent to your email address.",
        already_verified=False
    )


@router.post("/forgot-password", response_model=schemas.ForgotPasswordResponse)
def forgot_password(req: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiate the password recovery flow. Generates a secure single-use 6-digit OTP code.
    Always returns a generic success message to prevent account enumeration.
    """
    user = crud.get_user_by_email(db, req.email)
    code = f"{secrets.randbelow(900000) + 100000}"

    if user:
        crud.create_password_reset_code(db, req.email, code, expires_in_minutes=10)
        send_verification_email(req.email, code)

    # In development/test mode, expose code to assist frictionless verification
    dev_code = code if (user and os.getenv("ENVIRONMENT") != "production") else None

    return schemas.ForgotPasswordResponse(
        message="If an account exists for this email, a verification code has been sent.",
        dev_code=dev_code
    )


@router.post("/verify-reset-code", response_model=schemas.VerifyResetCodeResponse)
def verify_reset_code(req: schemas.VerifyResetCodeRequest, db: Session = Depends(get_db)):
    """
    Validate the single-use 6-digit verification code with attempt rate-limiting.
    Issues a short-lived cryptographic reset token upon successful verification.
    """
    user = crud.get_user_by_email(db, req.email)
    active_code = crud.get_latest_reset_code(db, req.email)

    if not user or not active_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification code is invalid."
        )

    if active_code.attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many verification attempts. Please request a new code."
        )

    if active_code.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification code has expired. Please request a new code."
        )

    if crud.hash_secret(req.code) != active_code.code_hash:
        active_code.attempts += 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification code is invalid."
        )

    # Invalidate the used OTP code
    active_code.is_used = True
    db.commit()

    # Generate a cryptographically secure 32-byte URL-safe reset token
    reset_token = secrets.token_urlsafe(32)
    crud.create_password_reset_token(db, user.id, reset_token, expires_in_minutes=15)

    return schemas.VerifyResetCodeResponse(
        message="Code verified successfully.",
        reset_token=reset_token
    )


@router.post("/reset-password", response_model=schemas.ResetPasswordResponse)
def reset_password(req: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset user password using the single-use reset token and strong password policy.
    Invalidates the reset token immediately after successful password update.
    """
    token_record = crud.get_valid_reset_token(db, req.reset_token)

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token expired or already used."
        )

    if token_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset session has expired. Please start again."
        )

    user = crud.update_user_password(db, token_record.user_id, req.new_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    # A successful email OTP recovery confirms email address ownership
    user.email_verified = True

    # Invalidate token immediately
    token_record.is_used = True
    db.commit()

    return schemas.ResetPasswordResponse(
        message="Password updated successfully."
    )



@router.get("/verification-config")
def get_verification_config():
    """Show email configuration status without exposing secrets."""
    from ..services.email_service import get_email_config

    cfg = get_email_config()
    return {
        "frontend_url": cfg["frontend_url"],
        "email_provider": "Resend",
        "sender": cfg["sender"],
        "email_configured": bool(cfg["api_key"] and cfg["sender"]),
    }
