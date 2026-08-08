# dengue-allocator

**A national dengue decision-support platform for Sri Lanka** — forecast → causal
effect → allocation, behind four role-based portals.

AI Challenge Sri Lanka 2026 — Phase 1 submission.

---

## The one thing to read first

This platform puts three very different kinds of number on the same screen:

| | Example | What it is |
|---|---|---|
| **Observed** | 1,231 health facilities; 3.93 beds per 1,000 | Measured and published by a named authority |
| **Modelled** | 107 cases forecast for Colombo in 2 weeks | Model output from observed inputs, with an interval |
| **Planning estimate** | 59 admissions, 14 platelet units | Published clinical ratios applied to a forecast |

Rendered identically, the third borrows the credibility of the first — and that is
how a decision-support tool causes a bad decision. So **every quantity carries a
provenance tier**, enforced in code rather than by discipline: a `Quantity` tagged
`ASSUMED` *cannot be constructed* without stating its basis.

```python
>>> Quantity(100.0, ProvenanceTier.ASSUMED, "beds")
ValueError: A Quantity tagged ASSUMED must state its basis. An unexplained
planning estimate is indistinguishable from a fabricated number.
```

**Where no public data exists, the platform says so instead of showing a number.**
Live bed occupancy, ICU census, platelet stock, staffing rosters and ambulance
positions are not published for Sri Lanka — those panels render an explanation and
a note about what feed would enable them.

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
| **2. Effect** | How many cases does sending *k* teams to district *d* actually avert? | Mechanistic SEI-SIR compartmental model, intervened on directly | ✅ **Implemented** |
| **3. Allocate** | Given a fixed weekly budget, where do teams go? | Integer linear program (PuLP/CBC) | ✅ **Implemented** |

### Why three stages instead of one model

The tempting shortcut is to rank districts by forecast cases and send teams to the
top of the list. That is wrong for a reason worth stating plainly:

> **A forecasting model cannot estimate an intervention effect from observational
> data.** Historically, teams were sent *to* outbreaks. Regressing cases on
> team-weeks therefore recovers a *positive* coefficient — the model concludes
> that vector control causes dengue.

Stage 2 breaks that confounding by modelling transmission mechanistically and
intervening on the vector parameters directly — a genuine *do*-operation on a
simulated system, not an association read off history. Stage 3 exists because the
returns to control effort **saturate**: the tenth team in Colombo averts far fewer
cases than the first team in Gampaha, so the optimal allocation is not a sorted
list.

**All three stages are implemented and wired end to end**, with a dashboard over
the top. The one remaining stub is the STGNN (`models/stgnn.py`), a planned Stage 1
upgrade.

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
   STAGE 2          ┌─────────────────────────────────────────────┐
   causal           │  SEI-SIR fitted per district, then the      │
                    │  vector parameters INTERVENED on:           │
                    │  adulticide ↑μ_v · source reduction ↓K      │
                    │  → concave cases-averted curve per district │
                    └──────────────────────┬──────────────────────┘
                                           ▼
   STAGE 3          ┌─────────────────────────────────────────────┐
   allocate         │  ILP over x[d,k] ∈ {0,1}: maximise averted  │
                    │  cases s.t. budget, high-risk floor,        │
                    │  per-district cap, weekly continuity        │
                    └──────────────────────┬──────────────────────┘
                                           ▼
                    ┌─────────────────────────────────────────────┐
   dashboard        │  Streamlit — reads cached artifacts only,   │
                    │  never computes at request time             │
                    └─────────────────────────────────────────────┘
```

### Why the stages compose the way they do

Stage 2 supplies the **shape** of each district's response curve — its concavity
and how districts differ from one another. Stage 1 supplies the **level** — how
many cases are actually at stake in the next few weeks. `build_effect_table`
joins them by anchoring each district's mechanistic baseline to its Stage 1
forecast. That split matters because the mechanistic model's absolute scale is
not trustworthy (see the ρ identifiability note below), while its relative
structure is.

Stage 3 then consumes only the effect curves. It never sees the raw forecast,
which keeps the optimisation honest: everything it optimises against has already
been through the causal step.

---

## Quickstart

Requires Python ≥ 3.11.

```bash
git clone https://github.com/OWNER/dengue-allocator.git
cd dengue-allocator

