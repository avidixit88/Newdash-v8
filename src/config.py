import datetime as dt

APP_NAME = "NextCure Signal Room"
APP_VERSION = "v2.0 Therapy + Planning Intelligence"
API_URL = "https://clinicaltrials.gov/api/v2/studies"
TODAY = dt.date.today()

TARGET_LANES = {
    "B7-H4 / VTCN1": ["B7-H4", "B7H4", "VTCN1", "B7 H4", "LNCB74", "B7-H4 ADC", "anti-B7-H4", "b7 h4"],
    "CDH6": ["CDH6", "cadherin 6", "cadherin-6", "SIM0505", "CDH6 ADC", "anti-CDH6", "raludotatug", "r-dxd", "rdxd", "CUSP06"],
    "Alzheimer's / ApoE4": ["Alzheimer", "Alzheimer's", "ApoE4", "APOE4", "APOE", "NC181"],
    "Bone / Siglec-15": ["osteogenesis imperfecta", "bone disease", "bone", "Siglec-15", "SIGLEC15", "NC605"],
}

PRESET_QUERIES = [
    "B7-H4 OR VTCN1 OR LNCB74 OR B7H4",
    "CDH6 OR cadherin 6 OR SIM0505 OR raludotatug deruxtecan OR CUSP06",
    "Alzheimer ApoE4 OR APOE4 OR NC181",
    "Siglec-15 OR osteogenesis imperfecta OR NC605 bone",
]

PRESET_PAGE_SIZE = 100
ACTIVE_STATUSES = {"Recruiting", "Not yet recruiting", "Active, not recruiting", "Enrolling by invitation"}
PLANNED_STATUSES = {"Not yet recruiting"}
STATUS_FOCUS = ["Recruiting", "Not yet recruiting", "Active, not recruiting", "Enrolling by invitation"]

STATUS_GROUP_ORDER = [
    "Active / Recruiting",
    "Active / Not Recruiting",
    "Planned / Not Yet Recruiting",
    "Completed",
    "Terminated / Withdrawn / Suspended",
    "Unknown / Not Listed",
]

STATUS_GROUP_MAP = {
    "Recruiting": "Active / Recruiting",
    "Enrolling by invitation": "Active / Recruiting",
    "Active, not recruiting": "Active / Not Recruiting",
    "Not yet recruiting": "Planned / Not Yet Recruiting",
    "Completed": "Completed",
    "Terminated": "Terminated / Withdrawn / Suspended",
    "Withdrawn": "Terminated / Withdrawn / Suspended",
    "Suspended": "Terminated / Withdrawn / Suspended",
    "No longer available": "Terminated / Withdrawn / Suspended",
    "Temporarily not available": "Terminated / Withdrawn / Suspended",
    "Approved for marketing": "Completed",
    "Available": "Active / Recruiting",
    "Status not listed": "Unknown / Not Listed",
}

PHASE_ORDER = [
    "Early Phase 1", "Phase 1", "Phase 1/2", "Phase 2", "Phase 2/3", "Phase 3", "Phase 4",
    "Not Applicable / Non-phased Study", "Phase Missing From Registry"
]

# Explicit modality classification so Michael can distinguish true ADC activity
# from antibodies, biologics, diagnostics, vaccines, or general oncology trials.
ADC_TERMS = [
    "adc", "antibody-drug conjugate", "antibody drug conjugate", "drug conjugate",
    "deruxtecan", "dxd", "auristatin", "mmae", "maytansinoid", "dm1", "dm4",
    "pyrrolobenzodiazepine", "pbd", "payload", "linker", "conjugate"
]

ADC_ASSET_TERMS = [
    "lncb74", "sim0505", "raludotatug deruxtecan", "r-dxd", "rdxd", "cusp06",
    "xmt-1660", "sgn-b7h4v", "vobramitamab duocarmazine"
]

