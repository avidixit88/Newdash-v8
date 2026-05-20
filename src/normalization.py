import datetime as dt
import re
from typing import Any, Dict, List, Tuple
import pandas as pd
from .config import ACTIVE_STATUSES, PLANNED_STATUSES, TARGET_LANES, COMBO_CLASSIFIERS, COMBO_STRUCTURE_TERMS, TODAY, LANE_STRATEGY_RULES, NON_ONCOLOGY_CLASSIFIERS, ADC_TERMS, ADC_ASSET_TERMS, NON_ADC_MODALITY_TERMS, ONCOLOGY_ADC_LANES, STATUS_GROUP_MAP
from .utils import safe_str, get_nested


def normalize_phase(phases: List[str]) -> str:
    """Map ClinicalTrials.gov phase codes into executive-ready labels.

    NA is not a missing phase. It means the study does not use an FDA-style
    drug phase classification. Truly absent phase data is separated so it does
    not look like a normal category.
    """
    if not phases:
        return "Phase Missing From Registry"
    phase_map = {
        "EARLY_PHASE1": "Early Phase 1",
        "PHASE1": "Phase 1",
        "PHASE2": "Phase 2",
        "PHASE3": "Phase 3",
        "PHASE4": "Phase 4",
        "NA": "Not Applicable / Non-phased Study",
    }
    clean = [phase_map.get(str(p).strip().upper(), str(p).replace("_", " ").title()) for p in phases]
    joined = "/".join([c.strip() for c in clean if c.strip()])
    return joined.replace("Phase 1/Phase 2", "Phase 1/2").replace("Phase 2/Phase 3", "Phase 2/3") or "Phase Missing From Registry"


def prettify_status(status: str | None) -> str:
    if not status:
        return "Status not listed"
    return status.replace("_", " ").title().replace("And", "and").replace("By", "by")



def classify_status_group(status: str | None) -> str:
    """Convert ClinicalTrials.gov recruitment status into executive buckets."""
    clean = safe_str(status).strip() or "Status not listed"
    return STATUS_GROUP_MAP.get(clean, "Unknown / Not Listed")

def parse_date_struct(module: Dict[str, Any], key: str):
    return get_nested(module, [key, "date"])


def extract_locations(protocol: Dict[str, Any]) -> Tuple[List[str], List[str], int]:
    locs = (protocol.get("contactsLocationsModule", {}) or {}).get("locations", []) or []
    countries, states = [], []
    for loc in locs:
        if isinstance(loc, dict):
            if loc.get("country"):
                countries.append(loc["country"])
            if loc.get("state"):
                states.append(loc["state"])
    return sorted(set(countries)), sorted(set(states)), len(locs)


def extract_arms_and_interventions(protocol: Dict[str, Any]) -> Tuple[List[str], List[str], str]:
    arms = protocol.get("armsInterventionsModule", {}) or {}
    arm_texts = []
    for arm in arms.get("armGroups", []) or []:
        if isinstance(arm, dict):
            arm_texts.append(" ".join([safe_str(arm.get("label")), safe_str(arm.get("description")), safe_str(arm.get("interventionNames"))]))
    names, types = [], []
    for item in arms.get("interventions", []) or []:
        if isinstance(item, dict):
            names.append(safe_str(item.get("name")))
            types.append(safe_str(item.get("type")))
    return names, types, " | ".join([t for t in arm_texts if t])


