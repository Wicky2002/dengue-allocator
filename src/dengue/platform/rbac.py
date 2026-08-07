"""Role-based access control.

Four roles, mirroring how Sri Lanka's public health system actually delegates:

======================  ==============================================================
Role                    Sees
======================  ==============================================================
``PUBLIC``              Risk maps, forecasts, prevention advice, nearby clinics
``HOSPITAL_STAFF``      + readiness planning, bed/supply projections for their facility
``MOH_OFFICER``         + district intervention planning, team deployment, hotspots
``NATIONAL_ADMIN``      + nationwide view, user management, model config, audit log
======================  ==============================================================

Two design decisions worth stating.

**Permissions are additive by rank, but scope is orthogonal to them.** A
hospital administrator and an MOH officer may hold overlapping permissions while
seeing entirely different rows: one is scoped to a facility, the other to a
district. Collapsing "what you may do" and "what you may see" into a single
level is the usual way health dashboards leak data across regions, so
:class:`Principal` carries both.

**Public data is a deny-by-default subset, not a redaction.** The public portal
is built from permissions the public role actually holds, rather than by
computing the full picture and hiding parts of it. A redaction bug then shows
missing information rather than exposing hospital occupancy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from dengue import config


class Role(str, Enum):
    """Who the viewer is."""

    PUBLIC = "public"
    HOSPITAL_STAFF = "hospital_staff"
    MOH_OFFICER = "moh_officer"
    NATIONAL_ADMIN = "national_admin"

    @property
    def label(self) -> str:
        return {
            Role.PUBLIC: "Public",
            Role.HOSPITAL_STAFF: "Hospital staff",
            Role.MOH_OFFICER: "MOH / Regional Health Officer",
            Role.NATIONAL_ADMIN: "National administrator",
        }[self]

    @property
    def description(self) -> str:
        return {
            Role.PUBLIC: "Citizens checking risk where they live.",
            Role.HOSPITAL_STAFF: "Clinical and administrative staff preparing a facility.",
            Role.MOH_OFFICER: "District health officers planning vector control and campaigns.",
            Role.NATIONAL_ADMIN: "Ministry of Health — nationwide oversight and configuration.",
        }[self]


class Permission(str, Enum):
    """A single capability. Grouped by the portal that introduces it."""

    # Public
    VIEW_PUBLIC_RISK = "view_public_risk"
    VIEW_FORECAST = "view_forecast"
    VIEW_PREVENTION = "view_prevention"
    VIEW_CLINIC_LOCATIONS = "view_clinic_locations"
    SUBSCRIBE_ALERTS = "subscribe_alerts"

    # Hospital
    VIEW_HOSPITAL_READINESS = "view_hospital_readiness"
    VIEW_SUPPLY_PLANNING = "view_supply_planning"
    VIEW_ADMISSION_FORECAST = "view_admission_forecast"

    # MOH
    VIEW_DISTRICT_OPERATIONS = "view_district_operations"
    VIEW_TEAM_ALLOCATION = "view_team_allocation"
    EDIT_INTERVENTION_PLAN = "edit_intervention_plan"
    VIEW_BUDGET_OPTIMISER = "view_budget_optimiser"
    RUN_SCENARIO = "run_scenario"

    # National admin
    VIEW_NATIONAL_OPERATIONS = "view_national_operations"
    MANAGE_USERS = "manage_users"
    CONFIGURE_MODELS = "configure_models"
    VIEW_AUDIT_LOG = "view_audit_log"
    VIEW_SYSTEM_HEALTH = "view_system_health"
    TRIGGER_RETRAIN = "trigger_retrain"


_PUBLIC_PERMISSIONS: frozenset[Permission] = frozenset(
    {
        Permission.VIEW_PUBLIC_RISK,
        Permission.VIEW_FORECAST,
        Permission.VIEW_PREVENTION,
        Permission.VIEW_CLINIC_LOCATIONS,
        Permission.SUBSCRIBE_ALERTS,
    }
)

_HOSPITAL_PERMISSIONS: frozenset[Permission] = _PUBLIC_PERMISSIONS | {
    Permission.VIEW_HOSPITAL_READINESS,
    Permission.VIEW_SUPPLY_PLANNING,
    Permission.VIEW_ADMISSION_FORECAST,
}

_MOH_PERMISSIONS: frozenset[Permission] = _HOSPITAL_PERMISSIONS | {
    Permission.VIEW_DISTRICT_OPERATIONS,
    Permission.VIEW_TEAM_ALLOCATION,
    Permission.EDIT_INTERVENTION_PLAN,
    Permission.VIEW_BUDGET_OPTIMISER,
    Permission.RUN_SCENARIO,
}

_ADMIN_PERMISSIONS: frozenset[Permission] = _MOH_PERMISSIONS | {
    Permission.VIEW_NATIONAL_OPERATIONS,
    Permission.MANAGE_USERS,
    Permission.CONFIGURE_MODELS,
    Permission.VIEW_AUDIT_LOG,
    Permission.VIEW_SYSTEM_HEALTH,
    Permission.TRIGGER_RETRAIN,
}

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.PUBLIC: _PUBLIC_PERMISSIONS,
    Role.HOSPITAL_STAFF: _HOSPITAL_PERMISSIONS,
    Role.MOH_OFFICER: _MOH_PERMISSIONS,
    Role.NATIONAL_ADMIN: _ADMIN_PERMISSIONS,
}


@dataclass(frozen=True)
class Principal:
    """An authenticated viewer: a role plus the data scope it applies to.

    Attributes
    ----------
    role:
        The viewer's role.
    name:
        Display name.
    districts:
        Districts this principal may see operational detail for. Empty means
        **all** districts, which is only legitimate for a national admin --
        enforced in :meth:`__post_init__`.
    facility:
        Facility name, for hospital staff.

    Examples
    --------
    >>> p = Principal(Role.MOH_OFFICER, "RDHS Gampaha", districts=("gampaha",))
    >>> p.can(Permission.VIEW_TEAM_ALLOCATION)
    True
    >>> p.can(Permission.MANAGE_USERS)
    False
    >>> p.may_see_district("colombo")
    False
    """

    role: Role
    name: str = ""
    districts: tuple[str, ...] = field(default_factory=tuple)
    facility: str = ""

    def __post_init__(self) -> None:
        unknown = [d for d in self.districts if d not in config.DISTRICT_BY_ID]
        if unknown:
            raise ValueError(f"Principal scoped to unknown districts: {unknown}")

        # Guard against the most consequential misconfiguration: a non-admin
        # silently receiving nationwide scope because its district list was
        # left empty.
        if not self.districts and self.role in (Role.HOSPITAL_STAFF, Role.MOH_OFFICER):
            raise ValueError(
                f"Role {self.role.value!r} must be scoped to at least one district. "
                "An empty district list means nationwide access, which this role "
                "must not have."
            )

    @property
    def permissions(self) -> frozenset[Permission]:
        return ROLE_PERMISSIONS[self.role]

    def can(self, permission: Permission) -> bool:
        """Whether this principal holds ``permission``."""
        return permission in self.permissions

    def require(self, permission: Permission) -> None:
        """Raise :class:`PermissionError` unless the principal holds ``permission``."""
        if not self.can(permission):
            raise PermissionError(
                f"Role {self.role.value!r} does not have permission {permission.value!r}"
            )

    @property
    def has_national_scope(self) -> bool:
        return self.role is Role.NATIONAL_ADMIN or not self.districts

    def may_see_district(self, district_id: str) -> bool:
        """Whether operational detail for ``district_id`` is in scope."""
        if self.role is Role.PUBLIC:
            # Public risk information is national and non-sensitive by design.
            return True
        if self.has_national_scope:
            return True
        return district_id in self.districts

    def visible_districts(self) -> tuple[str, ...]:
        """Districts this principal may see operational detail for."""
        if self.has_national_scope or self.role is Role.PUBLIC:
            return config.DISTRICT_IDS
        return self.districts

    def scope_label(self) -> str:
        if self.role is Role.PUBLIC:
            return "Sri Lanka (public information)"
        if self.has_national_scope:
            return "Sri Lanka (all districts)"
        names = [config.get_district(d).name for d in self.districts]
        if self.facility:
            return f"{self.facility} — {', '.join(names)}"
        return ", ".join(names)


def filter_to_scope(frame, principal: Principal, column: str = "district_id"):
    """Restrict a DataFrame to the principal's district scope.

    The single choke point for scope enforcement: panels call this rather than
    each re-implementing the check, so there is one place to audit.
    """
    if principal.has_national_scope or principal.role is Role.PUBLIC:
        return frame
    if column not in getattr(frame, "columns", []):
        return frame
    return frame[frame[column].isin(principal.visible_districts())]


#: Demo principals for the portal switcher. Not credentials -- this build has no
#: authentication backend, and the UI says so plainly.
DEMO_PRINCIPALS: dict[Role, Principal] = {
    Role.PUBLIC: Principal(Role.PUBLIC, "Member of the public"),
    Role.HOSPITAL_STAFF: Principal(
        Role.HOSPITAL_STAFF,
        "Duty officer",
        districts=("colombo",),
        facility="National Hospital, Colombo",
    ),
    Role.MOH_OFFICER: Principal(Role.MOH_OFFICER, "RDHS Gampaha", districts=("gampaha", "colombo")),
    Role.NATIONAL_ADMIN: Principal(Role.NATIONAL_ADMIN, "MoH administrator"),
}
