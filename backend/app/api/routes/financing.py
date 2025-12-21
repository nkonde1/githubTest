# backend/app/api/routes/financing.py
"""
Financing and lending routes.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.financing import LoanApplication, FinancingOffer
from app.services.financing import FinancingService
from app.schemas.financing import (
    FinancingApplicationCreate,
    FinancingApplicationResponse,
    FinancingOfferResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/offers", response_model=List[FinancingOfferResponse])
def get_financing_offers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get available financing offers for the user."""
    
    # Get active offers for user
    offers = db.query(FinancingOffer).filter(
        FinancingOffer.user_id == current_user.id,
        FinancingOffer.is_active == True,
        FinancingOffer.valid_until > func.now()
    ).all()
    
    return [FinancingOfferResponse.from_orm(offer) for offer in offers]


@router.post("/offers/generate")
def generate_financing_offers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Generate personalized financing offers using ML."""
    
    financing_service = FinancingService(db)
    offers = financing_service.generate_offers_for_user(current_user.id)
    
    return {
        "message": f"Generated {len(offers)} financing offers",
        "offers": [FinancingOfferResponse.from_orm(offer) for offer in offers]
    }


@router.post("/applications", response_model=FinancingApplicationResponse)
def create_financing_application(
    application_data: FinancingApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Submit a financing application."""
    
    financing_service = FinancingService(db)
    application = financing_service.create_application(current_user.id, application_data)
    
    logger.info(f"Financing application created: {application.id} for user {current_user.email}")
    
    return FinancingApplicationResponse.from_orm(application)


@router.get("/applications", response_model=List[FinancingApplicationResponse])
def get_financing_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get user's financing applications."""
    
    applications = db.query(FinancingApplication).filter(
        FinancingApplication.user_id == current_user.id
    ).order_by(desc(FinancingApplication.created_at)).all()
    
    return [FinancingApplicationResponse.from_orm(app) for app in applications]


@router.get("/applications/{application_id}", response_model=FinancingApplicationResponse)
def get_financing_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get specific financing application details."""
    
    application = db.query(FinancingApplication).filter(
        FinancingApplication.id == application_id,
        FinancingApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financing application not found"
        )
    
    return FinancingApplicationResponse.from_orm(application)