make setup       # venv + pinned deps (uses uv when available, else venv+pip)
make baseline    # Stage 1 backtest — prints the model comparison table
make pipeline    # all 3 stages — writes every dashboard artifact
make app         # launch the dashboard
```

**Both `make baseline` and `make pipeline` run fully offline** against a synthetic
panel: no network, no API keys, no manual steps.

To run against real data:

```bash
make data            # run every ingest step (needs network)
make panel           # assemble data/processed/panel.parquet
make baseline-real   # backtest against the real panel
make pipeline-real   # all 3 stages against the real panel
```

| Target | What it does |
|---|---|
| `make setup` | Create `.venv`, install pinned dependencies |
| `make data` | Run all four ingest modules |
| `make panel` | Build the district-week panel + feature matrix |
| `make baseline` | **Offline** backtest of all Stage 1 models, prints comparison table |
| `make pipeline` | **Offline** run of all 3 stages, writes dashboard artifacts |
| `make all` | `baseline` + `pipeline` |
| `make tune` | GA hyperparameter + ensemble-weight search, offline (~20 min) |
| `make test` | Run the test suite (no network, no slow GA end-to-end test) |
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

# make tune
python -m dengue.tuning.runner --synthetic --n-weeks 520

# make test / lint
python -m pytest -m "not network and not slow"
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
| **OCHA / HDX** (`cod-ab-lka`) | District boundary polygons for the maps | v03, 2022 | **CC-BY-IGO** | [data.humdata.org](https://data.humdata.org/dataset/cod-ab-lka) |
| **OpenStreetMap** (Overpass) | 1,231 hospital & clinic locations | live | **ODbL-1.0** | [openstreetmap.org](https://www.openstreetmap.org/copyright) |
| **World Bank** (`SH.MED.BEDS.ZS`) | Hospital beds per 1,000 — national | 3.93 (2023) | **CC-BY-4.0** | [data.worldbank.org](https://data.worldbank.org/indicator/SH.MED.BEDS.ZS) |
| Dept. of Census & Statistics | District populations, land areas | 2023 projections | Government publication | [statistics.gov.lk](http://www.statistics.gov.lk/) |
| *Clinical planning ratios* | Hospitalisation %, ICU %, LOS, platelet demand | — | *literature — **not** Sri Lankan measurements* | `platform/hospital.py` |

### Source status, verified 2026-08

| Source | Status | Note |
|---|---|---|
| colmozzie | ✅ **Working** | Package archived on CRAN; fetched from `src/contrib/Archive/`. Parsed with a purpose-built RData reader (no `pyreadr`/`rpy2` dependency). Downloads and parses in < 5 s. |
| Open-Meteo | ✅ **Working** | All four daily variables confirmed served. No API key. |
| ReliefWeb | ⚠️ **Gated** | **v1 is decommissioned (HTTP 410).** v2 is current but returns **HTTP 403** without a *pre-approved* `appname` (required since 2025-11-01). Module targets v2 and raises with remediation steps. Request an appname at [reliefweb.int/contact](https://reliefweb.int/contact), then set `RELIEFWEB_APPNAME` in `.env`. |
| WER PDFs | ⚠️ **Parser ready, no automated discovery** | epid.gov.lk is reachable but its WER index is paginated HTML with no stable machine-readable feed. The parser is implemented and unit-tested against a synthetic fixture; supply PDFs explicitly via `wer_pdf.load({iso_week: path})`. |
| HDX boundaries | ✅ **Working** | 25/25 districts matched to the registry; simplified 133 MB → 175 KB and committed. |
| OSM facilities | ✅ **Working** (locations only) | 1,231 facilities across all 25 districts. **Bed tagging is 1/1,231**, so capacity is estimated, not measured. |
| World Bank beds | ✅ **Working** | 3.93 beds per 1,000 (2023) → ~87,000 national beds. |
| Hospital occupancy / ICU / platelet stock / staffing | ❌ **No public source exists** | Not published for Sri Lanka. These panels show an explanation, never a placeholder number. |

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

### GA hyperparameter tuning

`make tune` runs a hand-rolled genetic algorithm (`src/dengue/tuning/`) over LightGBM's
hyperparameters — tournament selection, uniform crossover, kind-specific mutation
(Gaussian / log-space Gaussian / integer step), linear mutation-rate annealing, elitism,
early stopping on a fitness plateau, and a hard wall-clock cap. Fitness is evaluated only
against a short tail slice of the `val` fold, through the same unmodified
`rolling_origin` / `score_predictions` harness used everywhere else — `test` is touched
exactly once, by a confirmation run *after* the search has already picked a winner, so
the numbers below are not gamed against the fold they're reported on. A second, much
cheaper genome searches ensemble-blend weights across the three base models.

> ⚠️ Also run against the **synthetic** panel — see the caveat above.

<!-- TUNING_TABLE_START -->
On this run (population 8, generations 5 — converged via early stopping after 2
generations, ~3.5 min — plus a confirmation backtest on the full 25-district panel,
~17 min total): reproduce with `make tune` then `make baseline`.

**Fold: `test`**, default vs. GA-tuned LightGBM:

| model | h | `pinball_mean` ↓ | `coverage_80` →0.80 | `interval_width` | `high_risk_recall` ↑ |
|:---|--:|--:|--:|--:|--:|
| lgbm_quantile (default) | 2 | **2.014** | 0.668 | **15.70** | 0.393 |
| lgbm_quantile_tuned     | 2 | 2.043 | **0.692** | 15.83 | **0.417** |
| lgbm_quantile (default) | 3 | **2.355** | 0.692 | **16.37** | **0.314** |
| lgbm_quantile_tuned     | 3 | 2.376 | **0.720** | 16.80 | 0.304 |
| lgbm_quantile (default) | 4 | 2.035 | 0.684 | **16.30** | **0.412** |
| lgbm_quantile_tuned     | 4 | **2.014** | 0.686 | 16.67 | 0.392 |

**What this shows:** the tuned genome does **not** clearly win on `pinball_mean` — it's
within noise of the default at h=2/h=3 and ties it at h=4. What it *does* do is move
`coverage_80` consistently toward the 0.80 nominal target (0.668→0.692, 0.692→0.720,
0.684→0.686), closing part of the under-coverage gap that is LightGBM's documented
weakness in this project. That is the composite fitness (`pinball_mean × (1 + 2.0 ×
miscalibration gap)`) doing exactly what it was built to do: trade a small, mostly
noise-level amount of pinball loss for materially better calibration, rather than
gaming the headline metric by tightening intervals further. A larger population/
generation budget than this machine's ~17-minute run allows would likely separate the
two more; SARIMA still edges out both LightGBM variants at h=3/h=4 in the full
comparison table above, which the tuning run doesn't change.

Ensemble-weight search (30 generations, converged early, seconds): **w_naive=0.02,
w_sarima=0.45, w_lgbm=0.54** — near-zero weight on the weakest model, roughly even
split between the two competitive ones. Weights are written to
`data/processed/tuned_hyperparams.json` alongside the LightGBM params; blending them
into the comparison table is a natural next step, not yet wired into `make baseline`.
<!-- TUNING_TABLE_END -->

### Stage 2 — fitted SEI-SIR

25/25 districts converged. Median R₀ **2.92** (range 0.95–5.08), which sits in the
plausible band for endemic dengue; R₀ < 1 districts are the low-burden northern ones
where transmission is import-driven rather than self-sustaining.

The effect curves are **monotone and concave** in every district — tested, not
assumed (`tests/test_causal.py::test_returns_diminish`). That property is what makes
the Stage 3 piecewise-linear representation exact rather than an approximation.

> **ρ is fixed, not fitted.** R₀ and the reporting fraction trade off almost exactly:
> halving both produces nearly the same notified-case curve, so fitting both yields a
> ridge rather than a peak. ρ is pinned at 0.10 from the serological literature and
> three parameters are fitted per district. **The absolute scale of averted cases
> inherits that assumption.** The district *ranking* — which is all Stage 3 consumes —
> is far more robust to it, and `sensitivity_to_reporting_fraction()` measures this
> rather than asserting it.

### Stage 3 — allocation

Budget sweep, median risk posture, 25 districts, cap 12 teams/district, high-risk
floor of 2:

| Budget (team-weeks) | Rank-and-fill | **ILP** | ILP uplift | Shadow price |
|--:|--:|--:|--:|--:|
| 20 | 93.0 | **93.3** | +0.3% | 4.93 |
| 40 | 159.6 | **171.6** | +7.5% | 3.28 |
| 60 | 220.6 | **230.3** | +4.4% | 2.65 |
| 100 | 306.5 | **320.9** | +4.7% | 1.97 |
| 160 | 398.2 | **414.8** | +4.2% | 1.21 |

**Median ILP uplift over rank-and-fill: +4.2%**, at zero extra operational cost —
the same teams, the same constraints, just placed better.

The **shadow price** is the marginal cases averted per additional team-week, from the
LP relaxation's dual on the budget constraint. It falls monotonically from 4.93 to
1.21 across the sweep, which is the number that answers "should we fund more teams?"
— and it says the 20th team is worth about four times the 160th.

> **A note on how this comparison is constructed.** An earlier version of the greedy
> baseline ignored the high-risk floor, and consequently "beat" the ILP by 10% at tight
> budgets — not because rank-and-fill is better, but because it was solving an easier,
> operationally infeasible problem. Both strategies now satisfy identical constraints,
> so the margin above comes from allocation logic alone. There is a regression test
> pinning this (`test_greedy_honours_the_high_risk_floor`).

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
  causal/sei_sir.py      Stage 2 — SEI-SIR, fitting, intervention effects
  optim/allocate.py      Stage 3 — allocation ILP, budget sweep, greedy baseline
  tuning/
    genetic.py           model-agnostic GA engine (selection, crossover, mutation)
    search_spaces.py      LGBM + ensemble-weight genomes and decoders
    fitness.py            rolling_origin-backed fitness, pinball+coverage composite
    runner.py             `make tune` CLI — LGBM search, confirmation, ensemble search
  eval/
    backtest.py          rolling-origin harness + `make baseline` CLI
    metrics.py           pinball, coverage, MAE/MAPE, lead time
  pipeline.py            all 3 stages end to end + `make pipeline` CLI
  utils/                 io, logging, synthetic panel
app/
  streamlit_app.py       dashboard — reads cached artifacts, never computes
  theme.py               validated palette + Altair theme
tests/                   schema · leakage · names · folds · causal · optim
```

