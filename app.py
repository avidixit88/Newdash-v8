import streamlit as st
from src.styles import CSS
from src.analytics import run_clinical_analysis, build_signal_feed
from src import charts
from src.ui import (
    render_sidebar, render_hero, render_idle_panel, render_snapshot,
    render_lane_cards, section, render_signal_feed, render_footer
)

st.set_page_config(page_title="NextCure Signal Room", page_icon="🧬", layout="wide", initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)
render_sidebar()

if "scan_ran" not in st.session_state:
    st.session_state.scan_ran = False

render_hero()
run_scan = st.button("Run Analysis", key="run_analysis")
if run_scan:
    st.session_state.scan_ran = True

if not st.session_state.scan_ran:
    render_idle_panel()
    st.stop()

progress = st.progress(0)
status_box = st.empty()
status_box.caption("Initializing clinical registry scan…")
progress.progress(20)
status_box.caption("Filtering preset B7-H4, CDH6, Alzheimer’s, and bone disease lanes…")
progress.progress(45)
bundle = run_clinical_analysis()
progress.progress(75)
status_box.caption("Building charts, line-of-therapy context, forward catalyst views, and evidence layer…")
progress.progress(100)
status_box.caption("Clinical intelligence layer online. Preset scan complete.")

df = bundle["df"]
active_df = bundle["active_df"]
planned_start_df = bundle["planned_start_df"]
expected_completion_df = bundle["expected_completion_df"]

section("Executive Snapshot", "A restrained top-line readout based only on structured trial registry data.")
render_snapshot(bundle)

section("Lane Cards", "The four NextCure-relevant focus areas, kept separate so Michael can see where each signal comes from.")
render_lane_cards(bundle)


