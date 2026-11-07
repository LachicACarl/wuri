from dataclasses import dataclass

from .indicators import FRAMEWORK_INDICATORS

FRAMEWORK_EDITIONS = {
    "WURI": "2026",
    "THE": "2026",
    "QS": "2026",
    "UI GreenMetric": "2025",
}


@dataclass(frozen=True)
class FrameworkDefinition:
    framework_id: str
    official_name: str
    methodology_version: str | None
    criteria: dict[str, str]
    weight_status: str
    criteria_status: str
    source_url: str | None
    source_checked_at: str | None

    def as_dict(self) -> dict:
        return {
            "framework_id": self.framework_id,
            "official_name": self.official_name,
            "methodology_version": self.methodology_version,
            "criteria": self.criteria,
            "weight_status": self.weight_status,
            "criteria_status": self.criteria_status,
            "source_url": self.source_url,
            "source_checked_at": self.source_checked_at,
        }


def framework_catalog() -> list[dict]:
    return [
        {
            **definition.as_dict(),
            "methodology_version": FRAMEWORK_EDITIONS[framework],
            "criteria_ids": sorted(definition.criteria),
        }
        for framework, definition in FRAMEWORK_DEFINITIONS.items()
    ]


# Prototype indicator descriptions are retained for retrieval, but their
# official provenance and weights must be verified before final scoring.
FRAMEWORK_DEFINITIONS = {
    framework: FrameworkDefinition(
        framework_id=framework,
        official_name=framework,
        methodology_version=None,
        criteria=dict(indicators),
        weight_status="unverified",
        criteria_status="provisional_retrieval_catalog",
        source_url=None,
        source_checked_at=None,
    )
    for framework, indicators in FRAMEWORK_INDICATORS.items()
}


def verified_frameworks() -> list[str]:
    return [
        framework
        for framework, definition in FRAMEWORK_DEFINITIONS.items()
        if definition.weight_status == "verified"
        and definition.criteria_status == "verified"
    ]
