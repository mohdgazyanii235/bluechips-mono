import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings


async def send_email(to: str, subject: str, html_body: str) -> bool:
    if settings.APP_ENV != "production":
        print(f"[DEV EMAIL] To: {to} | Subject: {subject}")
        return True

    if not settings.SMTP_USER:
        print(f"[WARN] SMTP not configured — email to {to} not sent")
        return False

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


async def send_downgrade_photo_warning(
    escort_email: str,
    stage_name: str,
    current_photos: int,
    new_limit: int,
    excess: int,
    new_tier: str,
    billing_date: str,
) -> bool:
    photos_url = f"{settings.FRONTEND_URL}/dashboard/profile"
    tier_label = new_tier.capitalize()
    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0E8; padding: 40px; border-radius: 8px;">
        <h1 style="color: #C9A84C; font-size: 28px; margin-bottom: 8px;">Bluechips London</h1>
        <p style="color: #888; margin-bottom: 32px; font-size: 13px; letter-spacing: 2px; text-transform: uppercase;">Action Required</p>
        <h2 style="font-size: 20px; margin-bottom: 16px;">⚠️ Remove {excess} photo{'s' if excess > 1 else ''} before {billing_date}</h2>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 16px;">Hi {stage_name},</p>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 16px;">
            You've scheduled a downgrade to the <strong style="color: #C9A84C;">{tier_label}</strong> plan,
            which allows up to <strong>{new_limit} photos</strong>.
        </p>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 16px;">
            You currently have <strong>{current_photos} photos</strong> uploaded.
            Please remove at least <strong style="color: #E87040;">{excess} photo{'s' if excess > 1 else ''}</strong>
            before <strong>{billing_date}</strong> — otherwise your profile will be automatically
            paused until you bring the total within the new limit.
        </p>
        <a href="{photos_url}"
           style="display: inline-block; background: #C9A84C; color: #0A0A0A; padding: 14px 32px;
                  text-decoration: none; font-weight: bold; border-radius: 4px; letter-spacing: 1px; margin-bottom: 32px;">
            MANAGE MY PHOTOS
        </a>
        <p style="color: #555; font-size: 12px; margin-top: 32px;">
            This is an automated message. Questions? Contact {settings.ADMIN_EMAIL}
        </p>
    </div>
    """
    return await send_email(escort_email, f"Action required: remove {excess} photo{'s' if excess > 1 else ''} by {billing_date}", html)


async def send_profile_paused_photo_limit(
    escort_email: str,
    stage_name: str,
    current_photos: int,
    photo_limit: int,
    new_tier: str,
) -> bool:
    photos_url = f"{settings.FRONTEND_URL}/dashboard/profile"
    excess = current_photos - photo_limit
    tier_label = new_tier.capitalize()
    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0E8; padding: 40px; border-radius: 8px;">
        <h1 style="color: #C9A84C; font-size: 28px; margin-bottom: 8px;">Bluechips London</h1>
        <p style="color: #888; margin-bottom: 32px; font-size: 13px; letter-spacing: 2px; text-transform: uppercase;">Profile Paused</p>
        <h2 style="font-size: 20px; margin-bottom: 16px;">Your profile has been paused</h2>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 16px;">Hi {stage_name},</p>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 16px;">
            Your plan has changed to <strong style="color: #C9A84C;">{tier_label}</strong>,
            which allows a maximum of <strong>{photo_limit} photos</strong>.
            You currently have <strong>{current_photos} photos</strong> on your profile.
        </p>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 32px;">
            Your profile has been <strong style="color: #E87040;">temporarily hidden from search</strong>
            until you remove <strong>{excess} photo{'s' if excess > 1 else ''}</strong>.
            As soon as you're within the limit your profile will go live again automatically — no need to contact us.
        </p>
        <a href="{photos_url}"
           style="display: inline-block; background: #C9A84C; color: #0A0A0A; padding: 14px 32px;
                  text-decoration: none; font-weight: bold; border-radius: 4px; letter-spacing: 1px; margin-bottom: 32px;">
            REMOVE PHOTOS NOW
        </a>
        <p style="line-height: 1.7; color: #888; font-size: 13px; margin-bottom: 16px;">
            Want to keep all your photos? <a href="{settings.FRONTEND_URL}/dashboard/subscription"
            style="color: #C9A84C;">Upgrade your plan</a> to restore full access.
        </p>
        <p style="color: #555; font-size: 12px; margin-top: 32px;">
            Questions? Contact {settings.ADMIN_EMAIL}
        </p>
    </div>
    """
    return await send_email(escort_email, "Your profile has been paused — action required", html)