NON_ADC_MODALITY_TERMS = {
    "Naked / unconjugated antibody": ["monoclonal antibody", "mab", "antibody"],
    "Cell therapy / immune cell product": ["car-t", "cart", "car t", "t cell", "nk cell", "cell therapy"],
    "Small molecule / targeted agent": ["inhibitor", "small molecule", "tyrosine kinase", "parp", "atr inhibitor", "wee1 inhibitor"],
    "Diagnostic / biomarker / observational": ["observational", "diagnostic", "biomarker", "imaging", "registry", "questionnaire"],
    "Vaccine / immune therapy": ["vaccine", "peptide", "immunotherapy"],
}

ONCOLOGY_ADC_LANES = {"B7-H4 / VTCN1", "CDH6"}

# Clinically meaningful buckets for ADC / oncology trial strategy.
COMBO_CLASSIFIERS = {
    "IO / checkpoint": {
        "agents": ["pembrolizumab", "keytruda", "nivolumab", "opdivo", "atezolizumab", "tecentriq", "durvalumab", "imfinzi", "avelumab", "cemiplimab", "dostarlimab", "balstilimab"],
        "terms": ["pd-1", "pd1", "pd-l1", "pdl1", "checkpoint", "immune checkpoint", "immunotherapy", "anti-pd", "anti pd"],
    },
    "Chemo / platinum / taxane": {
        "agents": ["carboplatin", "cisplatin", "oxaliplatin", "paclitaxel", "docetaxel", "nab-paclitaxel", "gemcitabine", "doxorubicin", "liposomal doxorubicin", "topotecan", "pemetrexed", "capecitabine", "eribulin", "irinotecan", "etoposide"],
        "terms": ["chemotherapy", "platinum", "taxane", "standard chemotherapy", "standard of care chemotherapy"],
    },
    "Anti-VEGF / angiogenesis": {
        "agents": ["bevacizumab", "avastin", "cediranib", "ramucirumab", "aflibercept"],
        "terms": ["anti-vegf", "vegf", "angiogenesis"],
    },
    "PARP / DNA damage": {
        "agents": ["olaparib", "lynparza", "niraparib", "zejula", "rucaparib", "talazoparib", "veliparib", "berzosertib", "adavosertib"],
        "terms": ["parp", "dna damage", "ddr", "atr inhibitor", "wee1 inhibitor"],
    },
    "HER2 / EGFR / targeted pathway": {
        "agents": ["trastuzumab", "herceptin", "pertuzumab", "perjeta", "tucatinib", "lapatinib", "osimertinib", "erlotinib", "gefitinib", "cetuximab", "panitumumab", "selpercatinib", "larotrectinib", "entrectinib", "alpelisib", "capivasertib"],
        "terms": ["her2", "egfr", "ret inhibitor", "ntrk", "pi3k", "akt inhibitor", "targeted therapy"],
    },
    "Endocrine / hormonal": {
        "agents": ["letrozole", "anastrozole", "exemestane", "fulvestrant", "tamoxifen", "elacestrant", "goserelin"],
        "terms": ["endocrine", "hormonal therapy", "estrogen receptor", "er-positive", "er positive"],
    },
    "Radiation / radiopharmaceutical": {
        "agents": ["lutetium", "actinium", "radium", "iodine i-131", "external beam radiation"],
        "terms": ["radiation", "radiotherapy", "radiopharmaceutical", "radioligand"],
    },
    "ADC / multi-ADC strategy": {
        "agents": ["trastuzumab deruxtecan", "enhertu", "sacituzumab govitecan", "trodelvy", "datopotamab deruxtecan", "dato-dxd", "raludotatug deruxtecan", "r-dxd", "mirvetuximab soravtansine", "elrema", "adc"],
        "terms": ["antibody-drug conjugate", "antibody drug conjugate", "adc plus", "adc in combination", "dual-payload adc", "multi-adc"],
    },
}

COMBO_STRUCTURE_TERMS = [
    "combination", "combined with", "in combination with", "plus", "added to", "with pembrolizumab", "with chemotherapy", "co-administered", "coadministered", "partner agent"
]

