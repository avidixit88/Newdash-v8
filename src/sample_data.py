import pandas as pd

def sample_trials_raw() -> pd.DataFrame:
    data = [
        ["NCT-DEMO-001","B7-H4 ADC in advanced solid tumors","NextCure","Recruiting","Phase 1","Interventional",96,"Anticipated","2024-03-01","2026-12-01","2027-05-01","Ovarian Cancer, Solid Tumor","B7-H4 ADC","Experimental: B7-H4 ADC monotherapy dose escalation","United States, Canada","New Jersey, Texas",8,"B7-H4"],
        ["NCT-DEMO-002","CDH6 targeted ADC in ovarian cancer","Competitor A","Active, not recruiting","Phase 1/2","Interventional",142,"Actual","2023-09-15","2026-07-15","2026-11-15","Ovarian Cancer","CDH6 ADC + pembrolizumab","CDH6 ADC plus pembrolizumab expansion cohort","United States, Spain","California",11,"CDH6"],
        ["NCT-DEMO-003","B7-H4 antibody in gynecologic malignancies","Competitor B","Recruiting","Phase 2","Interventional",210,"Anticipated","2022-10-12","2026-09-30","2027-01-30","Ovarian Cancer, Endometrial Cancer","Anti-B7-H4 + carboplatin paclitaxel","Combination with carboplatin and paclitaxel","United States, Germany, France","",19,"B7-H4"],
        ["NCT-DEMO-004","ApoE4 targeted agent in early Alzheimer's disease","Neuro Sponsor","Not yet recruiting","Phase 1","Interventional",72,"Anticipated","2026-08-01","2027-08-01","2028-02-01","Alzheimer Disease","ApoE4 antibody","Experimental: ApoE4 targeted therapy","United States","Massachusetts",4,"ApoE4"],
        ["NCT-DEMO-005","Siglec-15 therapy for osteogenesis imperfecta","Bone Sponsor","Recruiting","Phase 1","Interventional",48,"Anticipated","2025-01-05","2026-10-15","2027-02-15","Osteogenesis Imperfecta","Siglec-15 antibody","Dose escalation in bone fragility disorder","United States, Italy","",6,"Siglec-15"],
        ["NCT-DEMO-006","ADC combination study in platinum-resistant ovarian cancer","Competitor C","Not yet recruiting","Phase 1","Interventional",64,"Anticipated","2026-07-01","2027-09-01","2028-02-01","Platinum-Resistant Ovarian Cancer","ADC + Immunotherapy","ADC plus PD-1 inhibitor","United States","Texas",5,"B7-H4"],
    ]
    cols = ["nct_id","title","sponsor","status","phase","study_type","enrollment","enrollment_type","start_date","primary_completion_date","completion_date","conditions","interventions","arm_text","countries","states","site_count","source_query"]
    return pd.DataFrame(data, columns=cols)
