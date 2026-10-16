import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# In-memory test spy for automated testing verification without invoking external SMTP
_test_sent_emails: List[Dict[str, Any]] = []


def get_test_sent_emails() -> List[Dict[str, Any]]:
    """Retrieve recorded outgoing emails for testing inspection."""
    return list(_test_sent_emails)


def clear_test_sent_emails() -> None:
    """Clear the test email mailbox."""
    _test_sent_emails.clear()


def get_smtp_config() -> Dict[str, Any]:
    """Retrieve validated SMTP configuration from environment variables."""
    load_dotenv(override=True)
    raw_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").strip().rstrip("/")
    if not raw_frontend_url:
        raw_frontend_url = "http://localhost:5173"

    return {
        "host": os.getenv("EMAIL_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("EMAIL_PORT", "587")),
        "username": os.getenv("EMAIL_USERNAME", "noveraaglobal@gmail.com"),
        "password": os.getenv("EMAIL_PASSWORD", ""),
        "sender": os.getenv("EMAIL_FROM", "Noveraa Global <noveraaglobal@gmail.com>"),
        "frontend_url": raw_frontend_url
    }


def send_account_verification_email(to_email: str, name: Optional[str], token: str) -> bool:
    """
    Send an email verification link using Gmail SMTP (smtp.gmail.com:587 STARTTLS).
    Sender Identity: Noveraa Global <noveraaglobal@gmail.com>
    Verification link: {FRONTEND_URL}/verify-email?token={token}
    """
    config = get_smtp_config()
    display_name = (name or "").strip()
    salutation_name = display_name if display_name else "there"
    verification_url = f"{config['frontend_url']}/verify-email?token={token}"

    # Record in test spy for automated test verification
    _test_sent_emails.append({
        "type": "account_verification",
        "to": to_email,
        "name": display_name,
        "token": token,
        "verification_url": verification_url,
    })

    subject = "Verify your ProjectPulse account"

    text_body = (
        f"Hello {salutation_name},\n\n"
        f"Welcome to ProjectPulse.\n"
        f"Thanks for creating your ProjectPulse account. Please verify your email address to activate your account:\n\n"
        f"  {verification_url}\n\n"
        f"This verification link will expire in 24 hours.\n"
        f"If you did not create this account, you can safely ignore this email.\n\n"
        f"Regards,\n"
        f"Noveraa Global\n"
        f"ProjectPulse Team\n"
        f"Track. Analyze. Predict. Deliver."
    )

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Verify your ProjectPulse account</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f9fafb; margin: 0; padding: 24px; color: #111827;">
  <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e5e7eb; padding: 32px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);">
    <div style="margin-bottom: 24px;">
      <h2 style="margin: 0; font-size: 20px; font-weight: 700; color: #2563eb;">ProjectPulse</h2>
      <p style="margin: 4px 0 0 0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #6b7280; font-weight: 600;">Track. Analyze. Predict. Deliver.</p>
    </div>
    <h3 style="margin: 0 0 12px 0; font-size: 16px; color: #111827;">Welcome to ProjectPulse</h3>
    <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.5; color: #4b5563;">
      Hello <strong>{salutation_name}</strong>,<br><br>
      Thanks for creating your ProjectPulse account. Please verify your email address to activate your account and start predicting project delivery timelines.
    </p>
    <div style="text-align: center; margin: 28px 0;">
      <a href="{verification_url}" style="display: inline-block; background-color: #2563eb; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; padding: 12px 28px; border-radius: 6px;">Verify Email</a>
    </div>
    <p style="margin: 0 0 8px 0; font-size: 12px; color: #6b7280;">
      This verification link will expire in 24 hours.
    </p>
    <p style="margin: 0 0 16px 0; font-size: 12px; color: #6b7280;">
      If the button above does not work, copy and paste this URL into your browser:<br>
      <a href="{verification_url}" style="color: #2563eb; word-break: break-all;">{verification_url}</a>
    </p>
    <p style="margin: 0 0 24px 0; font-size: 12px; color: #9ca3af;">
      If you did not create this account, you can safely ignore this email.
    </p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="margin: 0; font-size: 11px; color: #9ca3af; text-align: center;">
      — Noveraa Global • ProjectPulse
    </p>
  </div>
</body>
</html>"""

    # If real SMTP credentials are provided, attempt delivery
    if config["password"] and config["username"]:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = config["sender"]
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(config["host"], config["port"]) as server:
                server.starttls()
                server.login(config["username"], config["password"])
                server.sendmail(config["sender"], [to_email], msg.as_string())
            return True
        except Exception as exc:
            # Safe sanitization: Never log passwords or tokens
            print(f"[AUTH EMAIL ERROR] Email delivery via Gmail SMTP failed: {type(exc).__name__}")
            return False

    # Development fallback
    print(f"[AUTH DEV EMAIL] Verification link for {to_email} (User: {salutation_name}) generated successfully.")
    return True


def send_verification_email(to_email: str, code: str) -> bool:
    """
    Send a 6-digit password reset verification code.
    If SMTP credentials are configured, sends real email.
    Otherwise, logs safely to the server console.
    """
    config = get_smtp_config()

    _test_sent_emails.append({
        "type": "password_reset_code",
        "to": to_email,
        "code": code,
    })

    if config["password"] and config["username"]:
        try:
            msg = MIMEMultipart()
            msg["From"] = config["sender"]
            msg["To"] = to_email
            msg["Subject"] = "ProjectPulse — Password Reset Verification Code"

            body = (
                f"Hello,\n\n"
                f"Your ProjectPulse password reset verification code is:\n\n"
                f"  {code}\n\n"
                f"This code will expire in 10 minutes.\n"
                f"If you did not request a password reset, please ignore this email.\n\n"
                f"— Noveraa Global • ProjectPulse Team\n"
                f"Track. Analyze. Predict. Deliver."
            )
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(config["host"], config["port"]) as server:
                server.starttls()
                server.login(config["username"], config["password"])
                server.sendmail(config["sender"], [to_email], msg.as_string())
            return True
        except Exception as exc:
            print(f"[AUTH EMAIL ERROR] Failed to send OTP code via SMTP: {type(exc).__name__}")
            return False

    # Safe local development / testing log
    print(f"[AUTH DEV EMAIL] Verification code for {to_email}: {code} (expires in 10 minutes)")
    return True