async def send_profile_reactivated(escort_email: str, stage_name: str) -> bool:
    dashboard_url = f"{settings.FRONTEND_URL}/dashboard"
    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0E8; padding: 40px; border-radius: 8px;">
        <h1 style="color: #C9A84C; font-size: 28px; margin-bottom: 8px;">Bluechips London</h1>
        <p style="color: #888; margin-bottom: 32px; font-size: 13px; letter-spacing: 2px; text-transform: uppercase;">Profile Live</p>
        <h2 style="font-size: 20px; margin-bottom: 16px;">✓ Your profile is live again</h2>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 16px;">Hi {stage_name},</p>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 32px;">
            You've brought your photo count within your plan's limit — your profile is now
            <strong style="color: #4ADE80;">visible in search again</strong>. No further action needed.
        </p>
        <a href="{dashboard_url}"
           style="display: inline-block; background: #C9A84C; color: #0A0A0A; padding: 14px 32px;
                  text-decoration: none; font-weight: bold; border-radius: 4px; letter-spacing: 1px;">
            GO TO DASHBOARD
        </a>
        <p style="color: #555; font-size: 12px; margin-top: 32px;">
            This is an automated message. Questions? Contact {settings.ADMIN_EMAIL}
        </p>
    </div>
    """
    return await send_email(escort_email, "✓ Your profile is live again", html)


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


async def send_profile_completion_reminder(to: str, stage_name: str) -> bool:
    """Friendly nudge for escorts who verified email but haven't finished their profile."""
    dashboard_url = f"{settings.FRONTEND_URL}/dashboard/profile"
    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #F5F0E8; padding: 40px; border-radius: 8px;">
        <h1 style="color: #C9A84C; font-size: 28px; margin-bottom: 8px;">Bluechips London</h1>
        <p style="color: #888; margin-bottom: 32px; font-size: 13px; letter-spacing: 2px; text-transform: uppercase;">Premium Companion Directory</p>
        <h2 style="font-size: 20px; margin-bottom: 16px;">Your profile is almost ready, {stage_name}.</h2>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 20px;">
            Quick reminder — your Bluechips London profile is set up but not yet complete. To start showing up in client searches, you'll need:
        </p>
        <ul style="line-height: 1.9; color: #ccc; margin-bottom: 28px; padding-left: 20px;">
            <li>Your age and the London borough you work in</li>
            <li>At least one photo</li>
            <li>A short about-me description</li>
            <li>Your hourly rate</li>
        </ul>
        <p style="line-height: 1.7; color: #ccc; margin-bottom: 28px;">
            It takes about five minutes. Once done, you're live and visible to clients across London.
        </p>
        <a href="{dashboard_url}"
           style="display: inline-block; background: #C9A84C; color: #0A0A0A; padding: 14px 32px;
                  text-decoration: none; font-weight: bold; border-radius: 4px; letter-spacing: 1px;">
            FINISH MY PROFILE
        </a>
        <p style="margin-top: 32px; color: #555; font-size: 12px;">
            This is an automated reminder. You're receiving it because your Bluechips London profile is incomplete. You can sign in to manage your account at any time.
        </p>
    </div>
    """
    return await send_email(to, f"{stage_name}, your profile is one step away", html)
