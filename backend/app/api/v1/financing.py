from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.financing import FinancingOffer
from app.services.credit_score import CreditScoreService
from app.services.loan_provider import LoanProviderService
from datetime import datetime, timedelta
import uuid

router = APIRouter()

@router.get("/score")
async def get_credit_score(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's business credit score.
    """
    try:
        service = CreditScoreService(db)
        score_data = await service.calculate_score(str(current_user.id))
        return score_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/offers")
async def get_loan_offers(
    score: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available loan offers based on credit score.
    Persists offers to the database if they don't exist.
    """
    try:
        # 1. Calculate Score if needed
        if score is None:
            score_service = CreditScoreService(db)
            score_data = await score_service.calculate_score(str(current_user.id))
            score = score_data["score"]
            
        # 2. Get Simulated Offers
        provider = LoanProviderService()
        raw_offers = provider.get_offers(score)
        
        # 3. Persist Offers to DB
        saved_offers = []
        for offer_data in raw_offers:
            # Check if this specific offer already exists for the user (deduplication)
            # We assume unique combination of lender_name and loan_name for now
            stmt = select(FinancingOffer).where(
                FinancingOffer.user_id == current_user.id,
                FinancingOffer.lender_name == offer_data["provider"],
                # We could add more checks but this is a simple heuristic
                FinancingOffer.status == "pending"
            )
            result = await db.execute(stmt)
            existing_offer = result.scalars().first()
            
            if not existing_offer:
                # Map raw offer to DB model
                # We take the max amount and max term as the "offer" limits
                new_offer = FinancingOffer(
                    id=str(uuid.uuid4()),
                    user_id=current_user.id,
                    offer_type="term_loan", # Defaulting to term loan
                    amount=offer_data["amount_range"]["max"],
                    interest_rate=offer_data["interest_rate"] / 100.0, # Convert percentage to decimal
                    term_months=max(offer_data["term_months"]),
                    status="pending",
                    approval_probability=0.85, # Simulated probability
                    requirements=offer_data["requirements"],
                    conditions={"term_options": offer_data["term_months"]},
                    lender_name=offer_data["provider"],
                    lender_logo_url=offer_data["logo_url"],
                    expires_at=datetime.utcnow() + timedelta(days=30)
                )
                db.add(new_offer)
                saved_offers.append(new_offer)
            else:
                saved_offers.append(existing_offer)
        
        if saved_offers:
            await db.commit()
            
        # Return the raw offers structure as frontend expects it, 
        # but we could also return the saved_offers objects if we wanted to change frontend.
        # For now, let's stick to the contract but maybe add the ID?
        # The user asked to "upload... into financing_offers table".
        # The frontend still expects the structure from LoanProviderService.
        
        return {"offers": raw_offers, "based_on_score": score, "persisted_count": len(saved_offers)}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply")
async def apply_for_loan(
    application_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Placeholder for application logic
    return {"status": "submitted", "message": "Application received"}
