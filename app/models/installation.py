"""
Tenant app installation models representing App Shop lifecycle states.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class InstallationStatus(str, Enum):
    PENDING_AUTH = "PENDING_AUTH"
    INSTALLED = "INSTALLED"
    CONFIGURED = "CONFIGURED"
    SUSPENDED = "SUSPENDED"
    UNINSTALLED = "UNINSTALLED"


class AppInstallation(BaseModel):
    installation_id: str = Field(..., description="Unique installation ID")
    tenant_id: str = Field(..., description="Organization or company tenant identifier")
    app_id: str = Field(..., description="Target application ID")
    status: InstallationStatus = Field(default=InstallationStatus.INSTALLED)
    granted_scopes: list[str] = Field(default_factory=list)
    config_values: Dict[str, Any] = Field(default_factory=dict, description="Encrypted/stored credentials and settings")
    installed_by: str = Field("system-admin", description="Admin user initiating install")
    installed_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class InstallAppRequest(BaseModel):
    app_id: str = Field(..., description="App to install")
    config_values: Optional[Dict[str, Any]] = Field(default_factory=dict)
    granted_scopes: Optional[list[str]] = Field(default_factory=list)


class ConfigureAppRequest(BaseModel):
    config_values: Dict[str, Any]
