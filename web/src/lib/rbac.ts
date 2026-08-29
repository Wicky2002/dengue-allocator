/**
 * Roles, permissions and scope -- mirrored from `dengue.platform.rbac`.
 *
 * Two properties carried over from the engine and worth restating, because both
 * are easy to lose in a rewrite:
 *
 * **Permissions are additive by rank; scope is orthogonal to them.** A hospital
 * administrator and an MOH officer can hold overlapping permissions while
 * seeing entirely different rows -- one is scoped to a facility, the other to a
 * district. `Principal` therefore carries both, and collapsing them into a
 * single "level" is the usual way a health dashboard leaks data across regions.
 *
 * **Public data is a deny-by-default subset, not a redaction.** The public
 * pages are built from permissions the public role actually holds, rather than
 * by computing the full picture and hiding parts of it -- so a bug here shows
 * missing information rather than exposing hospital occupancy.
 */

import constants from '@/generated/constants.json';

export type RoleKey = 'public' | 'hospital_staff' | 'moh_officer' | 'national_admin';

export type Permission = string;

export interface RoleDef {
  key: RoleKey;
  label: string;
  description: string;
  permissions: Permission[];
}

export const ROLES: RoleDef[] = constants.roles as RoleDef[];

const ROLE_BY_KEY = new Map(ROLES.map((r) => [r.key, r]));

export function role(key: RoleKey): RoleDef {
  const found = ROLE_BY_KEY.get(key);
  if (!found) throw new Error(`Unknown role: ${key}`);
  return found;
}

export interface Principal {
  role: RoleKey;
  displayName: string;
  /** Districts this principal may see rows for. Empty means nationwide. */
  districts: string[];
  facility?: string | null;
  email?: string | null;
}

export const PUBLIC_PRINCIPAL: Principal = {
  role: 'public',
  displayName: 'Member of the public',
  districts: [],
};

export function can(principal: Principal, permission: Permission): boolean {
  return role(principal.role).permissions.includes(permission);
}

/**
 * Whether a role requires at least one district to have any scope at all.
 *
 * The one check that must never be forked: an account with a district-scoped
 * role and zero districts falls through to "nationwide" everywhere in this
 * codebase that doesn't explicitly guard against it (`filterToScope` below,
 * `isInScope`, the district-picker UI) -- the same failure
 * `dengue.platform.rbac.Principal.__post_init__` refuses to construct in
 * Python. One helper here means a future scoped role is one line, not four
 * call sites to remember.
 */
export function isDistrictScopedRole(key: RoleKey): boolean {
  return key === 'hospital_staff' || key === 'moh_officer';
}

/**
 * Whether `districtId` is visible under a scope list.
 *
 * `null` and `[]` both mean nationwide -- two conventions exist in this
 * codebase (`Principal.districts` is always `string[]`, some components pass
 * `string[] | null`) and this accepts either rather than forcing every call
 * site to normalise first.
 */
export function isInScope(districtId: string | null | undefined, districts: string[] | null): boolean {
  if (districtId == null) return false;
  if (districts == null || districts.length === 0) return true;
  return districts.includes(districtId);
}

/** Human-readable description of what this principal can see. */
export function scopeLabel(principal: Principal): string {
  if (principal.role === 'public') return 'Public information only';
  if (principal.districts.length === 0) return 'All 25 districts';
  if (principal.districts.length === 1) return `${principal.districts[0]} district`;
  return `${principal.districts.length} districts`;
}

/**
 * Restrict rows to the principal's scope.
 *
 * Applied at every read of district-level data rather than at render: a filter
 * that lives in a component is one refactor away from being dropped.
 */
export function filterToScope<T extends { district_id?: string | null }>(
  rows: T[],
  principal: Principal,
): T[] {
  return rows.filter((row) => isInScope(row.district_id, principal.districts));
}

/** Which route each role lands on after signing in. */
export const HOME_ROUTE: Record<RoleKey, string> = {
  public: '/public',
  hospital_staff: '/hospital',
  moh_officer: '/moh',
  national_admin: '/admin',
};
