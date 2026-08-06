# dengue-allocator

**Forecast → causal effect → allocation pipeline for dengue vector control in Sri Lanka.**

AI Challenge Sri Lanka 2026 — Phase 1 submission.

---

## The problem

Sri Lanka is in an active dengue outbreak. Roughly **87,500 cases** have been notified
in 2026 year-to-date, and the National Dengue Control Unit (NDCU) has designated
**137 high-risk MOH areas**. The Ministry of Health has a fixed number of
vector-control teams each week and must decide where to send them.

That decision is currently made largely reactively — teams follow reported case
surges. By the time a surge appears in the weekly notification data, transmission
has already been running for two to three weeks: the delay from a mosquito
acquiring the virus through the extrinsic incubation period, human infection, the
intrinsic incubation period, care-seeking, and notification. **Reacting to
notified cases means arriving late.**

Getting ahead of that requires answering three separate questions, and they are
genuinely different questions:

| Stage | Question | Method | Status |
|---|---|---|---|
| **1. Forecast** | Where will cases be in 2–4 weeks, and how confident are we? | Probabilistic district-level quantile forecasts | ✅ **Implemented** |
| **2. Effect** | How many cases does sending *k* teams to district *d* actually avert? | Mechanistic SEI-SIR compartmental model | 🚧 Scaffolded |
| **3. Allocate** | Given a fixed weekly budget, where do teams go? | Integer linear program | 🚧 Scaffolded |

### Why three stages instead of one model

The tempting shortcut is to rank districts by forecast cases and send teams to the
top of the list. That is wrong for a reason worth stating plainly:

> **A forecasting model cannot estimate an intervention effect from observational
> data.** Historically, teams were sent *to* outbreaks. Regressing cases on
> team-weeks therefore recovers a *positive* coefficient — the model concludes
> that vector control causes dengue.

Stage 2 exists to break that confounding by modelling transmission mechanistically
and intervening on vector parameters directly. Stage 3 exists because the returns
to control effort **saturate** — the tenth team in Colombo averts far fewer cases
than the first team in Gampaha — so the optimal allocation is not a sorted list.

**This session delivers Stage 1 end to end, plus the evaluation harness.** Stages 2
and 3 ship as typed signatures with full design notes and `NotImplementedError`.

---

## Architecture

```
                    ┌─────────────────────────────────────────────┐
   data sources     │  colmozzie · Open-Meteo · ReliefWeb · WER   │
                    └──────────────────────┬──────────────────────┘
                                           │  normalise → district_id, iso_week
                                           ▼
                    ┌─────────────────────────────────────────────┐
   frozen contract  │   data/processed/panel.parquet               │
                    │   one row per district-week (25 districts)   │
                    └──────────────────────┬──────────────────────┘
                                           ▼
                    ┌─────────────────────────────────────────────┐
   features         │  lags · rolling stats · climate · monsoon   │
                    │  phase · neighbour-weighted incidence       │
                    │  ── strictly causal: only data ≤ t ──       │
                    └──────────────────────┬──────────────────────┘
                                           ▼
   STAGE 1          ┌─────────────────────────────────────────────┐
   forecast         │  SeasonalNaive · SARIMA · LightGBM quantile │
                    │  → q0.1 / q0.5 / q0.9 at h = 2, 3, 4 weeks  │
                    └──────────────────────┬──────────────────────┘
                                           ▼
                    ┌─────────────────────────────────────────────┐
   evaluation       │  rolling-origin backtest, expanding window  │
                    │  pinball · coverage · MAE/MAPE · lead time  │
                    └──────────────────────┬──────────────────────┘
                                           ▼
   STAGE 2 🚧       ┌─────────────────────────────────────────────┐
   causal           │  SEI-SIR → cases averted per team-week      │
                    └──────────────────────┬──────────────────────┘
                                           ▼
   STAGE 3 🚧       ┌─────────────────────────────────────────────┐
   allocate         │  ILP: maximise averted cases s.t. budget,   │
                    │  high-risk floor, per-district cap          │
                    └─────────────────────────────────────────────┘
```

