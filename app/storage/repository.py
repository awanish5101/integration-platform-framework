"""
Thread-safe repository simulating persistence with tenant isolation.
"""
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from app.models.app_manifest import AppManifest
from app.models.installation import AppInstallation, InstallationStatus
from app.models.employee import EmployeeResponse, EmployeeCreate, EmployeeUpdate
from app.models.webhook import WebhookEvent, WebhookStatus


class InMemoryRepository:
    def __init__(self):
        self._lock = threading.RLock()
        
        # In-memory tables
        self._apps: Dict[str, AppManifest] = {}
        self._installations: Dict[str, AppInstallation] = {}  # key: f"{tenant_id}:{app_id}"
        self._employees: Dict[str, EmployeeResponse] = {}     # key: employee_id
        self._webhooks: Dict[str, WebhookEvent] = {}          # key: event_id
        
        # Seed default App Shop catalog
        self._seed_default_apps()

    def _seed_default_apps(self):
        apps = [
            AppManifest(
                app_id="slack-enterprise",
                name="Slack Enterprise Grid",
                slug="slack",
                category="COMMUNICATION",
                description="Automate Slack workspace provisioning, user channels, and employee onboarding invites.",
                version="2.1.0",
                author="Rippling Integration Team",
                documentation_url="https://docs.rippling.com/integrations/slack",
                required_scopes=["users:read", "users:write", "channels:write"],
                supported_events=["employee.onboarded", "employee.offboarded", "employee.updated"],
                config_schema={
                    "type": "object",
                    "properties": {
                        "api_token": {"type": "string", "description": "Bot User OAuth Token"},
                        "default_channel": {"type": "string", "default": "#general"}
                    },
                    "required": ["api_token"]
                }
            ),
            AppManifest(
                app_id="google-workspace",
                name="Google Workspace",
                slug="google-workspace",
                category="IT_ADMIN",
                description="Provision Google accounts, Gmail inboxes, and Google Drive access within 90 seconds.",
                version="1.8.4",
                author="Rippling Integration Team",
                documentation_url="https://docs.rippling.com/integrations/google",
                required_scopes=["admin.directory.user", "admin.directory.group"],
                supported_events=["employee.onboarded", "employee.offboarded"],
                config_schema={
                    "type": "object",
                    "properties": {
                        "service_account_json": {"type": "string"},
                        "primary_domain": {"type": "string"}
                    },
                    "required": ["service_account_json", "primary_domain"]
                }
            ),
            AppManifest(
                app_id="github-enterprise",
                name="GitHub Enterprise",
                slug="github",
                category="IT_ADMIN",
                description="Manage engineering organization memberships, team assignments, and SAML SSO links.",
                version="2.0.1",
                author="Rippling Integration Team",
                documentation_url="https://docs.rippling.com/integrations/github",
                required_scopes=["admin:org", "read:user"],
                supported_events=["employee.onboarded", "employee.offboarded", "employee.department_changed"],
                config_schema={
                    "type": "object",
                    "properties": {
                        "org_name": {"type": "string"},
                        "access_token": {"type": "string"}
                    },
                    "required": ["org_name", "access_token"]
                }
            )
        ]
        for app in apps:
            self._apps[app.app_id] = app

    # --- App Shop / Marketplace Operations ---
    def get_all_apps(self, category: Optional[str] = None, search: Optional[str] = None) -> List[AppManifest]:
        with self._lock:
            apps = list(self._apps.values())
            if category:
                apps = [a for a in apps if a.category.upper() == category.upper()]
            if search:
                query = search.lower()
                apps = [a for a in apps if query in a.name.lower() or query in a.description.lower() or query in a.slug.lower()]
            return apps

    def get_app_by_id(self, app_id: str) -> Optional[AppManifest]:
        with self._lock:
            return self._apps.get(app_id)

    def register_app(self, app: AppManifest) -> AppManifest:
        with self._lock:
            self._apps[app.app_id] = app
            return app

    # --- Installations ---
    def get_installation(self, tenant_id: str, app_id: str) -> Optional[AppInstallation]:
        with self._lock:
            key = f"{tenant_id}:{app_id}"
            return self._installations.get(key)

    def list_tenant_installations(self, tenant_id: str) -> List[AppInstallation]:
        with self._lock:
            return [
                inst for inst in self._installations.values()
                if inst.tenant_id == tenant_id and inst.status != InstallationStatus.UNINSTALLED
            ]

    def save_installation(self, installation: AppInstallation) -> AppInstallation:
        with self._lock:
            key = f"{installation.tenant_id}:{installation.app_id}"
            installation.updated_at = datetime.utcnow()
            self._installations[key] = installation
            return installation

    def delete_installation(self, tenant_id: str, app_id: str) -> bool:
        with self._lock:
            key = f"{tenant_id}:{app_id}"
            if key in self._installations:
                self._installations[key].status = InstallationStatus.UNINSTALLED
                self._installations[key].updated_at = datetime.utcnow()
                return True
            return False

    # --- Employee Records (Standardized API V2) ---
    def create_employee(self, tenant_id: str, data: EmployeeCreate) -> EmployeeResponse:
        with self._lock:
            employee_id = f"emp_{uuid.uuid4().hex[:12]}"
            now = datetime.utcnow()
            emp = EmployeeResponse(
                employee_id=employee_id,
                tenant_id=tenant_id,
                created_at=now,
                updated_at=now,
                **data.model_dump()
            )
            self._employees[employee_id] = emp
            return emp

    def get_employee(self, tenant_id: str, employee_id: str) -> Optional[EmployeeResponse]:
        with self._lock:
            emp = self._employees.get(employee_id)
            if emp and emp.tenant_id == tenant_id:
                return emp
            return None

    def list_employees(
        self,
        tenant_id: str,
        department: Optional[str] = None,
        status: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> (List[EmployeeResponse], Optional[str]):
        with self._lock:
            records = [e for e in self._employees.values() if e.tenant_id == tenant_id]
            if department:
                records = [e for e in records if e.department.lower() == department.lower()]
            if status:
                records = [e for e in records if e.employment_status.value == status.upper()]
            
            # Sort deterministically by employee_id
            records.sort(key=lambda x: x.employee_id)
            
            # Cursor pagination
            start_idx = 0
            if cursor:
                for idx, r in enumerate(records):
                    if r.employee_id > cursor:
                        start_idx = idx
                        break
                else:
                    start_idx = len(records)
            
            paged = records[start_idx : start_idx + limit]
            next_cursor = paged[-1].employee_id if len(paged) == limit and (start_idx + limit < len(records)) else None
            return paged, next_cursor

    def update_employee(self, tenant_id: str, employee_id: str, update: EmployeeUpdate) -> Optional[EmployeeResponse]:
        with self._lock:
            emp = self.get_employee(tenant_id, employee_id)
            if not emp:
                return None
            
            dump = update.model_dump(exclude_unset=True)
            updated_dict = emp.model_dump()
            updated_dict.update(dump)
            updated_dict["updated_at"] = datetime.utcnow()
            
            updated_emp = EmployeeResponse(**updated_dict)
            self._employees[employee_id] = updated_emp
            return updated_emp

    def delete_employee(self, tenant_id: str, employee_id: str) -> bool:
        with self._lock:
            emp = self.get_employee(tenant_id, employee_id)
            if emp:
                del self._employees[employee_id]
                return True
            return False

    # --- Webhooks & Dead Letter Queue (DLQ) ---
    def record_webhook(self, event: WebhookEvent) -> WebhookEvent:
        with self._lock:
            self._webhooks[event.event_id] = event
            return event

    def get_webhook(self, event_id: str) -> Optional[WebhookEvent]:
        with self._lock:
            return self._webhooks.get(event_id)

    def list_dlq_events(self, tenant_id: Optional[str] = None) -> List[WebhookEvent]:
        with self._lock:
            return [
                w for w in self._webhooks.values()
                if w.status == WebhookStatus.FAILED_DLQ and (tenant_id is None or w.tenant_id == tenant_id)
            ]


# Singleton instance
repo = InMemoryRepository()
