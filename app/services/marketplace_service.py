"""
Marketplace / App Shop lifecycle service managing app discovery, validation, and installations.
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.app_manifest import AppManifest
from app.models.installation import AppInstallation, InstallationStatus, InstallAppRequest, ConfigureAppRequest
from app.storage.repository import repo


class MarketplaceService:
    def __init__(self, repository=repo):
        self.repo = repository

    def browse_apps(self, category: Optional[str] = None, search: Optional[str] = None) -> List[AppManifest]:
        return self.repo.get_all_apps(category=category, search=search)

    def get_app_details(self, app_id: str) -> Optional[AppManifest]:
        return self.repo.get_app_by_id(app_id)

    def install_app(self, tenant_id: str, request: InstallAppRequest) -> AppInstallation:
        app = self.repo.get_app_by_id(request.app_id)
        if not app:
            raise ValueError(f"Application '{request.app_id}' not found in App Shop catalog.")

        # Validate config values against manifest config_schema if required
        schema = app.config_schema or {}
        required_props = schema.get("required", [])
        provided_config = request.config_values or {}
        
        missing_configs = [prop for prop in required_props if prop not in provided_config]
        status = InstallationStatus.CONFIGURED if not missing_configs else InstallationStatus.PENDING_AUTH

        installation_id = f"inst_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        installation = AppInstallation(
            installation_id=installation_id,
            tenant_id=tenant_id,
            app_id=request.app_id,
            status=status,
            granted_scopes=request.granted_scopes or app.required_scopes,
            config_values=provided_config,
            installed_at=now,
            updated_at=now
        )
        return self.repo.save_installation(installation)

    def configure_app(self, tenant_id: str, app_id: str, request: ConfigureAppRequest) -> AppInstallation:
        installation = self.repo.get_installation(tenant_id, app_id)
        if not installation:
            raise ValueError(f"App '{app_id}' is not currently installed for tenant '{tenant_id}'.")

        app = self.repo.get_app_by_id(app_id)
        if app and app.config_schema:
            required_props = app.config_schema.get("required", [])
            for prop in required_props:
                if prop not in request.config_values:
                    raise ValueError(f"Missing mandatory configuration property: '{prop}'")

        installation.config_values.update(request.config_values)
        installation.status = InstallationStatus.CONFIGURED
        installation.updated_at = datetime.utcnow()
        return self.repo.save_installation(installation)

    def list_installed_apps(self, tenant_id: str) -> List[AppInstallation]:
        return self.repo.list_tenant_installations(tenant_id)

    def uninstall_app(self, tenant_id: str, app_id: str) -> bool:
        return self.repo.delete_installation(tenant_id, app_id)


marketplace_service = MarketplaceService()
