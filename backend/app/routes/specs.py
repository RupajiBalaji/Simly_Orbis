"""
Specification Authoring and Validation Routes (backend/app/routes/specs.py)

Provides API endpoints for the Section 8.14 authoring form:
1. POST /api/specs/validate — Field-level schema and semantic validation.
2. POST /api/specs/dry-run  — Execution of scripted actions against an authoring spec.
3. POST /api/specs/export   — Spec export with admin approval flag (approved=False).
"""

from __future__ import annotations

import copy
import json
import time
import uuid
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.lab.engine import apply_action, create_session
from app.lab.experiments import _EXPERIMENTS
from app.lab.models import ActionRequest, ActionType, LabSession
from app.security import resolve_client_ip
from app.specs.adapter import spec_to_experiment_definition
from app.specs.validator import ValidationReport, validate_spec_data

router = APIRouter(prefix="/api/specs", tags=["specs"])

MAX_SPEC_PAYLOAD_BYTES = 512 * 1024  # 512 KB
_VALIDATE_RATE_LIMIT = 60  # max 60 calls per minute per IP
_IP_TIMESTAMPS: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str) -> None:
    """Enforce in-memory sliding window rate limit (Section 10.3 / Task F4)."""
    now = time.time()
    cutoff = now - 60.0
    _IP_TIMESTAMPS[client_ip] = [t for t in _IP_TIMESTAMPS[client_ip] if t > cutoff]
    if len(_IP_TIMESTAMPS[client_ip]) >= _VALIDATE_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: maximum 60 spec validation requests per minute.",
        )
    _IP_TIMESTAMPS[client_ip].append(now)


class FieldError(BaseModel):
    """Field-level error message pointing at exact JSON path."""
    path: str
    message: str


class DryRunAction(BaseModel):
    """Single action to execute in dry run sequence."""
    action: ActionType
    target: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class DryRunStepResult(BaseModel):
    """Outcome of single action in dry-run sequence."""
    step_index: int
    action: str
    target: str | None
    accepted: bool
    message: str
    violations: list[dict[str, Any]]


class DryRunResponse(BaseModel):
    """Complete summary of spec dry run."""
    success: bool
    spec_id: str
    total_steps_executed: int
    final_score: int
    violations: list[dict[str, Any]]
    step_results: list[DryRunStepResult]


class DryRunRequest(BaseModel):
    """Payload to dry-run an authoring spec with scripted action sequence."""
    spec_data: dict[str, Any]
    actions: list[DryRunAction] = Field(default_factory=list)


class ValidateSpecRequest(BaseModel):
    """Payload to validate an authoring spec."""
    spec_data: dict[str, Any]
    dry_run_actions: list[DryRunAction] = Field(default_factory=list)


class ValidateSpecResponse(BaseModel):
    """Response containing field-level validation results."""
    valid: bool
    error_count: int
    errors: list[FieldError]
    dry_run: DryRunResponse | None = None


class ExportSpecRequest(BaseModel):
    """Payload to validate and export spec with admin approval flag."""
    spec_data: dict[str, Any]


class ExportSpecResponse(BaseModel):
    """Exported spec with approval metadata."""
    approved: bool
    approval_status: str
    exported_spec: dict[str, Any]


@router.post("/validate", response_model=ValidateSpecResponse, summary="Validate authoring spec")
async def validate_spec_endpoint(request: Request) -> ValidateSpecResponse:
    """
    Validate spec data and return field-level errors pointing at exact paths.
    Enforces maximum payload size limit (512KB), sliding-window rate limit,
    strict schema-only parsing (no eval/exec), zero file writes, and optional dry run.
    """
    client_ip = getattr(request.state, "client_ip", None)
    if not client_ip:
        client_ip = resolve_client_ip(request) or (
            request.client.host if request.client and request.client.host else "127.0.0.1"
        )
    _check_rate_limit(client_ip)

    # 1. Enforce payload size limit (512 KB)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_SPEC_PAYLOAD_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Payload exceeds maximum limit of 512KB",
                )
        except ValueError:
            pass

    raw_bytes = await request.body()
    if len(raw_bytes) > MAX_SPEC_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Payload exceeds maximum limit of 512KB",
        )

    # 2. Strict schema-only JSON parsing (no file writes, no code execution)
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed JSON: {e}",
        )

    if not isinstance(payload, dict) or "spec_data" not in payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must be a JSON object containing 'spec_data'",
        )

    spec_data = payload["spec_data"]
    if not isinstance(spec_data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'spec_data' must be a JSON object",
        )

    # 3. Reject hostile prototype pollution or script injection keys
    for hostile_key in ("__proto__", "constructor", "prototype", "__class__"):
        if hostile_key in spec_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hostile payload property detected: {hostile_key}",
            )

    report = validate_spec_data(spec_data)
    errors = [FieldError(path=e.path, message=e.message) for e in report.errors]

    # 4. Optional dry run execution if scripted actions supplied in validation request
    dry_run_res = None
    dry_actions = payload.get("dry_run_actions")
    if report.valid and dry_actions and isinstance(dry_actions, list):
        try:
            parsed_actions = [DryRunAction(**a) for a in dry_actions]
            dry_req = DryRunRequest(spec_data=spec_data, actions=parsed_actions)
            dry_run_res = await dry_run_spec_endpoint(dry_req)
        except Exception as ex:
            errors.append(FieldError(path="dry_run_actions", message=f"Dry run execution error: {ex}"))

    return ValidateSpecResponse(
        valid=report.valid and len(errors) == 0,
        error_count=len(errors),
        errors=errors,
        dry_run=dry_run_res,
    )


