"""
AI-driven tooling for simplifying third-party connectivity, schema inference, and connector generation.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class FieldMapping(BaseModel):
    source_field: str
    target_field: str
    confidence: float
    transformation: Optional[str] = None


class SchemaAnalysisResult(BaseModel):
    source_entity: str
    target_entity: str
    mappings: List[FieldMapping]
    unmapped_fields: List[str]
    compatibility_score: float


class SchemaDriftReport(BaseModel):
    has_breaking_changes: bool
    missing_required_fields: List[str]
    newly_added_fields: List[str]
    type_conflicts: List[Dict[str, str]]
    risk_level: str  # "LOW", "MEDIUM", "HIGH"


class AIConnectorService:
    # Rippling Standardized HRIS Field Aliases
    HRIS_STANDARD_FIELDS = {
        "email": ["email", "work_email", "primary_email", "mail", "user_email", "login_email"],
        "first_name": ["first_name", "given_name", "fname", "forename", "firstName"],
        "last_name": ["last_name", "family_name", "lname", "surname", "lastName"],
        "title": ["title", "job_title", "designation", "role_title", "position"],
        "department": ["department", "dept", "business_unit", "cost_center", "team"],
        "start_date": ["start_date", "hire_date", "joining_date", "startDate", "employment_date"],
        "employment_status": ["status", "employment_status", "work_status", "active_flag"],
        "manager_id": ["manager_id", "reports_to", "supervisor_id", "manager_email"]
    }

    def synthesize_connector_mapping(self, source_payload: Dict[str, Any], entity_type: str = "employee") -> SchemaAnalysisResult:
        """
        Synthesizes a schema mapping from a sample third-party payload to the standardized HRIS schema.
        Calculates semantic confidence scores and recommends transformations.
        """
        mappings: List[FieldMapping] = []
        unmapped: List[str] = []
        
        flat_keys = list(source_payload.keys())
        matched_targets = set()

        for key in flat_keys:
            key_clean = key.lower().replace("-", "_").replace(" ", "_")
            best_match = None
            best_score = 0.0

            for target_field, aliases in self.HRIS_STANDARD_FIELDS.items():
                if key_clean == target_field.lower():
                    best_match = target_field
                    best_score = 1.0
                    break
                elif key_clean in [a.lower() for a in aliases]:
                    best_match = target_field
                    best_score = 0.95
                    break
                elif any(a in key_clean for a in aliases):
                    best_match = target_field
                    best_score = 0.75
                    break

            if best_match and best_match not in matched_targets:
                transformation = None
                if "date" in best_match:
                    transformation = "iso8601_date_parser"
                elif "email" in best_match:
                    transformation = "lowercase_trim"
                
                mappings.append(FieldMapping(
                    source_field=key,
                    target_field=best_match,
                    confidence=best_score,
                    transformation=transformation
                ))
                matched_targets.add(best_match)
            else:
                unmapped.append(key)

        score = round(len(mappings) / max(len(self.HRIS_STANDARD_FIELDS), 1), 2)
        return SchemaAnalysisResult(
            source_entity=entity_type,
            target_entity="rippling_hris_employee_v2",
            mappings=mappings,
            unmapped_fields=unmapped,
            compatibility_score=score
        )

    def detect_schema_drift(self, expected_schema: Dict[str, Any], observed_payload: Dict[str, Any]) -> SchemaDriftReport:
        """
        Proactively detects schema drift to fulfill Zero-KTLO platform resilience.
        """
        expected_props = expected_schema.get("properties", {})
        required_fields = set(expected_schema.get("required", []))
        observed_keys = set(observed_payload.keys())

        missing_required = list(required_fields - observed_keys)
        newly_added = list(observed_keys - set(expected_props.keys()))
        type_conflicts = []

        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            dict: "object",
            list: "array"
        }

        for k, v in observed_payload.items():
            if k in expected_props:
                expected_type = expected_props[k].get("type")
                actual_type = type_map.get(type(v), "unknown")
                if expected_type and expected_type != actual_type:
                    type_conflicts.append({
                        "field": k,
                        "expected": expected_type,
                        "observed": actual_type
                    })

        has_breaking = len(missing_required) > 0 or len(type_conflicts) > 0
        risk = "HIGH" if has_breaking else ("MEDIUM" if len(newly_added) > 0 else "LOW")

        return SchemaDriftReport(
            has_breaking_changes=has_breaking,
            missing_required_fields=missing_required,
            newly_added_fields=newly_added,
            type_conflicts=type_conflicts,
            risk_level=risk
        )

    def generate_connector_stub(self, app_slug: str, mappings: List[FieldMapping]) -> str:
        """
        Generates Python connector code implementing standardized transformations.
        """
        class_name = "".join(part.capitalize() for part in app_slug.replace("-", "_").split("_")) + "Connector"
        lines = [
            f"class {class_name}:",
            f'    """Standardized connector adapter generated for {app_slug}."""',
            "    def __init__(self, client):",
            "        self.client = client",
            "",
            "    def transform_to_standard(self, raw_record: dict) -> dict:",
            "        return {"
        ]
        for m in mappings:
            transform_str = f"raw_record.get('{m.source_field}')"
            if m.transformation == "lowercase_trim":
                transform_str = f"str(raw_record.get('{m.source_field}', '')).strip().lower()"
            lines.append(f"            '{m.target_field}': {transform_str},")
        lines.append("        }")
        return "\n".join(lines)


ai_connector_service = AIConnectorService()