---

## Quickstart

Requires Python ≥ 3.11.

```bash
git clone https://github.com/OWNER/dengue-allocator.git
cd dengue-allocator

make setup       # venv + pinned deps (uses uv when available, else venv+pip)
make baseline    # trains all Stage 1 baselines, prints the comparison table
```

**`make baseline` runs fully offline** against a synthetic panel. That is the
acceptance criterion for the scaffold: no network, no API keys, no manual steps.

To run against real data:

```bash
make data            # run every ingest step (needs network)
make panel           # assemble data/processed/panel.parquet
make baseline-real   # backtest against the real panel
make app             # Streamlit dashboard (reads cached artifacts only)
```

| Target | What it does |
|---|---|
| `make setup` | Create `.venv`, install pinned dependencies |
| `make data` | Run all four ingest modules |
| `make panel` | Build the district-week panel + feature matrix |
| `make baseline` | **Offline** backtest of all Stage 1 models, prints comparison table |
| `make test` | Run the test suite (no network) |
| `make lint` | ruff check + format check |
| `make app` | Launch the Streamlit dashboard |

<details>
<summary><b>No <code>make</code> on your machine? (Windows without Git Bash / MSYS)</b></summary>

Every target is a thin wrapper around one command. The direct equivalents, from the
repo root with the venv active:

```bash
# make setup
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"

# make baseline   ← the offline acceptance criterion
python -m dengue.eval.backtest --synthetic --n-weeks 520 --stride 4

# make panel
python -m dengue.features.build_panel --features

# make test / lint
python -m pytest -m "not network"
python -m ruff check src tests app && python -m ruff format --check src tests app

# make app
python -m streamlit run app/streamlit_app.py
```

Note `clean` and `clean-data` use `find`/`rm`, so those two targets need a POSIX
shell (Git Bash, WSL, macOS, Linux).

</details>

---

## Data provenance

