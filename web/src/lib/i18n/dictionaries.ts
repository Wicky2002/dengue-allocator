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
  'alerts.save': 'Save preferences',
  'alerts.saved': 'Saved in this browser.',
  'alerts.noticeTitle': 'No alerts will actually be sent',
  'alerts.noticeBody':
    'This build stores your choice in this browser only. Delivery needs an SMS or email gateway, which is not connected — so nothing here registers you for anything, and the platform says so rather than leaving you expecting a message.',

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
  'alerts.save': 'මනාපයන් සුරකින්න',
  'alerts.saved': 'මෙම බ්‍රව්සරයේ සුරකින ලදී.',
  'alerts.noticeTitle': 'දැනුම්දීම් යවනු නොලැබේ',
  'alerts.noticeBody':
    'මෙම අනුවාදය ඔබේ තේරීම මෙම බ්‍රව්සරයේ පමණක් ගබඩා කරයි. දැනුම්දීම් යැවීමට SMS හෝ ඊමේල් සේවාවක් අවශ්‍ය වන අතර එය තවම සම්බන්ධ කර නොමැත.',

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
  'alerts.save': 'விருப்பங்களைச் சேமி',
  'alerts.saved': 'இந்த உலாவியில் சேமிக்கப்பட்டது.',
  'alerts.noticeTitle': 'எச்சரிக்கைகள் அனுப்பப்பட மாட்டா',
  'alerts.noticeBody':
    'இந்தப் பதிப்பு உங்கள் தேர்வை இந்த உலாவியில் மட்டுமே சேமிக்கிறது. அனுப்புவதற்கு SMS அல்லது மின்னஞ்சல் சேவை தேவை, அது இன்னும் இணைக்கப்படவில்லை.',

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
