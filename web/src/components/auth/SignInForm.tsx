'use client';

import React from 'react';
import { useActionState } from 'react';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

import { Callout } from '@/components/ui/Callout';
import { useT } from '@/components/i18n/LocaleProvider';
import { signIn, type SignInState } from '@/app/signin/actions';

const INITIAL: SignInState = { error: null };

export function SignInForm() {
  const [state, action, pending] = useActionState(signIn, INITIAL);
  const [showPassword, setShowPassword] = React.useState(false);
  const t = useT();

  return (
    <form action={action} className="space-y-4">
      {state.error ? <Callout tone="danger">{t(state.error)}</Callout> : null}

      <label className="block">
        <span className="text-sm font-medium text-text-700">{t('signin.emailLabel')}</span>
        <input
          type="email"
          name="email"
          autoComplete="username"
          required
          className="mt-1.5 w-full rounded-sm border border-border px-3 py-2.5 text-sm focus:border-primary-700"
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium text-text-700">{t('signin.passwordLabel')}</span>
        <div className="relative mt-1.5">
          <input
            type={showPassword ? 'text' : 'password'}
            name="password"
            autoComplete="current-password"
            required
            className="w-full rounded-sm border border-border px-3 py-2.5 pr-10 text-sm focus:border-primary-700"
          />
          <button
            type="button"
            onClick={() => setShowPassword((value) => !value)}
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
        </div>
      </label>

      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-sm bg-primary-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-800 disabled:opacity-60"
      >
        {pending ? t('signin.submitting') : t('signin.submit')}
      </button>
    </form>
  );
}

export default SignInForm;