## The platform — four portals

`make app` serves role-based portals over the same engine. **Different users see
different information**, because a citizen does not need hospital occupancy and a
regional officer does not need nationwide user management.

| Role | Sees |
|---|---|
| **Public** | Risk map, district forecast, trends, prevention advice, alerts, education |
| **Hospital staff** | + projected admissions, ICU, bed occupancy, supply demand, staffing, facility map |
| **MOH / Regional officer** | + hotspots, team deployment, intervention schedule, scenarios, budget optimiser |
| **National administrator** | + nationwide view, data provenance, model config, roles, system health |

Three design decisions worth stating.

**Permissions are additive by rank; scope is orthogonal to them.** A hospital
administrator and an MOH officer may hold overlapping permissions while seeing
entirely different *rows* — one scoped to a facility, one to a district. Collapsing
"what you may do" and "what you may see" into a single level is the usual way health
dashboards leak data across regions, so `Principal` carries both. A role that should
be district-scoped **cannot be constructed without a district**:

```python
>>> Principal(Role.MOH_OFFICER, "unscoped")
ValueError: Role 'moh_officer' must be scoped to at least one district.
An empty district list means nationwide access, which this role must not have.
```

**The public portal is a deny-by-default subset, not a redaction.** It is built from
the permissions the public role actually holds, rather than by computing the full
picture and hiding parts. A bug then shows *missing* information instead of exposing
hospital occupancy.