@router.post("/dry-run", response_model=DryRunResponse, summary="Dry-run authoring spec")
async def dry_run_spec_endpoint(body: DryRunRequest) -> DryRunResponse:
    """
    Simulate scripted actions against an in-memory session built from authoring spec.
    Never alters persistent database state.
    """
    report = validate_spec_data(body.spec_data)
    if not report.valid or report.spec is None:
        err_details = "; ".join(f"{e.path}: {e.message}" for e in report.errors)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot dry run invalid spec: {err_details}",
        )

    spec = report.spec
    temp_id = f"dryrun_{uuid.uuid4().hex[:8]}"

    # Bridge to temporary ExperimentDefinition
    # Choose base apparatus/inventory according to district
    from app.lab.experiments.titration import TITRATION_BENCH_EXPERIMENT
    from app.lab.experiments.pk_ward import PK_WARD_EXPERIMENT
    from app.lab.experiments.launch_bench import LAUNCH_BENCH_EXPERIMENT
    from app.lab.experiments.dose_lab import DOSE_LAB_EXPERIMENT

    base_exp = TITRATION_BENCH_EXPERIMENT
    if spec.district == "pharma":
        base_exp = DOSE_LAB_EXPERIMENT if "dose" in spec.id or "sim" in spec.engine.id else PK_WARD_EXPERIMENT
    elif spec.district == "space":
        base_exp = LAUNCH_BENCH_EXPERIMENT

    exp_def = spec_to_experiment_definition(
        spec,
        base_apparatus=copy.deepcopy(base_exp.apparatus),
        base_inventory=copy.deepcopy(base_exp.inventory),
        required_ppe=list(base_exp.required_ppe),
    )
    exp_def.id = temp_id

    _EXPERIMENTS[temp_id] = exp_def
    try:
        session = create_session(temp_id, "AuthoringDryRun")
        step_results: list[DryRunStepResult] = []

        for idx, act in enumerate(body.actions):
            req = ActionRequest(action=act.action, target=act.target, params=act.params)
            res = apply_action(session, req)
            vios = [
                {
                    "rule_id": v.rule_id,
                    "title": v.title,
                    "severity": v.severity,
                    "penalty": v.penalty_points,
                }
                for v in res.violations
            ]
            step_results.append(
                DryRunStepResult(
                    step_index=idx + 1,
                    action=act.action.value,
                    target=act.target,
                    accepted=res.accepted,
                    message=res.message,
                    violations=vios,
                )
            )

        final_score = max(0, min(100, sum(session.score_parts.values())))
        all_violations = [
            {
                "rule_id": v.rule_id,
                "title": v.title,
                "severity": v.severity,
                "penalty": v.penalty_points,
            }
            for v in session.violations
        ]

        return DryRunResponse(
            success=True,
            spec_id=spec.id,
            total_steps_executed=len(step_results),
            final_score=final_score,
            violations=all_violations,
            step_results=step_results,
        )
    finally:
        _EXPERIMENTS.pop(temp_id, None)


@router.post("/export", response_model=ExportSpecResponse, summary="Export spec with approval flag")
async def export_spec_endpoint(body: ExportSpecRequest) -> ExportSpecResponse:
    """
    Validate and export an authoring spec with approved=False (approval flag)
    per section 8.14 (requires admin approval before reaching public students).
    """
    report = validate_spec_data(body.spec_data)
    if not report.valid:
        err_details = "; ".join(f"{e.path}: {e.message}" for e in report.errors)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot export invalid spec: {err_details}",
        )

    exported = copy.deepcopy(body.spec_data)
    exported["approved"] = False
    exported["approval_status"] = "pending_admin_approval"

    return ExportSpecResponse(
        approved=False,
        approval_status="pending_admin_approval",
        exported_spec=exported,
    )
