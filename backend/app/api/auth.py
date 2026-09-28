"""
backend/app/api/auth.py
Demo authentication endpoints.
Provides demo login, token generation, and customer profile retrieval.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.db.store import get_store
from backend.app.services.identity import create_token, get_current_customer

router = APIRouter(prefix="/api", tags=["auth"])


class LoginRequest(BaseModel):
    customer_id: str = Field(..., description="Demo customer identifier to sign in as.")


class CustomerResponse(BaseModel):
    id: str
    display_name: str
    email_masked: str


class LoginResponse(BaseModel):
    token: str
    customer: CustomerResponse


@router.get("/customers", response_model=List[CustomerResponse])
def list_demo_customers():
    """Returns available seeded demo customers for the login picker."""
    store = get_store()
    customers = store.list_customers()
    return [
        CustomerResponse(
            id=c["id"],
            display_name=c["display_name"],
            email_masked=c["email_masked"],
        )
        for c in customers
    ]


@router.post("/login", response_model=LoginResponse)
def demo_login(req: LoginRequest):
    """
    Demo login endpoint: verifies customer exists and issues a signed session token.
    No passwords in demo environment.
    """
    cid = req.customer_id.strip().lower()
    store = get_store()
    customer = store.get_customer(cid)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{cid}' not found in demo database.",
        )

    token = create_token(cid)
    return LoginResponse(
        token=token,
        customer=CustomerResponse(
            id=customer["id"],
            display_name=customer["display_name"],
            email_masked=customer["email_masked"],
        ),
    )


@router.get("/me", response_model=CustomerResponse)
def get_current_user_profile(
    customer_id: str = Depends(get_current_customer),
):
    """Returns the authenticated customer profile decoded from the Authorization header."""
    store = get_store()
    customer = store.get_customer(customer_id)
    return CustomerResponse(
        id=customer["id"],
        display_name=customer["display_name"],
        email_masked=customer["email_masked"],
    )