**Nothing computes at request time.** Every figure is a cached Parquet artifact. The
budget slider looks like it re-solves the ILP; it does not — `make pipeline` solves
60 scenarios ahead of time and the slider indexes a lookup. Same for the scenario
simulator, which is an ODE integration.

### Maps

District choropleths use **OCHA/HDX Common Operational Dataset** boundaries
(CC-BY-IGO) — the boundaries UN humanitarian responders actually use. The raw admin-2
layer is 22 MB inside a 133 MB archive; `ingest/boundaries.py` simplifies it
(Douglas-Peucker + 4 dp coordinates) to **175 KB**, small enough to commit so the app
renders offline.

Facility locations are **real**: 1,231 hospitals and clinics from OpenStreetMap
(ODbL). Bed counts are *not* — only 1 of 1,231 facilities carries a `beds` tag, so
per-facility capacity is not shown and district capacity is estimated from World Bank
national bed density instead.

Charts use a validated categorical palette in fixed slot order (the ordering is the
colourblind-safety mechanism, not decoration), a single-hue blue ramp for magnitude,
and reserved status colours never reused as a series. Rainfall-versus-cases is drawn
as **stacked panels, not a dual axis** — two y-scales let the author manufacture any
apparent correlation by choosing the scales, which is exactly the claim that figure
is making.

