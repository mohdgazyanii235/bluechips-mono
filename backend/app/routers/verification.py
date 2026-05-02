from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.database import get_db
from app.models.escort import Escort
from app.models.verification import Verification
from app.services.storage_service import upload_document
from app.services.email_service import send_verification_submitted_to_admin
from app.routers.deps import get_current_verified_escort, get_current_escort
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/submit-identity-documents", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def submit_identity_verification(
    background_tasks: BackgroundTasks,
    id_document: UploadFile = File(...),
    selfie: UploadFile = File(...),
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    # Check subscription tier
    if escort.subscription_tier not in ["essential", "premium", "elite"]:
        raise HTTPException(status_code=400, detail="Identity verification is only available for paid subscribers")

    # Check if already verified
    if escort.verification_level >= 2:
        raise HTTPException(status_code=400, detail="Identity already verified or pending review")

    # Check if already pending
    existing_result = await db.execute(
        select(Verification).where(
            Verification.escort_id == escort.id,
            Verification.level == 2,
            Verification.status == "pending",
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Verification already submitted and pending review")

    id_bytes = await id_document.read()
    selfie_bytes = await selfie.read()

    id_key = await upload_document(id_bytes, id_document.filename or "id.jpg")
    selfie_key = await upload_document(selfie_bytes, selfie.filename or "selfie.jpg")

    verification = Verification(
        escort_id=escort.id,
        level=2,
        id_document_url=id_key,
        selfie_url=selfie_key,
        status="pending",
    )
    db.add(verification)
    await db.flush()

    # Queue admin notification email
    background_tasks.add_task(
        send_verification_submitted_to_admin,
        escort_stage_name=escort.stage_name,
        escort_email=escort.email,
        submission_level=2,
    )

    return MessageResponse(message="Documents submitted successfully. Your application will be reviewed within 1 hour.")


@router.post("/submit-blue-tick-documents", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def submit_blue_tick(
    background_tasks: BackgroundTasks,
    match_selfie: UploadFile = File(...),
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    # Require active blue tick subscription
    if not escort.blue_tick_stripe_subscription_id:
        raise HTTPException(status_code=400, detail="Please subscribe to the Blue Tick add-on first (£10 setup + £3.99/month)")

    # Check if identity verified first
    if escort.verification_level < 2:
        raise HTTPException(status_code=400, detail="Please complete identity verification first")

    # Check if already pending
    existing_result = await db.execute(
        select(Verification).where(
            Verification.escort_id == escort.id,
            Verification.level == 3,
            Verification.status == "pending",
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Blue Tick verification already pending")

    selfie_bytes = await match_selfie.read()
    selfie_key = await upload_document(selfie_bytes, match_selfie.filename or "match_selfie.jpg")

    verification = Verification(
        escort_id=escort.id,
        level=3,
        match_selfie_url=selfie_key,
        status="pending",
    )
    db.add(verification)
    await db.flush()

    # Queue admin notification email
    background_tasks.add_task(
        send_verification_submitted_to_admin,
        escort_stage_name=escort.stage_name,
        escort_email=escort.email,
        submission_level=3,
    )

    return MessageResponse(message="Blue Tick request submitted successfully. Your application will be reviewed within 1 hour.")


@router.get("/status")
async def get_verification_status(
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Verification)
        .where(Verification.escort_id == escort.id)
        .order_by(Verification.submitted_at.desc())
    )
    verifications = result.scalars().all()

    # Find pending verification if any
    pending_submission = None
    for v in verifications:
        if v.status == "pending":
            pending_submission = {
                "id": str(v.id),
                "level": v.level,
                "submitted_at": v.submitted_at.isoformat(),
                "estimated_review_time_minutes": 60,
                "level_name": "Identity Verification" if v.level == 2 else "Blue Tick",
            }
            break

    return {
        "verification_level": escort.verification_level,
        "subscription_tier": escort.subscription_tier,
        "subscription_expires_at": escort.subscription_expires_at.isoformat() if escort.subscription_expires_at else None,
        "pending_submission": pending_submission,
        "submissions": [
            {
                "id": str(v.id),
                "level": v.level,
                "level_name": "Identity Verification" if v.level == 2 else "Blue Tick",
                "status": v.status,
                "submitted_at": v.submitted_at.isoformat(),
                "reviewed_at": v.reviewed_at.isoformat() if v.reviewed_at else None,
                "admin_notes": v.admin_notes,
            }
            for v in verifications
        ],
    }
