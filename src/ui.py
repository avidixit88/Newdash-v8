import datetime as dt
import streamlit as st
from .config import APP_VERSION, TARGET_LANES
from .analytics import split_multi_rows


def render_sidebar():
    with st.sidebar:
        st.markdown("### BuildWell Control Notes")
        st.caption(f"{APP_VERSION}. Executive-facing flow remains one button only.")
        st.markdown("**Preset lanes**")
        for lane in TARGET_LANES:
            st.caption(f"• {lane}")
        st.caption("Architecture: UI → analytics service → ingestion client → normalization layer. Later the same layers can move behind FastAPI/Postgres without rebuilding the Streamlit UI.")


def render_hero():
    st.markdown("""
    <div class="hero">
        <div class="eyebrow">NextCure Signal Room</div>
        <h1>Clinical Intelligence Console</h1>
        <p>A rebuilt executive-grade intelligence system focused on B7-H4, CDH6, Alzheimer’s/ApoE4, and bone/Siglec-15 clinical registry signals. Evidence first. Charts first. Narrative last.</p>
        <div class="pill-row">
            <span class="pill">B7-H4 / VTCN1</span><span class="pill">CDH6</span><span class="pill">Alzheimer’s / ApoE4</span><span class="pill">Bone / Siglec-15</span><span class="pill">Preset scan · max 100 results/lane</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_idle_panel():
    st.markdown("""
    <div class="power-panel"><div class="eyebrow">System idle</div>
    <h3 style="margin:.35rem 0 .2rem 0;color:#fff;">Press Run Analysis to power on the console.</h3>
    <p style="color:#9caac3;margin:0;">The app will use preset NextCure lanes, pull up to 100 registry results per lane, classify geography, enrollment, phase quality, forward-looking catalysts, and combination-therapy strategy.</p></div>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, note: str):
    st.markdown(f"""
    <div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>
    """, unsafe_allow_html=True)


def section(title: str, subtitle: str):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_snapshot(bundle: dict):
    df, active_df, planned_df = bundle["df"], bundle["active_df"], bundle["planned_df"]
    countries = split_multi_rows(df, "countries", "country")["country"].nunique() if not df.empty else 0
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: metric_card("Trials Captured", f"{len(df):,}", "Unique studies returned across selected lanes.")
    with c2: metric_card("Active / Near-Active", f"{len(active_df):,}", "Recruiting, not yet recruiting, active, or invitation-based.")
    with c3: metric_card("Planned", f"{len(planned_df):,}", "Not yet recruiting or future-start studies.")
    with c4: metric_card("Patients Planned", f"{int(df['enrollment'].sum()):,}", "Total listed enrollment across captured studies.")
    with c5: metric_card("Countries", f"{countries:,}", "Distinct countries listed in trial locations.")


def render_lane_cards(bundle: dict):
    df = bundle["df"]
    cols = st.columns(4)
    for idx, lane in enumerate(bundle["lane_names"]):
        lane_df = df[df["target_lane"] == lane]
        active_lane = lane_df[lane_df["is_active"]]
        enroll = int(lane_df["enrollment"].sum()) if not lane_df.empty else 0
        high_rel = int((lane_df.get("lane_relevance_label", "") == "High relevance to NextCure lane").sum()) if not lane_df.empty else 0
        moderate_rel = int((lane_df.get("lane_relevance_label", "") == "Moderate relevance to NextCure lane").sum()) if not lane_df.empty else 0
        with cols[idx]:
            st.markdown(f'<div class="lane-card"><div class="lane-title">{lane}</div><div class="lane-sub">{len(lane_df)} studies captured · {len(active_lane)} active/near-active · {enroll:,} listed patients<br><span style="color:#f4d991;">{high_rel} high relevance · {moderate_rel} moderate relevance</span></div></div>', unsafe_allow_html=True)


def render_signal_feed(signals: list[tuple[str, str]]):
    for title, body in signals:
        st.markdown(f'<div class="signal"><strong>{title}</strong><br>{body}</div>', unsafe_allow_html=True)


def render_footer():
    st.markdown(f'<p class="caption">Data source: ClinicalTrials.gov API v2 /api/v2/studies. Last app refresh: {dt.datetime.now().strftime("%Y-%m-%d %H:%M")}. Structured registry fields and conservative keyword extraction only.</p>', unsafe_allow_html=True)