def parse_study(study: Dict[str, Any], source_query: str) -> Dict[str, Any]:
    protocol = study.get("protocolSection", {}) or {}
    ident = protocol.get("identificationModule", {}) or {}
    status = protocol.get("statusModule", {}) or {}
    sponsor = protocol.get("sponsorCollaboratorsModule", {}) or {}
    design = protocol.get("designModule", {}) or {}
    cond = protocol.get("conditionsModule", {}) or {}
    descr = protocol.get("descriptionModule", {}) or {}
    eligibility = protocol.get("eligibilityModule", {}) or {}
    intervention_names, intervention_types, arm_text = extract_arms_and_interventions(protocol)
    countries, states, site_count = extract_locations(protocol)
    conditions = cond.get("conditions", []) or []
    title = ident.get("briefTitle", "Untitled study")
    text_blob = " ".join([title, safe_str(descr.get("briefSummary", "")), safe_str(conditions), safe_str(intervention_names), arm_text, source_query, safe_str(eligibility.get("eligibilityCriteria", ""))])
    nct_id = ident.get("nctId", "")
    return {
        "nct_id": nct_id,
        "title": title,
        "sponsor": get_nested(sponsor, ["leadSponsor", "name"], "Sponsor not listed"),
        "collaborators": ", ".join([c.get("name", "") for c in sponsor.get("collaborators", []) if isinstance(c, dict)][:5]),
        "status": prettify_status(status.get("overallStatus")),
        "phase": normalize_phase(design.get("phases", []) or []),
        "study_type": design.get("studyType", "Study type not listed"),
        "enrollment": get_nested(design, ["enrollmentInfo", "count"], 0) or 0,
        "enrollment_type": get_nested(design, ["enrollmentInfo", "type"], "Enrollment type not listed") or "Enrollment type not listed",
        "start_date": parse_date_struct(status, "startDateStruct"),
        "primary_completion_date": parse_date_struct(status, "primaryCompletionDateStruct"),
        "completion_date": parse_date_struct(status, "completionDateStruct"),
        "last_update": parse_date_struct(status, "lastUpdateSubmitDateStruct"),
        "conditions": ", ".join(conditions[:8]),
        "interventions": ", ".join([n for n in intervention_names if n][:8]),
        "intervention_types": ", ".join(sorted(set([t for t in intervention_types if t]))),
        "arm_text": arm_text[:1000],
        "countries": ", ".join(countries) if countries else "Location not listed",
        "states": ", ".join(states) if states else "State not listed",
        "site_count": site_count,
        "source_query": source_query,
        "text_blob": text_blob,
        "url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
    }


def extract_target_lane(row: pd.Series) -> str:
    text = safe_str(row.get("text_blob", "")).lower()
    for lane, aliases in TARGET_LANES.items():
        if any(alias.lower() in text for alias in aliases):
            return lane
    return "Other / Unclassified"


def extract_indication_hint(text: str) -> str:
    t = safe_str(text).lower()
    if any(x in t for x in ["ovarian", "fallopian", "peritoneal", "endometrial", "cervical", "gynecologic"]): return "Ovarian / Gynecologic"
    if "breast" in t: return "Breast"
    if "lung" in t or "nsclc" in t: return "Lung / NSCLC"
    if "alzheimer" in t or "dementia" in t: return "Alzheimer's"
    if "osteogenesis" in t or "bone" in t or "osteoporosis" in t: return "Bone Disease"
    if "solid" in t or "tumor" in t or "neoplasm" in t: return "Solid Tumor"
    return "Other indication"


def _combo_evidence_text(row: pd.Series) -> str:
    return " ".join([
        safe_str(row.get("title", "")),
        safe_str(row.get("conditions", "")),
        safe_str(row.get("interventions", "")),
        safe_str(row.get("intervention_types", "")),
        safe_str(row.get("arm_text", "")),
        safe_str(row.get("text_blob", "")),
    ])


def _classifier_payload_for_lane(lane: str) -> Dict[str, Dict[str, List[str]]]:
    """Use oncology ADC classifiers only where they make sense.

    B7-H4 and CDH6 are oncology/ADC lanes, so checkpoint, chemo, PARP, VEGF,
    targeted pathway and multi-ADC categories are relevant. Alzheimer's/ApoE4
    and bone/Siglec-15 are side-channel registry-watch lanes, so they get
    biology/biomarker/diagnostic classifiers instead of irrelevant ADC combo
    buckets.
    """
    if lane in {"Alzheimer's / ApoE4", "Bone / Siglec-15"}:
        return NON_ONCOLOGY_CLASSIFIERS
    return COMBO_CLASSIFIERS


def _find_combo_hits(row: pd.Series) -> Dict[str, List[str]]:
    text = _combo_evidence_text(row).lower()
    lane = safe_str(row.get("target_lane", ""))
    payloads = _classifier_payload_for_lane(lane)
    hits: Dict[str, List[str]] = {}
    for category, payload in payloads.items():
        matched = []
        for agent in payload.get("agents", []):
            if re.search(r"\b" + re.escape(agent.lower()) + r"\b", text):
                matched.append(agent)
        for term in payload.get("terms", []):
            if term.lower() in text:
                matched.append(term)
        if matched:
            hits[category] = sorted(set([m.strip() for m in matched if m.strip()]))
    return hits