# Lane-specific interpretation layer. This keeps combo therapy useful to Michael's actual targets
# instead of treating every oncology combination as equally relevant.
LANE_STRATEGY_RULES = {
    "B7-H4 / VTCN1": {
        "watch_classes": ["IO / checkpoint", "Chemo / platinum / taxane", "PARP / DNA damage", "Anti-VEGF / angiogenesis"],
        "patient_terms": ["ovarian", "gynecologic", "breast", "endometrial", "triple-negative", "platinum-resistant", "parp", "b7-h4 high", "vtcn1"],
        "rationale": "B7-H4 is most strategically useful here as an ovarian/gynecologic and breast ADC/immuno-oncology lane. The key watch is whether sponsors are pairing B7-H4 agents with checkpoint blockade, platinum/taxane chemotherapy, PARP/DNA-damage approaches, or anti-VEGF backbones."
    },
    "CDH6": {
        "watch_classes": ["Chemo / platinum / taxane", "Anti-VEGF / angiogenesis", "PARP / DNA damage", "IO / checkpoint"],
        "patient_terms": ["ovarian", "fallopian", "peritoneal", "renal", "platinum-resistant", "high-grade serous", "bevacizumab", "cdh6 expressing"],
        "rationale": "CDH6 is most relevant as an ovarian/peritoneal/fallopian and renal ADC lane. For Michael, the most useful signal is how CDH6 ADC trials position against platinum resistance, prior bevacizumab exposure, PARP/DNA-damage history, and broader combo expansion."
    },
    "Alzheimer's / ApoE4": {
        "watch_classes": ["Neuro / Alzheimer biologic", "Biomarker / genetics", "Device / diagnostic / non-drug"],
        "patient_terms": ["alzheimer", "apoe4", "apoe", "amyloid", "tau", "mild cognitive impairment", "dementia", "neurodegeneration"],
        "rationale": "This is not an ADC combo lane. It should be treated as a neurodegeneration registry-watch lane focused on ApoE4/genetic selection, biologic interventions, biomarker endpoints, and patient selection rather than oncology combination therapy."
    },
    "Bone / Siglec-15": {
        "watch_classes": ["Bone / rare disease therapy", "Device / diagnostic / non-drug", "Biomarker / genetics"],
        "patient_terms": ["osteogenesis imperfecta", "bone", "fracture", "osteoporosis", "siglec-15", "skeletal", "mineral density"],
        "rationale": "This is not an ADC combo lane. It should be treated as a bone/rare-disease registry-watch lane focused on osteogenesis imperfecta, bone remodeling biology, skeletal endpoints, and patient population definition."
    },
}

NON_ONCOLOGY_CLASSIFIERS = {
    "Neuro / Alzheimer biologic": {
        "agents": ["lecanemab", "donanemab", "aducanumab", "gantenerumab", "remternetug", "crenezumab", "solanezumab"],
        "terms": ["amyloid", "tau", "anti-amyloid", "anti amyloid", "neurodegeneration", "cognitive", "mild cognitive impairment", "dementia"]
    },
    "Biomarker / genetics": {
        "agents": [],
        "terms": ["apoe4", "apoe", "genotype", "biomarker", "genetic", "mutation", "expression", "high expression", "patient selection", "amyloid pet", "csf", "tau pet", "plasma biomarker", "cognitive endpoint"]
    },
    "Bone / rare disease therapy": {
        "agents": ["setrusumab", "romosozumab", "denosumab", "teriparatide", "bisphosphonate", "zoledronic acid"],
        "terms": ["osteogenesis imperfecta", "bone mineral density", "fracture", "skeletal", "bone formation", "bone resorption", "rare disease"]
    },
    "Device / diagnostic / non-drug": {
        "agents": [],
        "terms": ["observational", "diagnostic", "imaging", "questionnaire", "registry", "device", "screening"]
    },
}
