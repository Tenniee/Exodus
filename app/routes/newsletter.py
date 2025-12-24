"""
Newsletter subscription routes
Handles newsletter email subscriptions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.newsletter import NewsletterSubscription
from app.schemas.newsletter import NewsletterSubscribe, NewsletterSubscriptionResponse

# ============================================================================
# ROUTER SETUP
# ============================================================================

# Create an APIRouter for newsletter endpoints
router = APIRouter(
    prefix="/newsletter",
    tags=["Newsletter"]
)

# ============================================================================
# SUBSCRIBE ENDPOINT
# ============================================================================

@router.post("/subscribe", response_model=NewsletterSubscriptionResponse, status_code=status.HTTP_201_CREATED)
def subscribe_to_newsletter(subscription_data: NewsletterSubscribe, db: Session = Depends(get_db)):
    """
    Subscribe an email to the newsletter
    
    Process:
    1. Check if email is already subscribed
    2. Create new subscription in database
    3. Return subscription details
    
    Args:
        subscription_data: Email address to subscribe
        db: Database session (automatically injected)
    
    Returns:
        Subscription details with ID and timestamp
    
    Raises:
        HTTPException 400 if email is already subscribed
    """
    # Check if this email is already subscribed
    # db.query() starts a query on the NewsletterSubscription table
    # .filter() adds a WHERE clause to check if email matches
    # .first() returns the first result or None
    existing_subscription = db.query(NewsletterSubscription).filter(
        NewsletterSubscription.email == subscription_data.email.lower()
    ).first()
    
    if existing_subscription:
        # Email is already subscribed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already subscribed to the newsletter"
        )
    
    # Create a new newsletter subscription
    new_subscription = NewsletterSubscription(
        email=subscription_data.email.lower().strip()  # Store email in lowercase, trimmed
    )
    
    # Add the subscription to the database session
    db.add(new_subscription)
    
    # Commit the transaction (save to database)
    # The subscribed_at timestamp is automatically set by the database
    db.commit()
    
    # Refresh to get the auto-generated ID and timestamp
    db.refresh(new_subscription)
    
    # Return the subscription details
    return new_subscription


# ============================================================================
# ============================================================================
# ============================================================================