### Scenario simulator

"What if heavy rain next week?" re-integrates the **fitted SEI-SIR model** with a
perturbed input. It is not a lookup table, and that matters: rain raises carrying
capacity, which raises the vector population weeks later, which raises transmission
after the incubation period. A tool built on a regression coefficient would show an
instant bump. This one shows the lag, because the lag is in the model — and it shows
that heavy rain *plus* a heatwave is worse than the sum of the two, because more
mosquitoes and a shorter incubation period multiply rather than add.

### Budget optimiser

Splits an envelope across vector control, awareness, hospital preparedness and
emergency reserve, using concave return curves and greedy marginal allocation
(provably optimal for concave objectives — the water-filling argument).

| Envelope | Vector | Awareness | Hospital | Reserve | Marginal return |
|--:|--:|--:|--:|--:|--:|
| LKR 5M | 60% | 15% | 15% | 10% | — |
| LKR 20M | 51% | 22% | 17% | 10% | +47 per extra M |
| LKR 80M | 42% | 20% | 28% | 10% | +15 per extra M |

The split **shifts** as the envelope grows: vector control saturates, so money moves
to hospital preparedness. That shift is the useful output.

> **Only the vector-control curve is anchored to a model** (Stage 2's effect table).
> The other three use assumed elasticities, not measured Sri Lankan
> cost-effectiveness. Read the recommendation as a structured argument about
> trade-offs, not as an evidence-based funding instruction — and the UI says exactly
> that on the page.

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
`artifacts/*.parquet` by `make pipeline`. A dashboard that retrains on page load is
unusable during an outbreak, when the cost of a slow page is a delayed decision.

**Stage 2 uses one binary per (district, intensity level), not one integer per
district.** A single integer variable would force a *linear* effect assumption and
throw away exactly the diminishing returns that make the problem interesting. The
binary-per-level encoding represents the concave curve exactly while keeping the
program linear — and because the per-district constraint makes each district's
variables a special-ordered set, CBC solves these in milliseconds.

**Stage 2 integrates daily, not weekly.** The EIP and the mosquito lifespan are both
1–2 weeks, so a weekly step would smear the two processes the model exists to
separate. Daily steps aggregated to ISO weeks cost ~8s per district fit, which is
affordable at 25 districts.

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
