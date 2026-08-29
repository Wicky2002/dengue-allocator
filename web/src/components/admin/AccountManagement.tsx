'use client';

import React from 'react';
import { useActionState } from 'react';
import {
  UserPlusIcon,
  PencilSquareIcon,
  ClipboardDocumentIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';

import { Callout } from '@/components/ui/Callout';
import { Badge } from '@/components/ui/Badge';
import { ROLES, isDistrictScopedRole, type RoleKey } from '@/lib/rbac';
import {
  createAccount,
  updateAccount,
  setAccountActive,
  deleteAccount,
  type AccountActionState,
  type AccountRow,
} from '@/app/admin/accounts/actions';

const ASSIGNABLE_ROLES = ROLES.filter((r) => r.key !== 'public');
const EMPTY_STATE: AccountActionState = { error: null, success: null };

/**
 * Administration → Users & roles' actual account management.
 *
 * Every mutation here calls a Server Action that independently re-checks the
 * caller is `national_admin` before doing anything — this component's own
 * page-level gate is a UI convenience, not the security boundary. See
 * `src/app/admin/accounts/actions.ts` for where that boundary actually is.
 */
export function AccountManagement({
  districts,
  initialAccounts,
}: {
  districts: { district_id: string; name: string }[];
  initialAccounts: AccountRow[] | { error: string };
}) {
  const [accounts, setAccounts] = React.useState<AccountRow[] | { error: string }>(
    initialAccounts,
  );
  const [editing, setEditing] = React.useState<AccountRow | null>(null);
  const [creating, setCreating] = React.useState(false);

  const refresh = React.useCallback(async () => {
    // A Server Action re-fetch keeps this table live after a mutation
    // without a full page reload -- `listAccounts` itself is one of the
    // same re-verified actions, so there's nothing extra to trust here.
    const { listAccounts } = await import('@/app/admin/accounts/actions');
    setAccounts(await listAccounts());
  }, []);

  if ('error' in accounts) {
    return <Callout tone="warning" title="Account management unavailable">{accounts.error}</Callout>;
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-text-600">
          {accounts.length} account{accounts.length === 1 ? '' : 's'}
        </p>
        <button
          type="button"
          onClick={() => setCreating(true)}
          className="inline-flex items-center gap-2 rounded-sm bg-primary-700 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-800"
        >
          <UserPlusIcon className="h-4 w-4" aria-hidden />
          New account
        </button>
      </div>

      <div className="overflow-x-auto rounded-sm border border-border bg-white shadow-card">
        <table className="w-full min-w-[860px] border-collapse text-sm">
          <thead className="border-b border-border bg-bg-100 text-xs uppercase tracking-wide text-text-500">
            <tr>
              <th scope="col" className="px-4 py-3 text-left">Account</th>
              <th scope="col" className="px-4 py-3 text-left">Role</th>
              <th scope="col" className="px-4 py-3 text-left">Scope</th>
              <th scope="col" className="px-4 py-3 text-left">Status</th>
              <th scope="col" className="px-4 py-3 text-left">Last sign-in</th>
              <th scope="col" className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((account) => (
              <tr key={account.id} className="border-b border-border last:border-0">
                <td className="px-4 py-2.5">
                  <span className="block font-medium text-text-900">{account.display_name}</span>
                  <span className="block text-xs text-text-500">{account.email}</span>
                </td>
                <td className="px-4 py-2.5 text-text-700">
                  {ROLES.find((r) => r.key === account.role)?.label ?? account.role}
                </td>
                <td className="px-4 py-2.5 text-text-600">
                  {account.role === 'national_admin'
                    ? 'Nationwide'
                    : account.districts.length > 0
                      ? account.districts
                          .map((id) => districts.find((d) => d.district_id === id)?.name ?? id)
                          .join(', ')
                      : '—'}
                  {account.facility ? (
                    <span className="block text-xs text-text-500">{account.facility}</span>
                  ) : null}
                </td>
                <td className="px-4 py-2.5">
                  <Badge tone={account.active ? 'success' : 'neutral'}>
                    {account.active ? 'Active' : 'Deactivated'}
                  </Badge>
                </td>
                <td className="num px-4 py-2.5 text-text-600">
                  {account.last_sign_in_at
                    ? new Date(account.last_sign_in_at).toLocaleDateString('en-GB', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })
                    : 'Never'}
                </td>
                <td className="px-4 py-2.5">
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setEditing(account)}
                      className="inline-flex items-center gap-1 rounded-sm border border-border px-2.5 py-1.5 text-xs font-medium text-text-700 hover:bg-bg-100"
                    >
                      <PencilSquareIcon className="h-3.5 w-3.5" aria-hidden />
                      Edit
                    </button>
                    <DeactivateButton account={account} onDone={refresh} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {creating ? (
        <CreateAccountDialog
          districts={districts}
          onClose={() => setCreating(false)}
          onCreated={refresh}
        />
      ) : null}
      {editing ? (
        <EditAccountDialog
          account={editing}
          districts={districts}
          onClose={() => setEditing(null)}
          onSaved={refresh}
        />
      ) : null}
    </div>
  );
}

function DeactivateButton({
  account,
  onDone,
}: {
  account: AccountRow;
  onDone: () => void;
}) {
  const [pending, startTransition] = React.useTransition();
  const [confirming, setConfirming] = React.useState(false);

  const toggle = () => {
    startTransition(async () => {
      await setAccountActive(account.id, !account.active);
      setConfirming(false);
      onDone();
    });
  };

  if (confirming) {
    return (
      <span className="inline-flex items-center gap-1.5">
        <span className="text-xs text-text-600">
          {account.active ? 'Deactivate?' : 'Reactivate?'}
        </span>
        <button
          type="button"
          onClick={toggle}
          disabled={pending}
          className="rounded-sm bg-state-600 px-2 py-1 text-xs font-semibold text-white hover:bg-state-700 disabled:opacity-60"
        >
          Yes
        </button>
        <button
          type="button"
          onClick={() => setConfirming(false)}
          className="rounded-sm border border-border px-2 py-1 text-xs font-medium text-text-600 hover:bg-bg-100"
        >
          No
        </button>
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={() => setConfirming(true)}
      className="inline-flex items-center gap-1 rounded-sm border border-border px-2.5 py-1.5 text-xs font-medium text-text-700 hover:bg-bg-100"
    >
      {account.active ? 'Deactivate' : 'Reactivate'}
    </button>
  );
}

function RoleAndScopeFields({
  role,
  setRole,
  selectedDistricts,
  toggleDistrict,
  facility,
  setFacility,
  districts,
}: {
  role: RoleKey | '';
  setRole: (role: RoleKey) => void;
  selectedDistricts: string[];
  toggleDistrict: (id: string) => void;
  facility: string;
  setFacility: (value: string) => void;
  districts: { district_id: string; name: string }[];
}) {
  const needsDistricts = role !== '' && isDistrictScopedRole(role);
  return (
    <>
      <label className="block">
        <span className="text-sm font-medium text-text-700">Role</span>
        <select
          name="role"
          required
          value={role}
          onChange={(event) => setRole(event.target.value as RoleKey)}
          className="mt-1.5 w-full rounded-sm border border-border px-3 py-2 text-sm"
        >
          <option value="" disabled>
            Choose a role
          </option>
          {ASSIGNABLE_ROLES.map((r) => (
            <option key={r.key} value={r.key}>
              {r.label}
            </option>
          ))}
        </select>
      </label>

      {needsDistricts ? (
        <fieldset>
          <legend className="text-sm font-medium text-text-700">
            Districts <span className="font-normal text-text-500">(at least one)</span>
          </legend>
          <div className="mt-2 flex max-h-40 flex-wrap gap-1.5 overflow-y-auto rounded-sm border border-border p-2">
            {districts.map((district) => {
              const active = selectedDistricts.includes(district.district_id);
              return (
                <button
                  key={district.district_id}
                  type="button"
                  onClick={() => toggleDistrict(district.district_id)}
                  aria-pressed={active}
                  className={`rounded-sm border px-2 py-1 text-xs font-medium ${
                    active
                      ? 'border-primary-700 bg-primary-700 text-white'
                      : 'border-border text-text-600 hover:border-primary-300'
                  }`}
                >
                  {district.name}
                </button>
              );
            })}
          </div>
          {selectedDistricts.map((id) => (
            <input key={id} type="hidden" name="districts" value={id} />
          ))}
        </fieldset>
      ) : null}

      <label className="block">
        <span className="text-sm font-medium text-text-700">
          Facility <span className="font-normal text-text-500">(optional)</span>
        </span>
        <input
          type="text"
          name="facility"
          value={facility}
          onChange={(event) => setFacility(event.target.value)}
          placeholder="e.g. National Hospital, Colombo"
          className="mt-1.5 w-full rounded-sm border border-border px-3 py-2 text-sm"
        />
      </label>
    </>
  );
}

function DialogShell({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-sm border border-border bg-white p-6 shadow-lift">
        <div className="mb-5 flex items-center justify-between">
          <h3 className="text-h3">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-text-500 hover:text-text-900"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function CreateAccountDialog({
  districts,
  onClose,
  onCreated,
}: {
  districts: { district_id: string; name: string }[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [state, formAction, pending] = useActionState(createAccount, EMPTY_STATE);
  const [role, setRole] = React.useState<RoleKey | ''>('');
  const [selectedDistricts, setSelectedDistricts] = React.useState<string[]>([]);
  const [facility, setFacility] = React.useState('');
  const [copied, setCopied] = React.useState(false);

  const toggleDistrict = (id: string) =>
    setSelectedDistricts((current) =>
      current.includes(id) ? current.filter((value) => value !== id) : [...current, id],
    );

  React.useEffect(() => {
    if (state.success) onCreated();
  }, [state.success, onCreated]);

  if (state.temporaryPassword) {
    return (
      <DialogShell title="Account created" onClose={onClose}>
        <Callout tone="success" title={state.success ?? 'Account created.'}>
          {state.emailSent ? (
            <>
              The account holder can also be given this password directly as a backup, in case
              the email doesn&rsquo;t arrive — it is shown only this once and this app does not
              store it.
            </>
          ) : (
            <>
              The email could not be sent automatically. Copy this temporary password now and
              hand it to the account holder out of band — it is shown only this once and this
              app does not store it.
            </>
          )}
        </Callout>
        <div className="mt-4 flex items-center gap-2 rounded-sm border border-border bg-bg-100 p-3">
          <code className="flex-1 break-all font-mono text-sm">{state.temporaryPassword}</code>
          <button
            type="button"
            onClick={() => {
              navigator.clipboard?.writeText(state.temporaryPassword ?? '');
              setCopied(true);
            }}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-sm bg-primary-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-primary-800"
          >
            {copied ? <CheckIcon className="h-3.5 w-3.5" /> : <ClipboardDocumentIcon className="h-3.5 w-3.5" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="mt-5 w-full rounded-sm bg-primary-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-800"
        >
          Done
        </button>
      </DialogShell>
    );
  }

  return (
    <DialogShell title="New staff account" onClose={onClose}>
      <form action={formAction} className="space-y-4">
        {state.error ? <Callout tone="danger">{state.error}</Callout> : null}

        <label className="block">
          <span className="text-sm font-medium text-text-700">Email address</span>
          <input
            type="email"
            name="email"
            required
            className="mt-1.5 w-full rounded-sm border border-border px-3 py-2 text-sm"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-text-700">Display name</span>
          <input
            type="text"
            name="display_name"
            required
            className="mt-1.5 w-full rounded-sm border border-border px-3 py-2 text-sm"
          />
        </label>

        <RoleAndScopeFields
          role={role}
          setRole={setRole}
          selectedDistricts={selectedDistricts}
          toggleDistrict={toggleDistrict}
          facility={facility}
          setFacility={setFacility}
          districts={districts}
        />

        <p className="text-xs text-text-500">
          A temporary password is generated automatically and emailed to this address if
          available; it&rsquo;s also shown once here as a backup. The account holder is asked to
          set their own password the first time they sign in.
        </p>

        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-sm bg-primary-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-800 disabled:opacity-60"
        >
          {pending ? 'Creating…' : 'Create account'}
        </button>
      </form>
    </DialogShell>
  );
}

function EditAccountDialog({
  account,
  districts,
  onClose,
  onSaved,
}: {
  account: AccountRow;
  districts: { district_id: string; name: string }[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [state, formAction, pending] = useActionState(updateAccount, EMPTY_STATE);
  const [role, setRole] = React.useState<RoleKey | ''>(account.role);
  const [selectedDistricts, setSelectedDistricts] = React.useState<string[]>(account.districts);
  const [facility, setFacility] = React.useState(account.facility ?? '');
  const [confirmingDelete, setConfirmingDelete] = React.useState(false);
  const [deletePending, startDeleteTransition] = React.useTransition();

  const toggleDistrict = (id: string) =>
    setSelectedDistricts((current) =>
      current.includes(id) ? current.filter((value) => value !== id) : [...current, id],
    );

  React.useEffect(() => {
    if (state.success) onSaved();
  }, [state.success, onSaved]);

  return (
    <DialogShell title={`Edit ${account.display_name}`} onClose={onClose}>
      <form action={formAction} className="space-y-4">
        <input type="hidden" name="id" value={account.id} />
        {state.error ? <Callout tone="danger">{state.error}</Callout> : null}

        <p className="text-sm text-text-500">{account.email}</p>

        <label className="block">
          <span className="text-sm font-medium text-text-700">Display name</span>
          <input
            type="text"
            name="display_name"
            defaultValue={account.display_name}
            required
            className="mt-1.5 w-full rounded-sm border border-border px-3 py-2 text-sm"
          />
        </label>

        <RoleAndScopeFields
          role={role}
          setRole={setRole}
          selectedDistricts={selectedDistricts}
          toggleDistrict={toggleDistrict}
          facility={facility}
          setFacility={setFacility}
          districts={districts}
        />

        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-sm bg-primary-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-800 disabled:opacity-60"
        >
          {pending ? 'Saving…' : 'Save changes'}
        </button>
      </form>

      <div className="mt-6 border-t border-border pt-4">
        <p className="text-xs text-text-500">
          Deactivating (from the table) is reversible and keeps this account&rsquo;s audit
          history. Deleting is not — use it only for an account created by mistake.
        </p>
        {confirmingDelete ? (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs font-medium text-state-700">Delete permanently?</span>
            <button
              type="button"
              disabled={deletePending}
              onClick={() =>
                startDeleteTransition(async () => {
                  await deleteAccount(account.id);
                  onSaved();
                  onClose();
                })
              }
              className="rounded-sm bg-state-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-state-700 disabled:opacity-60"
            >
              Yes, delete
            </button>
            <button
              type="button"
              onClick={() => setConfirmingDelete(false)}
              className="rounded-sm border border-border px-2.5 py-1 text-xs font-medium text-text-600 hover:bg-bg-100"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setConfirmingDelete(true)}
            className="mt-2 text-xs font-medium text-state-600 hover:underline"
          >
            Delete this account permanently
          </button>
        )}
      </div>
    </DialogShell>
  );
}

export default AccountManagement;
