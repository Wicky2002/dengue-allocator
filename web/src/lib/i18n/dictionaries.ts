/**
 * Translations.
 *
 * English is the source of truth: every key is defined in `en`, and a missing
 * key in another language falls back to it rather than rendering a blank or a
 * raw key. That fallback is deliberate for a health platform — an untranslated
 * English sentence is recoverable, a missing warning sign is not.
 *
 * Coverage is the site chrome and the **public** pages, which are what a
 * citizen reads. The staff portals stay in English: their vocabulary is the
 * modelling vocabulary (quantile intervals, shadow prices, pinball loss), and a
 * half-translated clinical planning table is worse than a consistently English
 * one for the people who actually use it.
 */

import type { Locale } from './config';

export type Dictionary = Record<string, string>;

const en: Dictionary = {
  // --- Government banner --------------------------------------------------
  'banner.official': 'An official platform of the',
  'banner.government': 'Government of Sri Lanka',
  'banner.howYouKnow': "Here's how you know",
  'banner.operatedTitle': 'Operated by the Ministry of Health',
  'banner.operatedBody':
    'Forecasts, intervention effects and allocations published here are produced by the Ministry’s dengue decision-support pipeline, from named public sources listed in full at the foot of every page.',
  'banner.accessTitle': 'Public information is open; staff data is not',
  'banner.accessBody':
    'District risk needs no account. Hospital, district-operations and administration data require a staff account whose district scope is set by an administrator — never chosen by the person signing in.',
  'banner.language': 'Language',

  // --- Chrome -------------------------------------------------------------
  'site.name': 'DengueSentinel',
  'site.ministry': 'Ministry of Health · Sri Lanka',
  'nav.national': 'National overview',
  'nav.public': 'My district',
  'nav.hospital': 'Hospital readiness',
  'nav.moh': 'District operations',
  'nav.admin': 'Administration',
  'nav.method': 'Method',
  'nav.signIn': 'Staff sign in',
  'nav.signOut': 'Sign out',
  'nav.menuOpen': 'Open menu',
  'nav.menuClose': 'Close menu',
  'nav.skip': 'Skip to content',
  'nav.home': 'Home',
  'nav.privacy': 'Data protection notice',

  // --- Footer -------------------------------------------------------------
  'footer.blurb':
    'Forecast, causal effect and allocation for dengue vector control across the twenty-five districts of Sri Lanka.',
  'footer.platform': 'Platform',
  'footer.contact': 'Contact',
  'footer.sources': 'Data sources',
  'footer.rights':
    'Ministry of Health, Democratic Socialist Republic of Sri Lanka. Decision support only — not a clinical diagnosis tool.',
  'footer.ambulance': 'Suwa Sariya ambulance',
  'footer.ndcu': 'National Dengue Control Unit',
  'footer.epid': 'Epidemiology Unit',

  // --- Public page --------------------------------------------------------
  'public.eyebrow': 'Public information',
  'public.title': 'Dengue risk where you live',
  'public.lede':
    'No account needed. This page shows the forecast for one district, what it means, and what you can do about it this week.',
  'public.yourDistrict': 'Your district',
  'public.horizon': 'Forecast horizon',
  'public.weeks': 'weeks',
  'public.forecastCases': 'Forecast cases',
  'public.weeksAhead': 'weeks ahead',
  'public.likelyRange': 'Likely range',
  'public.cases': 'cases',
  'public.interval': '80% interval',
  'public.vsAverage': 'vs the recent 4-week average',
  'public.weeklyIncidence': 'Weekly incidence',
  'public.per100k': 'per 100,000',
  'public.rankNationally': 'Rank nationally',
  'public.of': 'of',
  'public.population': 'Population',
  'public.facilities': 'Health facilities',
  'public.hospitals': 'hospitals',
  'public.whatToDo': 'What you should do',
  'public.weeklyCasesIn': 'Weekly cases in',
  'public.casesCaption':
    'Notified cases, as published by the Epidemiology Unit. This is what has already happened — the forecast above is what comes next.',
  'public.rainfallTitle': 'Rainfall and cases here',
  'public.rainfallCaption':
    'Rain fills containers, larvae develop, adult mosquitoes emerge — and only then does transmission rise. Cases in this district follow rainfall by roughly 6–8 weeks.',
  'public.protectEyebrow': 'Protect yourself',
  'public.protectTitle': 'Symptoms, prevention, and when to go to hospital',
  'public.symptoms': 'Symptoms',
  'public.symptom1': 'High fever, severe headache, pain behind the eyes',
  'public.symptom2': 'Muscle and joint pain',
  'public.symptom3': 'Nausea, vomiting, skin rash',
  'public.warningTitle': 'Go to hospital immediately',
  'public.warningBody':
    'Severe abdominal pain, persistent vomiting, bleeding gums or nose, blood in vomit or stool, or extreme drowsiness. These are warning signs of severe dengue.',
  'public.prevention': 'Prevention',
  'public.prevent1': 'Empty and scrub water containers weekly',
  'public.prevent2': 'Cover water tanks and barrels',
  'public.prevent3': 'Clear roof gutters; discard tyres and containers',
  'public.prevent4': 'Use repellent — Aedes bites during the day',
  'public.prevent5': 'Fit window and door screens',
  'public.emergency': 'Emergency',
  'public.reportBreeding': 'Report a breeding site to your local Public Health Inspector.',
  'public.disclaimerTitle': 'This is decision support, not a diagnosis.',
  'public.disclaimerBody':
    'The forecast describes district-level risk, not your personal risk. If you have symptoms, see a clinician — do not wait for the numbers on this page to change.',

  // --- Myth vs fact -------------------------------------------------------
  'myth.title': 'Myth vs fact',
  'myth.label': 'Myth',
  'fact.label': 'Fact',
  'myth.1': 'Dengue mosquitoes bite at night.',
  'fact.1':
    'Aedes aegypti bites mainly in daylight, peaking early morning and late afternoon. Bed nets alone will not protect you.',
  'myth.2': 'Dengue only breeds in dirty water.',
  'fact.2':
    'It prefers clean standing water — exactly what collects in your water tank, plant trays and buckets.',
  'myth.3': 'You can only get dengue once.',
  'fact.3':
    'There are four serotypes. A second infection with a different serotype carries a higher risk of severe disease.',

  // --- Alerts -------------------------------------------------------------
  'alerts.title': 'Get alerts for your district',
  'alerts.districts': 'Districts',
  'alerts.weekly': 'Weekly forecast summary',
  'alerts.outbreakOnly': 'Outbreak warnings only',
  'alerts.email': 'Email address',
  'alerts.save': 'Subscribe',
  'alerts.saved': 'Saved in this browser.',
  'alerts.subscribedTitle': 'Subscribed',
  'alerts.subscribed': 'You\u2019ll hear from us at the next weekly refresh.',
  'alerts.noticeTitle': 'What you\u2019ll receive',
  'alerts.noticeBody':
    'Real subscriptions, stored for real, sent by the same scheduled job that refreshes the data every week. No account needed \u2014 resubmit this form any time to change your preferences.',

  // --- Risk bands ---------------------------------------------------------
  'risk.low': 'Low',
  'risk.moderate': 'Moderate',
  'risk.high': 'High',
  'risk.severe': 'Very high',

  // --- Shared -------------------------------------------------------------
  'common.translationNote':
    'Staff portals and technical pages are available in English only.',
  // --- Engine recommendations -------------------------------------------
  // Keyed by a slug of the English text the engine emits, so a wording change
  // upstream falls back to English rather than silently showing a translation
  // of a sentence that no longer exists.
  'rec.use-repellent-and-cover-arms-and-legs-during-the-day.action':
    'Use repellent and cover arms and legs during the day',
  'rec.use-repellent-and-cover-arms-and-legs-during-the-day.rationale':
    'Aedes bites in daylight, peaking early morning and late afternoon — unlike the night-biting malaria vector, so bed nets alone are not enough.',
  'rec.fit-window-screens-and-use-mosquito-coils-indoors.action':
    'Fit window screens and use mosquito coils indoors',
  'rec.fit-window-screens-and-use-mosquito-coils-indoors.rationale':
    'Transmission in Sri Lanka is largely peri-domestic; most exposure happens in and around the home.',
  'rec.remove-standing-water-around-your-home-weekly.action':
    'Remove standing water around your home weekly',
  'rec.remove-standing-water-around-your-home-weekly.rationale':
    'Aedes aegypti breeds in clean water in containers — tyres, tanks, plant trays, gutters. Removing habitat is the single most effective household action.',
  'rec.seek-medical-care-for-fever-lasting-more-than-two-days.action':
    'Seek medical care for fever lasting more than two days',
  'rec.seek-medical-care-for-fever-lasting-more-than-two-days.rationale':
    'Early presentation is what prevents dengue haemorrhagic fever; severe disease is largely a complication of late fluid management.',
  // --- Homepage -----------------------------------------------------------
  'home.eyebrow': 'National dengue decision support',
  'home.title': 'Send vector-control teams before the surge, not after it.',
  'home.lede':
    'DengueSentinel forecasts district dengue risk two to four weeks ahead, estimates what an intervention would actually avert, and allocates a fixed number of teams to where they avert the most cases.',
  'home.reactingQuote':
    'By the time a surge appears in weekly notification data, transmission has been running for two to three weeks. Reacting to that data is reacting to a fortnight-old picture.',
  'home.viewNational': 'View the national picture',
  'home.checkDistrict': 'Check my district',
  'home.currentForecast': 'Current forecast',
  'home.weeksAhead': 'weeks ahead',
  'home.targetWeek': 'Target week',
  'home.forecastCasesNationwide': 'Forecast cases, nationwide',
  'home.districtsHighRisk': 'Districts at high risk or above',
  'home.highestRiskDistrict': 'Highest risk district',
  'home.per100kWeek': 'per 100,000/week',
  'home.modelledNote': 'Modelled figures from the',
  'home.modelledNote2':
    'model. Every quantity on this platform states whether it is observed, modelled, or a planning estimate.',
  'home.simulatedTitle': 'Simulated data',
  'home.simulatedBody':
    'This run used the synthetic panel — realistic dynamics, but not observations. Do not read any figure here as real epidemiology. Run',
  'home.simulatedBody2': 'for live figures.',
  'home.realTitle': 'Real data',
  'home.realBody': 'Epidemiology Unit WER reports and Open-Meteo, pipeline run',
  'home.realBody2': '. Full provenance is in the administration portal.',
  'home.snapshotEyebrow': 'National snapshot',
  'home.snapshotTitle': 'Where dengue is heading next',
  'home.snapshotDescription':
    "All {n} districts, {h} weeks ahead. Ranked by incidence per 100,000 rather than case counts, so a small district's outbreak is not hidden behind Colombo's population.",
  'home.fullOverview': 'Full overview',
  'home.districtsForecast': 'Districts forecast',
  'home.highRiskOrAbove': 'High risk or above',
  'home.aboveThreshold': 'Above 3.5 per 100,000/week',
  'home.forecastCases': 'Forecast cases',
  'home.nationwide': 'Nationwide',
  'home.casesLastWeek': 'Cases last week',
  'home.notifiedNationwide': 'Notified, nationwide',
  'home.districtsUnit': 'districts',
  'home.ofTwentyFive': 'of 25',
  'home.readEyebrow': 'How to read this platform',
  'home.readTitle': 'Three very different kinds of number, never rendered the same way',
  'home.readDescription':
    'A planning estimate shown in the same style as a measurement borrows its credibility — and that is how a decision-support tool causes a bad decision. Provenance is enforced in code here, not by discipline.',
  'home.tier': 'Tier',
  'home.example': 'Example:',
  'home.example1': '1,231 health facilities; 3.93 beds per 1,000 people.',
  'home.example2': 'cases forecast for',
  'home.example3': 'in',
  'home.example3b': 'weeks.',
  'home.example4':
    'Admissions and platelet units, from published clinical ratios applied to a forecast.',
  'home.noDataTitle': 'Where no public data exists, the platform says so.',
  'home.noDataBody':
    'Live bed occupancy, ICU census, platelet stock, staffing rosters and ambulance positions are not published for Sri Lanka. Those panels render an explanation and name the feed that would enable them, rather than a plausible-looking number.',
  'home.rolesEyebrow': 'Role-based access',
  'home.rolesTitle': 'Four portals over one engine',
  'home.rolesDescription':
    'Permissions are additive by rank; scope is separate from them. A hospital administrator and an MOH officer can hold overlapping permissions while seeing entirely different rows.',
  'home.role.public.title': 'Public',
  'home.role.public.access': 'No account needed',
  'home.role.public.description':
    'Risk where you live, what the forecast means, prevention advice and nearby clinics.',
  'home.role.hospital.title': 'Hospital staff',
  'home.role.hospital.access': 'Staff account',
  'home.role.hospital.description':
    'Admission and severe-case projections, bed pressure, and supply planning for the weeks ahead.',
  'home.role.moh.title': 'MOH / Regional officer',
  'home.role.moh.access': 'Staff account',
  'home.role.moh.description':
    'Team allocation, intervention planning, scenario comparison and budget split for your district.',
  'home.role.admin.title': 'National administrator',
  'home.role.admin.access': 'Ministry account',
  'home.role.admin.description':
    'Nationwide operations, model configuration, data provenance, user management and the audit log.',
  'home.open': 'Open',
  'home.engineEyebrow': 'The engine',
  'home.engineTitle': 'Forecast → causal effect → allocation',
  'home.engineLede':
    'A forecast alone cannot tell you where to send a team. Knowing which district will have the most cases is not the same as knowing where an intervention averts the most — that requires an effect estimate and a constrained allocation.',
  'home.stage1.title': 'Probabilistic forecast',
  'home.stage1.body':
    'District case forecasts with an 80% interval, from an ensemble backtested against every baseline on rolling-origin folds.',
  'home.stage2.title': 'Mechanistic effect',
  'home.stage2.body':
    'A per-district SEI-SIR model, fitted to that district’s own history, estimates the cases a given number of team-weeks would avert.',
  'home.stage3.title': 'Constrained allocation',
  'home.stage3.body':
    'An integer programme distributes a fixed team budget to maximise expected cases averted, with an equity floor for facility-poor districts.',
  'home.howBuilt': 'How the models are built and validated',
  'home.noDataYetTitle': 'No pipeline data yet',
  'home.noDataYetBody':
    'This app renders artifacts written by the Python pipeline. Build them, then export them for the browser:',
  'home.noDataYetNote': 'Both run fully offline against the synthetic panel.',
  // --- National overview ---------------------------------------------------
  'nat.crumb': 'National overview',
  'nat.eyebrow': 'National overview',
  'nat.title': 'Every district, ranked by forecast risk',
  'nat.description':
    'Identical for every role: all 25 districts, before anything role-scoped narrows the view. Week of {week}.',
  'nat.metaModel': 'Model',
  'nat.metaPanel': 'Panel',
  'nat.metaPipelineRun': 'Pipeline run',
  'nat.simulatedTitle': 'Simulated data',
  'nat.simulatedBody':
    'This run used the synthetic panel. Realistic dynamics, but not observations — do not read any figure below as real epidemiology.',
  'nat.veryHigh': 'very high',
  'nat.high': 'high',
  'nat.hindsightEyebrow': 'Hindsight',
  'nat.hindsightTitle': 'How the forecast actually did',
  'nat.hindsightDescription':
    'Scrub to any week of the panel. The left map is what was notified; the right is what the model called for that same week while standing {h} weeks earlier, with none of the data in between.',
  'nat.chartObservedForecast': 'National cases: observed and forecast',
  'nat.chartObservedForecastCaption':
    'Solid line: observed notifications. Dashed line with band: the forecast median and 80% interval, summed across districts.',
  'nat.chartRainfall': 'Rainfall and cases',
  'nat.chartRainfallCaption':
    'Cases follow rainfall by roughly 6–8 weeks: rain fills containers, larvae develop, adult mosquitoes emerge, and only then does transmission rise. That lag is what makes a two-week-ahead forecast possible at all.',
  'nat.backtestEyebrow': 'Backtest',
  'nat.backtestTitle': 'Why this model',
  'nat.backtestDescription':
    'Mean {metric} across rolling-origin folds at {h} weeks ahead — lower is better. Every baseline is refit at each fold origin, so no model sees data from after the week it is predicting.',
  'nat.modelComparison': 'Model comparison',
  'nat.noBacktestScores': 'No backtest scores in this export.',
  'nat.intervalMeaningTitle': 'What the interval means',
  'nat.intervalMeaningBody':
    'Each district forecast is a set of quantiles, not a point. The 80% interval says the model expects the true count to fall inside it four weeks out of five — it is the width of that interval, not the median, that should decide how much slack a plan carries.',
  'nat.widestInterval': 'Widest interval',
  'nat.backtestFolds': 'Backtest folds',
  'nat.panelWindow': 'Panel window',
  'nat.districtWeeks': 'District-weeks',
  'nat.detailEyebrow': 'Detail',
  'nat.detailTitle': 'All districts',
  'nat.detailDescription':
    'Forecast, interval, population and health-facility count for every district at this horizon.',
  'nat.reportEyebrow': 'Report',
  'nat.reportTitle': 'Take this away as a document',
  'nat.reportDescription':
    'A PDF snapshot of this overview: the same headline figures and ranked district table, with the same data-source caveat, for circulating outside the platform.',
  // --- Risk explorer / district table --------------------------------------
  'nat.riskMap': 'Risk map',
  'nat.everyDistrictRanked': 'Every district, ranked',
  'nat.weeksAheadClick': 'weeks ahead · click a district',
  'nat.per100kWeekUnit': 'per 100,000/week',
  'nat.openDistrict': 'Open district',
  'nat.col.district': 'District',
  'nat.col.risk': 'Risk',
  'nat.col.forecastCases': 'Forecast cases',
  'nat.col.interval80': '80% interval',
  'nat.col.per100k': 'Per 100k/wk',
  'nat.col.population': 'Population',
  'nat.col.facilities': 'Facilities',
  'nat.report.filePrefix': 'National overview —',
  'nat.report.desc': 'PDF · headline figures and all 25 districts ranked',
  'nat.report.pipelineRun': 'pipeline run',
  'nat.report.download': 'Download report',
  // --- History compare ------------------------------------------------------
  'hist.viewPastWeek': 'View a past week',
  'hist.description': 'The same week seen twice: what was notified, and what the model called',
  'hist.weeksEarlier': 'weeks earlier.',
  'hist.weekBeginning': 'Week beginning',
  'hist.previousWeek': 'Previous week',
  'hist.nextWeek': 'Next week',
  'hist.weekLabel': 'Week',
  'hist.backtestedTicks': 'weeks with a back-tested forecast',
  'hist.observed': 'Observed',
  'hist.predictedAhead': 'Predicted,',
  'hist.noNotifiedCases': 'No notified cases recorded for this week.',
  'hist.casesThatWeek': 'Cases that week',
  'hist.predictedCases': 'Predicted cases',
  'hist.highestRisk': 'Highest risk',
  'hist.under': 'under',
  'hist.per100kWkUnit': 'per 100k/wk',
  'hist.noPredictionForWeek':
    'No back-tested forecast for this week at this horizon. The predicted series covers a shorter span than the observed one.',
  'crumb.public': 'Dengue risk in my district',
  'prov.observed': 'Observed',
  'prov.modelled': 'Modelled',
  'prov.assumed': 'Planning estimate',
  'prov.user_input': 'Entered by you',

  // --- Method page ----------------------------------------------------------
  'method.crumb': 'How it works',
  'method.eyebrow': 'Method',
  'method.title': 'How this platform decides anything',
  'method.description':
    'Three stages, each answering a question the previous one cannot. Knowing which district will have the most cases is not the same as knowing where a team averts the most.',
  'method.metaPanel': 'Panel',
  'method.metaDistrictWeeks': 'District-weeks',
  'method.metaLastRun': 'Last run',
  'method.engineEyebrow': 'The engine',
  'method.engineTitle': 'Forecast → causal effect → allocation',
  'method.engineDescription':
    'Each stage writes an artifact. The dashboard reads those artifacts and never recomputes them, which is why moving a slider here is instant during an outbreak.',
  'method.stage1': 'Stage 1',
  'method.stage1Title': 'Probabilistic district forecasts',
  'method.stage1Body':
    'A quantile model produces a median and an 80% interval for each district, two to four weeks ahead. Every baseline — seasonal naive, SARIMA, gradient boosting — is refit at each rolling-origin fold, so no model ever sees data from after the week it is predicting. The comparison table on the national overview is that backtest, not a claim.',
  'method.stage1DetailTemplate': 'Best on {metric} at 2 weeks: {list}.',
  'method.stage2': 'Stage 2',
  'method.stage2Title': 'Mechanistic intervention effect',
  'method.stage2Body':
    'A compartmental SEI-SIR model is fitted per district against that district’s own history, then re-integrated with vector control applied. The difference between the two integrations is the cases averted for a given number of team-weeks — a causal quantity, not a correlation read off the forecast.',
  'method.stage2DetailTemplate':
    'Effects are computed over a {horizon}-week horizon and cached as a curve per district, which is what makes the marginal return of the next team-week available instantly.',
  'method.stage3': 'Stage 3',
  'method.stage3Title': 'Constrained allocation',
  'method.stage3Body':
    'An integer programme distributes a fixed weekly team budget to maximise total expected cases averted, subject to the effect curves from Stage 2 and an equity floor for facility-poor districts. The floor is what stops the optimiser from writing off small, under-served districts whose absolute case counts can never compete with Colombo’s.',
  'method.stage3Detail':
    'The whole budget sweep is solved offline and cached, so the budget slider indexes solutions rather than re-solving.',
  'method.whyForecastEyebrow': 'Why forecast at all',
  'method.whyForecastTitle': 'Reacting to notifications is reacting to a fortnight-old picture',
  'method.whyForecastBody1':
    'By the time a surge appears in weekly notification data, transmission has already been running for two to three weeks: a mosquito acquires the virus, the extrinsic incubation period passes, a person is infected, the intrinsic incubation period passes, they seek care, and the case is notified. Teams dispatched at that point are treating a wave that has already broken.',
  'method.whyForecastBody2':
    'Rainfall is what makes an earlier signal possible. Rain fills containers, larvae develop, adults emerge, and only then does transmission rise — a lag of roughly six to eight weeks that the forecast exploits.',
  'method.riskBandsEyebrow': 'Risk bands',
  'method.riskBandsTitle': 'Why incidence, not case counts',
  'method.riskBandsDescription':
    'Colombo has 2.48 million residents and Mullaitivu around 100,000. Ranking districts by raw counts would paint Colombo red every week of the year and leave a genuine Mullaitivu outbreak green.',
  'method.riskBandBelow': 'Below 1.5',
  'method.riskBandAndAboveTemplate': '{threshold} and above',
  'method.riskBandPerWeek': 'per 100,000 per week',
  'method.riskBandsCalloutPrefix': 'These are ',
  'method.riskBandsCalloutBold': 'operational planning thresholds, not a clinical standard',
  'method.riskBandsCalloutSuffix':
    '. No internationally agreed incidence cut-off defines a dengue outbreak — published thresholds are endemicity-specific and usually derived per country. They were recalibrated against the real district-week distribution, and they are exposed as constants so they can be recalibrated again.',
  'method.provenanceEyebrow': 'Provenance',
  'method.provenanceTitle': 'Every quantity states what it is',
  'method.provenanceDescription':
    'Enforced in code, not by discipline: a quantity tagged as a planning estimate cannot be constructed in the engine without stating its basis.',
  'method.provenanceCalloutBold': 'Where no public data exists, the platform says so.',
  'method.provenanceCalloutSuffix':
    ' Live bed occupancy, ICU census, platelet stock, staffing rosters and ambulance positions are not published for Sri Lanka. Those panels render an explanation and name the feed that would enable them, rather than a number that looks plausible.',
  'method.accessEyebrow': 'Access',
  'method.accessTitle': 'Permissions are additive; scope is separate',
  'method.accessDescription':
    'A hospital administrator and an MOH officer can hold overlapping permissions while seeing entirely different rows — one is scoped to a facility, the other to a district. Collapsing the two into a single level is the usual way a health dashboard leaks data across regions.',
  'method.permissionsCountTemplate': '{n} permissions',
  'method.accessCalloutPrefix': 'The public pages are a ',
  'method.accessCalloutBold': 'deny-by-default subset, not a redaction',
  'method.accessCalloutSuffix':
    '. They are built from permissions the public role actually holds, rather than by computing the full picture and hiding parts of it — so a bug here shows missing information rather than exposing hospital occupancy.',
  'method.decisionSupportTitle': 'Decision support, not a clinical tool',
  'method.decisionSupportBody':
    'Nothing on this platform diagnoses a patient or prescribes treatment. It describes district-level risk and resource implications to help allocate finite public health capacity — and every figure it shows is only as good as the assumption stated beside it.',

  // --- Data protection (PDPA) notice -----------------------------------------
  'privacy.eyebrow': 'Legal',
  'privacy.description':
    'What this platform collects, why, how long it is kept, and how to ask about your own data — under Sri Lanka’s Personal Data Protection Act No. 9 of 2022.',
  'privacy.notice':
    'This notice describes the platform as built. If anything below stops matching what the running system actually does, the system is wrong and this notice is not — update the code, not this page, to bring them back into agreement.',
  'privacy.controllerEyebrow': 'Controller',
  'privacy.controllerTitle': 'Who operates this platform',
  'privacy.controllerBody':
    'The Ministry of Health, Sri Lanka, is the controller for the personal data described below. Requests concerning your own data — access, correction, or a question about how it is used — should be directed to the Ministry through the contact channels in the footer of this site.',
  'privacy.collectedEyebrow': 'What is collected',
  'privacy.collectedTitle': 'The two kinds of data on this platform',
  'privacy.publicDataTitle': 'Public risk information',
  'privacy.publicDataBody':
    'District-level forecasts, case counts and risk bands. This is aggregate epidemiological data — no individual is identified or identifiable in it, and no personal data is collected from a visitor to view it. Choosing a district or a language, and any alert preference you set, is stored only in your own browser (see “Alert preferences” below) and never reaches this platform’s servers.',
  'privacy.staffDataTitle': 'Staff accounts',
  'privacy.staffDataBody':
    'For hospital, district-operations and administration accounts: an email address, a display name, an assigned role, and a district or facility scope. Accounts are created by an administrator, not by self-registration, and this is the minimum needed to authenticate a member of staff and restrict what they can see to their own facility or district.',
  'privacy.legalBasisEyebrow': 'Legal basis',
  'privacy.legalBasisTitle': 'Why this processing is lawful',
  'privacy.legalBasisBody':
    'Public risk information is published in the exercise of the Ministry’s public health function — no consent is sought or needed to view it, in the same way a weekly epidemiological bulletin needs none. Staff account data is processed under the same public function, on the basis that it is necessary to operate a restricted-access system for vector-control planning; it is not used for any purpose beyond operating this platform.',
  'privacy.auditEyebrow': 'Audit log',
  'privacy.auditTitle': 'What is recorded about a staff sign-in',
  'privacy.auditBody':
    'Signing in, signing out, and viewing a staff portal are recorded — timestamp, account email, role, district scope at the time, and which page was viewed. This exists to let an administrator answer “who looked at what, and when” if that is ever needed, and is visible only to national-administrator accounts. It does not record what any account did on a page beyond which page it opened, and it is never used for performance monitoring or any purpose beyond that accountability record.',
  'privacy.retentionEyebrow': 'Retention',
  'privacy.retentionTitle': 'How long data is kept',
  'privacy.retentionStaffTitle': 'Staff account records',
  'privacy.retentionStaffBody':
    'Kept for the lifetime of the account, and removed by an administrator when access is withdrawn.',
  'privacy.retentionAuditTitle': 'Audit log entries',
  'privacy.retentionAuditBodyPrefix':
    'Deleted automatically after 365 days, once an operator has enabled the scheduled purge (',
  'privacy.retentionAuditBodySuffix':
    '). Until that has been run on this deployment, entries are retained indefinitely — ask your administrator whether it has been enabled.',
  'privacy.retentionAggTitle': 'Aggregate epidemiological data',
  'privacy.retentionAggBody':
    'Retained as a historical record — it is never personal data, so PDPA retention limits on personal data do not apply to it.',
  'privacy.rightsEyebrow': 'Your rights',
  'privacy.rightsTitle': 'Access, correction, and questions',
  'privacy.rightsBody':
    'Under the PDPA, you may ask what personal data this platform holds about you, ask for it to be corrected if it is wrong, and ask questions about how it is used. For a staff account, the fastest route is your own administrator; for anything else, use the contact details in the footer of this site.',
  'privacy.notCoveredTitle': 'What this notice does not cover',
  'privacy.notCoveredBody':
    'This page states the platform’s own data handling. It does not cover data held by the Epidemiology Unit, hospitals, or other bodies whose published statistics this platform reads and displays — those bodies are separate controllers for their own records, and requests about them should go to them directly.',

  // --- Staff sign-in ----------------------------------------------------------
  'signin.introPrefix': 'Public risk information needs no account — ',
  'signin.introLink': 'check your district',
  'signin.introSuffix':
    ' without signing in. An account is for hospital, MOH and Ministry staff, and determines both what you can do and which districts you can see.',
  'signin.footerNote':
    'Accounts are created by a national administrator, not by self-registration. Access is scoped to your own facility or district — signing in does not widen what the platform will show you beyond that.',
  'signin.emailLabel': 'Email address',
  'signin.passwordLabel': 'Password',
  'signin.showPassword': 'Show password',
  'signin.hidePassword': 'Hide password',
  'signin.submitting': 'Signing in…',
  'signin.submit': 'Sign in',
  'signin.error.missingFields': 'Enter your email address and password.',
  'signin.error.rateLimited': 'Too many attempts. Wait a few minutes and try again.',
  'signin.error.invalidCredentials': 'Those credentials were not accepted. Check your email and password.',

  // --- Staff-portal access notice (shown to a signed-out or under-permissioned visitor) ---
  'notice.staffOnlyTemplate': '{portal} is staff-only',
  'notice.availableToTemplate':
    'This portal is available to {roles}. Public risk information for every district needs no account at all.',
  'notice.checkDistrict': 'Check a district instead',
  'notice.footerPrefix': 'Public data here is a ',
  'notice.footerBold': 'deny-by-default subset, not a redaction',
  'notice.footerSuffix':
    ' — these pages are built from the permissions a role actually holds, so a bug shows missing information rather than exposing hospital occupancy.',
  'notice.howAccessWorks': 'How access works',
  'notice.rolesMoh': 'MOH officers, regional health officers and national administrators',
  'notice.rolesHospital': 'hospital staff, MOH officers and national administrators',
  'notice.rolesAdmin': 'national administrators',
};

