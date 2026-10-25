
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
        "- Noveraa Global | ProjectPulse Team\n"
        "Track. Analyze. Predict. Deliver."
    )

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
      <span style="font-size:30px;font-weight:700;letter-spacing:8px;color:#2563eb;">{code}</span>
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
