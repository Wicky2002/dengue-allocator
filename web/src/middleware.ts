import { NextResponse, type NextRequest } from 'next/server';
import { createServerClient, type CookieOptions } from '@supabase/ssr';

import { LOCALE_COOKIE, isLocale } from '@/lib/i18n/config';

/**
 * Applies `?lang=si|ta|en` to the request and pins it in the cookie.
 *
 * The language otherwise lives only in a cookie, which makes it invisible in a
 * URL — so a Tamil speaker could not send a colleague the page they were
 * actually looking at. Honouring the parameter here gives every page a
 * shareable per-language link without restructuring all eight routes under a
 * `/[locale]` segment, and the cookie set alongside it means the choice sticks
 * for the rest of the visit.
 */
function applyLocale(request: NextRequest, response: NextResponse): NextResponse {
  const requested = request.nextUrl.searchParams.get('lang');
  if (!isLocale(requested)) return response;

  request.cookies.set(LOCALE_COOKIE, requested);
  response.cookies.set(LOCALE_COOKIE, requested, {
    path: '/',
    maxAge: 60 * 60 * 24 * 365,
    sameSite: 'lax',
  });
  return response;
}

/**
 * A fresh per-request nonce, and the Content-Security-Policy built around it.
 *
 * `script-src` is nonce-gated with `strict-dynamic` — Next's own inline
 * hydration script and every script it loads from that pass, nothing else
 * does. `style-src` keeps `unsafe-inline`: several charts set an SVG fill or a
 * bar width via a React `style` prop, which compiles to inline `style="..."`
 * attributes — nonces don't reach those in practice, and inline styles are a
 * far smaller injection surface than inline scripts.
 *
 * `connect-src` allow-lists the configured Supabase project host, since the
 * client SDK calls it directly from the browser for auth and the `profiles`
 * read.
 *
 * THIS IS PRODUCTION-ONLY (see `middleware` below) — Next's dev server runs
 * Fast Refresh and its webpack HMR runtime via `eval()`, which a CSP without
 * `unsafe-eval` correctly blocks. That block doesn't just disable source
 * maps: it stops the dev bundle's own module loader from running at all, so
 * no client component hydrates — the map, the charts, the language switcher,
 * everything that needs JavaScript goes silently blank. That is exactly what
 * broke a live demo the first time this shipped, from testing the CSP only
 * against `next dev` on a different port and a `next start` production build,
 * never against the literal `next dev` process the demo was actually running.
 * A relaxed `unsafe-eval` policy for dev would reopen the exact class of
 * script-injection hole this header exists to close, so dev gets no CSP
 * instead, and the strict policy is verified against `next build && next
 * start` only.
 */
function buildCsp(nonce: string): string {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseHost = supabaseUrl ? new URL(supabaseUrl).origin : '';

  return [
    `default-src 'self'`,
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`,
    `style-src 'self' 'unsafe-inline'`,
    `img-src 'self' data: blob:`,
    `font-src 'self' data:`,
    `connect-src 'self'${supabaseHost ? ` ${supabaseHost}` : ''}`,
    `frame-ancestors 'none'`,
    `base-uri 'self'`,
    `form-action 'self'`,
    `object-src 'none'`,
    `upgrade-insecure-requests`,
  ].join('; ');
}

/**
 * Headers that don't touch script execution, so they're safe in dev too:
 * clickjacking, MIME sniffing, referrer leakage, and unneeded browser feature
 * access all have a one-line fix regardless of which compliance framework, if
 * any, a deployment cares about.
 */
function applyBaselineHeaders(response: NextResponse): NextResponse {
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=(), interest-cohort=()',
  );
  return response;
}

/** CSP + HSTS. Only ever called for a production build — see `buildCsp`'s docstring. */
function applyProductionSecurityHeaders(response: NextResponse, csp: string): NextResponse {
  response.headers.set('Content-Security-Policy', csp);
  response.headers.set('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload');
  return response;
}

export async function middleware(request: NextRequest) {
  const isProd = process.env.NODE_ENV === 'production';

  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');
  const csp = buildCsp(nonce);

  // Mirrored onto the outgoing request headers (not only the response) --
  // Next's documented CSP recipe: it's what lets a Server Component read the
  // same nonce via `headers()`, and lets Next apply it to its own
  // framework-injected scripts. Built even in dev so the plumbing is
  // identical either way; only `isProd` decides whether it's ever sent.
  const requestHeaders = new Headers(request.headers);
  if (isProd) {
    requestHeaders.set('x-nonce', nonce);
    requestHeaders.set('Content-Security-Policy', csp);
  }

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

  const finish = (response: NextResponse): NextResponse => {
    response = applyBaselineHeaders(response);
    return isProd ? applyProductionSecurityHeaders(response, csp) : response;
  };

  if (!url || !key) {
    const response = applyLocale(
      request,
      NextResponse.next({ request: { headers: requestHeaders } }),
    );
    return finish(response);
  }

  let response = applyLocale(request, NextResponse.next({ request: { headers: requestHeaders } }));

  const supabase = createServerClient(url, key, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (cookiesToSet: { name: string; value: string; options: CookieOptions }[]) => {
        for (const { name, value } of cookiesToSet) {
          request.cookies.set(name, value);
        }
        response = NextResponse.next({ request: { headers: requestHeaders } });
        for (const { name, value, options } of cookiesToSet) {
          response.cookies.set(name, value, options);
        }
      },
    },
  });

  // Touching the user is what performs the refresh; the result is read by the
  // pages through their own server client.
  await supabase.auth.getUser();

  response = applyLocale(request, response);
  return finish(response);
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|data/|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)'],
};