const si: Dictionary = {
  'banner.official': 'මෙය නිල වේදිකාවකි —',
  'banner.government': 'ශ්‍රී ලංකා රජය',
  'banner.howYouKnow': 'මෙය තහවුරු කරගන්නා ආකාරය',
  'banner.operatedTitle': 'සෞඛ්‍ය අමාත්‍යාංශය විසින් මෙහෙයවනු ලැබේ',
  'banner.operatedBody':
    'මෙහි පළ කරන පුරෝකථන, මැදිහත්වීම්වල බලපෑම් සහ සම්පත් වෙන් කිරීම් සෞඛ්‍ය අමාත්‍යාංශයේ ඩෙංගු තීරණ-සහාය ක්‍රියාවලිය මගින් නිපදවනු ලැබේ. සියලු මූලාශ්‍ර සෑම පිටුවකම පහළින් නම් සහිතව දක්වා ඇත.',
  'banner.accessTitle': 'මහජන තොරතුරු විවෘතයි; කාර්ය මණ්ඩල දත්ත නොවේ',
  'banner.accessBody':
    'දිස්ත්‍රික් අවදානම බැලීමට ගිණුමක් අවශ්‍ය නැත. රෝහල්, දිස්ත්‍රික් මෙහෙයුම් සහ පරිපාලන දත්ත සඳහා කාර්ය මණ්ඩල ගිණුමක් අවශ්‍ය වන අතර, එහි දිස්ත්‍රික් විෂය පථය පරිපාලකයෙකු විසින් තීරණය කරයි — පිවිසෙන පුද්ගලයා විසින් නොවේ.',
  'banner.language': 'භාෂාව',

  'site.ministry': 'සෞඛ්‍ය අමාත්‍යාංශය · ශ්‍රී ලංකාව',
  'nav.national': 'ජාතික දළ විශ්ලේෂණය',
  'nav.public': 'මගේ දිස්ත්‍රික්කය',
  'nav.hospital': 'රෝහල් සූදානම',
  'nav.moh': 'දිස්ත්‍රික් මෙහෙයුම්',
  'nav.admin': 'පරිපාලනය',
  'nav.method': 'ක්‍රමවේදය',
  'nav.signIn': 'කාර්ය මණ්ඩල පිවිසුම',
  'nav.signOut': 'ඉවත් වන්න',
  'nav.menuOpen': 'මෙනුව විවෘත කරන්න',
  'nav.menuClose': 'මෙනුව වසන්න',
  'nav.skip': 'අන්තර්ගතයට යන්න',
  'nav.home': 'මුල් පිටුව',
  'nav.privacy': 'දත්ත ආරක්ෂණ නිවේදනය',

  'footer.blurb':
    'ශ්‍රී ලංකාවේ දිස්ත්‍රික්ක විසිපහ පුරා ඩෙංගු මදුරු මර්දනය සඳහා පුරෝකථනය, හේතු-සම්බන්ධ බලපෑම සහ සම්පත් වෙන් කිරීම.',
  'footer.platform': 'වේදිකාව',
  'footer.contact': 'සම්බන්ධ වන්න',
  'footer.sources': 'දත්ත මූලාශ්‍ර',
  'footer.rights':
    'සෞඛ්‍ය අමාත්‍යාංශය, ශ්‍රී ලංකා ප්‍රජාතාන්ත්‍රික සමාජවාදී ජනරජය. තීරණ සහාය සඳහා පමණි — රෝග විනිශ්චය මෙවලමක් නොවේ.',
  'footer.ambulance': 'සුව සැරිය ගිලන් රථය',
  'footer.ndcu': 'ජාතික ඩෙංගු මර්දන ඒකකය',
  'footer.epid': 'වසංගත රෝග විද්‍යා අංශය',

  'public.eyebrow': 'මහජන තොරතුරු',
  'public.title': 'ඔබ ජීවත් වන ප්‍රදේශයේ ඩෙංගු අවදානම',
  'public.lede':
    'ගිණුමක් අවශ්‍ය නැත. මෙම පිටුව එක් දිස්ත්‍රික්කයක් සඳහා පුරෝකථනය, එහි අර්ථය සහ මේ සතියේ ඔබට කළ හැකි දේ පෙන්වයි.',
  'public.yourDistrict': 'ඔබේ දිස්ත්‍රික්කය',
  'public.horizon': 'පුරෝකථන කාලය',
  'public.weeks': 'සති',
  'public.forecastCases': 'පුරෝකථිත රෝගීන්',
  'public.weeksAhead': 'සති ඉදිරියට',
  'public.likelyRange': 'සම්භාව්‍ය පරාසය',
  'public.cases': 'රෝගීන්',
  'public.interval': '80% විශ්වාස පරාසය',
  'public.vsAverage': 'පසුගිය සති 4 සාමාන්‍යයට සාපේක්ෂව',
  'public.weeklyIncidence': 'සතිපතා රෝගී අනුපාතය',
  'public.per100k': '100,000කට',
  'public.rankNationally': 'ජාතික ශ්‍රේණිගත කිරීම',
  'public.of': 'න්',
  'public.population': 'ජනගහනය',
  'public.facilities': 'සෞඛ්‍ය ආයතන',
  'public.hospitals': 'රෝහල්',
  'public.whatToDo': 'ඔබ කළ යුතු දේ',
  'public.weeklyCasesIn': 'සතිපතා රෝගීන් —',
  'public.casesCaption':
    'වසංගත රෝග විද්‍යා අංශය විසින් පළ කරන ලද වාර්තා වූ රෝගීන්. මෙය දැනටමත් සිදු වූ දෙයයි — ඉහත පුරෝකථනය ඊළඟට සිදු වන දෙයයි.',
  'public.rainfallTitle': 'මෙම දිස්ත්‍රික්කයේ වර්ෂාව සහ රෝගීන්',
  'public.rainfallCaption':
    'වර්ෂාවෙන් භාජන පිරී, කීටයන් වර්ධනය වී, මදුරුවන් බිහි වේ — ඉන් පසුව පමණක් රෝග පැතිරීම වැඩි වේ. මෙම දිස්ත්‍රික්කයේ රෝගීන් වර්ෂාවෙන් සති 6–8කට පසුව වැඩි වේ.',
  'public.protectEyebrow': 'ඔබව ආරක්ෂා කරගන්න',
  'public.protectTitle': 'රෝග ලක්ෂණ, වැළැක්වීම සහ රෝහල් ගත විය යුතු අවස්ථා',
  'public.symptoms': 'රෝග ලක්ෂණ',
  'public.symptom1': 'අධික උණ, දරුණු හිසරදය, ඇස් පිටුපස වේදනාව',
  'public.symptom2': 'මාංශ පේශි සහ සන්ධි වේදනාව',
  'public.symptom3': 'ඔක්කාරය, වමනය, සමේ කුෂ්ඨ',
  'public.warningTitle': 'වහාම රෝහලට යන්න',
  'public.warningBody':
    'දරුණු උදර වේදනාව, නොනවතින වමනය, විදුරුමස් හෝ නාසයෙන් ලේ ගැලීම, වමනයේ හෝ මලපහේ ලේ, හෝ අධික නිදිමත. මේවා දරුණු ඩෙංගු රෝගයේ අනතුරු ඇඟවීමේ ලක්ෂණ වේ.',
  'public.prevention': 'වැළැක්වීම',
  'public.prevent1': 'ජල භාජන සතිපතා හිස් කර සෝදා පිරිසිදු කරන්න',
  'public.prevent2': 'ජල ටැංකි සහ බැරල් වසා තබන්න',
  'public.prevent3': 'වහලයේ ජල බේසම් පිරිසිදු කරන්න; පැරණි ටයර් සහ භාජන ඉවත් කරන්න',
  'public.prevent4': 'මදුරු විකර්ෂක භාවිත කරන්න — ඒඩීස් මදුරුවා දිවා කාලයේ දෂ්ට කරයි',
  'public.prevent5': 'ජනෙල් සහ දොරවල් සඳහා දැල් සවි කරන්න',
  'public.emergency': 'හදිසි අවස්ථා',
  'public.reportBreeding':
    'මදුරු බෝවන ස්ථානයක් ඔබේ ප්‍රදේශයේ මහජන සෞඛ්‍ය පරීක්ෂකවරයාට දැනුම් දෙන්න.',
  'public.disclaimerTitle': 'මෙය තීරණ සහාය සඳහා මිස රෝග විනිශ්චය සඳහා නොවේ.',
  'public.disclaimerBody':
    'මෙම පුරෝකථනය දිස්ත්‍රික් මට්ටමේ අවදානම විස්තර කරයි, ඔබේ පෞද්ගලික අවදානම නොවේ. රෝග ලක්ෂණ ඇත්නම් වෛද්‍යවරයෙකු හමුවන්න — මෙම පිටුවේ අංක වෙනස් වන තෙක් බලා නොසිටින්න.',

  'myth.title': 'මිථ්‍යාව සහ සත්‍යය',
  'myth.label': 'මිථ්‍යාව',
  'fact.label': 'සත්‍යය',
  'myth.1': 'ඩෙංගු මදුරුවන් රාත්‍රියේ දෂ්ට කරයි.',
  'fact.1':
    'ඒඩීස් ඊජිප්ටයි මදුරුවා ප්‍රධාන වශයෙන් දහවල් කාලයේ, උදෑසන සහ සවස් වරුවේ දෂ්ට කරයි. මදුරු දැල් පමණක් ඔබව ආරක්ෂා නොකරයි.',
  'myth.2': 'ඩෙංගු මදුරුවන් බෝවන්නේ අපිරිසිදු ජලයේ පමණි.',
  'fact.2':
    'ඔවුන් කැමති පිරිසිදු, නිශ්චල ජලයටයි — එනම් ඔබේ ජල ටැංකියේ, ගෙවතු බඳුන්වල සහ බාල්දිවල එකතු වන ජලයයි.',
  'myth.3': 'ඩෙංගු වැළඳෙන්නේ එක් වරක් පමණි.',
  'fact.3':
    'ඩෙංගු වෛරසයේ වර්ග හතරක් ඇත. වෙනස් වර්ගයකින් දෙවන වරට ආසාදනය වීමේදී දරුණු රෝගී තත්ත්වයක් ඇතිවීමේ අවදානම වැඩිය.',

  'alerts.title': 'ඔබේ දිස්ත්‍රික්කය සඳහා දැනුම්දීම් ලබා ගන්න',
  'alerts.districts': 'දිස්ත්‍රික්ක',
  'alerts.weekly': 'සතිපතා පුරෝකථන සාරාංශය',
  'alerts.outbreakOnly': 'රෝග පැතිරීමේ අනතුරු ඇඟවීම් පමණි',
  'alerts.email': 'විද්‍යුත් තැපැල් ලිපිනය',
  'alerts.save': 'දායක වන්න',
  'alerts.saved': 'මෙම බ්‍රව්සරයේ සුරකින ලදී.',
  'alerts.subscribedTitle': 'දායක විය',
  'alerts.subscribed': 'ඊළඟ සතිපතා යාවත්කාලීනයේදී ඔබට දැනුම් දෙනු ලැබේ.',
  'alerts.noticeTitle': 'ඔබට ලැබෙන දේ',
  'alerts.noticeBody':
    'සැබෑ දායකත්ව, සැබවින්ම ගබඩා කර, සෑම සතියකම දත්ත යාවත්කාලීන කරන එම නියමිත කාර්යය මගින්ම යවනු ලැබේ. ගිණුමක් අවශ්‍ය නැත — ඔබේ මනාපයන් වෙනස් කිරීමට ඕනෑම වේලාවක මෙම පෝරමය නැවත ඉදිරිපත් කරන්න.',

  'risk.low': 'අඩු',
  'risk.moderate': 'මධ්‍යම',
  'risk.high': 'ඉහළ',
  'risk.severe': 'ඉතා ඉහළ',

  'common.translationNote': 'කාර්ය මණ්ඩල පිටු සහ තාක්ෂණික පිටු ඉංග්‍රීසි භාෂාවෙන් පමණි.',
  'rec.use-repellent-and-cover-arms-and-legs-during-the-day.action':
    'දිවා කාලයේ මදුරු විකර්ෂක භාවිත කර අත් සහ පාද ආවරණය කරන්න',
  'rec.use-repellent-and-cover-arms-and-legs-during-the-day.rationale':
    'ඒඩීස් මදුරුවා දහවල් කාලයේ, විශේෂයෙන් උදෑසන සහ සවස් වරුවේ දෂ්ට කරයි — රාත්‍රියේ දෂ්ට කරන මැලේරියා මදුරුවා මෙන් නොව. එබැවින් මදුරු දැල් පමණක් ප්‍රමාණවත් නොවේ.',
  'rec.fit-window-screens-and-use-mosquito-coils-indoors.action':
    'ජනෙල් සඳහා දැල් සවි කර ගෘහය තුළ මදුරු දඟර භාවිත කරන්න',
  'rec.fit-window-screens-and-use-mosquito-coils-indoors.rationale':
    'ශ්‍රී ලංකාවේ ඩෙංගු පැතිරීම ප්‍රධාන වශයෙන් නිවෙස් අවට සිදු වේ; බොහෝ ආසාදන ඇති වන්නේ නිවසේ සහ ඒ අවට ය.',
  'rec.remove-standing-water-around-your-home-weekly.action':
    'නිවස වටා රැඳී ඇති ජලය සතිපතා ඉවත් කරන්න',
  'rec.remove-standing-water-around-your-home-weekly.rationale':
    'ඒඩීස් ඊජිප්ටයි මදුරුවා බෝවන්නේ භාජනවල ඇති පිරිසිදු ජලයේ ය — ටයර්, ටැංකි, ගෙවතු බඳුන්, ජල බේසම්. බෝවන ස්ථාන ඉවත් කිරීම ගෘහස්ථ මට්ටමින් ගත හැකි ඵලදායීම ක්‍රියාමාර්ගයයි.',
  'rec.seek-medical-care-for-fever-lasting-more-than-two-days.action':
    'දින දෙකකට වඩා පවතින උණක් සඳහා වෛද්‍ය ප්‍රතිකාර ලබා ගන්න',
  'rec.seek-medical-care-for-fever-lasting-more-than-two-days.rationale':
    'ඉක්මනින් වෛද්‍ය ප්‍රතිකාර ලබා ගැනීම ඩෙංගු රක්තපාත උණ වැළැක්වීමට උපකාරී වේ; දරුණු තත්ත්වයන් බොහෝ විට ඇති වන්නේ ප්‍රමාද වූ තරල කළමනාකරණය නිසා ය.',
  'home.eyebrow': 'ජාතික ඩෙංගු තීරණ සහාය',
  'home.title': 'රෝග පැතිරීමට පෙර මදුරු මර්දන කණ්ඩායම් යවන්න, පසුව නොව.',
  'home.lede':
    'ඩෙංගුසෙන්ටිනල් සති දෙකේ සිට හතරක් තුළ දිස්ත්‍රික් ඩෙංගු අවදානම පුරෝකථනය කර, මැදිහත්වීමකින් සැබවින්ම වළක්වා ගත හැකි දේ ඇස්තමේන්තු කර, කණ්ඩායම් වැඩිම රෝගීන් වළක්වන ස්ථානවලට වෙන් කරයි.',
  'home.reactingQuote':
    'සතිපතා වාර්තා දත්තවල රෝග පැතිරීමක් පෙනෙන විට, රෝග ව්‍යාප්තිය සති 2-3ක් තිස්සේ සිදු වෙමින් තිබේ. එම දත්තවලට ප්‍රතිචාර දැක්වීම යනු සති දෙකකට පෙර පැවති තත්ත්වයකට ප්‍රතිචාර දැක්වීමයි.',
  'home.viewNational': 'ජාතික දළ විශ්ලේෂණය බලන්න',
  'home.checkDistrict': 'මගේ දිස්ත්‍රික්කය පරීක්ෂා කරන්න',
  'home.currentForecast': 'වත්මන් පුරෝකථනය',
  'home.weeksAhead': 'සති ඉදිරියට',
  'home.targetWeek': 'ඉලක්ක සතිය',
  'home.forecastCasesNationwide': 'පුරෝකථිත රෝගීන්, දේශීයව',
  'home.districtsHighRisk': 'ඉහළ අවදානම හෝ ඊට වැඩි දිස්ත්‍රික්ක',
  'home.highestRiskDistrict': 'වැඩිම අවදානම් දිස්ත්‍රික්කය',
  'home.per100kWeek': '100,000කට/සතියකට',
  'home.modelledNote': 'ආදර්ශයෙන් ලද අගයන්',
  'home.modelledNote2':
    'ආකෘතිය. මෙම වේදිකාවේ සෑම ප්‍රමාණයක්ම එය නිරීක්ෂිතද, ආදර්ශිතද, නැතහොත් සැලසුම් ඇස්තමේන්තුවක්ද යන්න දක්වයි.',
  'home.simulatedTitle': 'අනුකරණය කළ දත්ත',
  'home.simulatedBody':
    'මෙම ධාවනය කෘතිම දත්ත සමූහය භාවිත කළේය — යථාර්ථවාදී ගතිකයන්, නමුත් නිරීක්ෂණ නොවේ. මෙහි ඇති කිසිදු අගයක් සැබෑ වසංගත රෝග විද්‍යාවක් ලෙස නොසලකන්න. ධාවනය කරන්න',
  'home.simulatedBody2': 'සජීවී අගයන් සඳහා.',
  'home.realTitle': 'සැබෑ දත්ත',
  'home.realBody': 'වසංගත රෝග විද්‍යා අංශයේ WER වාර්තා සහ Open-Meteo, ක්‍රියාවලිය ධාවනය කළේ',
  'home.realBody2': '. සම්පූර්ණ මූලාශ්‍ර තොරතුරු පරිපාලන වේදිකාවේ ඇත.',
  'home.snapshotEyebrow': 'ජාතික දළ විශ්ලේෂණය',
  'home.snapshotTitle': 'ඩෙංගු ඊළඟට යොමු වන්නේ කොහටද',
  'home.snapshotDescription':
    'සියලුම දිස්ත්‍රික්ක {n}, සති {h}ක් ඉදිරියට. රෝගී සංඛ්‍යාවට වඩා 100,000කට අනුපාතය අනුව ශ්‍රේණිගත කර ඇත, එවිට කුඩා දිස්ත්‍රික්කයක රෝග පැතිරීමක් කොළඹ ජනගහනය පිටුපස සැඟවෙන්නේ නැත.',
  'home.fullOverview': 'සම්පූර්ණ දළ විශ්ලේෂණය',
  'home.districtsForecast': 'පුරෝකථිත දිස්ත්‍රික්ක',
  'home.highRiskOrAbove': 'ඉහළ අවදානම හෝ ඊට වැඩි',
  'home.aboveThreshold': '100,000කට 3.5 හෝ ඊට වැඩි/සතියකට',
  'home.forecastCases': 'පුරෝකථිත රෝගීන්',
  'home.nationwide': 'දේශීයව',
  'home.casesLastWeek': 'පසුගිය සතියේ රෝගීන්',
  'home.notifiedNationwide': 'දේශීයව වාර්තා වූ',
  'home.districtsUnit': 'දිස්ත්‍රික්ක',
  'home.ofTwentyFive': '25න්',
  'home.readEyebrow': 'මෙම වේදිකාව කියවන ආකාරය',
  'home.readTitle': 'එකිනෙකට වෙනස් වූ ප්‍රමාණ වර්ග තුනක්, කිසිදා එකම ආකාරයෙන් නොපෙන්වයි',
  'home.readDescription':
    'මිනුමක ශෛලියෙන්ම පෙන්වන සැලසුම් ඇස්තමේන්තුවක් එහි විශ්වසනීයත්වය ණයට ගනී — තීරණ-සහාය මෙවලමක් වැරදි තීරණයකට තුඩු දෙන ආකාරය එයයි. මූලාශ්‍ර තොරතුරු මෙහි ක්‍රමලේඛනයේ බලාත්මක කර ඇත, විනයෙන් නොවේ.',
  'home.tier': 'මට්ටම',
  'home.example': 'උදාහරණය:',
  'home.example1': 'සෞඛ්‍ය ආයතන 1,231ක්; 1,000කට ඇඳන් 3.93ක්.',
  'home.example2': 'රෝගීන් පුරෝකථනය කර ඇත',
  'home.example3': 'තුළ',
  'home.example3b': 'සති.',
  'home.example4':
    'ප්‍රකාශිත සායනික අනුපාත පුරෝකථනයකට යොදන ලද ඇතුළත්කිරීම් සහ ප්ලේට්ලට් ඒකක.',
  'home.noDataTitle': 'මහජන දත්ත නොමැති තැන, වේදිකාව එසේ පවසයි.',
  'home.noDataBody':
    'සජීවී ඇඳන් හිසින් තිබීම, ICU ගණන, ප්ලේට්ලට් තොග, කාර්ය මණ්ඩල ලේඛන සහ ගිලන් රථ පිහිටීම් ශ්‍රී ලංකාව සඳහා පළ නොකෙරේ. ඒ පැනල පැහැදිලි කිරීමක් සහ එය සක්‍රීය කරන දත්ත සම්ප්‍රේෂණයක් නම් කරයි, විශ්වසනීය පෙනුමක් ඇති අගයක් නොව.',
  'home.rolesEyebrow': 'භූමිකා පදනම් වූ ප්‍රවේශය',
  'home.rolesTitle': 'එක් එන්ජිමක් මත වේදිකා හතරක්',
  'home.rolesDescription':
    'අවසර ශ්‍රේණියෙන් එකතු වේ; විෂය පථය ඉන් වෙන් වේ. රෝහල් පරිපාලකයෙකුට සහ MOH නිලධාරියෙකුට වෙනස් පේළි දකිමින් අතිච්ඡාදනය වන අවසර තිබිය හැක.',
  'home.role.public.title': 'මහජනයා',
  'home.role.public.access': 'ගිණුමක් අවශ්‍ය නැත',
  'home.role.public.description':
    'ඔබ ජීවත් වන ස්ථානයේ අවදානම, පුරෝකථනයේ අර්ථය, වැළැක්වීමේ උපදෙස් සහ ආසන්න සායන.',
  'home.role.hospital.title': 'රෝහල් කාර්ය මණ්ඩලය',
  'home.role.hospital.access': 'කාර්ය මණ්ඩල ගිණුම',
  'home.role.hospital.description':
    'ඇතුළත් කිරීම් සහ දරුණු අවස්ථා ඇස්තමේන්තු, ඇඳන් පීඩනය, සහ ඉදිරි සති සඳහා සැපයුම් සැලසුම්.',
  'home.role.moh.title': 'MOH / ප්‍රාදේශීය නිලධාරී',
  'home.role.moh.access': 'කාර්ය මණ්ඩල ගිණුම',
  'home.role.moh.description':
    'ඔබේ දිස්ත්‍රික්කය සඳහා කණ්ඩායම් වෙන් කිරීම, මැදිහත්වීම් සැලසුම්, දර්ශන සංසන්දනය සහ අයවැය බෙදීම.',
  'home.role.admin.title': 'ජාතික පරිපාලක',
  'home.role.admin.access': 'අමාත්‍යාංශ ගිණුම',
  'home.role.admin.description':
    'දේශීය මෙහෙයුම්, ආකෘති වින්‍යාසය, දත්ත මූලාශ්‍ර, පරිශීලක කළමනාකරණය සහ විගණන ලේඛනය.',
  'home.open': 'විවෘත කරන්න',
  'home.engineEyebrow': 'එන්ජිම',
  'home.engineTitle': 'පුරෝකථනය → හේතුඵල බලපෑම → වෙන් කිරීම',
  'home.engineLede':
    'තනිකරම පුරෝකථනයකින් කණ්ඩායමක් යැවිය යුතු තැන කිව නොහැක. වැඩිම රෝගීන් සිටින දිස්ත්‍රික්කය දැනගැනීම මැදිහත්වීමක් වැඩිම වළක්වන ස්ථානය දැනගැනීමට සමාන නොවේ — ඒ සඳහා බලපෑම් ඇස්තමේන්තුවක් සහ සීමිත වෙන් කිරීමක් අවශ්‍ය වේ.',
  'home.stage1.title': 'සම්භාවිතා පුරෝකථනය',
  'home.stage1.body':
    'සෑම මූලික ආකෘතියක්ම භ්‍රමණය වන මූලාරම්භ කොටස්වල පසුපරීක්ෂණය කරන ලද, 80% විශ්වාස පරාසයක් සහිත දිස්ත්‍රික් රෝගී පුරෝකථන.',
  'home.stage2.title': 'යාන්ත්‍රික බලපෑම',
  'home.stage2.body':
    'දිස්ත්‍රික්කයේම ඉතිහාසයට සවි කරන ලද SEI-SIR ආකෘතියක්, කණ්ඩායම්-සති ගණනකින් වළක්වා ගත හැකි රෝගීන් ඇස්තමේන්තු කරයි.',
  'home.stage3.title': 'සීමිත වෙන් කිරීම',
  'home.stage3.body':
    'නිශ්චිත සංඛ්‍යාත්මක වැඩසටහනක් නියත කණ්ඩායම් අයවැයක් වළක්වා ගත හැකි රෝගීන් උපරිම කිරීමට බෙදා හරියි, සෞඛ්‍ය ආයතන අඩු දිස්ත්‍රික්ක සඳහා සමානාත්ම සීමාවක් සමඟ.',
  'home.howBuilt': 'ආකෘති ගොඩනගා තහවුරු කරන ආකාරය',
  'home.noDataYetTitle': 'තවම ක්‍රියාවලි දත්ත නොමැත',
  'home.noDataYetBody':
    'මෙම යෙදුම Python ක්‍රියාවලියෙන් ලියන ලද කෞතුක වස්තු ප්‍රදර්ශනය කරයි. ඒවා තැනීමෙන් පසු බ්‍රව්සරය සඳහා අපනයනය කරන්න:',
  'home.noDataYetNote': 'දෙකම කෘතිම දත්ත සමූහයට එරෙහිව සම්පූර්ණයෙන් නොබැඳිව ධාවනය වේ.',
  'nat.crumb': 'ජාතික දළ විශ්ලේෂණය',
  'nat.eyebrow': 'ජාතික දළ විශ්ලේෂණය',
  'nat.title': 'සෑම දිස්ත්‍රික්කයක්ම, පුරෝකථිත අවදානම අනුව ශ්‍රේණිගත කර ඇත',
  'nat.description':
    'සෑම භූමිකාවක් සඳහාම සමානයි: භූමිකා-සීමිත දෙයක් දර්ශනය සීමා කිරීමට පෙර, දිස්ත්‍රික්ක 25ම. {week} සතිය.',
  'nat.metaModel': 'ආකෘතිය',
  'nat.metaPanel': 'දත්ත සමූහය',
  'nat.metaPipelineRun': 'ක්‍රියාවලි ධාවනය',
  'nat.simulatedTitle': 'අනුකරණය කළ දත්ත',
  'nat.simulatedBody':
    'මෙම ධාවනය කෘතිම දත්ත සමූහය භාවිත කළේය. යථාර්ථවාදී ගතිකයන්, නමුත් නිරීක්ෂණ නොවේ — පහත ඇති කිසිදු අගයක් සැබෑ වසංගත රෝග විද්‍යාවක් ලෙස නොසලකන්න.',
  'nat.veryHigh': 'ඉතා ඉහළ',
  'nat.high': 'ඉහළ',
  'nat.hindsightEyebrow': 'පසුවිපරම',
  'nat.hindsightTitle': 'පුරෝකථනය සැබවින්ම කෙසේ සිදු වූයේද',
  'nat.hindsightDescription':
    'දත්ත සමූහයේ ඕනෑම සතියකට ගමන් කරන්න. වම් සිතියම වාර්තා වූයේ කුමක්ද යන්නයි; දකුණු සිතියම ආකෘතිය සති {h}කට පෙර සිටගෙන, අතරමැදි කිසිදු දත්තයක් නොදැක, එම සතිය සඳහා පැවසූ දෙයයි.',
  'nat.chartObservedForecast': 'ජාතික රෝගීන්: නිරීක්ෂිත සහ පුරෝකථිත',
  'nat.chartObservedForecastCaption':
    'ඝන රේඛාව: නිරීක්ෂිත වාර්තා. පටි සහිත බිඳුම් රේඛාව: දිස්ත්‍රික්ක හරහා එකතු කළ පුරෝකථන මධ්‍ය අගය සහ 80% විශ්වාස පරාසය.',
  'nat.chartRainfall': 'වර්ෂාව සහ රෝගීන්',
  'nat.chartRainfallCaption':
    'රෝගීන් වර්ෂාවෙන් සති 6-8ක් පමණ පසුව අනුගමනය කරයි: වර්ෂාවෙන් භාජන පිරී, කීටයන් වර්ධනය වී, මදුරුවන් බිහි වේ, ඉන් පසුව පමණක් රෝග පැතිරීම වැඩි වේ. එම ප්‍රමාදය නිසාම සති දෙකකට පෙර පුරෝකථනයක් කළ හැකි වේ.',
  'nat.backtestEyebrow': 'පසුපරීක්ෂණය',
  'nat.backtestTitle': 'මෙම ආකෘතිය තෝරාගත්තේ ඇයි',
  'nat.backtestDescription':
    'සති {h}ක් ඉදිරියට භ්‍රමණය වන මූලාරම්භ කොටස්වල සාමාන්‍ය {metric} — අඩු අගය වඩා හොඳය. සෑම මූලික ආකෘතියක්ම සෑම කොටසකදීම නැවත සවි කරනු ලැබේ, එබැවින් කිසිදු ආකෘතියක් එය පුරෝකථනය කරන සතියෙන් පසු දත්ත නොදකියි.',
  'nat.modelComparison': 'ආකෘති සංසන්දනය',
  'nat.noBacktestScores': 'මෙම අපනයනයේ පසුපරීක්ෂණ ලකුණු නොමැත.',
  'nat.intervalMeaningTitle': 'විශ්වාස පරාසයේ අර්ථය',
  'nat.intervalMeaningBody':
    'සෑම දිස්ත්‍රික් පුරෝකථනයක්ම ලක්ෂ්‍යයක් නොව ප්‍රතිශතක් සමූහයකි. 80% විශ්වාස පරාසය පවසන්නේ සැබෑ ගණන සති 5න් 4ක් තුළ එයට අනුරූප වේ යැයි ආකෘතිය අපේක්ෂා කරන බවයි — සැලසුමකට කොපමණ ලිහිල් බවක් තිබිය යුතුද යන්න තීරණය කළ යුත්තේ එම පරාසයේ පළලින්මය, මධ්‍ය අගයෙන් නොවේ.',
  'nat.widestInterval': 'පළලම විශ්වාස පරාසය',
  'nat.backtestFolds': 'පසුපරීක්ෂණ කොටස්',
  'nat.panelWindow': 'දත්ත සමූහයේ කාල පරාසය',
  'nat.districtWeeks': 'දිස්ත්‍රික්-සති',
  'nat.detailEyebrow': 'විස්තර',
  'nat.detailTitle': 'සියලුම දිස්ත්‍රික්ක',
  'nat.detailDescription':
    'මෙම කාලය සඳහා සෑම දිස්ත්‍රික්කයක්ම සඳහා පුරෝකථනය, විශ්වාස පරාසය, ජනගහනය සහ සෞඛ්‍ය ආයතන ගණන.',
  'nat.reportEyebrow': 'වාර්තාව',
  'nat.reportTitle': 'මෙය ලේඛනයක් ලෙස රැගෙන යන්න',
  'nat.reportDescription':
    'මෙම දළ විශ්ලේෂණයේ PDF ස්නැප්ෂොට් එකක්: වේදිකාවෙන් පිටත බෙදාහැරීම සඳහා, එකම මූලික අගයන් සහ ශ්‍රේණිගත දිස්ත්‍රික් වගුව, එකම දත්ත මූලාශ්‍ර අවවාදය සමඟ.',
  'nat.riskMap': 'අවදානම් සිතියම',
  'nat.everyDistrictRanked': 'සෑම දිස්ත්‍රික්කයක්ම, ශ්‍රේණිගත කර ඇත',
  'nat.weeksAheadClick': 'සති ඉදිරියට · දිස්ත්‍රික්කයක් ක්ලික් කරන්න',
  'nat.per100kWeekUnit': '100,000කට/සතියකට',
  'nat.openDistrict': 'දිස්ත්‍රික්කය විවෘත කරන්න',
  'nat.col.district': 'දිස්ත්‍රික්කය',
  'nat.col.risk': 'අවදානම',
  'nat.col.forecastCases': 'පුරෝකථිත රෝගීන්',
  'nat.col.interval80': '80% විශ්වාස පරාසය',
  'nat.col.per100k': '100,000කට/සතියකට',
  'nat.col.population': 'ජනගහනය',
  'nat.col.facilities': 'ආයතන',
  'nat.report.filePrefix': 'ජාතික දළ විශ්ලේෂණය —',
  'nat.report.desc': 'PDF · මූලික අගයන් සහ ශ්‍රේණිගත දිස්ත්‍රික්ක 25ම',
  'nat.report.pipelineRun': 'ක්‍රියාවලි ධාවනය',
  'nat.report.download': 'වාර්තාව බාගන්න',
  'hist.viewPastWeek': 'පසුගිය සතියක් බලන්න',
  'hist.description': 'එකම සතිය දෙවරක් දක්නට ලැබේ: වාර්තා වූයේ කුමක්ද, සහ ආකෘතිය පැවසුවේ කුමක්ද',
  'hist.weeksEarlier': 'සති පෙර.',
  'hist.weekBeginning': 'ආරම්භක සතිය',
  'hist.previousWeek': 'පෙර සතිය',
  'hist.nextWeek': 'ඊළඟ සතිය',
  'hist.weekLabel': 'සතිය',
  'hist.backtestedTicks': 'පසුපරීක්ෂණය කළ පුරෝකථනයක් සහිත සති',
  'hist.observed': 'නිරීක්ෂිත',
  'hist.predictedAhead': 'පුරෝකථිත,',
  'hist.noNotifiedCases': 'මෙම සතිය සඳහා වාර්තා වූ රෝගීන් නොමැත.',
  'hist.casesThatWeek': 'එම සතියේ රෝගීන්',
  'hist.predictedCases': 'පුරෝකථිත රෝගීන්',
  'hist.highestRisk': 'වැඩිම අවදානම',
  'hist.under': 'අඩු',
  'hist.per100kWkUnit': '100,000කට/සතියකට',
  'hist.noPredictionForWeek':
    'මෙම කාලය සඳහා මෙම සතියට පසුපරීක්ෂණය කළ පුරෝකථනයක් නොමැත. පුරෝකථිත මාලාව නිරීක්ෂිත මාලාවට වඩා කෙටි කාල පරාසයක් ආවරණය කරයි.',
  'crumb.public': 'මගේ දිස්ත්‍රික්කයේ ඩෙංගු අවදානම',
  'prov.observed': 'නිරීක්ෂිත',
  'prov.modelled': 'ආදර්ශිත',
  'prov.assumed': 'සැලසුම් ඇස්තමේන්තුව',
  'prov.user_input': 'ඔබ ඇතුළත් කළ',

  // --- Method page ----------------------------------------------------------
  'method.crumb': 'මෙය ක්‍රියා කරන ආකාරය',
  'method.eyebrow': 'ක්‍රමවේදය',
  'method.title': 'මෙම වේදිකාව ඕනෑම තීරණයක් ගන්නා ආකාරය',
  'method.description':
    'අදියර තුනකි, එක් එක් අදියර පෙර අදියරට පිළිතුරු දිය නොහැකි ප්‍රශ්නයකට පිළිතුරු දෙයි. වැඩිම රෝගී සංඛ්‍යාව ඇති දිස්ත්‍රික්කය දැනගැනීම කණ්ඩායමකට වැඩිම ප්‍රතිලාභයක් ලබා දිය හැකි ස්ථානය දැනගැනීමට සමාන නොවේ.',
  'method.metaPanel': 'දත්ත සමූහය',
  'method.metaDistrictWeeks': 'දිස්ත්‍රික්-සති',
  'method.metaLastRun': 'අවසන් ධාවනය',
  'method.engineEyebrow': 'එන්ජිම',
  'method.engineTitle': 'පුරෝකථනය → හේතු-සම්බන්ධ බලපෑම → සම්පත් වෙන් කිරීම',
  'method.engineDescription':
    'සෑම අදියරක්ම කෞතුකයක් (artifact) ලියයි. උපකරණ පුවරුව එම කෞතුක කියවන අතර ඒවා කිසි විටෙකත් නැවත ගණනය නොකරයි — එබැවින් වසංගතයක් අතරතුර මෙහි සර්පනයක් ගෙනයාම ක්ෂණිකව සිදු වේ.',
  'method.stage1': 'අදියර 1',
  'method.stage1Title': 'සම්භාවිතා දිස්ත්‍රික් පුරෝකථන',
  'method.stage1Body':
    'ක්වන්ටයිල් ආකෘතියක් සෑම දිස්ත්‍රික්කයක් සඳහාම සති දෙකේ සිට හතර දක්වා කාලයක් සඳහා මධ්‍යස්ථයක් සහ 80% පරතරයක් නිපදවයි. සෘතුමය නොවෙනස් ආකෘතිය, SARIMA, ග්‍රේඩියන්ට් බූස්ටින් ඇතුළු සෑම මූලික ආකෘතියක්ම සෑම භ්‍රමණය-මූලාරම්භක නැවුම් කිරීමකදීම නැවත සකසනු ලැබේ — එබැවින් කිසිදු ආකෘතියක් එය පුරෝකථනය කරන සතියෙන් පසු දත්ත කිසි විටෙකත් නොදකියි. ජාතික දළ විශ්ලේෂණයේ ඇති සංසන්දන වගුව එම පසුපරීක්ෂණයයි, ප්‍රකාශයක් නොවේ.',
  'method.stage1DetailTemplate': 'සති 2දී {metric} අනුව හොඳම ප්‍රතිඵලය: {list}.',
  'method.stage2': 'අදියර 2',
  'method.stage2Title': 'යාන්ත්‍රික මැදිහත්වීම් බලපෑම',
  'method.stage2Body':
    'කොටස්-මූලික SEI-SIR ආකෘතියක් සෑම දිස්ත්‍රික්කයක්ම එහිම ඉතිහාසයට එරෙහිව සකසනු ලබන අතර, පසුව මදුරු මර්දනය යෙදූ විට නැවත ඒකාබද්ධ කරනු ලැබේ. එම ඒකාබද්ධ කිරීම් දෙක අතර වෙනස යනු නිශ්චිත කණ්ඩායම්-සති ගණනකට වළක්වා ගත් රෝගීන් සංඛ්‍යාවයි — එය හේතු-සම්බන්ධ ප්‍රමාණයකි, පුරෝකථනයෙන් කියවන සහසම්බන්ධතාවයක් නොවේ.',
  'method.stage2DetailTemplate':
    'බලපෑම් සති {horizon}ක කාල සීමාවක් තුළ ගණනය කර සෑම දිස්ත්‍රික්කයක් සඳහාම වක්‍රයක් ලෙස කෑෂ් කර ඇත — මෙය මීළඟ කණ්ඩායම-සතියේ අන්තර්ගත ප්‍රතිලාභය ක්ෂණිකව ලබා ගැනීමට හේතු වේ.',
  'method.stage3': 'අදියර 3',
  'method.stage3Title': 'සීමා සහිත සම්පත් වෙන් කිරීම',
  'method.stage3Body':
    'නිශ්චිත සති කණ්ඩායම් අයවැයක් අදියර 2හි බලපෑම් වක්‍ර සහ පහසුකම් අඩු දිස්ත්‍රික්කවල සාධාරණත්ව සීමාවකට යටත්ව, මුළු වළක්වා ගත් රෝගී සංඛ්‍යාව උපරිම කිරීමට නිඛිල ක්‍රමලේඛනයක් මගින් බෙදා හරිනු ලැබේ. එම සීමාව නොමැති නම්, කොළඹට කිසි විටෙකත් තරඟ කළ නොහැකි නිරපේක්ෂ රෝගී සංඛ්‍යා සහිත කුඩා, අඩු සේවා සපයන දිස්ත්‍රික්ක ප්‍රශස්තකරණය මගින් නොසලකා හරිනු ලැබේ.',
  'method.stage3Detail':
    'මුළු අයවැය පරාසය නොබැඳි ලෙස විසඳා කෑෂ් කර ඇත — එබැවින් අයවැය සර්පනය විසඳුම් නැවත විසඳනවා වෙනුවට ඒවා යොමු කරයි.',
  'method.whyForecastEyebrow': 'මුලින්ම පුරෝකථනය කරන්නේ ඇයි',
  'method.whyForecastTitle': 'දැනුම්දීම්වලට ප්‍රතිචාර දැක්වීම යනු සති දෙකක් පැරණි චිත්‍රයකට ප්‍රතිචාර දැක්වීමයි',
  'method.whyForecastBody1':
    'සතිපතා දැනුම්දීම් දත්තවල වර්ධනයක් පෙනෙන විට, බෝවීම දැනටමත් සති දෙක තුනක සිට සිදුවෙමින් පවතී: මදුරුවෙකු වෛරසය ලබා ගනී, බාහිර නිරෝධායන කාලය ගත වේ, පුද්ගලයෙකු ආසාදනය වේ, අභ්‍යන්තර නිරෝධායන කාලය ගත වේ, ඔවුන් ප්‍රතිකාර සොයයි, සහ රෝගය දැනුම් දෙනු ලැබේ. එම අවස්ථාවේදී යවනු ලබන කණ්ඩායම් දැනටමත් බිඳ වැටී ඇති රැල්ලකට ප්‍රතිකාර කරමින් සිටිති.',
  'method.whyForecastBody2':
    'වර්ෂාව මගින් වඩාත් කලින් සංඥාවක් හැකි කරයි. වර්ෂාව භාජන පුරවයි, කීටයන් වර්ධනය වේ, වැඩිහිටියන් මතු වේ, එමෙන්ම එවිට පමණි බෝවීම ඉහළ යන්නේ — පුරෝකථනය භාවිතා කරන දළ වශයෙන් සති හයේ සිට අටක් දක්වා ප්‍රමාදයකි.',
  'method.riskBandsEyebrow': 'අවදානම් කාණ්ඩ',
  'method.riskBandsTitle': 'රෝගී සංඛ්‍යා නොව, ව්‍යාප්තිය භාවිතා කරන්නේ ඇයි',
  'method.riskBandsDescription':
    'කොළඹට පදිංචිකරුවන් මිලියන 2.48ක් සිටින අතර මුලතිව්වට ආසන්න වශයෙන් 100,000ක් සිටී. දිස්ත්‍රික්ක අමු සංඛ්‍යා අනුව ශ්‍රේණිගත කිරීමෙන් වසරේ සෑම සතියකම කොළඹ රතු පැහැයෙන් පින්තාරු වන අතර සැබෑ මුලතිව් වසංගතයක් කොළ පැහැයෙන් හැරෙනු ඇත.',
  'method.riskBandBelow': '1.5ට අඩු',
  'method.riskBandAndAboveTemplate': '{threshold} සහ ඉහළ',
  'method.riskBandPerWeek': '100,000කට සතියකට',
  'method.riskBandsCalloutPrefix': 'මේවා ',
  'method.riskBandsCalloutBold': 'මෙහෙයුම් සැලසුම් සීමා මිතියි, සායනික ප්‍රමිතියක් නොවේ',
  'method.riskBandsCalloutSuffix':
    '. ඩෙංගු වසංගතයක් නිර්වචනය කරන ජාත්‍යන්තරව එකඟ වූ ව්‍යාප්ති සීමා මිතියක් නොමැත — ප්‍රකාශිත සීමා මිතීන් රෝග-ව්‍යාප්ති-විශේෂිත වන අතර සාමාන්‍යයෙන් රට අනුව ව්‍යුත්පන්න වේ. ඒවා සැබෑ දිස්ත්‍රික්-සති ව්‍යාප්තියට එරෙහිව නැවත සකස් කරන ලද අතර, ඒවා නැවත සකස් කළ හැකි වන පරිදි නියතයන් ලෙස හෙළිදරව් කර ඇත.',
  'method.provenanceEyebrow': 'මූලාරම්භය',
  'method.provenanceTitle': 'සෑම ප්‍රමාණයක්ම එය කුමක්දැයි ප්‍රකාශ කරයි',
  'method.provenanceDescription':
    'විනයෙන් නොව කේතයෙන් බලාත්මක කර ඇත: සැලසුම් ඇස්තමේන්තුවක් ලෙස ලේබල් කළ ප්‍රමාණයක් එහි පදනම ප්‍රකාශ නොකර එන්ජිමේ තැනිය නොහැක.',
  'method.provenanceCalloutBold': 'මහජන දත්ත නොමැති තැන, වේදිකාව එසේ පවසයි.',
  'method.provenanceCalloutSuffix':
    ' සජීවී ඇඳන් වාසය, ICU සංගණනය, ප්ලේට්ලට් තොග, කාර්ය මණ්ඩල නාම ලේඛන සහ ගිලන් රථ ස්ථාන ශ්‍රී ලංකාව සඳහා ප්‍රකාශයට පත් කර නොමැත. එම පැනල ඒවා සක්‍රීය කරන දෙනුම් සපයන්නා නම් කරමින් පැහැදිලි කිරීමක් පෙන්වයි, විශ්වසනීය පෙනෙන සංඛ්‍යාවක් නොව.',
  'method.accessEyebrow': 'ප්‍රවේශය',
  'method.accessTitle': 'අවසර එකතු වන සුළුය; විෂය පථය වෙනස් වේ',
  'method.accessDescription':
    'රෝහල් පරිපාලකයෙකුට සහ MOH නිලධාරියෙකුට එකිනෙකට වෙනස් පේළි දකිමින් අතිච්ඡාදනය වන අවසර තිබිය හැක — එකක් පහසුකමකට සීමිත වන අතර අනෙක දිස්ත්‍රික්කයකට සීමිත වේ. මේ දෙක තනි මට්ටමකට හැකිලීම සෞඛ්‍ය උපකරණ පුවරුවක් කලාප හරහා දත්ත කාන්දු කරන සාමාන්‍ය ආකාරයයි.',
  'method.permissionsCountTemplate': 'අවසර {n}ක්',
  'method.accessCalloutPrefix': 'මහජන පිටු යනු ',
  'method.accessCalloutBold': 'පෙරනිමියෙන් ප්‍රතික්ෂේප කරන උප කුලකයකි, සංස්කරණයක් නොවේ',
  'method.accessCalloutSuffix':
    '. ඒවා සම්පූර්ණ චිත්‍රය ගණනය කර එහි කොටස් සඟවනවා වෙනුවට, මහජන භූමිකාව සැබවින්ම දරන අවසර මත ගොඩනගා ඇත — එබැවින් මෙහි දෝෂයක් රෝහල් ධාරිතාව හෙළිදරව් කරනවා වෙනුවට තොරතුරු අස්ථානගත වී ඇති බව පෙන්වයි.',
  'method.decisionSupportTitle': 'තීරණ සහාය, සායනික මෙවලමක් නොවේ',
  'method.decisionSupportBody':
    'මෙම වේදිකාවේ කිසිවක් රෝගියෙකු රෝග විනිශ්චය නොකරයි හෝ ප්‍රතිකාර නියම නොකරයි. එය සීමිත මහජන සෞඛ්‍ය ධාරිතාව වෙන් කිරීමට උපකාර වීම සඳහා දිස්ත්‍රික් මට්ටමේ අවදානම සහ සම්පත් ප්‍රතිවිපාක විස්තර කරයි — සහ එය පෙන්වන සෑම ප්‍රමාණයක්ම එය අසල ප්‍රකාශිත උපකල්පනය තරම් පමණක් හොඳය.',

  // --- Data protection (PDPA) notice -----------------------------------------
  'privacy.eyebrow': 'නීතිමය',
  'privacy.description':
    'ශ්‍රී ලංකාවේ 2022 අංක 9 දරන පුද්ගලික දත්ත ආරක්ෂණ පනත යටතේ, මෙම වේදිකාව රැස් කරන දේ, ඇයි, කොපමණ කාලයක් තබා ගන්නේද, සහ ඔබේම දත්ත ගැන විමසන්නේ කෙසේද යන්න.',
  'privacy.notice':
    'මෙම නිවේදනය නිර්මාණය කරන ලද පරිදි වේදිකාව විස්තර කරයි. පහත ඇති කිසිවක් ක්‍රියාත්මක පද්ධතිය සැබවින්ම කරන දෙයට නොගැලපෙන්නේ නම්, පද්ධතිය වැරදිය මෙම නිවේදනය නොවේ — ඒවා නැවත එකඟතාවයට ගෙන ඒම සඳහා මෙම පිටුව නොව කේතය යාවත්කාලීන කරන්න.',
  'privacy.controllerEyebrow': 'පාලකයා',
  'privacy.controllerTitle': 'මෙම වේදිකාව මෙහෙයවන්නේ කවුරුන්ද',
  'privacy.controllerBody':
    'ශ්‍රී ලංකා සෞඛ්‍ය අමාත්‍යාංශය පහත විස්තර කරන පුද්ගලික දත්ත සඳහා පාලකයා වේ. ඔබේම දත්ත සම්බන්ධ ඉල්ලීම් — ප්‍රවේශය, නිවැරදි කිරීම, හෝ ඒවා භාවිතා කරන ආකාරය පිළිබඳ ප්‍රශ්නයක් — මෙම වෙබ් අඩවියේ පාදාසුරු ඇති සම්බන්ධතා මාර්ග හරහා අමාත්‍යාංශය වෙත යොමු කළ යුතුය.',
  'privacy.collectedEyebrow': 'රැස් කරන දේ',
  'privacy.collectedTitle': 'මෙම වේදිකාවේ ඇති දත්ත වර්ග දෙක',
  'privacy.publicDataTitle': 'මහජන අවදානම් තොරතුරු',
  'privacy.publicDataBody':
    'දිස්ත්‍රික් මට්ටමේ පුරෝකථන, රෝගී සංඛ්‍යා සහ අවදානම් කාණ්ඩ. මෙය සමස්ත වසංගත රෝග විද්‍යා දත්තයකි — කිසිදු පුද්ගලයෙකු එහි හඳුනාගත නොහැක, සහ එය බැලීමට පිවිසෙන්නෙකුගෙන් කිසිදු පුද්ගලික දත්තයක් රැස් නොකරයි. දිස්ත්‍රික්කයක් හෝ භාෂාවක් තෝරා ගැනීම, සහ ඔබ සකසන ඕනෑම දැනුම්දීම් අභිප්‍රාය මනාපයක් ඔබේම බ්‍රව්සරයේ පමණක් ගබඩා වන අතර (පහත “දැනුම්දීම් අභිප්‍රාය” බලන්න) එය කිසි විටෙකත් මෙම වේදිකාවේ සේවාදායකවලට ළඟා නොවේ.',
  'privacy.staffDataTitle': 'කාර්ය මණ්ඩල ගිණුම්',
  'privacy.staffDataBody':
    'රෝහල්, දිස්ත්‍රික්-මෙහෙයුම් සහ පරිපාලන ගිණුම් සඳහා: විද්‍යුත් තැපැල් ලිපිනයක්, දර්ශන නාමයක්, පවරන ලද භූමිකාවක්, සහ දිස්ත්‍රික් හෝ පහසුකම් විෂය පථයක්. ගිණුම් නිර්මාණය කරනු ලබන්නේ පරිපාලකයෙකු විසින් මිස ස්වයං-ලියාපදිංචියෙන් නොවේ, සහ මෙය කාර්ය මණ්ඩල සාමාජිකයෙකු සත්‍යාපනය කිරීමට සහ ඔවුන්ට දැකිය හැක්කේ තමන්ගේම පහසුකම හෝ දිස්ත්‍රික්කයට පමණක් සීමා කිරීමට අවශ්‍ය අවම දේ වේ.',
  'privacy.legalBasisEyebrow': 'නීතිමය පදනම',
  'privacy.legalBasisTitle': 'මෙම සැකසීම නීත්‍යානුකූල වන්නේ ඇයි',
  'privacy.legalBasisBody':
    'මහජන අවදානම් තොරතුරු අමාත්‍යාංශයේ මහජන සෞඛ්‍ය කාර්යභාරය ක්‍රියාත්මක කිරීමේදී ප්‍රකාශයට පත් කරනු ලැබේ — සතිපතා වසංගත රෝග විද්‍යා ප්‍රකාශනයකට කිසිදු එකඟතාවයක් අවශ්‍ය නොවන ආකාරයටම, එය බැලීමට කිසිදු එකඟතාවයක් සොයනු හෝ අවශ්‍ය නොවේ. කාර්ය මණ්ඩල ගිණුම් දත්ත සකසනු ලබන්නේ එම මහජන කාර්යභාරය යටතේම, එය මදුරු මර්දන සැලසුම් සඳහා සීමිත-ප්‍රවේශ පද්ධතියක් මෙහෙයවීමට අවශ්‍ය බවට පදනම මතය; එය මෙම වේදිකාව මෙහෙයවීමෙන් ඔබ්බට කිසිදු අරමුණක් සඳහා භාවිතා නොකරයි.',
  'privacy.auditEyebrow': 'විගණන ලේඛනය',
  'privacy.auditTitle': 'කාර්ය මණ්ඩල පිවිසුමක් ගැන වාර්තා වන්නේ කුමක්ද',
  'privacy.auditBody':
    'පිවිසීම, ඉවත් වීම, සහ කාර්ය මණ්ඩල පෝට්ලයක් නැරඹීම වාර්තා කරනු ලැබේ — වේලාව, ගිණුම් විද්‍යුත් තැපෑල, භූමිකාව, එම අවස්ථාවේ දිස්ත්‍රික් විෂය පථය, සහ නරඹන ලද පිටුව. මෙය පවතින්නේ අවශ්‍ය නම් "කවුරුන් කුමක් බැලුවේද, කවදාද" යන්නට පරිපාලකයෙකුට පිළිතුරු දීමට ඉඩ දීම සඳහා වන අතර, එය දිස්නීය වන්නේ ජාතික-පරිපාලක ගිණුම් සඳහා පමණි. එය පිටුවක් විවෘත කිරීමෙන් ඔබ්බට එම ගිණුම එම පිටුවේ කළ දේ වාර්තා නොකරන අතර, එය කිසි විටෙකත් කාර්යසාධන අධීක්ෂණය සඳහා හෝ එම වගවීමේ වාර්තාවෙන් ඔබ්බට කිසිදු අරමුණක් සඳහා භාවිතා නොකෙරේ.',
  'privacy.retentionEyebrow': 'රඳවා ගැනීම',
  'privacy.retentionTitle': 'දත්ත තබා ගන්නා කාලය',
  'privacy.retentionStaffTitle': 'කාර්ය මණ්ඩල ගිණුම් වාර්තා',
  'privacy.retentionStaffBody':
    'ගිණුමේ ආයු කාලය සඳහා තබා ගනු ලබන අතර, ප්‍රවේශය ඉවත් කරන විට පරිපාලකයෙකු විසින් ඉවත් කරනු ලැබේ.',
  'privacy.retentionAuditTitle': 'විගණන ලේඛන ඇතුළත් කිරීම්',
  'privacy.retentionAuditBodyPrefix':
    'මෙහෙයුම්කරුවෙකු කාලසටහන්ගත මකාදැමීම සක්‍රීය කළ පසු දින 365කට පසු ස්වයංක්‍රීයව මකා දමනු ලැබේ (',
  'privacy.retentionAuditBodySuffix':
    '). මෙය මෙම යෙදවීමේ ධාවනය කර නොමැති නම්, ඇතුළත් කිරීම් අනන්තවත් රඳවා තබා ගනු ලැබේ — එය සක්‍රීය කර ඇත්දැයි ඔබේ පරිපාලකයාගෙන් විමසන්න.',
  'privacy.retentionAggTitle': 'සමස්ත වසංගත රෝග විද්‍යා දත්ත',
  'privacy.retentionAggBody':
    'ඓතිහාසික වාර්තාවක් ලෙස රඳවා තබා ගනු ලැබේ — එය කිසි විටෙකත් පුද්ගලික දත්ත නොවන බැවින්, පුද්ගලික දත්ත සඳහා වන PDPA රඳවා ගැනීමේ සීමා එයට අදාළ නොවේ.',
  'privacy.rightsEyebrow': 'ඔබේ අයිතිවාසිකම්',
  'privacy.rightsTitle': 'ප්‍රවේශය, නිවැරදි කිරීම, සහ ප්‍රශ්න',
  'privacy.rightsBody':
    'PDPA යටතේ, මෙම වේදිකාව ඔබ ගැන දරා ඇති පුද්ගලික දත්ත මොනවාදැයි ඔබට විමසිය හැක, එය වැරදි නම් නිවැරදි කිරීමට ඉල්ලා සිටිය හැක, සහ එය භාවිතා කරන ආකාරය පිළිබඳ ප්‍රශ්න ඇසිය හැක. කාර්ය මණ්ඩල ගිණුමක් සඳහා, වේගවත්ම මාර්ගය ඔබේම පරිපාලකයාය; වෙනත් ඕනෑම දෙයක් සඳහා, මෙම වෙබ් අඩවියේ පාදාසුරු ඇති සම්බන්ධතා විස්තර භාවිතා කරන්න.',
  'privacy.notCoveredTitle': 'මෙම නිවේදනය ආවරණය නොකරන දේ',
  'privacy.notCoveredBody':
    'මෙම පිටුව වේදිකාවේම දත්ත හැසිරවීම ප්‍රකාශ කරයි. එය වසංගත රෝග විද්‍යා අංශය, රෝහල්, හෝ මෙම වේදිකාව කියවා පෙන්වන ප්‍රකාශිත සංඛ්‍යාලේඛන දරන අනෙකුත් ආයතන සතු දත්ත ආවරණය නොකරයි — එම ආයතන ඔවුන්ගේම වාර්තා සඳහා වෙනම පාලකයන් වන අතර, ඒවා පිළිබඳ ඉල්ලීම් ඍජුවම ඔවුන් වෙත යා යුතුය.',

  // --- Staff sign-in ----------------------------------------------------------
  'signin.introPrefix': 'මහජන අවදානම් තොරතුරු සඳහා ගිණුමක් අවශ්‍ය නොවේ — ',
  'signin.introLink': 'ඔබේ දිස්ත්‍රික්කය පරීක්ෂා කරන්න',
  'signin.introSuffix':
    ' පිවිසීමකින් තොරව. ගිණුමක් රෝහල්, MOH සහ අමාත්‍යාංශ කාර්ය මණ්ඩලය සඳහා වන අතර, ඔබට කළ හැකි දේ සහ ඔබට දැකිය හැකි දිස්ත්‍රික්ක යන දෙකම එය තීරණය කරයි.',
  'signin.footerNote':
    'ගිණුම් ජාතික පරිපාලකයෙකු විසින් නිර්මාණය කරනු ලබන්නේ මිස ස්වයං-ලියාපදිංචියෙන් නොවේ. ප්‍රවේශය ඔබේම පහසුකම හෝ දිස්ත්‍රික්කයට සීමා වී ඇත — පිවිසීම එයින් ඔබ්බට වේදිකාව ඔබට පෙන්වන දේ පුළුල් නොකරයි.',
  'signin.emailLabel': 'විද්‍යුත් තැපැල් ලිපිනය',
  'signin.passwordLabel': 'මුරපදය',
  'signin.showPassword': 'මුරපදය පෙන්වන්න',
  'signin.hidePassword': 'මුරපදය සඟවන්න',
  'signin.submitting': 'පිවිසෙමින්…',
  'signin.submit': 'පිවිසෙන්න',
  'signin.error.missingFields': 'ඔබේ විද්‍යුත් තැපැල් ලිපිනය සහ මුරපදය ඇතුළත් කරන්න.',
  'signin.error.rateLimited': 'උත්සාහයන් ඉතා වැඩිය. විනාඩි කිහිපයක් රැඳී නැවත උත්සාහ කරන්න.',
  'signin.error.invalidCredentials': 'එම අක්තපත්‍ර පිළිගත්තේ නැත. ඔබේ විද්‍යුත් තැපෑල සහ මුරපදය පරීක්ෂා කරන්න.',

  // --- Staff-portal access notice --------------------------------------------
  'notice.staffOnlyTemplate': '{portal} කාර්ය මණ්ඩලයට පමණි',
  'notice.availableToTemplate':
    'මෙම පෝට්ලය {roles} සඳහා ලබා ගත හැක. සෑම දිස්ත්‍රික්කයක් සඳහාම මහජන අවදානම් තොරතුරු සඳහා ගිණුමක් අවශ්‍ය නොවේ.',
  'notice.checkDistrict': 'ඒ වෙනුවට දිස්ත්‍රික්කයක් පරීක්ෂා කරන්න',
  'notice.footerPrefix': 'මෙහි මහජන දත්ත ',
  'notice.footerBold': 'පෙරනිමියෙන් ප්‍රතික්ෂේප කරන උප කුලකයකි, සංස්කරණයක් නොවේ',
  'notice.footerSuffix':
    ' — මෙම පිටු භූමිකාවක් සැබවින්ම දරන අවසර මත ගොඩනගා ඇත, එබැවින් දෝෂයක් රෝහල් ධාරිතාව හෙළිදරව් කරනවා වෙනුවට තොරතුරු අස්ථානගත වී ඇති බව පෙන්වයි.',
  'notice.howAccessWorks': 'ප්‍රවේශය ක්‍රියා කරන ආකාරය',
  'notice.rolesMoh': 'MOH නිලධාරීන්, ප්‍රාදේශීය සෞඛ්‍ය නිලධාරීන් සහ ජාතික පරිපාලකයන්',
  'notice.rolesHospital': 'රෝහල් කාර්ය මණ්ඩලය, MOH නිලධාරීන් සහ ජාතික පරිපාලකයන්',
  'notice.rolesAdmin': 'ජාතික පරිපාලකයන්',
};