def extract_combo_category(row: pd.Series) -> str:
    lane = safe_str(row.get("target_lane", ""))
    hits = _find_combo_hits(row)
    if not hits:
        if lane in {"Alzheimer's / ApoE4", "Bone / Siglec-15"}:
            return "No lane-specific therapy signal detected"
        return "Monotherapy / no partner agent detected"
    if len(hits) == 1:
        prefix = "Lane signal: " if lane in {"Alzheimer's / ApoE4", "Bone / Siglec-15"} else "Combo: "
        return prefix + next(iter(hits.keys()))
    return "Multi-signal regimen / design" if lane in {"Alzheimer's / ApoE4", "Bone / Siglec-15"} else "Combo: multi-class regimen"


def extract_combo_agents(row: pd.Series) -> str:
    hits = _find_combo_hits(row)
    agents = []
    for category_hits in hits.values():
        for hit in category_hits:
            if len(hit) > 2 and hit not in COMBO_STRUCTURE_TERMS:
                agents.append(hit.title().replace("Pd-1", "PD-1").replace("Pd-L1", "PD-L1"))
    return ", ".join(sorted(set(agents))) if agents else "No named partner agent detected"


def extract_combo_classes(row: pd.Series) -> str:
    hits = _find_combo_hits(row)
    lane = safe_str(row.get("target_lane", ""))
    if hits:
        return ", ".join(hits.keys())
    return "No lane-specific class detected" if lane in {"Alzheimer's / ApoE4", "Bone / Siglec-15"} else "No partner class detected"


def extract_combo_confidence(row: pd.Series) -> str:
    text = _combo_evidence_text(row).lower()
    lane = safe_str(row.get("target_lane", ""))
    hits = _find_combo_hits(row)
    if not hits:
        return "Low: no lane-specific signal found" if lane in {"Alzheimer's / ApoE4", "Bone / Siglec-15"} else "Low: no partner agent/class found"
    has_structure = any(term in text for term in COMBO_STRUCTURE_TERMS)
    agent_count = sum(len(v) for v in hits.values())
    if lane in {"Alzheimer's / ApoE4", "Bone / Siglec-15"}:
        return "High: explicit lane biology/patient-selection signal" if agent_count >= 2 else "Medium: lane biology signal detected"
    if has_structure and agent_count >= 2:
        return "High: explicit combo language + partner agent/class"
    if agent_count >= 1:
        return "Medium: partner agent/class detected"
    return "Low: weak combo evidence"


def extract_combo_evidence(row: pd.Series) -> str:
    # Keep it short and auditable for the evidence table.
    text = _combo_evidence_text(row)
    hits = _find_combo_hits(row)
    lane = safe_str(row.get("target_lane", ""))
    if not hits:
        if lane in {"Alzheimer's / ApoE4", "Bone / Siglec-15"}:
            return "No lane-specific biology, biomarker, diagnostic, or therapy signal detected in title/interventions/arms."
        return "No named partner agent or combination class detected in title/interventions/arms."
    flat = []
    for category, terms in hits.items():
        flat.append(f"{category}: {', '.join(terms[:5])}")
    return " | ".join(flat)[:500]


def lane_relevance_score(row: pd.Series) -> int:
    lane = safe_str(row.get("target_lane", ""))
    rules = LANE_STRATEGY_RULES.get(lane, {})
    text = _combo_evidence_text(row).lower()
    score = 0
    if lane and lane != "Other / Unclassified":
        score += 35
    classes = [c.strip() for c in safe_str(row.get("combo_classes", "")).split(",") if c.strip()]
    watch = set(rules.get("watch_classes", []))
    score += 15 * len([c for c in classes if c in watch])
    score += 8 * len([term for term in rules.get("patient_terms", []) if term.lower() in text])
    if row.get("is_active"):
        score += 10
    if safe_str(row.get("modality_class", "")) == "ADC / antibody-drug conjugate" and lane in {"B7-H4 / VTCN1", "CDH6"}:
        score += 15
    if safe_str(row.get("phase", "")).startswith("Phase 2") or safe_str(row.get("phase", "")).startswith("Phase 3"):
        score += 8
    return max(0, min(100, score))


def lane_relevance_label(score: int) -> str:
    if score >= 75:
        return "High relevance to NextCure lane"
    if score >= 50:
        return "Moderate relevance to NextCure lane"
    if score >= 25:
        return "Contextual / monitor only"
    return "Low relevance / weak lane match"


