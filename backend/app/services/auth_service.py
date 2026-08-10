import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserRegister
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    generate_random_token, verify_token, hash_reset_token
)
from app.core.config import settings
from datetime import datetime, timedelta

logger = logging.getLogger("texlify.auth")


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL SENDING  — auto-switches between Resend (production) and Gmail SMTP
# ─────────────────────────────────────────────────────────────────────────────

def _send_via_resend(to_email: str, subject: str, html: str) -> bool:
    """Send email using Resend API (production)."""
    try:
        import resend
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from":    f"Texlify <noreply@{settings.EMAIL_DOMAIN}>",
            "to":      [to_email],
            "subject": subject,
            "html":    html,
        })
        logger.info("Email sent via Resend to %s", to_email)
        return True
    except ImportError:
        logger.error("Resend package not installed — run: pip install resend")
        return False
    except Exception as e:
        logger.error("Resend send failed: %s: %s", type(e).__name__, e)
        return False


def _send_via_smtp(to_email: str, subject: str, html: str) -> bool:
    """Send email using Gmail SMTP (local dev)."""
    try:
        msg            = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Texlify <{settings.SMTP_EMAIL}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_EMAIL, to_email, msg.as_string())
        logger.info("Email sent via SMTP to %s", to_email)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP auth failed — check SMTP_EMAIL and SMTP_PASSWORD in .env")
        return False
    except Exception as e:
        logger.error("SMTP send failed: %s: %s", type(e).__name__, e)
        return False


def send_email(to_email: str, subject: str, html: str) -> bool:
    """
    Master send function — automatically uses:
      - Resend   if RESEND_API_KEY is set  (production)
      - Gmail    if SMTP_EMAIL + SMTP_PASSWORD are set  (local dev)
      - Logs warning if neither is configured
    """
    provider = settings.email_provider
    if provider == "resend":
        return _send_via_resend(to_email, subject, html)
    elif provider == "smtp":
        return _send_via_smtp(to_email, subject, html)
    else:
        logger.warning(
            "No email provider configured. "
            "Set RESEND_API_KEY (production) or "
            "SMTP_EMAIL + SMTP_PASSWORD (local dev) in .env"
        )
        return False


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────

def _reset_email_html(full_name: str, reset_link: str) -> str:
    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:600px;
                 margin:0 auto;padding:20px;background:#f9fafb">
      <div style="background:linear-gradient(135deg,#10B981,#059669);
                  padding:32px;border-radius:12px;text-align:center;
                  margin-bottom:24px">
        <h1 style="color:white;margin:0;font-size:28px;font-weight:800">
          Texlify
        </h1>
        <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px">
          AI-Powered Word Document Editor
        </p>
      </div>

      <div style="background:white;border-radius:12px;padding:32px;
                  box-shadow:0 2px 8px rgba(0,0,0,0.06)">
        <h2 style="color:#064E3B;margin:0 0 16px">Hi {full_name},</h2>
        <p style="color:#374151;line-height:1.6">
          We received a request to reset your Texlify password.
          Click the button below to choose a new one.
        </p>
        <p style="color:#374151;line-height:1.6">
          This link expires in <strong>1 hour</strong>.
          If you didn't request this, you can safely ignore this email.
        </p>

        <div style="text-align:center;margin:32px 0">
          <a href="{reset_link}"
             style="background:linear-gradient(135deg,#10B981,#059669);
                    color:white;padding:14px 36px;border-radius:8px;
                    text-decoration:none;font-weight:700;font-size:16px;
                    display:inline-block;box-shadow:0 4px 12px rgba(16,185,129,0.35)">
            Reset My Password
          </a>
        </div>

        <p style="color:#6B7280;font-size:13px;word-break:break-all">
          Or copy this link into your browser:<br>
          <a href="{reset_link}" style="color:#10B981">{reset_link}</a>
        </p>
      </div>

      <p style="color:#9CA3AF;font-size:12px;text-align:center;margin-top:20px">
        © {datetime.now().year} Texlify · You received this because a password
        reset was requested for your account.
      </p>
    </body>
    </html>
    """


def _welcome_email_html(full_name: str) -> str:
    dashboard_link = f"{settings.FRONTEND_URL}/dashboard"
    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:600px;
                 margin:0 auto;padding:20px;background:#f9fafb">
      <div style="background:linear-gradient(135deg,#10B981,#059669);
                  padding:32px;border-radius:12px;text-align:center;
                  margin-bottom:24px">
        <h1 style="color:white;margin:0;font-size:28px;font-weight:800">
          Texlify
        </h1>
        <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px">
          AI-Powered Word Document Editor
        </p>
      </div>

      <div style="background:white;border-radius:12px;padding:32px;
                  box-shadow:0 2px 8px rgba(0,0,0,0.06)">
        <h2 style="color:#064E3B;margin:0 0 16px">
          Welcome to Texlify, {full_name}! 🎉
        </h2>
        <p style="color:#374151;line-height:1.6">
          Your account is ready. You can now upload Word documents and
          edit them using simple natural language commands — no formatting
          knowledge required.
        </p>

        <div style="background:#F0FDF4;border-radius:10px;padding:20px;margin:24px 0">
          <p style="color:#064E3B;font-weight:700;margin:0 0 12px;font-size:15px">
            What you can do with Texlify:
          </p>
          <ul style="color:#374151;line-height:1.8;margin:0;padding-left:20px">
            <li>Apply academic formats — SPPU, IEEE, APA, MLA</li>
            <li>Format headings, fonts, margins and spacing</li>
            <li>Add tables, images, table of contents</li>
            <li>Insert page numbers, headers and footers</li>
            <li>100+ Word formatting actions via chat</li>
          </ul>
        </div>

        <div style="text-align:center;margin:28px 0">
          <a href="{dashboard_link}"
             style="background:linear-gradient(135deg,#10B981,#059669);
                    color:white;padding:14px 36px;border-radius:8px;
                    text-decoration:none;font-weight:700;font-size:16px;
                    display:inline-block;box-shadow:0 4px 12px rgba(16,185,129,0.35)">
            Open Texlify Dashboard
          </a>
        </div>
      </div>

      <p style="color:#9CA3AF;font-size:12px;text-align:center;margin-top:20px">
        © {datetime.now().year} Texlify · You received this because you
        created an account.
      </p>
    </body>
    </html>
    """


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC EMAIL FUNCTIONS  (called from AuthService)
# ─────────────────────────────────────────────────────────────────────────────

