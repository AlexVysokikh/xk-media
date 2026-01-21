"""
Pydantic schemas for request/response validation.
"""

from decimal import Decimal
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"


# ─────────────────────────────────────────────────────────────
# Payment schemas
# ─────────────────────────────────────────────────────────────

class CreateAdvertiserPaymentIn(BaseModel):
    """Request to create a payment for advertiser."""
    purpose: str = Field(..., min_length=1, max_length=500, description="Payment purpose/description")
    amount: Decimal = Field(..., gt=0, description="Payment amount")


class PaymentOut(BaseModel):
    """Payment response DTO."""
    id: int
    purpose: str | None = None
    amount: Decimal
    currency: str
    status: str
    pkInvoiceId: str | None = None
    payUrl: str | None = None
    pkPaymentId: str | None = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────
# User schemas (examples)
# ─────────────────────────────────────────────────────────────

# class UserCreate(BaseModel):
#     email: str
#     password: str
#
# class UserResponse(BaseModel):
#     id: int
#     email: str
#     
#     class Config:
#         from_attributes = True