def lane_specific_readout(row: pd.Series) -> str:
    lane = safe_str(row.get("target_lane", ""))
    rules = LANE_STRATEGY_RULES.get(lane, {})
    rationale = rules.get("rationale", "Registry record captured by preset lane search.")
    classes = safe_str(row.get("combo_classes", ""))
    agents = safe_str(row.get("combo_agents", ""))
    modality = safe_str(row.get("modality_class", ""))
    return f"{rationale} Modality: {modality}. Detected classes: {classes}. Detected agents/signals: {agents}."[:900]



def classify_adc_modality(row: pd.Series) -> str:
    """Classify whether a captured trial is truly ADC-relevant.

    This is intentionally conservative. For B7-H4 and CDH6, Michael needs to
    separate ADC programs from naked antibodies, diagnostic/observational
    studies, or generic pathway/target mentions. ClinicalTrials.gov does not
    expose a universal structured "modality" field, so we infer it from asset
    names, intervention names/types, title, arms, summaries and eligibility.
    """
    text = _combo_evidence_text(row).lower()
    lane = safe_str(row.get("target_lane", ""))

    if any(term.lower() in text for term in ADC_ASSET_TERMS):
        return "ADC / antibody-drug conjugate"
    if any(term.lower() in text for term in ADC_TERMS):
        return "ADC / antibody-drug conjugate"

    for label, terms in NON_ADC_MODALITY_TERMS.items():
        if any(term.lower() in text for term in terms):
            # Avoid calling an ADC merely "antibody" when a payload/conjugate term is present.
            if label == "Naked / unconjugated antibody" and any(term.lower() in text for term in ADC_TERMS):
                return "ADC / antibody-drug conjugate"
            return label

    if lane in ONCOLOGY_ADC_LANES:
        return "Oncology target mention / modality unclear"
    if lane == "Alzheimer's / ApoE4":
        return "Neuro / non-ADC registry lane"
    if lane == "Bone / Siglec-15":
        return "Bone / non-ADC registry lane"
    return "Modality unclear"


def adc_relevance_label(row: pd.Series) -> str:
    modality = safe_str(row.get("modality_class", ""))
    lane = safe_str(row.get("target_lane", ""))
    if modality == "ADC / antibody-drug conjugate":
        return "ADC-confirmed"
    if lane in ONCOLOGY_ADC_LANES:
        return "ADC-watch / modality unclear"
    return "Non-ADC side-channel"

def _lot_context_text(row: pd.Series) -> str:
    """High-recall registry text used for line-of-therapy and prior-therapy signals."""
    return _combo_evidence_text(row).lower()


LOT_PATTERNS = {
    "1L / frontline": [
        r"\b1l\b", r"\bfirst[-\s]?line\b", r"\bfront[-\s]?line\b", r"\bfrontline\b",
        r"\btreatment[-\s]?naive\b", r"\btreatment naive\b", r"\bpreviously untreated\b",
        r"\bno prior systemic therapy\b", r"\bno previous systemic therapy\b",
        r"\binitial treatment\b", r"\bnewly diagnosed\b", r"\bno prior treatment\b",
        r"\bpreviously untreated advanced\b", r"\bfirst line setting\b",
    ],
    "2L": [
        r"\b2l\b", r"\bsecond[-\s]?line\b", r"\bsecond line\b", r"\bone prior line\b",
        r"\b1 prior line\b", r"\bafter one prior\b", r"\bfollowing one prior\b",
        r"\b1 prior regimen\b", r"\bone previous regimen\b", r"\bafter 1 prior\b",
    ],
    "3L": [
        r"\b3l\b", r"\bthird[-\s]?line\b", r"\bthird line\b", r"\btwo prior lines\b",
        r"\b2 prior lines\b", r"\bafter two prior\b", r"\bfollowing two prior\b",
        r"\b2 prior regimens\b", r"\btwo previous regimens\b", r"\bafter 2 prior\b",
    ],
    "4L+ / heavily pretreated": [
        r"\b4l\b", r"\bfourth[-\s]?line\b", r"\bfourth line\b", r"\bfourth line or later\b",
        r"\b4th line\b", r"\bheavily pretreated\b", r"\bthree or more prior\b",
        r"\b3 or more prior\b", r"\bat least 3 prior\b", r"\b>=\s?3 prior\b",
        r"\bmultiple prior lines\b", r"\bmultiple prior regimens\b", r"\bprior standard therapies\b",
        r"\bexhausted standard\b", r"\bno standard therapy\b", r"\bstandard therapy.*failed\b",
    ],
    "Relapsed / refractory": [
        r"\brelapsed\b", r"\brefractory\b", r"\br/r\b", r"\bprogressed after\b",
        r"\bprogression after\b", r"\bdisease progression following\b", r"\bfailed prior\b",
        r"\bresistant\b", r"\bplatinum[-\s]?resistant\b", r"\bplatinum resistant\b",
        r"\brecurren[tc]\b", r"\brecurrent disease\b",
    ],
}

