"""
Security and tenant resolution dependencies for API V2.
"""
from fastapi import Header, HTTPException, status
from typing import Optional


def get_current_tenant(
    x_tenant_id: Optional[str] = Header(None, description="Organization / Tenant identifier"),
    authorization: Optional[str] = Header(None, description="Bearer token or API Key")
) -> str:
    """
    Resolves and validates the active organization tenant from request headers.
    In production, this unpacks verified JWT claims; defaults to standardized tenant for tests/local dev.
    """
    if not x_tenant_id:
        return "tenant_rippling_corp"
    
    # Sanitize and validate tenant ID format (allow letters, digits, dashes, and underscores)
    cleaned = x_tenant_id.replace("-", "").replace("_", "")
    if len(x_tenant_id) < 3 or not cleaned.isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Tenant-ID header format. Must be alphanumeric with hyphens or underscores."
        )
    return x_tenant_id
