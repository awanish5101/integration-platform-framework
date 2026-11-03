"""
API V2 Marketplace / App Shop routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional

from app.models.app_manifest import AppManifest
from app.models.installation import AppInstallation, InstallAppRequest, ConfigureAppRequest
from app.services.marketplace_service import marketplace_service
from app.core.security import get_current_tenant

router = APIRouter(prefix="/marketplace", tags=["Marketplace & App Shop"])


@router.get("/apps", response_model=List[AppManifest])
def list_apps(
    category: Optional[str] = Query(None, description="Filter by category (COMMUNICATION, IT_ADMIN, FINANCE)"),
    search: Optional[str] = Query(None, description="Search by app name or slug")
):
    """Discover applications available in the Rippling App Shop."""
    return marketplace_service.browse_apps(category=category, search=search)


@router.get("/apps/{app_id}", response_model=AppManifest)
def get_app(app_id: str):
    """Retrieve full manifest and configuration schema for a specific app."""
    app = marketplace_service.get_app_details(app_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"App '{app_id}' not found.")
    return app


@router.post("/install", response_model=AppInstallation, status_code=status.HTTP_201_CREATED)
def install_app(
    request: InstallAppRequest,
    tenant_id: str = Depends(get_current_tenant)
):
    """Install a third-party app into the organization's tenant ecosystem."""
    try:
        return marketplace_service.install_app(tenant_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/installations/{app_id}/configure", response_model=AppInstallation)
def configure_app(
    app_id: str,
    request: ConfigureAppRequest,
    tenant_id: str = Depends(get_current_tenant)
):
    """Configure credentials, OAuth tokens, and settings for an installed app."""
    try:
        return marketplace_service.configure_app(tenant_id, app_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/installations", response_model=List[AppInstallation])
def get_tenant_installations(tenant_id: str = Depends(get_current_tenant)):
    """List all integrations active for the calling tenant."""
    return marketplace_service.list_installed_apps(tenant_id)


@router.delete("/installations/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def uninstall_app(
    app_id: str,
    tenant_id: str = Depends(get_current_tenant)
):
    """Uninstall a third-party integration and revoke scoped credentials."""
    success = marketplace_service.uninstall_app(tenant_id, app_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App installation not found.")
    return None