PRIOR_THERAPY_PATTERNS = {
    "Prior platinum": [r"\bplatinum\b", r"\bcarboplatin\b", r"\bcisplatin\b", r"\boxaliplatin\b"],
    "Platinum-resistant": [r"\bplatinum[-\s]?resistant\b", r"\bplatinum resistant\b", r"\bplatinum[-\s]?refractory\b"],
    "Prior taxane": [r"\btaxane\b", r"\bpaclitaxel\b", r"\bdocetaxel\b", r"\bnab-paclitaxel\b"],
    "Prior PARP / DDR": [r"\bparp\b", r"\bolaparib\b", r"\bniraparib\b", r"\brucaparib\b", r"\batr inhibitor\b", r"\bwee1\b"],
    "Prior anti-VEGF": [r"\bbevacizumab\b", r"\banti[-\s]?vegf\b", r"\bvegf\b", r"\bavastin\b"],
    "Prior checkpoint / IO": [r"\bpd-1\b", r"\bpd1\b", r"\bpd-l1\b", r"\bpdl1\b", r"\bcheckpoint\b", r"\bimmunotherapy\b"],
    "Prior ADC exposure": [r"\bantibody[-\s]?drug conjugate\b", r"\badc\b", r"\bderuxtecan\b", r"\bsacituzumab\b", r"\bmirvetuximab\b"],
    "Biomarker-selected": [r"\bhigh expression\b", r"\bpositive\b", r"\bexpression\b", r"\bapoe4\b", r"\bgenotype\b", r"\bmutation\b"],
}

BIOLOGY_SIGNAL_PATTERNS = {
    "B7-H4 expression / VTCN1": [r"\bb7[-\s]?h4\b", r"\bvtcn1\b", r"\bb7h4\b", r"\bhigh expression\b"],
    "CDH6 expression / Cadherin-6": [r"\bcdh6\b", r"\bcadherin[-\s]?6\b", r"\bcdh6 expressing\b"],
    "Ovarian / gynecologic focus": [r"\bovarian\b", r"\bfallopian\b", r"\bperitoneal\b", r"\bendometrial\b", r"\bgynecologic\b"],
    "Breast focus": [r"\bbreast\b", r"\btnbc\b", r"\btriple[-\s]?negative\b"],
    "Renal focus": [r"\brenal\b", r"\bkidney\b", r"\brcc\b"],
    "ApoE4 / genetics": [r"\bapoe4\b", r"\bapoe\b", r"\bgenotype\b", r"\bhomozygous\b", r"\bheterozygous\b"],
    "Amyloid / tau biology": [r"\bamyloid\b", r"\btau\b", r"\bneurodegeneration\b", r"\bcognitive\b"],
    "Bone remodeling / skeletal": [r"\bsiglec[-\s]?15\b", r"\bosteogenesis imperfecta\b", r"\bbone mineral density\b", r"\bfracture\b", r"\bskeletal\b"],
}


def _match_labels(text: str, pattern_map: Dict[str, List[str]]) -> List[str]:
    hits = []
    for label, pats in pattern_map.items():
        if any(re.search(pat, text) for pat in pats):
            hits.append(label)
    return hits


def extract_line_of_therapy(row: pd.Series) -> str:
    """Extract richer line-of-therapy signal from registry text.

    ClinicalTrials.gov does not expose LOT as a consistent structured field. This
    method scans title, interventions, arms, descriptions and eligibility for
    explicit line phrases plus prior-treatment/refractory language. It remains
    conservative: if the registry does not say it, we label it as unspecified.
    """
    text = _lot_context_text(row)
    hits = _match_labels(text, LOT_PATTERNS)
    if not hits:
        return "Line not specified in registry text"
    specific = [h for h in hits if h != "Relapsed / refractory"]
    if len(specific) > 1:
        return "Multiple LOT signals: " + ", ".join(hits)
    return ", ".join(hits)