section("Recruitment & Development Status", "ClinicalTrials.gov status is now treated as a first-class intelligence layer: active/recruiting, active-not-recruiting, planned, completed, and terminated/withdrawn/suspended are separated instead of blended together.")
st1, st2 = st.columns([.9, 1.1])
with st1:
    st.plotly_chart(charts.status_overview_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
with st2:
    st.plotly_chart(charts.status_by_lane_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
st.plotly_chart(charts.status_by_modality_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
term_df = df[df["status_group"] == "Terminated / Withdrawn / Suspended"]
with st.expander("Terminated / withdrawn / suspended study watchlist", expanded=not term_df.empty):
    if term_df.empty:
        st.caption("No terminated, withdrawn, or suspended records were captured in the current preset scan.")
    else:
        st.plotly_chart(charts.terminated_watchlist_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
        st.dataframe(term_df[["nct_id", "target_lane", "sponsor", "status", "phase", "modality_class", "adc_relevance", "title", "conditions", "interventions", "last_update", "url"]].sort_values(["target_lane", "sponsor"]), use_container_width=True, hide_index=True)
with st.expander("How status is interpreted", expanded=False):
    st.markdown("""
    The raw ClinicalTrials.gov recruitment status remains in the evidence table, but the dashboard groups it for executive readability:

    - **Active / Recruiting**: Recruiting or enrolling by invitation.
    - **Active / Not Recruiting**: Active, not recruiting.
    - **Planned / Not Yet Recruiting**: Not yet recruiting or future-start records.
    - **Completed**: Completed or approved-for-marketing style records.
    - **Terminated / Withdrawn / Suspended**: Discontinued or paused records that should not be interpreted as active development momentum.
    """)

section("Active Trials by Phase", "Phase mix across active and near-active studies. This shows whether each lane is early exploratory, expansion-stage, or maturing.")
if active_df.empty:
    st.info("No active phase data found for the current scan.")
else:
    st.plotly_chart(charts.active_phase_chart(active_df), use_container_width=True, config=charts.CHART_CONFIG)

section("Geographic Trial Footprint", "Country and site concentration. This helps identify where trials are actually recruiting and where expansion may be happening.")
g1, g2 = st.columns([1.05, .95])
fig_country, fig_geo_heat, _country_counts = charts.country_charts(active_df if not active_df.empty else df)
with g1:
    st.plotly_chart(fig_country, use_container_width=True, config=charts.CHART_CONFIG)
with g2:
    st.plotly_chart(fig_geo_heat, use_container_width=True, config=charts.CHART_CONFIG)

section("Patient Population & Enrollment", "Listed enrollment is not prevalence, but it is a useful proxy for trial scale, sponsor commitment, and potential near-term data density.")
e1, e2 = st.columns([1, 1])
fig_enroll_lane, fig_enroll_ind = charts.enrollment_charts(df)
with e1:
    st.plotly_chart(fig_enroll_lane, use_container_width=True, config=charts.CHART_CONFIG)
with e2:
    st.plotly_chart(fig_enroll_ind, use_container_width=True, config=charts.CHART_CONFIG)

section("Target-Relevant Therapy Intelligence", "Tuned to Michael’s actual lanes. B7-H4 and CDH6 are oncology/ADC strategy lanes. Alzheimer’s/ApoE4 and bone/Siglec-15 remain side-channel biology and patient-selection watch lanes, not generic oncology combo buckets.")
tr1, tr2 = st.columns([1, 1])
with tr1:
    st.plotly_chart(charts.lane_relevance_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
with tr2:
    st.plotly_chart(charts.target_specific_signal_chart(df), use_container_width=True, config=charts.CHART_CONFIG)

cmb1, cmb2 = st.columns([1, 1])
with cmb1:
    st.plotly_chart(charts.combo_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
with cmb2:
    st.plotly_chart(charts.combo_class_chart(df), use_container_width=True, config=charts.CHART_CONFIG)

st.plotly_chart(charts.partner_agent_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
st.plotly_chart(charts.biology_signal_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
with st.expander("How target-relevant therapy intelligence is classified", expanded=False):
    st.markdown("""
    **B7-H4 / VTCN1** is interpreted as an ovarian/gynecologic and breast ADC/immuno-oncology lane. The important partner classes are checkpoint inhibitors, platinum/taxane chemotherapy, PARP/DNA-damage agents, and anti-VEGF backbones.

    **CDH6** is interpreted as an ovarian/peritoneal/fallopian and renal ADC lane. The important context is platinum-resistant disease, prior bevacizumab exposure, PARP/DNA-damage history, and whether sponsors begin moving CDH6 ADCs into combination expansion.

    **Alzheimer’s / ApoE4** is not treated as an oncology combo lane. It is classified for neurodegeneration biology, ApoE4/genetic selection, biomarker endpoints, and biologic interventions.

    **Bone / Siglec-15** is not treated as an oncology combo lane. It is classified for osteogenesis imperfecta, skeletal endpoints, rare-disease therapy signals, and bone biology.

    The evidence layer looks across the study title, conditions, intervention names, arm descriptions, summaries, and eligibility text.
    """)

st.markdown("#### Target-Relevant Evidence Highlights")
highlight_cols = ["nct_id", "target_lane", "adc_relevance", "modality_class", "lane_relevance_score", "lane_relevance_label", "sponsor", "phase", "status", "status_group", "indication_hint", "combo_classes", "combo_agents", "biology_signals", "line_of_therapy", "prior_therapy_context", "line_of_therapy_evidence", "lane_specific_readout", "url"]
st.dataframe(df[highlight_cols].sort_values(["lane_relevance_score", "target_lane"], ascending=[False, True]).head(30), use_container_width=True, hide_index=True)


section("ADC vs Non-ADC Modality", "Important distinction for Michael: a target mention is not the same as an ADC program. This audit separates ADC-confirmed trials from non-ADC, diagnostic, observational, neuro, bone, and unclear-modality records.")
mod1, mod2 = st.columns([1, 1])
with mod1:
    st.plotly_chart(charts.modality_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
with mod2:
    st.plotly_chart(charts.adc_relevance_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
with st.expander("How ADC vs non-ADC is classified", expanded=False):
    st.markdown("""
    The modality audit scans study titles, conditions, interventions, arm descriptions, summaries, and eligibility text.

    **ADC-confirmed** means the study mentions an ADC asset or ADC language such as antibody-drug conjugate, drug conjugate, deruxtecan/DXd, payload, linker, auristatin/MMAE, maytansinoid, or another conjugate signal.

    **ADC-watch / modality unclear** means the record is in a B7-H4 or CDH6 lane but does not clearly expose ADC language in the available registry text. We keep it visible but do not overstate it.

    Alzheimer’s/ApoE4 and bone/Siglec-15 are intentionally treated as non-ADC side-channel registry lanes.
    """)

section("Line of Therapy", "Expanded registry-text extraction for 1L, 2L, 3L, 4L+, relapsed/refractory, platinum-resistant, prior PARP, prior bevacizumab/VEGF, prior checkpoint, and prior ADC context. ClinicalTrials.gov does not provide this as a universal structured field, so this remains explicitly evidence-derived.")
lot1, lot2 = st.columns([1, 1])
with lot1:
    st.plotly_chart(charts.line_of_therapy_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
with lot2:
    st.plotly_chart(charts.prior_therapy_context_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
with st.expander("How line-of-therapy is extracted", expanded=False):
    st.markdown("""
    The app scans available registry text for phrases such as **first-line**, **frontline**, **treatment-naive**, **one prior line**, **two prior lines**, **three or more prior**, **heavily pretreated**, **relapsed**, **refractory**, **platinum-resistant**, **prior PARP**, **prior bevacizumab/VEGF**, **prior checkpoint/IO**, and **prior ADC exposure**.

    When no explicit phrase is found, the label remains **Line not specified in registry text** instead of guessing.
    """)

section("Forward-Looking Catalyst Calendar", "Forward events are split into planned/not-yet-recruiting records, dated trial starts, and expected primary completions. If one lane dominates here, the planned-records chart and table make clear whether that is the registry data or a date-field limitation.")
st.plotly_chart(charts.planned_trial_mix_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
with st.expander("Planned / not-yet-recruiting registry records", expanded=False):
    planned_table = bundle["planned_df"].copy()
    if planned_table.empty:
        st.caption("No planned or not-yet-recruiting records were captured in this scan.")
    else:
        for dc in ["start_date", "primary_completion_date", "completion_date", "last_update"]:
            if dc in planned_table:
                planned_table[dc] = planned_table[dc].dt.strftime("%b %d, %Y").fillna("Date not listed")
        st.dataframe(planned_table[["nct_id", "target_lane", "sponsor", "status", "phase", "start_date", "primary_completion_date", "completion_date", "title", "url"]].sort_values(["target_lane", "start_date"]), use_container_width=True, hide_index=True)
fc1, fc2 = st.columns([1, 1])
with fc1:
    st.markdown("#### Planned Trial Starts")
    if planned_start_df.empty:
        st.info("No future start dates found in the current scan.")
    else:
        st.plotly_chart(charts.forward_start_chart(planned_start_df), use_container_width=True, config=charts.CHART_CONFIG)
with fc2:
    st.markdown("#### Expected Primary Completions")
    if expected_completion_df.empty:
        st.info("No future primary completion dates found in the current scan.")
    else:
        st.plotly_chart(charts.forward_completion_chart(expected_completion_df), use_container_width=True, config=charts.CHART_CONFIG)

section("Sponsor / Competitor Activity", "Lead sponsor concentration across the focused registry scan.")
st.plotly_chart(charts.sponsor_chart(df), use_container_width=True, config=charts.CHART_CONFIG)

section("Clinical Trial Timeline", "Focused development-window view for the two core oncology target lanes only: B7-H4 and CDH6. Side-channel Alzheimer’s and bone records stay out of this chart so the ADC competitive window is not diluted.")
st.plotly_chart(charts.timeline_chart(df), use_container_width=True, config=charts.CHART_CONFIG)

section("Signal Feed", "Short observations generated from the structured data layer. This is not an LLM summary, it is a rules-based executive feed.")
render_signal_feed(build_signal_feed(bundle))

section("Evidence Table", "The auditable row-level dataset behind the charts. This is the trust layer.")
cols = ["nct_id", "target_lane", "adc_relevance", "modality_class", "lane_relevance_score", "lane_relevance_label", "title", "sponsor", "status", "status_group", "phase", "study_type", "enrollment", "enrollment_type", "start_date", "primary_completion_date", "completion_date", "countries", "site_count", "indication_hint", "combo_category", "combo_classes", "combo_agents", "biology_signals", "line_of_therapy", "prior_therapy_context", "line_of_therapy_evidence", "combo_evidence", "lane_specific_readout", "conditions", "interventions", "url"]
display_df = df[cols].sort_values(["target_lane", "sponsor", "phase"]).reset_index(drop=True).copy()
for dc in ["start_date", "primary_completion_date", "completion_date"]:
    display_df[dc] = display_df[dc].dt.strftime("%b %d, %Y").fillna("Date not listed")
st.dataframe(display_df, use_container_width=True, hide_index=True)
render_footer()
