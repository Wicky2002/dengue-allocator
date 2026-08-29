'use client';

import React from 'react';
import { useActionState } from 'react';

import { Callout } from '@/components/ui/Callout';
import { signIn, type SignInState } from '@/app/signin/actions';

const INITIAL: SignInState = { error: null };

export function SignInForm() {
  const [state, action, pending] = useActionState(signIn, INITIAL);

  return (
    <form action={action} className="space-y-4">
      {state.error ? <Callout tone="danger">{state.error}</Callout> : null}

      <label className="block">
        <span className="text-sm font-medium text-text-700">Email address</span>
        <input
          type="email"
          name="email"
          autoComplete="username"
          required
          className="mt-1.5 w-full rounded-sm border border-border px-3 py-2.5 text-sm focus:border-primary-700"
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium text-text-700">Password</span>
        <input
          type="password"
          name="password"
          autoComplete="current-password"
          required
          className="mt-1.5 w-full rounded-sm border border-border px-3 py-2.5 text-sm focus:border-primary-700"
        />
      </label>

      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-sm bg-primary-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-800 disabled:opacity-60"
      >
        {pending ? 'Signing in…' : 'Sign in'}
      </button>
    </form>
  );
}

export default SignInForm;