def send_reset_email(to_email: str, reset_token: str, full_name: str) -> bool:
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    html       = _reset_email_html(full_name, reset_link)
    sent       = send_email(
        to_email=to_email,
        subject="Texlify — Reset Your Password",
        html=html,
    )
    if not sent:
        logger.info(
            "Email not sent — manual reset link: %s/reset-password?token=%s",
            settings.FRONTEND_URL, reset_token
        )
    return sent


def send_welcome_email(to_email: str, full_name: str) -> bool:
    html = _welcome_email_html(full_name)
    return send_email(
        to_email=to_email,
        subject="Welcome to Texlify! 🎉",
        html=html,
    )


# ─────────────────────────────────────────────────────────────────────────────
# AUTH SERVICE
# ─────────────────────────────────────────────────────────────────────────────

class AuthService:

    @staticmethod
    def register(db: Session, data: UserRegister) -> User:
        existing = db.query(User).filter(
            User.email == data.email.lower()
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        if len(data.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        user = User(
            full_name=data.full_name,
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            verification_token=generate_random_token(),
            is_verified=True,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("New user registered: %s", user.email)
        try:
            send_welcome_email(user.email, user.full_name)
        except Exception as e:
            logger.warning("Welcome email failed (non-fatal): %s", e)
        return user

    @staticmethod
    def login(db: Session, email: str, password: str) -> dict:
        email = email.lower().strip()
        user  = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            logger.warning("Failed login attempt: %s", email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        logger.info("User logged in: %s", email)
        return {
            "access_token":  create_access_token({"sub": str(user.id)}),
            "refresh_token": create_refresh_token({"sub": str(user.id)}),
            "token_type":    "bearer",
            "user":          user,
        }

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> dict:
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        user = db.query(User).filter(
            User.id == int(payload["sub"])
        ).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return {
            "access_token": create_access_token({"sub": str(user.id)}),
            "token_type":   "bearer",
        }

    @staticmethod
    def forgot_password(db: Session, email: str) -> str:
        user = db.query(User).filter(
            User.email == email.lower().strip()
        ).first()
        if not user:
            # Always return same message to prevent email enumeration
            return "If this email exists a reset link has been sent"

        raw_token                 = generate_random_token()
        hashed                    = hash_reset_token(raw_token)
        user.reset_password_token = hashed
        user.reset_token_expires  = datetime.utcnow() + timedelta(hours=1)
        db.commit()

        send_reset_email(user.email, raw_token, user.full_name)
        return "If this email exists a reset link has been sent"

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        hashed = hash_reset_token(token)
        user   = db.query(User).filter(
            User.reset_password_token == hashed,
            User.reset_token_expires  >  datetime.utcnow()
        ).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token. Please request a new one."
            )
        user.hashed_password      = hash_password(new_password)
        user.reset_password_token = None
        user.reset_token_expires  = None
        db.commit()
        logger.info("Password reset successfully for %s", user.email)
        return True

    @staticmethod
    def change_password(db: Session, user: User,
                        current_password: str, new_password: str) -> bool:
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters"
            )
        user.hashed_password = hash_password(new_password)
        db.commit()
        logger.info("Password changed for user %s", user.email)
        return True

    @staticmethod
    def delete_account(db: Session, user: User, password: str) -> bool:
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )
        user.is_active = False
        user.email     = f"deleted_{user.id}_{user.email}"
        db.commit()
        logger.info("Account deleted: user_id=%s", user.id)
        return True