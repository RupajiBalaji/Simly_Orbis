"""
Shared module interface and data models for simulation districts.

Every district (pharma, chemistry, space, market) implements SimModule.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, Field

DistrictType = Literal["pharma", "chemistry", "space", "market"]


class RealityCheck(BaseModel):
    """Scientific or analytical sanity check validating module computation."""

    name: str = Field(..., description="Short name of the reality check")
    description: str = Field(..., description="Description of the test or expectation")
    expected: float = Field(..., description="Theoretical or benchmark expected value")
    actual: float = Field(..., description="Actual value calculated by the engine")
    tolerance: float = Field(..., description="Allowable relative tolerance fraction (e.g. 0.02 for 2%)")
    passed: bool = Field(..., description="Whether the check passed within tolerance")
    source_note: str = Field(..., description="Source citation or derivation for the expected value")


class RunResult(BaseModel):
    """Output of a simulation module run."""

    module_id: str = Field(..., description="Identifier of the executing module")
    params: dict[str, Any] = Field(..., description="Echoed input parameters")
    summary: dict[str, Any] = Field(..., description="Key scalar outputs and metrics")
    series: dict[str, list[float]] | None = Field(
        default=None,
        description="Named time series or coordinate traces (optional)",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any physiological, numerical, or boundary warnings",
    )
    duration_ms: float = Field(..., description="Computation duration in milliseconds")
    engine_version: str = Field(..., description="Core simulation engine version")


class SimModule(ABC):
    """
    Abstract base class for all district simulation modules.

    Modules perform pure computation with no disk/network I/O.
    """

    id: str
    name: str
    district: DistrictType
    description: str
    version: str
    params_model: type[BaseModel]

    @abstractmethod
    def run(self, params: BaseModel | dict[str, Any]) -> RunResult:
        """Execute simulation computation on validated parameters."""

    @abstractmethod
    def reality_checks(self) -> list[RealityCheck]:
        """Run benchmark scientific checks and return verification report."""
