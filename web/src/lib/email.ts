import 'server-only';

/**
 * Transactional email via Resend's REST API.
 *
 * Mirrors `dengue.platform.alerts._send_email` exactly -- same provider, same
 * plain REST call (no SDK dependency needed for one POST), same graceful
 * degradation: without `RESEND_API_KEY` this returns `sent: false` rather
 * than throwing, so a deployment with no email configured still lets an
 * admin create accounts -- it just falls back to the copy-and-hand-over
 * password flow instead of an automatic email.
 *
 * `RESEND_API_KEY` and `ALERT_FROM_EMAIL` are separate from the same-named
 * secrets the `refresh-data` GitHub Actions workflow uses -- that workflow
 * runs the Python side entirely outside Vercel, so this app needs its own
 * copies set as Vercel environment variables (see `.env.example`).
 */

const DEFAULT_FROM = 'DengueSentinel <onboarding@resend.dev>';

export interface SendEmailResult {
  sent: boolean;
  /** Present only when `sent` is false -- safe for a server log, not a user. */
  error?: string;
}

export async function sendEmail({
  to,
  subject,
  html,
}: {
  to: string;
  subject: string;
  html: string;
}): Promise<SendEmailResult> {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) return { sent: false, error: 'RESEND_API_KEY not set' };

  const from = process.env.ALERT_FROM_EMAIL || DEFAULT_FROM;
  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ from, to: [to], subject, html }),
    });
    if (!response.ok) {
      const body = await response.text().catch(() => '');
      return { sent: false, error: `Resend responded ${response.status}: ${body}` };
    }
    return { sent: true };
  } catch (err) {
    return { sent: false, error: err instanceof Error ? err.message : 'unknown error' };
  }
}
