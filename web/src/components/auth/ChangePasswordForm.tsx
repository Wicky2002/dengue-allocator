'use client';

import React from 'react';
import { useActionState } from 'react';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

import { Callout } from '@/components/ui/Callout';
import { useT } from '@/components/i18n/LocaleProvider';
import { changePassword, type ChangePasswordState } from '@/app/change-password/actions';

const INITIAL: ChangePasswordState = { error: null };

/** One toggle button, used identically in both password fields since they share one show/hide state. */
function ToggleVisibilityButton({
  showPassword,
  onToggle,
}: {
  showPassword: boolean;
  onToggle: () => void;
}) {
  const t = useT();
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={showPassword ? t('signin.hidePassword') : t('signin.showPassword')}
      aria-pressed={showPassword}
      className="absolute inset-y-0 right-0 grid w-10 place-items-center text-text-500 hover:text-text-700"
    >
      {showPassword ? (
        <EyeSlashIcon className="h-5 w-5" aria-hidden />
      ) : (
        <EyeIcon className="h-5 w-5" aria-hidden />
      )}
    </button>
  );
}

export function ChangePasswordForm() {
  const [state, action, pending] = useActionState(changePassword, INITIAL);
  const [showPassword, setShowPassword] = React.useState(false);
  const t = useT();

  return (
    <form action={action} className="space-y-4">
      {state.error ? <Callout tone="danger">{t(state.error)}</Callout> : null}

      <label className="block">
        <span className="text-sm font-medium text-text-700">
          {t('changePassword.newPasswordLabel')}
        </span>
        <div className="relative mt-1.5">
          <input
            type={showPassword ? 'text' : 'password'}
            name="password"
            autoComplete="new-password"
            required
            minLength={8}
            className="w-full rounded-sm border border-border px-3 py-2.5 pr-10 text-sm focus:border-primary-700"
          />
          <ToggleVisibilityButton
            showPassword={showPassword}
            onToggle={() => setShowPassword((value) => !value)}
          />
        </div>
      </label>

      <label className="block">
        <span className="text-sm font-medium text-text-700">
          {t('changePassword.confirmPasswordLabel')}
        </span>
        <div className="relative mt-1.5">
          <input
            type={showPassword ? 'text' : 'password'}
            name="confirm"
            autoComplete="new-password"
            required
            minLength={8}
            className="w-full rounded-sm border border-border px-3 py-2.5 pr-10 text-sm focus:border-primary-700"
          />
          <ToggleVisibilityButton
            showPassword={showPassword}
            onToggle={() => setShowPassword((value) => !value)}
          />
        </div>
      </label>

      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-sm bg-primary-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-800 disabled:opacity-60"
      >
        {pending ? t('changePassword.submitting') : t('changePassword.submit')}
      </button>
    </form>
  );
}

export default ChangePasswordForm;
