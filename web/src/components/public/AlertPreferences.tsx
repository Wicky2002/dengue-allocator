'use client';

import React from 'react';
import { BellAlertIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

import { Callout } from '@/components/ui/Callout';
import { useT } from '@/components/i18n/LocaleProvider';

const STORAGE_KEY = 'denguesentinel.alerts';

interface Preferences {
  districts: string[];
  weekly: boolean;
  outbreakOnly: boolean;
}

/**
 * Alert preferences.
 *
 * Saved in this browser only. Delivery would need an SMS or email gateway,
 * which is not connected — so the panel says exactly that rather than
 * implying a subscription that will never arrive. Storing the choice locally
 * is a genuine convenience (the district list is remembered on the next visit)
 * without pretending to be a registration.
 */
export function AlertPreferences({ districts }: { districts: { district_id: string; name: string }[] }) {
  const t = useT();
  const [open, setOpen] = React.useState(false);
  const [prefs, setPrefs] = React.useState<Preferences>({
    districts: [],
    weekly: true,
    outbreakOnly: false,
  });
  const [saved, setSaved] = React.useState(false);

  React.useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      // This is exactly what an effect is for: reading an external system
      // (localStorage) that doesn't exist during server rendering, so it
      // cannot be read during render without a hydration mismatch. There is
      // no render-time alternative here the way there is in HistoryCompare.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (raw) setPrefs(JSON.parse(raw) as Preferences);
    } catch {
      // Private windows and blocked site data both throw here. The panel works
      // perfectly well with defaults, so there is nothing to report.
    }
  }, []);

  const save = () => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    } catch {
      // Same as above -- the preference simply is not remembered.
    }
    setSaved(true);
    window.setTimeout(() => setSaved(false), 4000);
  };

  const toggleDistrict = (id: string) =>
    setPrefs((current) => ({
      ...current,
      districts: current.districts.includes(id)
        ? current.districts.filter((value) => value !== id)
        : [...current.districts, id],
    }));

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
        <div className="border-t border-border p-5">
          <fieldset>
            <legend className="text-[13px] font-semibold text-text-700">{t('alerts.districts')}</legend>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {districts.map((district) => {
                const active = prefs.districts.includes(district.district_id);
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
          </fieldset>

          <div className="mt-5 space-y-2.5">
            <label className="flex items-center gap-2.5 text-[14px] text-text-700">
              <input
                type="checkbox"
                checked={prefs.weekly}
                onChange={(event) => setPrefs((c) => ({ ...c, weekly: event.target.checked }))}
                className="h-4 w-4 accent-primary-700"
              />
              {t('alerts.weekly')}
            </label>
            <label className="flex items-center gap-2.5 text-[14px] text-text-700">
              <input
                type="checkbox"
                checked={prefs.outbreakOnly}
                onChange={(event) => setPrefs((c) => ({ ...c, outbreakOnly: event.target.checked }))}
                className="h-4 w-4 accent-primary-700"
              />
              {t('alerts.outbreakOnly')}
            </label>
          </div>

          <button
            type="button"
            onClick={save}
            className="mt-5 rounded-sm bg-primary-700 px-4 py-2.5 text-[14px] font-semibold text-white hover:bg-primary-800"
          >
            {t('alerts.save')}
          </button>

          {saved ? (
            <p className="mt-3 text-[13px] font-medium text-teal-800">
              {t('alerts.saved')}
            </p>
          ) : null}

          <Callout tone="warning" title={t('alerts.noticeTitle')} className="mt-5">
            {t('alerts.noticeBody')}
          </Callout>
        </div>
      ) : null}
    </div>
  );
}

export default AlertPreferences;
