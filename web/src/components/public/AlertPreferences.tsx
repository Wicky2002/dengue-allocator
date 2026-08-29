'use client';

import React from 'react';
import { useActionState } from 'react';
import { BellAlertIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

import { Callout } from '@/components/ui/Callout';
import { useT } from '@/components/i18n/LocaleProvider';
import { subscribeToAlerts, type AlertSubscribeState } from '@/app/public/actions';

const STORAGE_KEY = 'denguesentinel.alerts';

interface RememberedChoice {
  districts: string[];
  weekly: boolean;
  outbreakOnly: boolean;
}

const EMPTY_STATE: AlertSubscribeState = { error: null, success: false };

/**
 * Alert preferences.
 *
 * Submits to `subscribeToAlerts`, a real insert into the `alert_subscriptions`
 * table sent weekly by `dengue.platform.alerts.send_due_alerts` (a scheduled
 * job, not this page) — the same table and RPC the Streamlit app's own
 * subscription form writes to, so a subscriber reaches the same list
 * regardless of which front end they used to sign up.
 *
 * `localStorage` still remembers the district selection between visits — a
 * genuine convenience, not a substitute for the real subscription — since
 * there is no read path back to the server for an anonymous visitor's own
 * row (RLS grants insert only, on purpose: a submitted address can never be
 * enumerated from the client).
 */
export function AlertPreferences({ districts }: { districts: { district_id: string; name: string }[] }) {
  const t = useT();
  const [open, setOpen] = React.useState(false);
  const [state, formAction, pending] = useActionState(subscribeToAlerts, EMPTY_STATE);
  const [remembered, setRemembered] = React.useState<RememberedChoice>({
    districts: [],
    weekly: true,
    outbreakOnly: false,
  });
  const [selectedDistricts, setSelectedDistricts] = React.useState<string[]>([]);

  React.useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      // Reading localStorage can only happen client-side after mount, to
      // avoid a hydration mismatch against the server-rendered markup --
      // this is exactly what an effect is for, not a render-time shortcut.
      // Both pieces of state it seeds are set together, here, rather than
      // chaining a second effect off the first (which is what the earlier,
      // rejected version of this component did).
      if (!raw) return;
      const parsed = JSON.parse(raw) as RememberedChoice;
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setRemembered(parsed);
      setSelectedDistricts(parsed.districts);
    } catch {
      // Private windows and blocked site data both throw here. The form
      // works perfectly well with defaults, so there is nothing to report.
    }
  }, []);

  const toggleDistrict = (id: string) =>
    setSelectedDistricts((current) =>
      current.includes(id) ? current.filter((value) => value !== id) : [...current, id],
    );

  React.useEffect(() => {
    if (!state.success) return;
    try {
      window.localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ districts: selectedDistricts, weekly: true, outbreakOnly: false }),
      );
    } catch {
      // Same as above -- the reminder simply isn't saved; the real
      // subscription already succeeded regardless.
    }
  }, [state.success, selectedDistricts]);

  return (
    <div className="rounded-sm border border-border bg-white shadow-card">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left"
      >
        <span className="inline-flex items-center gap-2 font-semibold text-text-900">
          <BellAlertIcon className="h-5 w-5 text-primary-700" aria-hidden />
          {t('alerts.title')}
        </span>
        <ChevronDownIcon
          className={`h-5 w-5 text-text-500 transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden
        />
      </button>

      {open ? (
        <form action={formAction} className="border-t border-border p-5">
          {state.error ? (
            <Callout tone="danger" className="mb-4">
              {state.error}
            </Callout>
          ) : null}
          {state.success ? (
            <Callout tone="success" title={t('alerts.subscribedTitle')} className="mb-4">
              {t('alerts.subscribed')}
            </Callout>
          ) : null}

          <label className="block">
            <span className="text-[13px] font-semibold text-text-700">{t('alerts.email')}</span>
            <input
              type="email"
              name="email"
              required
              placeholder="you@example.com"
              className="mt-1.5 w-full rounded-sm border border-border px-3 py-2 text-sm"
            />
          </label>

          <fieldset className="mt-4">
            <legend className="text-[13px] font-semibold text-text-700">{t('alerts.districts')}</legend>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {districts.map((district) => {
                const active = selectedDistricts.includes(district.district_id);
                return (
                  <button
                    key={district.district_id}
                    type="button"
                    onClick={() => toggleDistrict(district.district_id)}
                    aria-pressed={active}
                    className={`rounded-sm border px-2.5 py-1 text-[12.5px] font-medium transition-colors ${
                      active
                        ? 'border-primary-700 bg-primary-700 text-white'
                        : 'border-border bg-white text-text-600 hover:border-primary-300'
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

          <div className="mt-5 space-y-2.5">
            <label className="flex items-center gap-2.5 text-[14px] text-text-700">
              <input
                type="checkbox"
                name="weekly"
                defaultChecked={remembered.weekly}
                className="h-4 w-4 accent-primary-700"
              />
              {t('alerts.weekly')}
            </label>
            <label className="flex items-center gap-2.5 text-[14px] text-text-700">
              <input
                type="checkbox"
                name="outbreakOnly"
                defaultChecked={remembered.outbreakOnly}
                className="h-4 w-4 accent-primary-700"
              />
              {t('alerts.outbreakOnly')}
            </label>
          </div>

          <button
            type="submit"
            disabled={pending}
            className="mt-5 rounded-sm bg-primary-700 px-4 py-2.5 text-[14px] font-semibold text-white hover:bg-primary-800 disabled:opacity-60"
          >
            {pending ? '…' : t('alerts.save')}
          </button>

          <Callout tone="info" title={t('alerts.noticeTitle')} className="mt-5">
            {t('alerts.noticeBody')}
          </Callout>
        </form>
      ) : null}
    </div>
  );
}

export default AlertPreferences;
