import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserRegister
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    generate_random_token, verify_token
)
from app.core.config import settings
from datetime import datetime, timedelta


def send_reset_email(to_email: str, reset_token: str, full_name: str):
    """Send password reset email using Gmail SMTP."""
    try:
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Texlify — Reset Your Password"
        msg["From"]    = settings.SMTP_EMAIL
        msg["To"]      = to_email

        html = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
        <div style="background:linear-gradient(135deg,#10B981,#059669);padding:30px;border-radius:12px;text-align:center;margin-bottom:24px">
            <h1 style="color:white;margin:0;font-size:28px">Texlify</h1>
            <p style="color:rgba(255,255,255,0.8);margin:8px 0 0">AI Word Document Editor</p>
        </div>
        <h2 style="color:#064E3B">Hi {full_name},</h2>
        <p style="color:#374151">We received a request to reset your Texlify password.</p>
        <p style="color:#374151">Click the button below to reset it. This link expires in <strong>1 hour</strong>.</p>
        <div style="text-align:center;margin:32px 0">
            <a href="{reset_link}"
               style="background:linear-gradient(135deg,#10B981,#059669);color:white;padding:14px 32px;
                      border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;display:inline-block">
                Reset My Password
            </a>
        </div>
        <p style="color:#6B7280;font-size:14px">Or copy this link:<br>
           <a href="{reset_link}" style="color:#10B981;word-break:break-all">{reset_link}</a>
        </p>
        <hr style="border:none;border-top:1px solid #E5E7EB;margin:24px 0">
        <p style="color:#9CA3AF;font-size:12px">
            If you did not request this, ignore this email — your password will not change.
        </p>
        </body></html>
        """

        part = MIMEText(html, "html")
        msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_EMAIL, to_email, msg.as_string())

        print(f"[EMAIL] Reset email sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send email: {e}")
        return False


class AuthService:

    @staticmethod
    def register(db: Session, data: UserRegister) -> User:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user = User(
            full_name=data.full_name,
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            verification_token=generate_random_token(),
            is_verified=True,
            is_active=True
        )
        db.add(user); db.commit(); db.refresh(user)
        return user

    @staticmethod
    def login(db: Session, email: str, password: str) -> dict:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        return {
            "access_token":  create_access_token({"sub": str(user.id)}),
            "refresh_token": create_refresh_token({"sub": str(user.id)}),
            "token_type":    "bearer",
            "user":          user
        }

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> dict:
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        return {
            "access_token": create_access_token({"sub": str(user.id)}),
            "token_type":   "bearer"
        }

    @staticmethod
    def forgot_password(db: Session, email: str) -> str:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            return "If this email exists, a reset link has been sent"
        reset_token = generate_random_token()
        user.reset_password_token = reset_token
        user.reset_token_expires  = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        # Send real email
        send_reset_email(user.email, reset_token, user.full_name)
        return "If this email exists, a reset link has been sent"

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        user = db.query(User).filter(
            User.reset_password_token == token,
            User.reset_token_expires > datetime.utcnow()
        ).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        user.hashed_password      = hash_password(new_password)
        user.reset_password_token = None
        user.reset_token_expires  = None
        db.commit()
        return True

    @staticmethod
    def change_password(db: Session, user: User,
                        current_password: str, new_password: str) -> bool:
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        user.hashed_password = hash_password(new_password)
        db.commit()
        return True

    @staticmethod
    def delete_account(db: Session, user: User, password: str) -> bool:
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )
        # Soft delete — deactivate account
        user.is_active = False
        user.email     = f"deleted_{user.id}_{user.email}"
        db.commit()
        return True