def extract_prior_therapy_context(row: pd.Series) -> str:
    text = _lot_context_text(row)
    hits = _match_labels(text, PRIOR_THERAPY_PATTERNS)
    return ", ".join(hits) if hits else "Prior-therapy context not specified"


def extract_biology_signals(row: pd.Series) -> str:
    text = _lot_context_text(row)
    hits = _match_labels(text, BIOLOGY_SIGNAL_PATTERNS)
    return ", ".join(hits) if hits else "No target biology signal beyond lane match"


def extract_line_of_therapy_evidence(row: pd.Series) -> str:
    text = _combo_evidence_text(row)
    lower = text.lower()
    evidence_terms = [
        "first-line", "frontline", "treatment-naive", "treatment naive", "previously untreated", "no prior systemic therapy",
        "second-line", "one prior", "1 prior", "third-line", "two prior", "2 prior", "fourth-line", "4th line",
        "heavily pretreated", "three or more prior", "3 or more prior", "multiple prior", "relapsed", "refractory",
        "platinum-resistant", "platinum resistant", "progressed after", "failed prior", "no standard therapy"
    ]
    found = [term for term in evidence_terms if term in lower]
    if not found:
        return "No explicit line-of-therapy phrase detected in available registry text."
    return "Detected phrase(s): " + ", ".join(sorted(set(found))[:14])


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["start_date", "primary_completion_date", "completion_date", "last_update"]:
        if c not in df:
            df[c] = pd.NaT
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["enrollment"] = pd.to_numeric(df.get("enrollment", 0), errors="coerce").fillna(0).astype(int)
    df["site_count"] = pd.to_numeric(df.get("site_count", 0), errors="coerce").fillna(0).astype(int)
    df["text_blob"] = df.apply(lambda r: " ".join([safe_str(r.get(c, "")) for c in ["title", "conditions", "interventions", "arm_text", "source_query"]]), axis=1)
    df["target_lane"] = df.apply(extract_target_lane, axis=1)
    df["indication_hint"] = df["conditions"].fillna("Other indication").apply(extract_indication_hint)
    df["status_group"] = df["status"].apply(classify_status_group)
    df["is_active"] = df["status"].isin(ACTIVE_STATUSES)
    df["is_planned"] = df["status"].isin(PLANNED_STATUSES) | ((df["start_date"].dt.date >= TODAY) & df["start_date"].notna())
    df["combo_category"] = df.apply(extract_combo_category, axis=1)
    df["combo_classes"] = df.apply(extract_combo_classes, axis=1)
    df["combo_agents"] = df.apply(extract_combo_agents, axis=1)
    df["combo_confidence"] = df.apply(extract_combo_confidence, axis=1)
    df["combo_evidence"] = df.apply(extract_combo_evidence, axis=1)
    df["modality_class"] = df.apply(classify_adc_modality, axis=1)
    df["adc_relevance"] = df.apply(adc_relevance_label, axis=1)
    df["lane_relevance_score"] = df.apply(lane_relevance_score, axis=1)
    df["lane_relevance_label"] = df["lane_relevance_score"].apply(lane_relevance_label)
    df["lane_specific_readout"] = df.apply(lane_specific_readout, axis=1)
    df["line_of_therapy"] = df.apply(extract_line_of_therapy, axis=1)
    df["line_of_therapy_evidence"] = df.apply(extract_line_of_therapy_evidence, axis=1)
    df["prior_therapy_context"] = df.apply(extract_prior_therapy_context, axis=1)
    df["biology_signals"] = df.apply(extract_biology_signals, axis=1)
    df["quarter_start"] = df["start_date"].dt.to_period("Q").astype(str).replace("NaT", "Date not listed")
    df["primary_completion_quarter"] = df["primary_completion_date"].dt.to_period("Q").astype(str).replace("NaT", "Date not listed")
    df["timeline_start"] = df["start_date"].fillna(pd.Timestamp(TODAY - dt.timedelta(days=365)))
    df["timeline_finish"] = df["completion_date"].fillna(df["primary_completion_date"]).fillna(pd.Timestamp(TODAY + dt.timedelta(days=365)))
    return df
