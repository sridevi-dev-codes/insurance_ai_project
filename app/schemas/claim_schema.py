# from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any


class ClaimDetails(BaseModel):
    claim_id: str
    policy_id: str
    claim_type: str
    incident_type: str
    incident_date: str
    reported_delay_days: int
    estimated_damage: float
    idv: float
    deductible: float
    previous_claims_90_days: int
    documents_submitted: List[str]
    policy_status: str

    @field_validator("policy_status")
    @classmethod
    def validate_policy_status(cls, v):
        if v.lower() != "active":
            raise ValueError("Policy must be active")
        return v

    @field_validator("estimated_damage")
    @classmethod
    def validate_damage(cls, v):
        if v <= 0:
            raise ValueError("Estimated damage must be greater than 0")
        return v

    @field_validator("idv")
    @classmethod
    def validate_idv(cls, v):
        if v <= 0:
            raise ValueError("IDV must be greater than 0")
        return v

    @field_validator("deductible")
    @classmethod
    def validate_deductible(cls, v):
        if v < 0:
            raise ValueError("Deductible cannot be negative")
        return v

class ClaimRequest(BaseModel):
    question: str = Field(
        ...,
        example="Is this motor insurance claim eligible for coverage?"
    )

    claim_details: ClaimDetails

class ClaimAssessmentResponse(BaseModel):
    claim_id: str

    eligibility: str = Field(
        ...,
        example="Approved"
    )

    fraud_risk: str = Field(
        ...,
        example="Low"
    )

    recommended_payout: float = Field(
        ...,
        example=290000
    )

    reasoning: List[str]

    citations: List[str]

    retrieved_documents: list[str] = []




