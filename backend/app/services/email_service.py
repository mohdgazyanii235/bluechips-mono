import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings


async def send_email(to: str, subject: str, html_body: str) -> bool:
    if not settings.SMTP_USER:
        print(f"[DEV] Email to {to}: {subject}")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


async def send_verification_email(to: str, stage_name: str, token: str) -> bool:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0E8; padding: 40px; border-radius: 8px;">
        <h1 style="color: #C9A84C; font-size: 28px; margin-bottom: 8px;">Bluechips London</h1>
        <p style="color: #888; margin-bottom: 32px; font-size: 13px; letter-spacing: 2px; text-transform: uppercase;">Premium Companion Directory</p>
        <h2 style="font-size: 20px; margin-bottom: 16px;">Welcome, {stage_name}</h2>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 32px;">
            Thank you for joining Bluechips London. Please verify your email address to activate your account.
        </p>
        <a href="{verify_url}"
           style="display: inline-block; background: #C9A84C; color: #0A0A0A; padding: 14px 32px;
                  text-decoration: none; font-weight: bold; border-radius: 4px; letter-spacing: 1px;">
            VERIFY MY EMAIL
        </a>
        <p style="margin-top: 32px; color: #555; font-size: 12px;">
            This link expires in 24 hours. If you did not create this account, please ignore this email.
        </p>
        <hr style="border-color: #1a1a1a; margin: 32px 0;">
        <p style="color: #333; font-size: 11px;">
            Bluechips London is a marketing directory for independent adult entertainers. We are not an escort agency.
        </p>
    </div>
    """
    return await send_email(to, "Verify your Bluechips London account", html)


async def send_welcome_email(to: str, stage_name: str) -> bool:
    dashboard_url = f"{settings.FRONTEND_URL}/dashboard"
    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0E8; padding: 40px; border-radius: 8px;">
        <h1 style="color: #C9A84C; font-size: 28px; margin-bottom: 8px;">Bluechips London</h1>
        <p style="color: #888; margin-bottom: 32px; font-size: 13px; letter-spacing: 2px; text-transform: uppercase;">Premium Companion Directory</p>
        <h2 style="font-size: 20px; margin-bottom: 16px;">You're in, {stage_name}.</h2>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 16px;">
            Your email has been verified. Complete your profile to start attracting high-quality clients.
        </p>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 32px;">
            We recommend adding at least 3 photos and getting verified for the best results.
        </p>
        <a href="{dashboard_url}"
           style="display: inline-block; background: #C9A84C; color: #0A0A0A; padding: 14px 32px;
                  text-decoration: none; font-weight: bold; border-radius: 4px; letter-spacing: 1px;">
            GO TO MY DASHBOARD
        </a>
    </div>
    """
    return await send_email(to, f"Welcome to Bluechips London, {stage_name}", html)


async def send_verification_submitted_to_admin(escort_stage_name: str, escort_email: str, submission_level: int) -> bool:
    portal_url = f"{settings.FRONTEND_URL}/admin/verifications"
    level_name = "Identity Verification" if submission_level == 2 else "Blue Tick Verification"
    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0E8; padding: 40px; border-radius: 8px;">
        <h1 style="color: #C9A84C; font-size: 28px; margin-bottom: 8px;">Bluechips London</h1>
        <p style="color: #888; margin-bottom: 32px; font-size: 13px; letter-spacing: 2px; text-transform: uppercase;">Admin Notification</p>
        <h2 style="font-size: 20px; margin-bottom: 16px;">New {level_name} Submission</h2>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 16px;">
            <strong>{escort_stage_name}</strong> ({escort_email}) has submitted {level_name.lower()}.
        </p>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 32px;">
            Please review and approve or deny the application.
        </p>
        <a href="{portal_url}"
           style="display: inline-block; background: #C9A84C; color: #0A0A0A; padding: 14px 32px;
                  text-decoration: none; font-weight: bold; border-radius: 4px; letter-spacing: 1px;">
            REVIEW IN ADMIN PORTAL
        </a>
        <p style="margin-top: 32px; color: #555; font-size: 12px;">
            This is an automated message, do not reply to this email.
        </p>
    </div>
    """
    return await send_email(settings.ADMIN_EMAIL, f"New Submission: {escort_stage_name}", html)


async def send_verification_approved_to_escort(escort_email: str, escort_stage_name: str, level: int) -> bool:
    dashboard_url = f"{settings.FRONTEND_URL}/dashboard"
    level_name = "Identity Verified" if level == 2 else "Blue Tick Verified"
    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0E8; padding: 40px; border-radius: 8px;">
        <h1 style="color: #C9A84C; font-size: 28px; margin-bottom: 8px;">Bluechips London</h1>
        <p style="color: #888; margin-bottom: 32px; font-size: 13px; letter-spacing: 2px; text-transform: uppercase;">Application Approved</p>
        <h2 style="font-size: 20px; margin-bottom: 16px;">✓ {level_name}</h2>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 16px;">
            Hi {escort_stage_name},
        </p>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 32px;">
            Congratulations! Your {level_name.lower()} has been approved. You can now enjoy all features of your subscription.
        </p>
        <a href="{dashboard_url}"
           style="display: inline-block; background: #C9A84C; color: #0A0A0A; padding: 14px 32px;
                  text-decoration: none; font-weight: bold; border-radius: 4px; letter-spacing: 1px;">
            GO TO DASHBOARD
        </a>
        <p style="margin-top: 32px; color: #555; font-size: 12px;">
            This is an automated message, do not reply to this email.
        </p>
    </div>
    """
    return await send_email(escort_email, f"✓ {level_name}", html)


async def send_verification_denied_to_escort(escort_email: str, escort_stage_name: str, admin_notes: str, level: int) -> bool:
    support_email = settings.ADMIN_EMAIL
    level_name = "Identity Verification" if level == 2 else "Blue Tick Verification"
    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0E8; padding: 40px; border-radius: 8px;">
        <h1 style="color: #C9A84C; font-size: 28px; margin-bottom: 8px;">Bluechips London</h1>
        <p style="color: #888; margin-bottom: 32px; font-size: 13px; letter-spacing: 2px; text-transform: uppercase;">Application Not Approved</p>
        <h2 style="font-size: 20px; margin-bottom: 16px;">✗ Application Not Approved</h2>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 16px;">
            Hi {escort_stage_name},
        </p>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 16px;">
            Unfortunately, your {level_name.lower()} submission was not approved.
        </p>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 32px;">
            <strong>Reason:</strong> {admin_notes}
        </p>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 32px;">
            Your payment has been refunded to your original payment method. You can resubmit your application anytime.
        </p>
        <p style="line-height: 1.7; color: #aaa; margin-bottom: 32px; font-size: 13px;">
            If you have questions, please contact: {support_email}
        </p>
        <p style="margin-top: 32px; color: #555; font-size: 12px;">
            This is an automated message, do not reply to this email.
        </p>
    </div>
    """
    return await send_email(escort_email, f"Application Not Approved", html)
