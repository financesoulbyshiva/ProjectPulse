
import os
from html import escape
from typing import Optional, List, Dict, Any
from urllib.parse import quote

import resend
from dotenv import load_dotenv


# In-memory test spy for automated testing.
_test_sent_emails: List[Dict[str, Any]] = []


def get_test_sent_emails() -> List[Dict[str, Any]]:
    """Retrieve recorded outgoing emails for testing."""
    return list(_test_sent_emails)


def clear_test_sent_emails() -> None:
    """Clear the test email mailbox."""
    _test_sent_emails.clear()


def get_email_config() -> Dict[str, str]:
    """Read Resend and frontend configuration."""
    load_dotenv(override=False)

    frontend_url = (
        os.getenv("FRONTEND_URL", "http://localhost:5173").strip().rstrip("/")
        or "http://localhost:5173"
    )

    return {
        "api_key": os.getenv("RESEND_API_KEY", "").strip(),
        "sender": os.getenv("RESEND_FROM_EMAIL", "").strip(),
        "frontend_url": frontend_url,
    }


def get_smtp_config() -> Dict[str, str]:
    """Compatibility wrapper for older code using the former function name."""
    config = get_email_config()

    # Resend sends email over HTTPS, not SMTP.
    return {
        **config,
        "host": "api.resend.com",
        "port": "443",
    }


def _send_email(
    to_email: str,
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
) -> bool:
    """Send an email through the Resend HTTPS API."""
    config = get_email_config()
    api_key = config["api_key"]
    sender = config["sender"]

    if not api_key or not sender:
        print(
            "[AUTH EMAIL ERROR] Resend configuration is missing. "
            "Check RESEND_API_KEY and RESEND_FROM_EMAIL."
        )
        return False

    params: Dict[str, Any] = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "text": text_body,
    }

    if html_body:
        params["html"] = html_body

    try:
        resend.api_key = api_key
        resend.Emails.send(params)
        return True
    except Exception as exc:
        # Do not log API keys, verification tokens, OTPs, or email contents.
        print(
            "[AUTH EMAIL ERROR] Resend delivery failed: "
            f"{type(exc).__name__}"
        )
        return False


def send_account_verification_email(
    to_email: str,
    name: Optional[str],
    token: str,
) -> bool:
    """Send the ProjectPulse account verification email."""
    config = get_email_config()
    display_name = (name or "").strip()
    salutation_name = display_name or "there"

    verification_url = (
        f"{config['frontend_url']}/verify-email"
        f"?token={quote(token, safe='')}"
    )

    # Preserve the test spy used by automated tests.
    _test_sent_emails.append({
        "type": "account_verification",
        "to": to_email,
        "name": display_name,
        "token": token,
        "verification_url": verification_url,
    })

    safe_name = escape(salutation_name)
    safe_url = escape(verification_url, quote=True)

    subject = "Verify your ProjectPulse account"

    text_body = (
        f"Hello {salutation_name},\n\n"
        "Welcome to ProjectPulse.\n"
        "Thanks for creating your ProjectPulse account. "
        "Please verify your email address to activate your account:\n\n"
        f"{verification_url}\n\n"
        "This verification link will expire in 24 hours.\n"
        "If you did not create this account, you can safely ignore this email.\n\n"
        "Regards,\n"
        "Noveraa Global\n"
        "ProjectPulse Team\n"
        "Track. Analyze. Predict. Deliver."
    )

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Verify your ProjectPulse account</title>
</head>
<body style="font-family:Arial,Helvetica,sans-serif;background:#f9fafb;margin:0;padding:24px;color:#111827;">
  <div style="max-width:520px;margin:0 auto;background:#ffffff;border-radius:8px;border:1px solid #e5e7eb;padding:32px;">
    <div style="margin-bottom:24px;">
      <h2 style="margin:0;font-size:20px;font-weight:700;color:#2563eb;">ProjectPulse</h2>
      <p style="margin:4px 0 0;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;color:#6b7280;font-weight:600;">Track. Analyze. Predict. Deliver.</p>
    </div>
    <h3 style="margin:0 0 12px;font-size:16px;color:#111827;">Welcome to ProjectPulse</h3>
    <p style="margin:0 0 16px;font-size:14px;line-height:1.5;color:#4b5563;">
      Hello <strong>{safe_name}</strong>,<br><br>
      Thanks for creating your ProjectPulse account. Please verify your email address to activate your account and start predicting project delivery timelines.
    </p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{safe_url}" style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;font-size:14px;font-weight:600;padding:12px 28px;border-radius:6px;">Verify Email</a>
    </div>
    <p style="margin:0 0 8px;font-size:12px;color:#6b7280;">This verification link will expire in 24 hours.</p>
    <p style="margin:0 0 16px;font-size:12px;color:#6b7280;">
      If the button does not work, copy and paste this URL into your browser:<br>
      <a href="{safe_url}" style="color:#2563eb;word-break:break-all;">{safe_url}</a>
    </p>
    <p style="margin:0 0 24px;font-size:12px;color:#9ca3af;">If you did not create this account, you can safely ignore this email.</p>
    <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;">
    <p style="margin:0;font-size:11px;color:#9ca3af;text-align:center;">Noveraa Global | ProjectPulse</p>
  </div>
</body>
</html>"""

    return _send_email(
        to_email=to_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )


def send_verification_email(to_email: str, code: str) -> bool:
    """Send a password-reset verification code through Resend."""
    _test_sent_emails.append({
        "type": "password_reset_code",
        "to": to_email,
        "code": code,
    })

    subject = "ProjectPulse - Password Reset Verification Code"

    text_body = (
        "Hello,\n\n"
        "Your ProjectPulse password reset verification code is:\n\n"
        f"  {code}\n\n"
        "This code will expire in 10 minutes.\n"
        "If you did not request a password reset, please ignore this email.\n\n"
        "Noveraa Global | ProjectPulse Team\n"
        "Track. Analyze. Predict. Deliver."
    )

    safe_code = escape(code)

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ProjectPulse Password Reset</title>
</head>
<body style="font-family:Arial,Helvetica,sans-serif;background:#f9fafb;margin:0;padding:24px;color:#111827;">
  <div style="max-width:520px;margin:0 auto;background:#ffffff;border-radius:8px;border:1px solid #e5e7eb;padding:32px;">
    <h2 style="margin:0;color:#2563eb;">ProjectPulse</h2>
    <p style="font-size:11px;color:#6b7280;">TRACK. ANALYZE. PREDICT. DELIVER.</p>
    <h3>Password Reset Verification</h3>
    <p>Hello,</p>
    <p>Use the verification code below to continue resetting your ProjectPulse password:</p>
    <div style="text-align:center;margin:28px 0;padding:18px;background:#f3f4f6;border-radius:8px;">
      <span style="font-size:30px;font-weight:700;letter-spacing:8px;color:#2563eb;">{safe_code}</span>
    </div>
    <p style="font-size:13px;color:#4b5563;">This code expires in 10 minutes. Do not share it with anyone.</p>
    <p style="font-size:12px;color:#6b7280;">If you did not request a password reset, you can safely ignore this email.</p>
    <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
    <p style="font-size:11px;color:#9ca3af;text-align:center;">Noveraa Global | ProjectPulse Team</p>
  </div>
</body>
</html>"""

    return _send_email(
        to_email=to_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