| Source | What we take | Coverage | Licence | URL |
|---|---|---|---|---|
| **colmozzie** (CRAN) | Weekly notified dengue cases + climate, Colombo district | 2008-W52 → 2014-W21, 279 weeks | **CC0-1.0** | [cran.r-project.org/package=colmozzie](https://cran.r-project.org/package=colmozzie) |
| **Open-Meteo Archive** | Daily precipitation, T-max/min, relative humidity per district centroid | 2010-01-01 → present | **CC-BY-4.0** | [archive-api.open-meteo.com](https://archive-api.open-meteo.com/v1/archive) |
| **ReliefWeb API v2** | NDCU / MoH situation reports; high-risk MOH area counts | 1996 → present | Per originating org | [api.reliefweb.int/v2](https://apidoc.reliefweb.int/) |
| **Epidemiology Unit WER** | District-level notifiable-disease tables (26 RDHS rows) | 2007 → present | Sri Lanka MoH publication | [epid.gov.lk](https://www.epid.gov.lk/weekly-epidemiological-report/) |
| Dept. of Census & Statistics | District populations, land areas | 2023 projections | Government publication | [statistics.gov.lk](http://www.statistics.gov.lk/) |

### Source status, verified 2026-08

| Source | Status | Note |
|---|---|---|
| colmozzie | ✅ **Working** | Package archived on CRAN; fetched from `src/contrib/Archive/`. Parsed with a purpose-built RData reader (no `pyreadr`/`rpy2` dependency). Downloads and parses in < 5 s. |
| Open-Meteo | ✅ **Working** | All four daily variables confirmed served. No API key. |
| ReliefWeb | ⚠️ **Gated** | **v1 is decommissioned (HTTP 410).** v2 is current but returns **HTTP 403** without a *pre-approved* `appname` (required since 2025-11-01). Module targets v2 and raises with remediation steps. Request an appname at [reliefweb.int/contact](https://reliefweb.int/contact), then set `RELIEFWEB_APPNAME` in `.env`. |
| WER PDFs | ⚠️ **Parser ready, no automated discovery** | epid.gov.lk is reachable but its WER index is paginated HTML with no stable machine-readable feed. The parser is implemented and unit-tested against a synthetic fixture; supply PDFs explicitly via `wer_pdf.load({iso_week: path})`. |

> **No case numbers are ever fabricated.** When a source fails, the pipeline raises,
> logs loudly, and falls back to a **clearly labelled synthetic panel** — simulated
> data, never real data with gaps filled in.

---

## The panel schema (frozen contract)

`data/processed/panel.parquet`, one row per district-week. This is the interface
between every workstream and does not change without updating all of them.

| Column | Type | Notes |
|---|---|---|
| `district_id` | `string` | Canonical slug, e.g. `nuwara_eliya` |
| `iso_week` | `period[W-SUN]` | ISO-8601 week (Mon–Sun) |
| `cases` | `Int64` | Notified dengue cases |
| `population` | `Int64` | District mid-year estimate |
| `rain_mm` | `float64` | Weekly total precipitation |
| `tmax` / `tmin` | `float64` | Mean of daily max / min, °C |
| `rh` | `float64` | Mean relative humidity, % |
| `high_risk_flag` | `boolean` | Nullable — `NA` where NDCU designation is unknown |

### Administrative subtleties that the registry encodes

These are easy to get wrong and each one silently corrupts the panel:

- **25 districts, but 26 RDHS reporting divisions.** Kalmunai reports separately from
  Ampara. Every Epidemiology Unit table has 26 data rows. `rdhs_to_district()` folds
  Kalmunai back into Ampara.
- **Colombo Municipal Council reports separately *inside* Colombo district.** CMC must
  be *added into* Colombo, never treated as a 26th district — otherwise Colombo is
  systematically undercounted.
- **Spelling varies across sources.** `normalise_district()` handles the variants seen
  in practice (Killinochchi/Kilinochchi, Mullaittivu/Mullativu, Moneragala/Monaragala,
  Rathnapura/Ratnapura, …) and raises loudly on anything unrecognised rather than
  silently dropping the row.

### Synthetic panel

`utils/synthetic.py::make_synthetic_panel(n_districts, n_weeks, seed)` produces an
**identically-shaped** panel with:

- **Bimodal seasonality** — peaks aligned to the southwest (Yala, mid-May onward) and
  northeast (Maha, December–February) monsoons, weighted by each district's climate zone.
- **Spatial correlation** — a latent log-risk field drawn from a Gaussian process over
  district centroids (exponential kernel, 80 km length scale), carried through time as
  an AR(1).
- **Overdispersion** — negative-binomial counts, because real notification data is far
  more variable than Poisson.
- **Multi-year epidemic waves** — serotype replacement drives 3–4 year cycles.

---

## Leakage safety

The single most common way a published dengue-forecasting result turns out to be
wrong is evaluation leakage. Three guarantees, each enforced by a test:

1. **No random splits, ever.** `eval/backtest.py` uses strict rolling-origin with an
   **expanding** window. At origin *t* the model sees weeks ≤ *t* and nothing else.
2. **No feature reads ahead.** Every derived column is a `groupby(district).shift(k≥1)`
   with trailing windows over already-shifted values. No centred windows, no `bfill`,
   no whole-series statistics spanning the train/test boundary.
3. **No pre-computed matrix.** Models receive a *raw panel truncated at the origin* and
   build features inside `.fit()`, so there is no shared matrix to leak through.

The central test is **truncation invariance** (`tests/test_no_leakage.py`):

> Rebuilding features on a panel truncated at week *T* must reproduce, exactly, what
> the full-panel build produced for every row at or before *T*.

If any feature peeks ahead, the truncated rebuild differs and the test fails. This
holds for features added later too — which is why it is written as a property test
rather than as assertions on specific shift values.

### Default backtest folds

| Fold | Trains on | Evaluated origins |
|---|---|---|
| `val` | everything through **2023** | **2024** |
| `test` | everything through **2024** | **2025 + 2026 YTD** |

Model selection uses `val`. `test` is touched once, at the end.

---

## Results

Stage 1 model comparison, rolling-origin backtest.

> ⚠️ **The table below is from the SYNTHETIC panel** — simulated data for pipeline
> development. It demonstrates that the harness runs end to end; it is **not** a
> real-world performance claim. Real-data results land once the WER backfill is in.

<!-- RESULTS_TABLE_START -->
**Fold: `test`** (trains through 2024, evaluates 2025 + 2026 YTD) — 25 districts, 520 weeks,
stride 8. Reproduce with `make baseline`.

| model | h | `pinball_mean` ↓ | `mae` ↓ | `mape` ↓ | `coverage_80` →0.80 | `interval_width` | `high_risk_recall` ↑ |
|:---|--:|--:|--:|--:|--:|--:|--:|
| lgbm_quantile  | 2 | **1.836** | **5.787** | 76.08 | 0.652 | **15.70** | 0.333 |
| sarima         | 2 | 1.879 | 5.925 | **64.07** | 0.768 | 17.70 | 0.405 |
| seasonal_naive | 2 | 3.787 | 10.784 | 125.42 | **0.812** | 51.07 | **0.429** |
| lgbm_quantile  | 3 | 2.144 | 6.611 | 74.57 | 0.676 | **16.44** | 0.183 |
| sarima         | 3 | **2.060** | **6.307** | **61.43** | 0.768 | 18.11 | **0.283** |
| seasonal_naive | 3 | 3.740 | 10.292 | 135.21 | **0.776** | 44.09 | 0.267 |
| lgbm_quantile  | 4 | 1.911 | 6.074 | 85.72 | 0.672 | **15.99** | 0.438 |
| sarima         | 4 | **1.846** | **5.753** | **69.65** | **0.804** | 18.44 | **0.500** |
| seasonal_naive | 4 | 3.087 | 8.720 | 115.51 | 0.812 | 40.45 | 0.333 |

**What this shows (on synthetic data):**

- Both learned models roughly **halve** the seasonal-naive pinball loss — the harness
  discriminates between models, which is what it is for.
- **LightGBM's intervals are under-covering** (0.65–0.68 against a 0.80 target). This is
  the expected failure mode of independently-fitted quantile regressors and is a real
  finding, not a bug: the model is overconfident. Conformalising the quantiles against a
  held-out calibration set is the standard fix and is the first thing to do next.
- **SARIMA is better calibrated** (0.768–0.804) and wins on pinball at h=3 and h=4, which
  is a useful reminder that the boosted model is not automatically the right answer.
- Seasonal-naive achieves near-nominal coverage only by being **~3× wider**, which is why
  coverage is never read without `interval_width` beside it.
<!-- RESULTS_TABLE_END -->

**Metrics reported**

- `pinball_mean` — **headline metric.** Mean pinball loss across quantiles; approximates
  CRPS. Proper scoring rule, so it is minimised only by an honestly calibrated
  distribution. Lower is better.
- `coverage_80` — empirical coverage of the 80% prediction interval. Target **0.80**;
  further away in *either* direction is worse.
- `interval_width` — reported alongside coverage, because coverage alone is trivially
  gamed by an infinitely wide interval.
- `mae` / `mape` — point accuracy on the median, for comparability with the literature.
  Note MAPE is asymmetric and punishes over-prediction more than under-prediction —
  which for outbreak response is the wrong way round. Prefer pinball when they disagree.
- `high_risk_recall` / `mean_lead_time_weeks` — operational detection. Lead time is
  measured against high-risk **onsets**: how much warning did we get *before* a district
  became a problem. A perfectly accurate forecast delivered the same week has zero
  operational value.

---

## Repository layout

```
src/dengue/
  config.py              district registry (25/26/CMC), centroids, adjacency, schema
  ingest/
    colmozzie.py         CRAN CC0 dataset + purpose-built RData reader
    openmeteo.py         Archive API → ISO-week aggregation, cached
    reliefweb.py         API v2, high-risk MOH counts, district counts
    wer_pdf.py           pdfplumber tables + validate_against_national_total()
  features/build_panel.py  leakage-safe feature engineering
  models/
    baseline.py          SeasonalNaive, SarimaBaseline
    lgbm_quantile.py     pooled LightGBM quantile regression
    stgnn.py             🚧 stub — GraphSAGE + GRU, pinball loss
  causal/sei_sir.py      🚧 Stage 2 stub
  optim/allocate.py      🚧 Stage 3 stub
  eval/
    backtest.py          rolling-origin harness + `make baseline` CLI
    metrics.py           pinball, coverage, MAE/MAPE, lead time
  utils/                 io, logging, synthetic panel
app/streamlit_app.py     dashboard — reads cached artifacts, never runs a model
tests/                   schema · leakage · name normalisation · fold ordering
```

---

## Design decisions worth flagging

**Python 3.12, not 3.11.** 3.11 is not installed on the development machine; the
project targets `>=3.11` and was developed and tested on 3.12.5. No 3.12-only syntax
is used.

**`uv` falls back to `venv`+`pip`.** `uv` was unavailable, so the Makefile detects it
and degrades gracefully. Versions are pinned in `pyproject.toml` either way.

**`geopandas` is an optional extra.** It pulls GDAL and is a routine source of install
failure on Windows. Nothing in Stage 1 needs it — the district graph is built from a
hardcoded adjacency table in `config.py`, which is auditable and has no binary
dependency. `make setup-full` installs it.

**SARIMA uses Fourier terms, not a 52-period seasonal order.** A literal
`seasonal_order=(P,D,Q,52)` adds 52 lags of state per district and takes minutes per
fit, times 25 districts times every backtest origin. Four Fourier harmonic pairs as
exogenous regressors capture the two-peak monsoon structure with 8 parameters instead
of 52, and fit in milliseconds.

**LightGBM is pooled, not per-district.** Mullaitivu, Mannar and Kilinochchi see fewer
than a hundred cases in a typical week; separate boosted models would overfit badly.
Pooling learns the shared climate-transmission response from high-volume districts
while `district_id` and `log_pop_density` absorb level differences.

**The Streamlit app never calls a model.** Everything it renders is materialised to
`artifacts/*.parquet` by `make baseline`. A dashboard that retrains on page load is
unusable during an outbreak, when the cost of a slow page is a delayed decision.

---

## Testing

```bash
make test          # no network
make test-all      # includes network-marked tests
make lint
```

Coverage of the things that would otherwise fail silently:

- **Schema** — exact columns, dtypes, Parquet round-trip of the `Period` index, physical
  plausibility (`tmin ≤ tmax`, non-negative cases, RH in 0–100).
- **Leakage** — truncation invariance, lag alignment, target/feature separation.
- **Name normalisation** — every RDHS division resolves; Kalmunai → Ampara; CMC →
  Colombo; unknown names raise.
- **Fold ordering** — no overlap, no reversal, expanding-window monotonicity, and a spy
  model asserting the harness never shows a model data past the origin.
- **WER parser** — against a synthetic fixture, including the specific failure mode of
  reading the cumulative (B) column instead of the weekly (A) column.

---

## Licence

MIT. Data sources retain their own licences — see the provenance table.

## Acknowledgements

- `colmozzie` — Thiyanga Talagala (CC0)
- Open-Meteo — ERA5 reanalysis (CC-BY-4.0)
- Epidemiology Unit, Ministry of Health, Sri Lanka
