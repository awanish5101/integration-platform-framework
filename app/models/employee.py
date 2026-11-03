"""
Standardized HRIS Employee Record models for API V2.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
from enum import Enum


class EmploymentStatus(str, Enum):
    ONBOARDING = "ONBOARDING"
    ACTIVE = "ACTIVE"
    LEAVE = "LEAVE"
    OFFBOARDED = "OFFBOARDED"


class EmployeeBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[\w\.\+-]+@[\w\.-]+\.\w+$", description="Corporate email address")
    department: str = Field("Engineering", max_length=100)
    title: str = Field(..., max_length=150)
    employment_status: EmploymentStatus = Field(default=EmploymentStatus.ACTIVE)
    start_date: date = Field(default_factory=date.today)
    manager_id: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = Field(None, pattern=r"^[\w\.\+-]+@[\w\.-]+\.\w+$")
    department: Optional[str] = None
    title: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None
    manager_id: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class EmployeeResponse(EmployeeBase):
    employee_id: str
    tenant_id: str
    external_sync_ids: Dict[str, str] = Field(default_factory=dict, description="Synced IDs in 3rd party apps, e.g. slack_user_id")
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseModel):
    data: list[Any]
    meta: Dict[str, Any]
    pagination: Dict[str, Any]