const ta: Dictionary = {
  'banner.official': 'இது ஒரு அதிகாரப்பூர்வ தளம் —',
  'banner.government': 'இலங்கை அரசாங்கம்',
  'banner.howYouKnow': 'இதை உறுதிசெய்வது எப்படி',
  'banner.operatedTitle': 'சுகாதார அமைச்சினால் இயக்கப்படுகிறது',
  'banner.operatedBody':
    'இங்கு வெளியிடப்படும் முன்னறிவிப்புகள், தலையீட்டு விளைவுகள் மற்றும் வளஒதுக்கீடுகள் சுகாதார அமைச்சின் டெங்கு முடிவெடுப்பு ஆதரவு அமைப்பினால் உருவாக்கப்படுகின்றன. அனைத்து மூலங்களும் ஒவ்வொரு பக்கத்தின் அடிப்பகுதியிலும் பெயரிடப்பட்டுள்ளன.',
  'banner.accessTitle': 'பொதுத் தகவல் திறந்தது; ஊழியர் தரவு அல்ல',
  'banner.accessBody':
    'மாவட்ட அபாயத்தைப் பார்க்க கணக்கு தேவையில்லை. மருத்துவமனை, மாவட்ட நடவடிக்கை மற்றும் நிர்வாகத் தரவுக்கு ஊழியர் கணக்கு தேவை; அதன் மாவட்ட வரம்பை நிர்வாகி நிர்ணயிக்கிறார் — உள்நுழைபவர் அல்ல.',
  'banner.language': 'மொழி',

  'site.ministry': 'சுகாதார அமைச்சு · இலங்கை',
  'nav.national': 'தேசிய பொதுநோக்கு',
  'nav.public': 'எனது மாவட்டம்',
  'nav.hospital': 'மருத்துவமனை தயார்நிலை',
  'nav.moh': 'மாவட்ட நடவடிக்கைகள்',
  'nav.admin': 'நிர்வாகம்',
  'nav.method': 'முறையியல்',
  'nav.signIn': 'ஊழியர் உள்நுழைவு',
  'nav.signOut': 'வெளியேறு',
  'nav.menuOpen': 'பட்டியைத் திற',
  'nav.menuClose': 'பட்டியை மூடு',
  'nav.skip': 'உள்ளடக்கத்திற்குச் செல்',
  'nav.home': 'முகப்பு',
  'nav.privacy': 'தரவு பாதுகாப்பு அறிவிப்பு',

  'footer.blurb':
    'இலங்கையின் இருபத்தைந்து மாவட்டங்களிலும் டெங்கு கொசு ஒழிப்புக்கான முன்னறிவிப்பு, காரண விளைவு மற்றும் வள ஒதுக்கீடு.',
  'footer.platform': 'தளம்',
  'footer.contact': 'தொடர்பு',
  'footer.sources': 'தரவு மூலங்கள்',
  'footer.rights':
    'சுகாதார அமைச்சு, இலங்கை ஜனநாயக சோசலிசக் குடியரசு. முடிவெடுப்பு ஆதரவுக்கு மட்டுமே — நோயறிதல் கருவி அல்ல.',
  'footer.ambulance': 'சுவசெரிய அம்புலன்ஸ்',
  'footer.ndcu': 'தேசிய டெங்கு ஒழிப்பு அலகு',
  'footer.epid': 'தொற்றுநோயியல் பிரிவு',

  'public.eyebrow': 'பொதுத் தகவல்',
  'public.title': 'நீங்கள் வாழும் இடத்தில் டெங்கு அபாயம்',
  'public.lede':
    'கணக்கு தேவையில்லை. இந்தப் பக்கம் ஒரு மாவட்டத்திற்கான முன்னறிவிப்பையும், அதன் பொருளையும், இந்த வாரம் நீங்கள் செய்யக்கூடியதையும் காட்டுகிறது.',
  'public.yourDistrict': 'உங்கள் மாவட்டம்',
  'public.horizon': 'முன்னறிவிப்பு காலம்',
  'public.weeks': 'வாரங்கள்',
  'public.forecastCases': 'முன்னறிவிக்கப்பட்ட நோயாளிகள்',
  'public.weeksAhead': 'வாரங்களுக்கு முன்னதாக',
  'public.likelyRange': 'சாத்தியமான வரம்பு',
  'public.cases': 'நோயாளிகள்',
  'public.interval': '80% நம்பகத்தன்மை வரம்பு',
  'public.vsAverage': 'கடந்த 4 வார சராசரியுடன் ஒப்பிடும்போது',
  'public.weeklyIncidence': 'வாராந்திர நோய் விகிதம்',
  'public.per100k': '100,000 பேருக்கு',
  'public.rankNationally': 'தேசிய தரவரிசை',
  'public.of': 'இல்',
  'public.population': 'மக்கள்தொகை',
  'public.facilities': 'சுகாதார நிலையங்கள்',
  'public.hospitals': 'மருத்துவமனைகள்',
  'public.whatToDo': 'நீங்கள் செய்ய வேண்டியவை',
  'public.weeklyCasesIn': 'வாராந்திர நோயாளிகள் —',
  'public.casesCaption':
    'தொற்றுநோயியல் பிரிவு வெளியிட்ட அறிவிக்கப்பட்ட நோயாளிகள். இது ஏற்கனவே நடந்தது — மேலே உள்ள முன்னறிவிப்பு அடுத்து வருவது.',
  'public.rainfallTitle': 'இந்த மாவட்டத்தில் மழையும் நோயாளிகளும்',
  'public.rainfallCaption':
    'மழை கலன்களை நிரப்புகிறது, லார்வாக்கள் வளர்கின்றன, கொசுக்கள் உருவாகின்றன — அதன் பிறகுதான் நோய்ப் பரவல் அதிகரிக்கிறது. இந்த மாவட்டத்தில் நோயாளிகள் மழைக்குப் பின் சுமார் 6–8 வாரங்களில் அதிகரிக்கின்றனர்.',
  'public.protectEyebrow': 'உங்களைப் பாதுகாத்துக் கொள்ளுங்கள்',
  'public.protectTitle': 'அறிகுறிகள், தடுப்பு, மற்றும் எப்போது மருத்துவமனை செல்வது',
  'public.symptoms': 'அறிகுறிகள்',
  'public.symptom1': 'கடும் காய்ச்சல், கடுமையான தலைவலி, கண்களுக்குப் பின்னால் வலி',
  'public.symptom2': 'தசை மற்றும் மூட்டு வலி',
  'public.symptom3': 'குமட்டல், வாந்தி, தோல் தடிப்பு',
  'public.warningTitle': 'உடனடியாக மருத்துவமனைக்குச் செல்லுங்கள்',
  'public.warningBody':
    'கடுமையான வயிற்று வலி, தொடர்ச்சியான வாந்தி, ஈறுகள் அல்லது மூக்கில் இரத்தப்போக்கு, வாந்தி அல்லது மலத்தில் இரத்தம், அல்லது அதிகமான மயக்கம். இவை கடுமையான டெங்கு நோயின் எச்சரிக்கை அறிகுறிகள்.',
  'public.prevention': 'தடுப்பு',
  'public.prevent1': 'நீர்க் கலன்களை வாரந்தோறும் காலி செய்து கழுவுங்கள்',
  'public.prevent2': 'நீர்த் தாங்கிகளையும் பீப்பாய்களையும் மூடி வையுங்கள்',
  'public.prevent3': 'கூரை நீர்ப்பாதைகளைச் சுத்தம் செய்யுங்கள்; பழைய டயர்களையும் கலன்களையும் அகற்றுங்கள்',
  'public.prevent4': 'கொசு விரட்டியைப் பயன்படுத்துங்கள் — ஏடிஸ் கொசு பகலில் கடிக்கும்',
  'public.prevent5': 'ஜன்னல் மற்றும் கதவுகளுக்கு வலைகளைப் பொருத்துங்கள்',
  'public.emergency': 'அவசர நிலை',
  'public.reportBreeding':
    'கொசு உற்பத்தி இடத்தை உங்கள் பொது சுகாதார பரிசோதகருக்குத் தெரிவியுங்கள்.',
  'public.disclaimerTitle': 'இது முடிவெடுப்பு ஆதரவு, நோயறிதல் அல்ல.',
  'public.disclaimerBody':
    'இந்த முன்னறிவிப்பு மாவட்ட அளவிலான அபாயத்தை விவரிக்கிறது, உங்கள் தனிப்பட்ட அபாயத்தை அல்ல. அறிகுறிகள் இருந்தால் மருத்துவரை அணுகுங்கள் — இந்தப் பக்கத்தின் எண்கள் மாறும் வரை காத்திருக்க வேண்டாம்.',

  'myth.title': 'கட்டுக்கதையும் உண்மையும்',
  'myth.label': 'கட்டுக்கதை',
  'fact.label': 'உண்மை',
  'myth.1': 'டெங்கு கொசுக்கள் இரவில் கடிக்கும்.',
  'fact.1':
    'ஏடிஸ் ஏஜிப்டை கொசு முக்கியமாகப் பகலில், அதிகாலையிலும் மாலையிலும் கடிக்கிறது. கொசுவலை மட்டும் உங்களைப் பாதுகாக்காது.',
  'myth.2': 'டெங்கு கொசு அழுக்கு நீரில் மட்டுமே உற்பத்தியாகும்.',
  'fact.2':
    'அது சுத்தமான, தேங்கிய நீரையே விரும்புகிறது — உங்கள் நீர்த் தாங்கி, செடித் தட்டுகள், வாளிகளில் தேங்கும் நீர்.',
  'myth.3': 'டெங்கு ஒருமுறை மட்டுமே வரும்.',
  'fact.3':
    'நான்கு வகை டெங்கு வைரஸ்கள் உள்ளன. வேறு வகையால் இரண்டாவது முறை தொற்று ஏற்பட்டால் கடுமையான நோய்க்கான அபாயம் அதிகம்.',

  'alerts.title': 'உங்கள் மாவட்டத்திற்கான எச்சரிக்கைகளைப் பெறுங்கள்',
  'alerts.districts': 'மாவட்டங்கள்',
  'alerts.weekly': 'வாராந்திர முன்னறிவிப்புச் சுருக்கம்',
  'alerts.outbreakOnly': 'நோய்ப் பரவல் எச்சரிக்கைகள் மட்டும்',
  'alerts.email': 'மின்னஞ்சல் முகவரி',
  'alerts.save': 'குழுசேர்',
  'alerts.saved': 'இந்த உலாவியில் சேமிக்கப்பட்டது.',
  'alerts.subscribedTitle': 'குழுசேர்க்கப்பட்டது',
  'alerts.subscribed': 'அடுத்த வாராந்திர புதுப்பிப்பில் உங்களுக்குத் தெரிவிக்கப்படும்.',
  'alerts.noticeTitle': 'நீங்கள் பெறுவது',
  'alerts.noticeBody':
    'உண்மையான குழுசேர்க்கைகள், உண்மையாகவே சேமிக்கப்பட்டு, ஒவ்வொரு வாரமும் தரவைப் புதுப்பிக்கும் அதே திட்டமிடப்பட்ட பணியால் அனுப்பப்படுகின்றன. கணக்கு தேவையில்லை — உங்கள் விருப்பங்களை மாற்ற எப்போது வேண்டுமானாலும் இந்த படிவத்தை மீண்டும் சமர்ப்பிக்கவும்.',

  'risk.low': 'குறைவு',
  'risk.moderate': 'மிதமான',
  'risk.high': 'அதிகம்',
  'risk.severe': 'மிக அதிகம்',

  'common.translationNote': 'ஊழியர் பக்கங்களும் தொழில்நுட்பப் பக்கங்களும் ஆங்கிலத்தில் மட்டுமே.',
  'rec.use-repellent-and-cover-arms-and-legs-during-the-day.action':
    'பகலில் கொசு விரட்டியைப் பயன்படுத்தி கை கால்களை மூடி வையுங்கள்',
  'rec.use-repellent-and-cover-arms-and-legs-during-the-day.rationale':
    'ஏடிஸ் கொசு பகலில், குறிப்பாக அதிகாலையிலும் மாலையிலும் கடிக்கிறது — இரவில் கடிக்கும் மலேரியா கொசுவைப் போலல்லாமல். எனவே கொசுவலை மட்டும் போதாது.',
  'rec.fit-window-screens-and-use-mosquito-coils-indoors.action':
    'ஜன்னல்களுக்கு வலைகளைப் பொருத்தி வீட்டுக்குள் கொசுச் சுருள்களைப் பயன்படுத்துங்கள்',
  'rec.fit-window-screens-and-use-mosquito-coils-indoors.rationale':
    'இலங்கையில் டெங்கு பரவல் பெரும்பாலும் வீடுகளைச் சுற்றியே நிகழ்கிறது; பெரும்பாலான தொற்றுகள் வீட்டிலும் அதன் அருகிலும் ஏற்படுகின்றன.',
  'rec.remove-standing-water-around-your-home-weekly.action':
    'வீட்டைச் சுற்றித் தேங்கியுள்ள நீரை வாரந்தோறும் அகற்றுங்கள்',
  'rec.remove-standing-water-around-your-home-weekly.rationale':
    'ஏடிஸ் ஏஜிப்டை கொசு கலன்களில் உள்ள சுத்தமான நீரில் உற்பத்தியாகிறது — டயர்கள், தாங்கிகள், செடித் தட்டுகள், நீர்ப்பாதைகள். உற்பத்தி இடங்களை அகற்றுவதே வீட்டு மட்டத்தில் செய்யக்கூடிய மிகவும் பயனுள்ள செயல்.',
  'rec.seek-medical-care-for-fever-lasting-more-than-two-days.action':
    'இரண்டு நாட்களுக்கு மேல் நீடிக்கும் காய்ச்சலுக்கு மருத்துவ சிகிச்சை பெறுங்கள்',
  'rec.seek-medical-care-for-fever-lasting-more-than-two-days.rationale':
    'விரைவில் மருத்துவரை அணுகுவதே டெங்கு இரத்தக்கசிவுக் காய்ச்சலைத் தடுக்கிறது; கடுமையான நோய் பெரும்பாலும் தாமதமான திரவ மேலாண்மையின் விளைவே.',
  'home.eyebrow': 'தேசிய டெங்கு முடிவெடுப்பு ஆதரவு',
  'home.title': 'நோய்ப் பரவலுக்கு முன்னரே கொசு ஒழிப்புக் குழுக்களை அனுப்புங்கள், பின்னர் அல்ல.',
  'home.lede':
    'டெங்குசென்டினல் இரண்டு முதல் நான்கு வாரங்கள் முன்னதாக மாவட்ட டெங்கு அபாயத்தை முன்னறிவித்து, ஒரு தலையீடு உண்மையில் என்ன தடுக்கும் என்பதை மதிப்பிட்டு, மிக அதிக நோயாளிகளைத் தடுக்கும் இடங்களுக்குக் குழுக்களை ஒதுக்குகிறது.',
  'home.reactingQuote':
    'வாராந்திர அறிவிப்புத் தரவில் ஒரு பரவல் தோன்றும் நேரத்தில், பரவல் ஏற்கனவே இரண்டு முதல் மூன்று வாரங்களாக நடந்து கொண்டிருக்கிறது. அந்தத் தரவுக்கு பதிலளிப்பது என்பது இரண்டு வாரங்கள் பழைய நிலைமைக்கு பதிலளிப்பதாகும்.',
  'home.viewNational': 'தேசிய பொதுநோக்கைப் பார்க்கவும்',
  'home.checkDistrict': 'எனது மாவட்டத்தைச் சரிபார்க்கவும்',
  'home.currentForecast': 'தற்போதைய முன்னறிவிப்பு',
  'home.weeksAhead': 'வாரங்களுக்கு முன்னதாக',
  'home.targetWeek': 'இலக்கு வாரம்',
  'home.forecastCasesNationwide': 'முன்னறிவிக்கப்பட்ட நோயாளிகள், நாடு முழுவதும்',
  'home.districtsHighRisk': 'அதிக அபாயம் அல்லது அதற்கு மேற்பட்ட மாவட்டங்கள்',
  'home.highestRiskDistrict': 'மிக அதிக அபாயமுள்ள மாவட்டம்',
  'home.per100kWeek': '100,000 பேருக்கு/வாரத்திற்கு',
  'home.modelledNote': 'மாதிரியிலிருந்து பெறப்பட்ட புள்ளிவிவரங்கள்',
  'home.modelledNote2':
    'மாதிரி. இந்தத் தளத்தில் உள்ள ஒவ்வொரு அளவும் அது அவதானிக்கப்பட்டதா, மாதிரியாக்கப்பட்டதா, அல்லது திட்டமிடல் மதிப்பீடா என்பதைக் குறிப்பிடுகிறது.',
  'home.simulatedTitle': 'உருவகப்படுத்தப்பட்ட தரவு',
  'home.simulatedBody':
    'இந்த இயக்கம் செயற்கைத் தரவுத் தொகுப்பைப் பயன்படுத்தியது — யதார்த்தமான இயக்கவியல், ஆனால் அவதானிப்புகள் அல்ல. இங்குள்ள எந்த எண்ணையும் உண்மையான தொற்றுநோயியலாகக் கருத வேண்டாம். இயக்கவும்',
  'home.simulatedBody2': 'நேரடி புள்ளிவிவரங்களுக்கு.',
  'home.realTitle': 'உண்மையான தரவு',
  'home.realBody': 'தொற்றுநோயியல் பிரிவின் WER அறிக்கைகள் மற்றும் Open-Meteo, இயக்கம் நடத்தப்பட்டது',
  'home.realBody2': '. முழு மூல தகவல் நிர்வாகத் தளத்தில் உள்ளது.',
  'home.snapshotEyebrow': 'தேசிய பொதுநோக்கு',
  'home.snapshotTitle': 'டெங்கு அடுத்து எங்கு செல்கிறது',
  'home.snapshotDescription':
    'அனைத்து {n} மாவட்டங்களும், {h} வாரங்களுக்கு முன்னதாக. நோயாளிகள் எண்ணிக்கையை விட 100,000 பேருக்கான விகிதத்தால் தரவரிசைப்படுத்தப்பட்டுள்ளது, இதனால் ஒரு சிறிய மாவட்டத்தின் பரவல் கொழும்பின் மக்கள்தொகைக்குப் பின்னால் மறைக்கப்படாது.',
  'home.fullOverview': 'முழு பொதுநோக்கு',
  'home.districtsForecast': 'முன்னறிவிக்கப்பட்ட மாவட்டங்கள்',
  'home.highRiskOrAbove': 'அதிக அபாயம் அல்லது அதற்கு மேல்',
  'home.aboveThreshold': '100,000 பேருக்கு 3.5 அல்லது அதற்கு மேல்/வாரத்திற்கு',
  'home.forecastCases': 'முன்னறிவிக்கப்பட்ட நோயாளிகள்',
  'home.nationwide': 'நாடு முழுவதும்',
  'home.casesLastWeek': 'கடந்த வார நோயாளிகள்',
  'home.notifiedNationwide': 'நாடு முழுவதும் அறிவிக்கப்பட்டது',
  'home.districtsUnit': 'மாவட்டங்கள்',
  'home.ofTwentyFive': '25இல்',
  'home.readEyebrow': 'இந்தத் தளத்தை எப்படிப் படிப்பது',
  'home.readTitle': 'மூன்று வெவ்வேறு வகையான எண்கள், ஒருபோதும் ஒரே மாதிரி காட்டப்படாது',
  'home.readDescription':
    'ஒரு அளவீட்டின் பாணியிலேயே காட்டப்படும் திட்டமிடல் மதிப்பீடு அதன் நம்பகத்தன்மையைக் கடன் வாங்குகிறது — ஒரு முடிவெடுப்பு ஆதரவுக் கருவி தவறான முடிவுக்கு வழிவகுப்பது இப்படித்தான். மூல தகவல் இங்கே குறியீட்டில் அமல்படுத்தப்பட்டுள்ளது, ஒழுக்கத்தால் அல்ல.',
  'home.tier': 'நிலை',
  'home.example': 'உதாரணம்:',
  'home.example1': '1,231 சுகாதார நிலையங்கள்; 1,000 பேருக்கு 3.93 படுக்கைகள்.',
  'home.example2': 'நோயாளிகள் முன்னறிவிக்கப்பட்டுள்ளனர்',
  'home.example3': 'இல்',
  'home.example3b': 'வாரங்களில்.',
  'home.example4':
    'வெளியிடப்பட்ட மருத்துவ விகிதங்களை ஒரு முன்னறிவிப்புக்குப் பயன்படுத்தி பெறப்பட்ட அனுமதிகள் மற்றும் பிளேட்லெட் அலகுகள்.',
  'home.noDataTitle': 'பொதுத் தரவு இல்லாத இடத்தில், தளம் அதைத் தெரிவிக்கிறது.',
  'home.noDataBody':
    'நேரடி படுக்கை ஆக்கிரமிப்பு, ஐசியு எண்ணிக்கை, பிளேட்லெட் கையிருப்பு, பணியாளர் பட்டியல்கள் மற்றும் ஆம்புலன்ஸ் இருப்பிடங்கள் இலங்கைக்கு வெளியிடப்படவில்லை. அந்தப் பலகங்கள் ஒரு விளக்கத்தையும் அதை இயக்கக்கூடிய தரவு ஊட்டத்தையும் பெயரிடுகின்றன, நம்பகமான தோற்றமுடைய எண்ணை அல்ல.',
  'home.rolesEyebrow': 'பங்கு அடிப்படையிலான அணுகல்',
  'home.rolesTitle': 'ஒரு இயந்திரத்தின் மேல் நான்கு தளங்கள்',
  'home.rolesDescription':
    'அனுமதிகள் தரவரிசையால் கூட்டப்படும்; வரம்பு அவற்றிலிருந்து தனியானது. ஒரு மருத்துவமனை நிர்வாகியும் ஒரு MOH அதிகாரியும் முற்றிலும் வேறுபட்ட வரிசைகளைக் காணும்போது ஒன்றுடன் ஒன்று சேரும் அனுமதிகளை வைத்திருக்கலாம்.',
  'home.role.public.title': 'பொது மக்கள்',
  'home.role.public.access': 'கணக்கு தேவையில்லை',
  'home.role.public.description':
    'நீங்கள் வாழும் இடத்தில் அபாயம், முன்னறிவிப்பின் பொருள், தடுப்பு ஆலோசனை மற்றும் அருகிலுள்ள மருந்தகங்கள்.',
  'home.role.hospital.title': 'மருத்துவமனை ஊழியர்',
  'home.role.hospital.access': 'ஊழியர் கணக்கு',
  'home.role.hospital.description':
    'அனுமதி மற்றும் கடுமையான நோய் மதிப்பீடுகள், படுக்கை அழுத்தம், மற்றும் வரும் வாரங்களுக்கான வழங்கல் திட்டமிடல்.',
  'home.role.moh.title': 'MOH / பிராந்திய அதிகாரி',
  'home.role.moh.access': 'ஊழியர் கணக்கு',
  'home.role.moh.description':
    'உங்கள் மாவட்டத்திற்கான குழு ஒதுக்கீடு, தலையீட்டுத் திட்டமிடல், சூழ்நிலை ஒப்பீடு மற்றும் பட்ஜெட் பிரிவு.',
  'home.role.admin.title': 'தேசிய நிர்வாகி',
  'home.role.admin.access': 'அமைச்சு கணக்கு',
  'home.role.admin.description':
    'நாடு தழுவிய செயல்பாடுகள், மாதிரி உள்ளமைவு, தரவு மூல தகவல், பயனர் மேலாண்மை மற்றும் தணிக்கை பதிவு.',
  'home.open': 'திற',
  'home.engineEyebrow': 'இயந்திரம்',
  'home.engineTitle': 'முன்னறிவிப்பு → காரண விளைவு → ஒதுக்கீடு',
  'home.engineLede':
    'ஒரு முன்னறிவிப்பு மட்டும் ஒரு குழுவை எங்கு அனுப்புவது என்று சொல்ல முடியாது. அதிக நோயாளிகள் கொண்ட மாவட்டத்தை அறிவது, ஒரு தலையீடு அதிகம் தடுக்கும் இடத்தை அறிவதற்குச் சமமல்ல — அதற்கு ஒரு விளைவு மதிப்பீடும் ஒரு கட்டுப்படுத்தப்பட்ட ஒதுக்கீடும் தேவை.',
  'home.stage1.title': 'நிகழ்தகவு முன்னறிவிப்பு',
  'home.stage1.body':
    'ஒவ்வொரு அடிப்படை மாதிரியும் சுழலும் தோற்ற புள்ளிகளில் பின்சோதிக்கப்பட்ட, 80% நம்பகத்தன்மை வரம்புடன் கூடிய மாவட்ட நோயாளர் முன்னறிவிப்புகள்.',
  'home.stage2.title': 'இயந்திரவியல் விளைவு',
  'home.stage2.body':
    'மாவட்டத்தின் சொந்த வரலாற்றுக்கு பொருத்தப்பட்ட SEI-SIR மாதிரி, குறிப்பிட்ட எண்ணிக்கையிலான குழு-வாரங்களால் தடுக்கக்கூடிய நோயாளர்களை மதிப்பிடுகிறது.',
  'home.stage3.title': 'கட்டுப்படுத்தப்பட்ட ஒதுக்கீடு',
  'home.stage3.body':
    'ஒரு முழு எண் திட்டம் நிலையான குழு பட்ஜெட்டை மொத்த எதிர்பார்க்கப்படும் தடுக்கப்பட்ட நோயாளர்களை அதிகரிக்க பகிர்ந்தளிக்கிறது, வள வசதி குறைந்த மாவட்டங்களுக்கான சமநிலை வரம்புடன்.',
  'home.howBuilt': 'மாதிரிகள் எவ்வாறு கட்டமைக்கப்பட்டு சரிபார்க்கப்படுகின்றன',
  'home.noDataYetTitle': 'இதுவரை பைப்லைன் தரவு இல்லை',
  'home.noDataYetBody':
    'இந்த செயலி Python பைப்லைனால் எழுதப்பட்ட கோப்புகளை காட்டுகிறது. அவற்றை உருவாக்கி, பின்னர் உலாவிக்கு ஏற்றுமதி செய்யுங்கள்:',
  'home.noDataYetNote': 'இரண்டும் செயற்கைத் தரவுத் தொகுப்புக்கு எதிராக முழுமையாக இணைப்பில்லாமல் இயங்குகின்றன.',
  'nat.crumb': 'தேசிய பொதுநோக்கு',
  'nat.eyebrow': 'தேசிய பொதுநோக்கு',
  'nat.title': 'ஒவ்வொரு மாவட்டமும், முன்னறிவிக்கப்பட்ட அபாயத்தால் தரவரிசைப்படுத்தப்பட்டுள்ளது',
  'nat.description':
    'ஒவ்வொரு பங்கிற்கும் ஒரே மாதிரி: பங்கு-குறிப்பிட்ட எதுவும் காட்சியைக் குறுக்குவதற்கு முன், அனைத்து 25 மாவட்டங்களும். {week} வாரம்.',
  'nat.metaModel': 'மாதிரி',
  'nat.metaPanel': 'தரவுத் தொகுப்பு',
  'nat.metaPipelineRun': 'பைப்லைன் இயக்கம்',
  'nat.simulatedTitle': 'உருவகப்படுத்தப்பட்ட தரவு',
  'nat.simulatedBody':
    'இந்த இயக்கம் செயற்கைத் தரவுத் தொகுப்பைப் பயன்படுத்தியது. யதார்த்தமான இயக்கவியல், ஆனால் அவதானிப்புகள் அல்ல — கீழே உள்ள எந்த எண்ணையும் உண்மையான தொற்றுநோயியலாகக் கருத வேண்டாம்.',
  'nat.veryHigh': 'மிக அதிகம்',
  'nat.high': 'அதிகம்',
  'nat.hindsightEyebrow': 'பின்னோக்கிப் பார்வை',
  'nat.hindsightTitle': 'முன்னறிவிப்பு உண்மையில் எப்படி இருந்தது',
  'nat.hindsightDescription':
    'தரவுத் தொகுப்பின் எந்த வாரத்திற்கும் நகர்த்தவும். இடது வரைபடம் அறிவிக்கப்பட்டதைக் காட்டுகிறது; வலது வரைபடம் மாதிரி {h} வாரங்களுக்கு முன்னர் நின்று, இடையேயுள்ள எந்தத் தரவையும் காணாமல், அதே வாரத்திற்குக் கூறியதைக் காட்டுகிறது.',
  'nat.chartObservedForecast': 'தேசிய நோயாளிகள்: அவதானிக்கப்பட்டது மற்றும் முன்னறிவிக்கப்பட்டது',
  'nat.chartObservedForecastCaption':
    'திடமான கோடு: அவதானிக்கப்பட்ட அறிவிப்புகள். இடைவெளி கோடு பட்டையுடன்: மாவட்டங்கள் முழுவதும் கூட்டப்பட்ட முன்னறிவிப்பு நடுநிலை மற்றும் 80% நம்பகத்தன்மை வரம்பு.',
  'nat.chartRainfall': 'மழையும் நோயாளிகளும்',
  'nat.chartRainfallCaption':
    'நோயாளிகள் மழைக்குப் பின் சுமார் 6-8 வாரங்களில் பின்தொடர்கின்றனர்: மழை கலன்களை நிரப்புகிறது, லார்வாக்கள் வளர்கின்றன, கொசுக்கள் உருவாகின்றன, அதன் பிறகுதான் பரவல் அதிகரிக்கிறது. அந்த தாமதமே இரண்டு வாரங்களுக்கு முன்னதான முன்னறிவிப்பை சாத்தியமாக்குகிறது.',
  'nat.backtestEyebrow': 'பின்சோதனை',
  'nat.backtestTitle': 'ஏன் இந்த மாதிரி',
  'nat.backtestDescription':
    '{h} வாரங்களுக்கு முன்னதாக சுழலும் தோற்றப் புள்ளிகளில் சராசரி {metric} — குறைவானது சிறந்தது. ஒவ்வொரு அடிப்படை மாதிரியும் ஒவ்வொரு தோற்றப் புள்ளியிலும் மீண்டும் பொருத்தப்படுகிறது, எனவே எந்த மாதிரியும் அது முன்னறிவிக்கும் வாரத்திற்குப் பிந்தைய தரவைக் காணாது.',
  'nat.modelComparison': 'மாதிரி ஒப்பீடு',
  'nat.noBacktestScores': 'இந்த ஏற்றுமதியில் பின்சோதனை மதிப்பெண்கள் இல்லை.',
  'nat.intervalMeaningTitle': 'வரம்பு என்றால் என்ன',
  'nat.intervalMeaningBody':
    'ஒவ்வொரு மாவட்ட முன்னறிவிப்பும் ஒரு புள்ளி அல்ல, குவாண்டைல்களின் தொகுப்பு. 80% வரம்பு என்பது ஐந்து வாரங்களில் நான்கு வாரங்களுக்கு உண்மையான எண்ணிக்கை அதற்குள் விழும் என்று மாதிரி எதிர்பார்க்கிறது என்பதைக் குறிக்கிறது — ஒரு திட்டம் எவ்வளவு தளர்வைக் கொண்டிருக்க வேண்டும் என்பதை நிர்ணயிக்க வேண்டியது அந்த வரம்பின் அகலமே, நடுநிலை அல்ல.',
  'nat.widestInterval': 'மிக அகன்ற வரம்பு',
  'nat.backtestFolds': 'பின்சோதனை மடிப்புகள்',
  'nat.panelWindow': 'தரவுத் தொகுப்பு காலம்',
  'nat.districtWeeks': 'மாவட்ட-வாரங்கள்',
  'nat.detailEyebrow': 'விவரம்',
  'nat.detailTitle': 'அனைத்து மாவட்டங்களும்',
  'nat.detailDescription':
    'இந்த காலத்தில் ஒவ்வொரு மாவட்டத்திற்கும் முன்னறிவிப்பு, வரம்பு, மக்கள்தொகை மற்றும் சுகாதார நிலைய எண்ணிக்கை.',
  'nat.reportEyebrow': 'அறிக்கை',
  'nat.reportTitle': 'இதை ஒரு ஆவணமாக எடுத்துச் செல்லுங்கள்',
  'nat.reportDescription':
    'இந்த பொதுநோக்கின் PDF பிரதி: தளத்திற்கு வெளியே பகிர்வதற்கு, அதே முதன்மை எண்கள் மற்றும் தரவரிசைப்படுத்தப்பட்ட மாவட்ட அட்டவணை, அதே தரவு மூல எச்சரிக்கையுடன்.',
  'nat.riskMap': 'அபாய வரைபடம்',
  'nat.everyDistrictRanked': 'ஒவ்வொரு மாவட்டமும், தரவரிசைப்படுத்தப்பட்டுள்ளது',
  'nat.weeksAheadClick': 'வாரங்களுக்கு முன்னதாக · ஒரு மாவட்டத்தைக் கிளிக் செய்யவும்',
  'nat.per100kWeekUnit': '100,000 பேருக்கு/வாரத்திற்கு',
  'nat.openDistrict': 'மாவட்டத்தைத் திற',
  'nat.col.district': 'மாவட்டம்',
  'nat.col.risk': 'அபாயம்',
  'nat.col.forecastCases': 'முன்னறிவிக்கப்பட்ட நோயாளிகள்',
  'nat.col.interval80': '80% நம்பகத்தன்மை வரம்பு',
  'nat.col.per100k': '100,000 பேருக்கு/வாரத்திற்கு',
  'nat.col.population': 'மக்கள்தொகை',
  'nat.col.facilities': 'நிலையங்கள்',
  'nat.report.filePrefix': 'தேசிய பொதுநோக்கு —',
  'nat.report.desc': 'PDF · முதன்மை எண்கள் மற்றும் அனைத்து 25 மாவட்டங்களும் தரவரிசைப்படுத்தப்பட்டவை',
  'nat.report.pipelineRun': 'பைப்லைன் இயக்கம்',
  'nat.report.download': 'அறிக்கையைப் பதிவிறக்கு',
  'hist.viewPastWeek': 'கடந்த வாரத்தைப் பார்க்கவும்',
  'hist.description': 'ஒரே வாரம் இரண்டு முறை காணப்படுகிறது: எது அறிவிக்கப்பட்டது, மற்றும் மாதிரி என்ன கூறியது',
  'hist.weeksEarlier': 'வாரங்களுக்கு முன்.',
  'hist.weekBeginning': 'தொடங்கும் வாரம்',
  'hist.previousWeek': 'முந்தைய வாரம்',
  'hist.nextWeek': 'அடுத்த வாரம்',
  'hist.weekLabel': 'வாரம்',
  'hist.backtestedTicks': 'பின்சோதனை செய்யப்பட்ட முன்னறிவிப்புள்ள வாரங்கள்',
  'hist.observed': 'அவதானிக்கப்பட்டது',
  'hist.predictedAhead': 'முன்னறிவிக்கப்பட்டது,',
  'hist.noNotifiedCases': 'இந்த வாரத்திற்கு அறிவிக்கப்பட்ட நோயாளிகள் இல்லை.',
  'hist.casesThatWeek': 'அந்த வார நோயாளிகள்',
  'hist.predictedCases': 'முன்னறிவிக்கப்பட்ட நோயாளிகள்',
  'hist.highestRisk': 'மிக அதிக அபாயம்',
  'hist.under': 'குறைவு',
  'hist.per100kWkUnit': '100,000 பேருக்கு/வாரத்திற்கு',
  'hist.noPredictionForWeek':
    'இந்த காலத்தில் இந்த வாரத்திற்கு பின்சோதனை செய்யப்பட்ட முன்னறிவிப்பு இல்லை. முன்னறிவிக்கப்பட்ட தொடர் அவதானிக்கப்பட்டதை விட குறுகிய காலத்தை உள்ளடக்கியது.',
  'crumb.public': 'எனது மாவட்டத்தில் டெங்கு அபாயம்',
  'prov.observed': 'அவதானிக்கப்பட்டது',
  'prov.modelled': 'மாதிரியாக்கப்பட்டது',
  'prov.assumed': 'திட்டமிடல் மதிப்பீடு',
  'prov.user_input': 'நீங்கள் உள்ளிட்டது',

  // --- Method page ----------------------------------------------------------
  'method.crumb': 'இது எவ்வாறு செயல்படுகிறது',
  'method.eyebrow': 'முறை',
  'method.title': 'இந்த தளம் எதையும் எவ்வாறு தீர்மானிக்கிறது',
  'method.description':
    'மூன்று கட்டங்கள், ஒவ்வொன்றும் முந்தையது பதிலளிக்க முடியாத கேள்விக்கு பதிலளிக்கிறது. அதிக நோயாளர்கள் இருக்கும் மாவட்டத்தை அறிவது, ஒரு குழு அதிக பயனை அளிக்கும் இடத்தை அறிவதற்கு சமமல்ல.',
  'method.metaPanel': 'தரவுத்தொகுதி',
  'method.metaDistrictWeeks': 'மாவட்ட-வாரங்கள்',
  'method.metaLastRun': 'கடைசி இயக்கம்',
  'method.engineEyebrow': 'இயந்திரம்',
  'method.engineTitle': 'முன்னறிவிப்பு → காரண விளைவு → ஒதுக்கீடு',
  'method.engineDescription':
    'ஒவ்வொரு கட்டமும் ஒரு கலைப்பொருளை (artifact) எழுதுகிறது. டாஷ்போர்டு அந்த கலைப்பொருள்களை படிக்கிறது, ஒருபோதும் மீண்டும் கணக்கிடுவதில்லை — இதனால்தான் ஒரு பரவலின்போது இங்கு ஒரு சறுக்கியை நகர்த்துவது உடனடியாக இருக்கிறது.',
  'method.stage1': 'கட்டம் 1',
  'method.stage1Title': 'நிகழ்தகவு மாவட்ட முன்னறிவிப்புகள்',
  'method.stage1Body':
    'ஒரு க்வாண்டைல் மாதிரி ஒவ்வொரு மாவட்டத்திற்கும் இரண்டு முதல் நான்கு வாரங்கள் முன்கூட்டியே ஒரு நடுநிலை மற்றும் 80% இடைவெளியை உருவாக்குகிறது. பருவகால நேரடி, SARIMA, க்ரேடியன்ட் பூஸ்டிங் உள்ளிட்ட ஒவ்வொரு அடிப்படை மாதிரியும் ஒவ்வொரு உருள்-தோற்ற மடிப்பிலும் மீண்டும் பொருத்தப்படுகிறது — எனவே எந்த மாதிரியும் அது முன்னறிவிக்கும் வாரத்திற்குப் பிறகான தரவை ஒருபோதும் காணாது. தேசிய கண்ணோட்டத்தில் உள்ள ஒப்பீட்டு அட்டவணை அந்த பின்சோதனையே, ஒரு கூற்று அல்ல.',
  'method.stage1DetailTemplate': '2 வாரங்களில் {metric} அடிப்படையில் சிறந்தது: {list}.',
  'method.stage2': 'கட்டம் 2',
  'method.stage2Title': 'இயந்திரவியல் தலையீட்டு விளைவு',
  'method.stage2Body':
    'ஒரு பிரிவு-அடிப்படையிலான SEI-SIR மாதிரி ஒவ்வொரு மாவட்டத்திற்கும் அதன் சொந்த வரலாற்றுக்கு எதிராக பொருத்தப்பட்டு, பின்னர் வெக்டர் கட்டுப்பாடு பயன்படுத்தப்பட்டு மீண்டும் ஒருங்கிணைக்கப்படுகிறது. இரண்டு ஒருங்கிணைப்புகளுக்கும் இடையிலான வேறுபாடே கொடுக்கப்பட்ட குழு-வார எண்ணிக்கைக்கு தவிர்க்கப்பட்ட நோயாளர்கள் — இது ஒரு காரண அளவு, முன்னறிவிப்பில் இருந்து படிக்கப்படும் தொடர்பு அல்ல.',
  'method.stage2DetailTemplate':
    'விளைவுகள் {horizon} வார எல்லைக்கு மேல் கணக்கிடப்பட்டு ஒவ்வொரு மாவட்டத்திற்கும் ஒரு வளைவாக சேமிக்கப்படுகின்றன — இதுவே அடுத்த குழு-வாரத்தின் விளிம்பு வருமானத்தை உடனடியாக கிடைக்கச் செய்கிறது.',
  'method.stage3': 'கட்டம் 3',
  'method.stage3Title': 'கட்டுப்படுத்தப்பட்ட ஒதுக்கீடு',
  'method.stage3Body':
    'ஒரு முழு எண் திட்டம் நிலையான வாராந்திர குழு பட்ஜெட்டை, கட்டம் 2இன் விளைவு வளைவுகளுக்கும் வசதி குறைந்த மாவட்டங்களுக்கான சமத்துவ எல்லைக்கும் உட்பட்டு, மொத்த எதிர்பார்க்கப்படும் தவிர்க்கப்பட்ட நோயாளர்களை அதிகரிக்க பகிர்கிறது. அந்த எல்லையே கொழும்புடன் ஒருபோதும் போட்டியிட முடியாத முழுமையான நோயாளர் எண்ணிக்கை கொண்ட சிறிய, குறைவான சேவை பெறும் மாவட்டங்களை உகப்பாக்கி புறக்கணிக்காமல் தடுக்கிறது.',
  'method.stage3Detail':
    'முழு பட்ஜெட் வரம்பும் ஆஃப்லைனில் தீர்க்கப்பட்டு சேமிக்கப்படுகிறது — எனவே பட்ஜெட் சறுக்கி மீண்டும் தீர்ப்பதற்குப் பதிலாக தீர்வுகளை குறிப்பிடுகிறது.',
  'method.whyForecastEyebrow': 'ஏன் முன்னறிவிக்க வேண்டும்',
  'method.whyForecastTitle':
    'அறிவிப்புகளுக்கு எதிர்வினையாற்றுவது ஒரு பதினைந்து நாட்கள் பழைய படத்திற்கு எதிர்வினையாற்றுவதாகும்',
  'method.whyForecastBody1':
    'வாராந்திர அறிவிப்புத் தரவில் ஒரு அதிகரிப்பு தோன்றும் நேரத்தில், பரவல் ஏற்கனவே இரண்டு முதல் மூன்று வாரங்களாக நடந்துகொண்டிருக்கிறது: ஒரு கொசு வைரஸைப் பெறுகிறது, வெளிப்புற அடைகாப்பு காலம் கடக்கிறது, ஒரு நபர் தொற்றுகிறார், உள் அடைகாப்பு காலம் கடக்கிறது, அவர்கள் சிகிச்சை தேடுகிறார்கள், மற்றும் வழக்கு அறிவிக்கப்படுகிறது. அந்த நேரத்தில் அனுப்பப்படும் குழுக்கள் ஏற்கனவே உடைந்த ஒரு அலையை சிகிச்சை செய்கின்றன.',
  'method.whyForecastBody2':
    'மழையே முன்கூட்டிய சமிக்ஞையை சாத்தியமாக்குகிறது. மழை பாத்திரங்களை நிரப்புகிறது, லார்வாக்கள் வளர்கின்றன, வயது வந்தவை வெளிப்படுகின்றன, அதன் பிறகுதான் பரவல் அதிகரிக்கிறது — முன்னறிவிப்பு பயன்படுத்தும் தோராயமாக ஆறு முதல் எட்டு வாரங்கள் தாமதம்.',
  'method.riskBandsEyebrow': 'அபாய நிலைகள்',
  'method.riskBandsTitle': 'ஏன் வழக்கு எண்ணிக்கை அல்ல, பரவல் விகிதம்',
  'method.riskBandsDescription':
    'கொழும்பில் 2.48 மில்லியன் குடியிருப்பாளர்கள் உள்ளனர், முல்லைத்தீவில் சுமார் 100,000 பேர் உள்ளனர். மாவட்டங்களை மூல எண்ணிக்கை மூலம் தரவரிசைப்படுத்துவது ஆண்டின் ஒவ்வொரு வாரமும் கொழும்பை சிவப்பாக வரைந்து, உண்மையான முல்லைத்தீவு பரவலை பச்சையாக விடும்.',
  'method.riskBandBelow': '1.5க்கு கீழ்',
  'method.riskBandAndAboveTemplate': '{threshold} மற்றும் அதற்கு மேல்',
  'method.riskBandPerWeek': '100,000 பேருக்கு வாரத்திற்கு',
  'method.riskBandsCalloutPrefix': 'இவை ',
  'method.riskBandsCalloutBold': 'செயல்பாட்டு திட்டமிடல் வரம்புகள், மருத்துவ தரநிலை அல்ல',
  'method.riskBandsCalloutSuffix':
    '. டெங்கு பரவலை வரையறுக்கும் சர்வதேச அளவில் ஒப்புக் கொள்ளப்பட்ட ஒரு பரவல் வெட்டு-முறை எதுவும் இல்லை — வெளியிடப்பட்ட வரம்புகள் நோய்-பரவல்-குறிப்பிட்டவை மற்றும் பொதுவாக நாடு வாரியாக பெறப்படுகின்றன. அவை உண்மையான மாவட்ட-வார பரவலுக்கு எதிராக மறு அளவீடு செய்யப்பட்டு, மீண்டும் மறு அளவீடு செய்யக்கூடிய மாறிலிகளாக வெளிப்படுத்தப்பட்டுள்ளன.',
  'method.provenanceEyebrow': 'மூலாதாரம்',
  'method.provenanceTitle': 'ஒவ்வொரு அளவும் அது என்ன என்பதைக் கூறுகிறது',
  'method.provenanceDescription':
    'ஒழுக்கத்தால் அல்ல, குறியீட்டால் அமல்படுத்தப்பட்டது: ஒரு திட்டமிடல் மதிப்பீடாக குறிக்கப்பட்ட ஒரு அளவை அதன் அடிப்படையைக் கூறாமல் இயந்திரத்தில் உருவாக்க முடியாது.',
  'method.provenanceCalloutBold': 'பொது தரவு இல்லாத இடத்தில், தளம் அவ்வாறே கூறுகிறது.',
  'method.provenanceCalloutSuffix':
    ' நேரடி படுக்கை ஆக்கிரமிப்பு, ஐசியு கணக்கெடுப்பு, பிளேட்லெட் இருப்பு, பணியாளர் பட்டியல்கள் மற்றும் ஆம்புலன்ஸ் இருப்பிடங்கள் இலங்கைக்கு வெளியிடப்படவில்லை. அந்த பலகங்கள் நம்பகமாகத் தோன்றும் எண்ணிக்கைக்கு பதிலாக, அவற்றை இயக்கக்கூடிய ஊட்டத்தை பெயரிட்டு ஒரு விளக்கத்தை காட்டுகின்றன.',
  'method.accessEyebrow': 'அணுகல்',
  'method.accessTitle': 'அனுமதிகள் கூட்டு; எல்லை தனி',
  'method.accessDescription':
    'ஒரு மருத்துவமனை நிர்வாகியும் ஒரு MOH அதிகாரியும் முற்றிலும் வேறுபட்ட வரிசைகளைப் பார்க்கும் அதே வேளையில் ஒன்றுடன் ஒன்று அனுமதிகளை வைத்திருக்க முடியும் — ஒன்று ஒரு வசதிக்கு உட்பட்டது, மற்றொன்று ஒரு மாவட்டத்திற்கு. இரண்டையும் ஒரே நிலைக்குள் சுருக்குவது ஒரு சுகாதார டாஷ்போர்டு பிராந்தியங்கள் முழுவதும் தரவை கசிய வைக்கும் வழக்கமான வழியாகும்.',
  'method.permissionsCountTemplate': '{n} அனுமதிகள்',
  'method.accessCalloutPrefix': 'பொது பக்கங்கள் ஒரு ',
  'method.accessCalloutBold': 'இயல்பாக-மறுக்கும் துணைக்குழு, ஒரு தணிக்கை அல்ல',
  'method.accessCalloutSuffix':
    '. முழு படத்தையும் கணக்கிட்டு அதன் பகுதிகளை மறைப்பதற்குப் பதிலாக, பொது பங்கு உண்மையில் வைத்திருக்கும் அனுமதிகளின் அடிப்படையில் அவை கட்டமைக்கப்பட்டுள்ளன — எனவே இங்கு ஒரு பிழை மருத்துவமனை ஆக்கிரமிப்பை வெளிப்படுத்துவதற்குப் பதிலாக விடுபட்ட தகவலைக் காட்டுகிறது.',
  'method.decisionSupportTitle': 'முடிவு ஆதரவு, மருத்துவ கருவி அல்ல',
  'method.decisionSupportBody':
    'இந்த தளத்தில் எதுவும் ஒரு நோயாளியை கண்டறியவோ சிகிச்சையை பரிந்துரைக்கவோ செய்யாது. வரையறுக்கப்பட்ட பொது சுகாதார திறனை ஒதுக்க உதவ மாவட்ட அளவிலான அபாயம் மற்றும் வள தாக்கங்களை இது விவரிக்கிறது — மேலும் இது காட்டும் ஒவ்வொரு புள்ளிவிவரமும் அதன் அருகில் கூறப்பட்ட அனுமானத்தைப் போலவே நல்லது.',

  // --- Data protection (PDPA) notice -----------------------------------------
  'privacy.eyebrow': 'சட்டம்',
  'privacy.description':
    'இலங்கையின் 2022ஆம் ஆண்டின் 9ஆம் இலக்க தனிநபர் தரவு பாதுகாப்பு சட்டத்தின் கீழ், இந்த தளம் எதை சேகரிக்கிறது, ஏன், எவ்வளவு காலம் வைத்திருக்கிறது, மற்றும் உங்கள் சொந்த தரவைப் பற்றி எவ்வாறு கேட்பது.',
  'privacy.notice':
    'இந்த அறிவிப்பு கட்டமைக்கப்பட்டவாறு தளத்தை விவரிக்கிறது. கீழே உள்ள எதுவும் இயங்கும் அமைப்பு உண்மையில் செய்வதுடன் பொருந்தாமல் நின்றால், அமைப்பு தவறானது, இந்த அறிவிப்பு அல்ல — அவற்றை மீண்டும் ஒப்புமைக்கு கொண்டு வர, இந்த பக்கத்தை அல்ல, குறியீட்டை புதுப்பிக்கவும்.',
  'privacy.controllerEyebrow': 'கட்டுப்படுத்துபவர்',
  'privacy.controllerTitle': 'இந்த தளத்தை இயக்குபவர் யார்',
  'privacy.controllerBody':
    'இலங்கை சுகாதார அமைச்சகம் கீழே விவரிக்கப்பட்ட தனிநபர் தரவுக்கான கட்டுப்படுத்துபவர் ஆகும். உங்கள் சொந்த தரவு தொடர்பான கோரிக்கைகள் — அணுகல், திருத்தம், அல்லது அது எவ்வாறு பயன்படுத்தப்படுகிறது என்பது பற்றிய கேள்வி — இந்த தளத்தின் அடிக்குறிப்பில் உள்ள தொடர்பு வழிகள் மூலம் அமைச்சகத்திற்கு அனுப்பப்பட வேண்டும்.',
  'privacy.collectedEyebrow': 'சேகரிக்கப்படுவது என்ன',
  'privacy.collectedTitle': 'இந்த தளத்தில் உள்ள இரண்டு வகையான தரவு',
  'privacy.publicDataTitle': 'பொது அபாய தகவல்',
  'privacy.publicDataBody':
    'மாவட்ட அளவிலான முன்னறிவிப்புகள், வழக்கு எண்ணிக்கைகள் மற்றும் அபாய நிலைகள். இது மொத்த தொற்றியல் தரவு — இதில் எந்த தனிநபரும் அடையாளம் காணப்படவில்லை அல்லது அடையாளம் காணக்கூடியதாக இல்லை, மேலும் அதைப் பார்க்க வருபவரிடமிருந்து எந்த தனிப்பட்ட தரவும் சேகரிக்கப்படவில்லை. ஒரு மாவட்டத்தையோ மொழியையோ தேர்ந்தெடுப்பது, மற்றும் நீங்கள் அமைக்கும் எந்த எச்சரிக்கை விருப்பமும் உங்கள் சொந்த உலாவியில் மட்டுமே சேமிக்கப்படுகிறது (கீழே "எச்சரிக்கை விருப்பங்கள்" பார்க்கவும்) மற்றும் இந்த தளத்தின் சேவையகங்களை ஒருபோதும் அடையாது.',
  'privacy.staffDataTitle': 'ஊழியர் கணக்குகள்',
  'privacy.staffDataBody':
    'மருத்துவமனை, மாவட்ட-செயல்பாடுகள் மற்றும் நிர்வாக கணக்குகளுக்கு: ஒரு மின்னஞ்சல் முகவரி, ஒரு காட்சி பெயர், ஒதுக்கப்பட்ட பங்கு, மற்றும் ஒரு மாவட்ட அல்லது வசதி எல்லை. கணக்குகள் சுய-பதிவின் மூலம் அல்லாமல் ஒரு நிர்வாகியால் உருவாக்கப்படுகின்றன, மேலும் இது ஒரு ஊழியரை அங்கீகரிக்கவும் அவர்கள் பார்க்கக்கூடியதை அவர்களின் சொந்த வசதி அல்லது மாவட்டத்திற்கு மட்டுப்படுத்தவும் தேவையான குறைந்தபட்சமாகும்.',
  'privacy.legalBasisEyebrow': 'சட்ட அடிப்படை',
  'privacy.legalBasisTitle': 'இந்த செயலாக்கம் ஏன் சட்டபூர்வமானது',
  'privacy.legalBasisBody':
    'பொது அபாய தகவல் அமைச்சகத்தின் பொது சுகாதார செயல்பாட்டைச் செயல்படுத்துவதில் வெளியிடப்படுகிறது — வாராந்திர தொற்றியல் அறிக்கைக்கு ஒப்புதல் தேவையில்லாத அதே வழியில், அதைப் பார்க்க ஒப்புதல் எதுவும் தேவையில்லை. ஊழியர் கணக்குத் தரவு அதே பொது செயல்பாட்டின் கீழ் செயலாக்கப்படுகிறது, வெக்டர்-கட்டுப்பாடு திட்டமிடலுக்கான கட்டுப்படுத்தப்பட்ட-அணுகல் அமைப்பை இயக்க அது அவசியம் என்ற அடிப்படையில்; இது இந்த தளத்தை இயக்குவதற்கு அப்பால் எந்த நோக்கத்திற்கும் பயன்படுத்தப்படாது.',
  'privacy.auditEyebrow': 'தணிக்கை பதிவு',
  'privacy.auditTitle': 'ஒரு ஊழியர் உள்நுழைவைப் பற்றி என்ன பதிவு செய்யப்படுகிறது',
  'privacy.auditBody':
    'உள்நுழைவது, வெளியேறுவது, மற்றும் ஒரு ஊழியர் போர்ட்டலைப் பார்ப்பது பதிவு செய்யப்படுகிறது — நேர முத்திரை, கணக்கு மின்னஞ்சல், பங்கு, அந்த நேரத்தில் மாவட்ட எல்லை, மற்றும் எந்த பக்கம் பார்க்கப்பட்டது. தேவைப்பட்டால் "யார் என்ன பார்த்தார்கள், எப்போது" என்பதற்கு ஒரு நிர்வாகி பதிலளிக்க இது இருக்கிறது, மேலும் இது தேசிய-நிர்வாகி கணக்குகளுக்கு மட்டுமே தெரியும். இது எந்த பக்கம் திறக்கப்பட்டது என்பதற்கு அப்பால் எந்த கணக்கும் ஒரு பக்கத்தில் என்ன செய்தது என்பதை பதிவு செய்யாது, மேலும் இது செயல்திறன் கண்காணிப்புக்கோ அந்த பொறுப்புணர்வு பதிவுக்கு அப்பால் எந்த நோக்கத்திற்கோ ஒருபோதும் பயன்படுத்தப்படாது.',
  'privacy.retentionEyebrow': 'தக்கவைப்பு',
  'privacy.retentionTitle': 'தரவு எவ்வளவு காலம் வைத்திருக்கப்படுகிறது',
  'privacy.retentionStaffTitle': 'ஊழியர் கணக்கு பதிவுகள்',
  'privacy.retentionStaffBody':
    'கணக்கின் வாழ்நாள் முழுவதும் வைக்கப்படுகிறது, மற்றும் அணுகல் திரும்பப் பெறப்படும்போது ஒரு நிர்வாகியால் அகற்றப்படுகிறது.',
  'privacy.retentionAuditTitle': 'தணிக்கை பதிவு உள்ளீடுகள்',
  'privacy.retentionAuditBodyPrefix':
    'ஒரு இயக்குனர் திட்டமிடப்பட்ட அகற்றலை இயக்கிய பிறகு 365 நாட்களுக்குப் பிறகு தானாக நீக்கப்படும் (',
  'privacy.retentionAuditBodySuffix':
    '). இது இந்த வரிசைப்படுத்தலில் இயக்கப்படாத வரை, உள்ளீடுகள் காலவரையின்றி தக்கவைக்கப்படும் — அது இயக்கப்பட்டதா என்று உங்கள் நிர்வாகியிடம் கேளுங்கள்.',
  'privacy.retentionAggTitle': 'மொத்த தொற்றியல் தரவு',
  'privacy.retentionAggBody':
    'ஒரு வரலாற்று பதிவாக தக்கவைக்கப்படுகிறது — இது ஒருபோதும் தனிப்பட்ட தரவு அல்ல, எனவே தனிப்பட்ட தரவுக்கான PDPA தக்கவைப்பு வரம்புகள் அதற்கு பொருந்தாது.',
  'privacy.rightsEyebrow': 'உங்கள் உரிமைகள்',
  'privacy.rightsTitle': 'அணுகல், திருத்தம், மற்றும் கேள்விகள்',
  'privacy.rightsBody':
    'PDPA இன் கீழ், இந்த தளம் உங்களைப் பற்றி வைத்திருக்கும் தனிப்பட்ட தரவு என்ன என்று நீங்கள் கேட்கலாம், அது தவறாக இருந்தால் திருத்தப்பட வேண்டும் என்று கேட்கலாம், மேலும் அது எவ்வாறு பயன்படுத்தப்படுகிறது என்பது பற்றிய கேள்விகளைக் கேட்கலாம். ஒரு ஊழியர் கணக்கிற்கு, வேகமான வழி உங்கள் சொந்த நிர்வாகி; வேறு எதற்கும், இந்த தளத்தின் அடிக்குறிப்பில் உள்ள தொடர்பு விவரங்களைப் பயன்படுத்தவும்.',
  'privacy.notCoveredTitle': 'இந்த அறிவிப்பு உள்ளடக்காதது',
  'privacy.notCoveredBody':
    'இந்த பக்கம் தளத்தின் சொந்த தரவு கையாளுதலை கூறுகிறது. இது தொற்றியல் பிரிவு, மருத்துவமனைகள், அல்லது இந்த தளம் படித்து காட்டும் வெளியிடப்பட்ட புள்ளிவிவரங்களை வைத்திருக்கும் பிற அமைப்புகளின் தரவை உள்ளடக்காது — அந்த அமைப்புகள் தங்கள் சொந்த பதிவுகளுக்கு தனி கட்டுப்படுத்துபவர்கள், மேலும் அவை பற்றிய கோரிக்கைகள் நேரடியாக அவர்களுக்கு செல்ல வேண்டும்.',

  // --- Staff sign-in ----------------------------------------------------------
  'signin.introPrefix': 'பொது அபாய தகவலுக்கு கணக்கு தேவையில்லை — ',
  'signin.introLink': 'உங்கள் மாவட்டத்தை சரிபார்க்கவும்',
  'signin.introSuffix':
    ' உள்நுழையாமல். ஒரு கணக்கு மருத்துவமனை, MOH மற்றும் அமைச்சக ஊழியர்களுக்கானது, மேலும் நீங்கள் என்ன செய்யலாம் மற்றும் எந்த மாவட்டங்களை பார்க்கலாம் என்பதை இது தீர்மானிக்கிறது.',
  'signin.footerNote':
    'கணக்குகள் சுய-பதிவின் மூலம் அல்லாமல் ஒரு தேசிய நிர்வாகியால் உருவாக்கப்படுகின்றன. அணுகல் உங்கள் சொந்த வசதி அல்லது மாவட்டத்திற்கு மட்டுப்படுத்தப்பட்டுள்ளது — உள்நுழைவது அதற்கு அப்பால் தளம் உங்களுக்குக் காட்டுவதை விரிவுபடுத்தாது.',
  'signin.emailLabel': 'மின்னஞ்சல் முகவரி',
  'signin.passwordLabel': 'கடவுச்சொல்',
  'signin.showPassword': 'கடவுச்சொல்லைக் காட்டு',
  'signin.hidePassword': 'கடவுச்சொல்லை மறை',
  'signin.submitting': 'உள்நுழைகிறது…',
  'signin.submit': 'உள்நுழைக',
  'signin.error.missingFields': 'உங்கள் மின்னஞ்சல் முகவரி மற்றும் கடவுச்சொல்லை உள்ளிடவும்.',
  'signin.error.rateLimited': 'முயற்சிகள் அதிகம். சில நிமிடங்கள் காத்திருந்து மீண்டும் முயற்சிக்கவும்.',
  'signin.error.invalidCredentials': 'அந்த சான்றுகள் ஏற்கப்படவில்லை. உங்கள் மின்னஞ்சல் மற்றும் கடவுச்சொல்லைச் சரிபார்க்கவும்.',

  // --- Staff-portal access notice --------------------------------------------
  'notice.staffOnlyTemplate': '{portal} ஊழியர்களுக்கு மட்டுமே',
  'notice.availableToTemplate':
    'இந்த போர்ட்டல் {roles} க்கு கிடைக்கும். ஒவ்வொரு மாவட்டத்திற்கும் பொது அபாய தகவலுக்கு கணக்கு தேவையில்லை.',
  'notice.checkDistrict': 'அதற்கு பதிலாக ஒரு மாவட்டத்தை சரிபார்க்கவும்',
  'notice.footerPrefix': 'இங்குள்ள பொது தரவு ஒரு ',
  'notice.footerBold': 'இயல்பாக-மறுக்கும் துணைக்குழு, ஒரு தணிக்கை அல்ல',
  'notice.footerSuffix':
    ' — இந்த பக்கங்கள் ஒரு பங்கு உண்மையில் வைத்திருக்கும் அனுமதிகளிலிருந்து கட்டமைக்கப்பட்டுள்ளன, எனவே ஒரு பிழை மருத்துவமனை ஆக்கிரமிப்பை வெளிப்படுத்துவதற்குப் பதிலாக விடுபட்ட தகவலைக் காட்டுகிறது.',
  'notice.howAccessWorks': 'அணுகல் எவ்வாறு செயல்படுகிறது',
  'notice.rolesMoh': 'MOH அதிகாரிகள், பிராந்திய சுகாதார அதிகாரிகள் மற்றும் தேசிய நிர்வாகிகள்',
  'notice.rolesHospital': 'மருத்துவமனை ஊழியர்கள், MOH அதிகாரிகள் மற்றும் தேசிய நிர்வாகிகள்',
  'notice.rolesAdmin': 'தேசிய நிர்வாகிகள்',
};

export const DICTIONARIES: Record<Locale, Dictionary> = { en, si, ta };

/**
 * A stable key for a piece of engine-authored text.
 *
 * The engine emits recommendations as English sentences with no identifier.
 * Slugging the sentence gives a translation key without changing the engine —
 * and means a reworded recommendation misses its key and renders in English,
 * which is the safe direction to fail for public health advice.
 */
export function recommendationKey(action: string): string {
  const slug = action
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
  return `rec.${slug}`;
}

/** Look up a key, falling back to English and then to the key itself. */
export function translate(locale: Locale, key: string): string {
  return DICTIONARIES[locale]?.[key] ?? DICTIONARIES.en[key] ?? key;
}
