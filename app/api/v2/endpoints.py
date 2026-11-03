"""
Standardized API V2 Employee Records Endpoints with Idempotency and Rate Limiting.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, Response, status
from typing import Optional, Dict, Any

from app.models.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    PaginatedResponse
)
from app.storage.repository import repo
from app.core.security import get_current_tenant
from app.core.idempotency import idempotency_manager
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/employees", tags=["HRIS Employee Records (API V2)"])


def enforce_rate_limit(request: Request, tenant_id: str):
    allowed, limit, remaining, retry_after = rate_limiter.check_rate_limit(tenant_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Too many requests.",
            headers={
                "Retry-After": str(int(retry_after) + 1),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0"
            }
        )


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    request: Request,
    response: Response,
    x_idempotency_key: Optional[str] = Header(None, description="Unique key for safe retries"),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Standardized API V2 Endpoint for onboarding an employee.
    Enforces atomic distributed idempotency via X-Idempotency-Key.
    """
    enforce_rate_limit(request, tenant_id)

    # Idempotency evaluation
    if x_idempotency_key:
        payload_hash = idempotency_manager.compute_hash(payload.model_dump(mode="json"))
        try:
            is_new, existing = idempotency_manager.acquire_lock(x_idempotency_key, payload_hash)
        except ValueError as err:
            raise HTTPException(status_code=422, detail=str(err))

        if not is_new:
            if existing.in_flight:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A request with this idempotency key is currently being processed."
                )
            # Replay cached response
            response.headers["X-Cache-Lookup"] = "HIT"
            response.status_code = existing.response_status
            return existing.response_body

    try:
        new_emp = repo.create_employee(tenant_id, payload)
        result_dict = new_emp.model_dump(mode="json")
        
        if x_idempotency_key:
            idempotency_manager.store_response(x_idempotency_key, status.HTTP_201_CREATED, result_dict)
            response.headers["X-Cache-Lookup"] = "MISS"

        return new_emp
    except Exception as e:
        if x_idempotency_key:
            idempotency_manager.release_on_error(x_idempotency_key)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=PaginatedResponse)
def list_employees(
    request: Request,
    department: Optional[str] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, ONBOARDING, OFFBOARDED)"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: str = Depends(get_current_tenant)
):
    """List employees for the tenant with deterministic cursor-based pagination."""
    enforce_rate_limit(request, tenant_id)
    employees, next_cursor = repo.list_employees(
        tenant_id=tenant_id,
        department=department,
        status=status,
        cursor=cursor,
        limit=limit
    )
    return PaginatedResponse(
        data=[e.model_dump(mode="json") for e in employees],
        meta={"total_returned": len(employees)},
        pagination={"cursor": cursor, "next_cursor": next_cursor, "limit": limit}
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant)
):
    """Retrieve full employee profile by ID."""
    enforce_rate_limit(request, tenant_id)
    emp = repo.get_employee(tenant_id, employee_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee '{employee_id}' not found.")
    return emp


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    request: Request,
    tenant_id: str = Depends(get_current_tenant)
):
    """Update employee record attributes."""
    enforce_rate_limit(request, tenant_id)
    updated = repo.update_employee(tenant_id, employee_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee '{employee_id}' not found.")
    return updated


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant)
):
    """Remove employee from records."""
    enforce_rate_limit(request, tenant_id)
    deleted = repo.delete_employee(tenant_id, employee_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee '{employee_id}' not found.")
    return None
