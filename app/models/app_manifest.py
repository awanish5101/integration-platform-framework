"""
Data models representing third-party applications in the App Shop / Marketplace.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional
from datetime import datetime


class AppManifest(BaseModel):
    app_id: str = Field(..., description="Unique machine identifier, e.g. 'slack-enterprise'")
    name: str = Field(..., description="Display name, e.g. 'Slack'")
    slug: str = Field(..., description="URL slug, e.g. 'slack'")
    category: str = Field(..., description="Category: 'COMMUNICATION', 'IT_ADMIN', 'FINANCE', 'IDENTITY'")
    description: str = Field(..., description="App description and capabilities")
    version: str = Field("1.0.0", description="SemVer release of integration")
    author: str = Field("Verified Partner", description="App developer or integration team")
    documentation_url: Optional[str] = None
    required_scopes: List[str] = Field(default_factory=list, description="OAuth permission scopes requested")
    supported_events: List[str] = Field(default_factory=list, description="Subscribed webhook event topics")
    config_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for required installation credentials")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AppManifestCreate(BaseModel):
    app_id: str
    name: str
    slug: str
    category: str
    description: str
    version: str = "1.0.0"
    author: str = "Internal Integration Team"
    documentation_url: Optional[str] = None
    required_scopes: List[str] = []
    supported_events: List[str] = []
    config_schema: Dict[str, Any] = {}
