# DengueSentinel — web

The Next.js front end for the DengueSentinel platform. It renders the artifacts
written by the Python pipeline in the repository root; it never runs a model.

## Run it

From the repository root:

```bash
make export-web   # artifacts/*.parquet -> web/public/data/*.json
make web-setup    # npm install (first time only)
make web          # re-exports, then starts the dev server on :3000
```

`make web-build` produces a production build the same way.

## How data gets here

Next cannot read Parquet, so `dengue.export_web` is the single bridge between
the engine and this app:

| Written to | What it is |
|---|---|
| `public/data/*.json` | One file per pipeline artifact, plus per-district assessments and the district registry |
| `public/data/districts.geojson` | Simplified district boundaries (OCHA/HDX, CC-BY-IGO) |
| `src/generated/constants.json` | Risk thresholds, the role/permission matrix, provenance tiers, clinical ratio defaults and the source registry |

`constants.json` is **generated, not hand-written**. A risk threshold or a
permission that drifted between the engine and the UI would paint a district the
wrong colour or show the wrong rows, with nothing failing anywhere — so there is
exactly one place to change either, and it is on the Python side.

**Re-run `make export-web` after every `make pipeline`,** or the browser keeps
showing the previous run.

## Rules this app inherits from the engine

**It never computes at request time.** Every figure comes from an artifact.
Sliders index precomputed sweeps rather than re-solving: the budget slider on
the MOH portal walks cached ILP solutions, and the scenario panel reads cached
ODE integrations. The one exception is the hospital portal's clinical-ratio
arithmetic, which is multiplication over 25 rows — see `src/lib/readiness.ts`
for why that does not breach the rule.

**Every number says what it is.** Observed, modelled, or a planning estimate.
`<ProvenanceChip>` takes the tier as a required prop, and refuses to render a
planning estimate without its basis — the same line `Quantity` holds in Python.

**Where no public data exists, the app says so.** `<NoDataPanel>` explains what
is missing and names the feed that would enable it, rather than filling the
space with a plausible number.

## Languages

Sinhala, English and Tamil, switchable from the banner at the top of every page.
English is the default.

The choice is stored in a cookie (`denguesentinel.locale`) and can also be set
per-request with `?lang=si|ta|en`, which the middleware applies and pins — so a
page in any language is a link someone can send.

```
src/lib/i18n/config.ts        The three locales, the cookie name, the default
src/lib/i18n/dictionaries.ts  Every string, keyed; English is the source of truth
src/lib/i18n/server.ts        getLocale() / getT() for server components
src/components/i18n/          LocaleProvider + useT() for client components
```

**A missing key falls back to English, never to a blank or a raw key.** That
direction is deliberate for a health platform: an untranslated English sentence
is recoverable, a missing warning sign is not.

**What is translated.** The site chrome (banner, navigation, footer) and the
whole public-facing district page — symptoms, prevention, emergency numbers, the
warning signs, and the engine's own recommendations. The staff portals stay in
English: their vocabulary *is* the modelling vocabulary (quantile intervals,
shadow prices, pinball loss), and a half-translated clinical planning table is
worse for the people who use it than a consistently English one.

**Engine-authored text** (the recommendations) has no identifier — the engine
emits English sentences. `recommendationKey()` slugs the sentence into a
translation key, so a reworded recommendation upstream misses its key and renders
in English rather than showing a translation of a sentence that no longer exists.

**Fonts.** Public Sans and Source Serif carry no Sinhala or Tamil glyphs, so
Noto Sans Sinhala and Noto Sans Tamil are loaded alongside them. Each declares
its own `unicode-range`, so an English page downloads neither.

**If per-language URLs become a requirement** (`/si/national` rather than
`/national?lang=si`), that means restructuring the routes under a `[locale]`
segment. The cookie plus `?lang=` was chosen to avoid that churn while still
giving every page a shareable link in each language.

## Access

Public pages need no account. Staff portals check a permission at the page, not
in middleware: a middleware redirect can only decide "signed in or not", while
each portal has to decide "holds this permission, for these districts". Scope is
applied at the data read (`filterToScope`), because a filter that lives in a
component is one refactor away from being dropped.

Copy `.env.example` to `.env.local` to configure sign-in, or set
`DENGUE_DEV_ROLE` to review the staff portals without a Supabase project.

## Layout

```
src/
  app/            One directory per route; server components fetch, client components interact
  components/
    ui/           Design system: Container, Button, Card, Badge, StatTile, ProvenanceChip, ...
    layout/       GovBanner, Header, LanguageSwitcher, PageHeader, Footer
    charts/       Choropleth, FacilityMap, HistoryCompare (inline SVG, d3-geo), Recharts wrappers
    i18n/         LocaleProvider + useT() for client components
    hospital/ moh/ admin/ public/    Portal-specific panels
  lib/
    data.ts       Server-side artifact access
    selectors.ts  Filters, joins and sorts over artifact rows — never new epidemiology
    risk.ts provenance.ts rbac.ts readiness.ts    Engine concepts, mirrored
    i18n/         Locales, dictionaries, server-side getT()
  generated/      constants.json, written by make export-web
```
