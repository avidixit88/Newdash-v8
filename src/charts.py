import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .config import PHASE_ORDER, TODAY
from .analytics import split_multi_rows

CHART_CONFIG = {"displayModeBar": False}


def chart_layout(fig: go.Figure, height: int = 410, legend: str = "bottom") -> go.Figure:
    """Apply the Signal Room chart theme.

    Legends are intentionally placed outside the plotting/title area wherever
    possible because the prior build let horizontal legends collide with chart
    titles. Bottom legends use extra bottom margin; right legends are used for
    dense timelines where a bottom legend would eat too much vertical space.
    """
    legend_cfg = {
        "font": {"color": "#ffffff", "size": 13},
        "title": {"font": {"color": "#ffffff", "size": 13}},
        "bgcolor": "rgba(8,13,24,.84)",
        "bordercolor": "rgba(190,205,235,.34)",
        "borderwidth": 1,
    }
    margin = {"l": 10, "r": 10, "t": 78, "b": 105}
    if legend == "right":
        legend_cfg.update({"orientation": "v", "yanchor": "top", "y": 1, "xanchor": "left", "x": 1.02})
        margin = {"l": 10, "r": 180, "t": 78, "b": 36}
    elif legend == "none":
        legend_cfg.update({"visible": False})
        margin = {"l": 10, "r": 10, "t": 78, "b": 40}
    else:
        legend_cfg.update({"orientation": "h", "yanchor": "top", "y": -0.28, "xanchor": "center", "x": 0.5})

    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eef5ff", "family": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"},
        margin=margin,
        legend=legend_cfg,
        title={"font": {"color": "#ffffff", "size": 18}, "x": 0.01, "xanchor": "left"},
        xaxis={"gridcolor": "rgba(164,183,219,.14)", "zerolinecolor": "rgba(164,183,219,.22)", "tickfont": {"color": "#e6eefc", "size": 12}, "title": {"font": {"color": "#f4f8ff"}}},
        yaxis={"gridcolor": "rgba(164,183,219,.14)", "zerolinecolor": "rgba(164,183,219,.22)", "tickfont": {"color": "#e6eefc", "size": 12}, "title": {"font": {"color": "#f4f8ff"}}},
    )
    return fig

def active_phase_chart(active_df: pd.DataFrame) -> go.Figure:
    phase_df = active_df.groupby(["target_lane", "phase"], as_index=False).agg(trials=("nct_id", "count"), enrollment=("enrollment", "sum"))
    fig = px.bar(phase_df, x="phase", y="trials", color="target_lane", hover_data=["enrollment"], category_orders={"phase": PHASE_ORDER}, title="Active / Near-Active Trials by Phase")
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 430)


def country_charts(df: pd.DataFrame) -> tuple[go.Figure, go.Figure, pd.DataFrame]:
    country_rows = split_multi_rows(df, "countries", "country")
    country_counts = country_rows.groupby("country", as_index=False).agg(trials=("nct_id", "count"), enrollment=("enrollment", "sum"), sites=("site_count", "sum")).sort_values("trials", ascending=False).head(18)
    fig_country = px.bar(country_counts.sort_values("trials"), x="trials", y="country", orientation="h", hover_data=["enrollment", "sites"], title="Active Trials by Country")
    fig_country.update_xaxes(title="Studies")
    fig_country.update_yaxes(title="")
    geo_lane = country_rows.groupby(["target_lane", "country"], as_index=False).agg(trials=("nct_id", "count"))
    geo_pivot = geo_lane.pivot_table(index="country", columns="target_lane", values="trials", aggfunc="sum", fill_value=0) if not geo_lane.empty else pd.DataFrame()
    fig_heat = px.imshow(geo_pivot, text_auto=True, aspect="auto", title="Country × Lane Density") if not geo_pivot.empty else go.Figure()
    return chart_layout(fig_country, 470, legend="none"), chart_layout(fig_heat, 470, legend="none"), country_counts


def enrollment_charts(df: pd.DataFrame) -> tuple[go.Figure, go.Figure]:
    enroll_lane = df.groupby("target_lane", as_index=False).agg(enrollment=("enrollment", "sum"), trials=("nct_id", "count")).sort_values("enrollment", ascending=False)
    fig_lane = px.bar(enroll_lane, x="target_lane", y="enrollment", hover_data=["trials"], title="Listed Enrollment by Lane")
    fig_lane.update_xaxes(title="")
    fig_lane.update_yaxes(title="Patients")
    enroll_ind = df.groupby("indication_hint", as_index=False).agg(enrollment=("enrollment", "sum"), trials=("nct_id", "count")).sort_values("enrollment", ascending=False)
    fig_ind = px.bar(enroll_ind, x="enrollment", y="indication_hint", orientation="h", hover_data=["trials"], title="Listed Enrollment by Patient Population")
    fig_ind.update_xaxes(title="Patients")
    fig_ind.update_yaxes(title="")
    return chart_layout(fig_lane, 430, legend="none"), chart_layout(fig_ind, 430, legend="none")


def combo_chart(df: pd.DataFrame) -> go.Figure:
    combo_df = df.groupby(["target_lane", "combo_category"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    fig = px.bar(
        combo_df, x="target_lane", y="trials", color="combo_category",
        hover_data=["enrollment"], title="Combination Strategy by Lane"
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 455)


def combo_class_chart(df: pd.DataFrame) -> go.Figure:
    rows = []
    for _, r in df.iterrows():
        classes = [c.strip() for c in str(r.get("combo_classes", "")).split(",") if c.strip() and c.strip() not in {"No partner class detected", "No lane-specific class detected"}]
        if not classes:
            classes = ["No partner class detected"]
        for cls in classes:
            rows.append({"target_lane": r.get("target_lane"), "combo_class": cls, "nct_id": r.get("nct_id"), "enrollment": r.get("enrollment", 0)})
    d = pd.DataFrame(rows)
    combo_df = d.groupby(["combo_class", "target_lane"], as_index=False).agg(trials=("nct_id", "count"), enrollment=("enrollment", "sum")) if not d.empty else pd.DataFrame(columns=["combo_class", "target_lane", "trials", "enrollment"])
    fig = px.bar(
        combo_df, x="trials", y="combo_class", color="target_lane", orientation="h",
        hover_data=["enrollment"], title="Detected Partner Classes"
    )
    fig.update_xaxes(title="Studies")
    fig.update_yaxes(title="")
    return chart_layout(fig, 560, legend="right")


def combo_confidence_chart(df: pd.DataFrame) -> go.Figure:
    conf = df.groupby(["combo_confidence", "target_lane"], as_index=False).agg(trials=("nct_id", "count"))
    fig = px.bar(conf, x="combo_confidence", y="trials", color="target_lane", title="Combination Extraction Confidence")
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 390)


def forward_start_chart(planned_start_df: pd.DataFrame) -> go.Figure:
    d = planned_start_df.copy()
    d["event_label"] = d["target_lane"] + " · " + d["sponsor"].str.slice(0, 22) + " · " + d["nct_id"]
    fig = px.scatter(d, x="start_date", y="event_label", size="enrollment", color="target_lane", hover_data=["title", "status", "phase", "indication_hint", "combo_category"], title="Forward Starts: Trials Expected to Begin")
    fig.update_yaxes(title="", autorange="reversed")
    fig.update_xaxes(title="Planned / estimated start date")
    return chart_layout(fig, max(430, min(820, 120 + len(d) * 24)))


def forward_completion_chart(expected_completion_df: pd.DataFrame) -> go.Figure:
    d = expected_completion_df.copy()
    d["event_label"] = d["target_lane"] + " · " + d["sponsor"].str.slice(0, 22) + " · " + d["nct_id"]
    fig = px.scatter(d, x="primary_completion_date", y="event_label", size="enrollment", color="phase", hover_data=["title", "status", "target_lane", "indication_hint", "combo_category"], title="Forward Completions: Primary Completion Windows")
    fig.update_yaxes(title="", autorange="reversed")
    fig.update_xaxes(title="Primary completion date")
    return chart_layout(fig, max(430, min(820, 120 + len(d) * 24)))


def sponsor_chart(df: pd.DataFrame) -> go.Figure:
    sponsor_counts = df.groupby("sponsor", as_index=False).agg(trials=("nct_id", "count"), active=("is_active", "sum"), enrollment=("enrollment", "sum"), sites=("site_count", "sum")).sort_values("trials", ascending=False).head(18)
    fig = px.bar(sponsor_counts.sort_values("trials"), x="trials", y="sponsor", orientation="h", hover_data=["active", "enrollment", "sites"], title="Top Sponsors by Trial Count")
    fig.update_yaxes(title="")
    fig.update_xaxes(title="Studies")
    return chart_layout(fig, 520, legend="none")


def timeline_chart(df: pd.DataFrame) -> go.Figure:
    # This development-window chart is intentionally focused only on the two
    # core oncology ADC lanes Michael asked to monitor: B7-H4 and CDH6.
    # Alzheimer's/ApoE4 and bone/Siglec-15 remain in other dashboard sections
    # as side-channel registry watch lanes, but they do not belong in this
    # oncology development-window view.
    core_lanes = ["B7-H4 / VTCN1", "CDH6"]
    d = df[df["target_lane"].isin(core_lanes)].copy()
    if d.empty:
        return chart_layout(go.Figure(), 420, legend="none")
    d["_future_weight"] = d["primary_completion_date"].fillna(d["completion_date"]).fillna(d["timeline_finish"])
    d = d.sort_values(["target_lane", "_future_weight", "timeline_start", "sponsor"])
    show_df = d.groupby("target_lane", group_keys=False).head(28).copy()
    show_df = show_df.sort_values(["target_lane", "timeline_start", "sponsor"]).head(60)
    show_df["label"] = show_df["target_lane"].str.slice(0, 18) + " · " + show_df["sponsor"].str.slice(0, 20) + " · " + show_df["nct_id"]
    fig = px.timeline(
        show_df,
        x_start="timeline_start",
        x_end="timeline_finish",
        y="label",
        color="modality_class",
        hover_data=["title", "sponsor", "target_lane", "status", "phase", "modality_class", "adc_relevance", "line_of_therapy", "enrollment", "countries", "combo_category", "conditions", "interventions"],
        title="Trial Development Windows: B7-H4 + CDH6 Core Oncology Lanes",
    )
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_xaxes(title="")
    return chart_layout(fig, max(560, min(1040, 90 + len(show_df) * 24)), legend="right")


def modality_chart(df: pd.DataFrame) -> go.Figure:
    d = df.groupby(["target_lane", "modality_class"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    fig = px.bar(
        d, x="target_lane", y="trials", color="modality_class",
        hover_data=["enrollment"], title="ADC vs Non-ADC Modality by Lane"
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 455, legend="right")


def adc_relevance_chart(df: pd.DataFrame) -> go.Figure:
    d = df.groupby(["target_lane", "adc_relevance"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    fig = px.bar(
        d, x="trials", y="target_lane", color="adc_relevance", orientation="h",
        hover_data=["enrollment"], title="ADC Relevance Audit"
    )
    fig.update_xaxes(title="Studies")
    fig.update_yaxes(title="")
    return chart_layout(fig, 430, legend="right")

def line_of_therapy_chart(df: pd.DataFrame) -> go.Figure:
    d = df.copy()
    # Keep explicit unknowns because LOT is not a universal structured registry field.
    g = d.groupby(["target_lane", "line_of_therapy"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    order = ["1L / frontline", "2L", "3L", "4L+ / heavily pretreated", "Relapsed / refractory"]
    fig = px.bar(
        g,
        x="target_lane",
        y="trials",
        color="line_of_therapy",
        hover_data=["enrollment"],
        category_orders={"line_of_therapy": order},
        title="Line-of-Therapy Signals by Target Lane",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 455)

def lane_relevance_chart(df: pd.DataFrame) -> go.Figure:
    d = df.groupby(["target_lane", "lane_relevance_label"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    order = ["High relevance to NextCure lane", "Moderate relevance to NextCure lane", "Contextual / monitor only", "Low relevance / weak lane match"]
    fig = px.bar(
        d, x="target_lane", y="trials", color="lane_relevance_label",
        hover_data=["enrollment"], category_orders={"lane_relevance_label": order},
        title="Target-Lane Relevance, Not Generic Oncology Activity"
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 430)


def target_specific_signal_chart(df: pd.DataFrame) -> go.Figure:
    rows = []
    for _, r in df.iterrows():
        classes = [c.strip() for c in str(r.get("combo_classes", "")).split(",") if c.strip()]
        classes = [c for c in classes if c not in {"No partner class detected", "No lane-specific class detected"}]
        if not classes:
            classes = ["No target-specific class detected"]
        for cls in classes:
            rows.append({"target_lane": r.get("target_lane"), "signal_class": cls, "nct_id": r.get("nct_id"), "enrollment": r.get("enrollment", 0), "score": r.get("lane_relevance_score", 0)})
    d = pd.DataFrame(rows)
    if d.empty:
        return chart_layout(go.Figure(), 430)
    g = d.groupby(["target_lane", "signal_class"], as_index=False).agg(trials=("nct_id", "count"), enrollment=("enrollment", "sum"), avg_relevance=("score", "mean"))
    fig = px.bar(
        g, x="trials", y="signal_class", color="target_lane", orientation="h",
        hover_data=["enrollment", "avg_relevance"],
        title="Target-Specific Therapy / Biology Signals"
    )
    fig.update_xaxes(title="Studies")
    fig.update_yaxes(title="")
    return chart_layout(fig, max(460, min(800, 170 + len(g) * 24)), legend="right")


def status_overview_chart(df: pd.DataFrame) -> go.Figure:
    """Executive status mix across all captured records."""
    from .config import STATUS_GROUP_ORDER
    d = df.groupby(["status_group"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum"), sites=("site_count", "sum")
    )
    fig = px.bar(
        d,
        x="status_group",
        y="trials",
        hover_data=["enrollment", "sites"],
        category_orders={"status_group": STATUS_GROUP_ORDER},
        title="Trial Status Mix: Active, Planned, Completed, Terminated",
    )
    fig.update_xaxes(title="", tickangle=-20)
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 430, legend="none")


def status_by_lane_chart(df: pd.DataFrame) -> go.Figure:
    """Status distribution by NextCure-relevant lane."""
    from .config import STATUS_GROUP_ORDER
    d = df.groupby(["target_lane", "status_group"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    fig = px.bar(
        d,
        x="target_lane",
        y="trials",
        color="status_group",
        hover_data=["enrollment"],
        category_orders={"status_group": STATUS_GROUP_ORDER},
        title="Status by Target Lane",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 455, legend="right")


def status_by_modality_chart(df: pd.DataFrame) -> go.Figure:
    """Status mix by ADC / non-ADC modality classification."""
    from .config import STATUS_GROUP_ORDER
    d = df.groupby(["modality_class", "status_group"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    fig = px.bar(
        d,
        x="trials",
        y="modality_class",
        color="status_group",
        orientation="h",
        hover_data=["enrollment"],
        category_orders={"status_group": STATUS_GROUP_ORDER},
        title="Status by ADC / Non-ADC Modality",
    )
    fig.update_xaxes(title="Studies")
    fig.update_yaxes(title="")
    return chart_layout(fig, max(430, min(760, 140 + 34 * max(1, d["modality_class"].nunique()))), legend="right")


def terminated_watchlist_chart(df: pd.DataFrame) -> go.Figure:
    """Terminated/withdrawn/suspended records, useful as a risk/competition audit."""
    d = df[df["status_group"] == "Terminated / Withdrawn / Suspended"].copy()
    if d.empty:
        return chart_layout(go.Figure(), 340, legend="none")
    d["event_date"] = d["last_update"].fillna(d["completion_date"]).fillna(d["primary_completion_date"]).fillna(d["start_date"])
    d["label"] = d["target_lane"].str.slice(0, 18) + " · " + d["sponsor"].str.slice(0, 22) + " · " + d["nct_id"]
    d = d.sort_values(["event_date", "target_lane"], ascending=[False, True]).head(30)
    fig = px.scatter(
        d,
        x="event_date",
        y="label",
        color="status",
        size="enrollment",
        hover_data=["title", "target_lane", "phase", "modality_class", "adc_relevance", "conditions", "interventions"],
        title="Terminated / Withdrawn / Suspended Watchlist",
    )
    fig.update_xaxes(title="Most relevant registry date available")
    fig.update_yaxes(title="", autorange="reversed")
    return chart_layout(fig, max(400, min(780, 120 + len(d) * 24)), legend="right")

# --- v2.0 overrides / enhanced intelligence charts ---

def _split_signal_rows(df: pd.DataFrame, source_col: str, value_name: str, exclude: set[str] | None = None) -> pd.DataFrame:
    exclude = exclude or set()
    rows = []
    for _, r in df.iterrows():
        vals = [v.strip() for v in str(r.get(source_col, "")).split(",") if v.strip()]
        vals = [v for v in vals if v not in exclude]
        if not vals:
            continue
        for v in vals:
            rows.append({
                "target_lane": r.get("target_lane"),
                value_name: v,
                "nct_id": r.get("nct_id"),
                "enrollment": r.get("enrollment", 0),
                "sponsor": r.get("sponsor"),
                "phase": r.get("phase"),
                "status": r.get("status"),
            })
    return pd.DataFrame(rows)


def line_of_therapy_chart(df: pd.DataFrame) -> go.Figure:
    d = df.copy()
    g = d.groupby(["target_lane", "line_of_therapy"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    order = [
        "1L / frontline", "2L", "3L", "4L+ / heavily pretreated", "Relapsed / refractory",
        "Multiple LOT signals: 1L / frontline, Relapsed / refractory",
        "Multiple LOT signals: 2L, Relapsed / refractory",
        "Multiple LOT signals: 3L, Relapsed / refractory",
        "Multiple LOT signals: 4L+ / heavily pretreated, Relapsed / refractory",
        "Line not specified in registry text",
    ]
    fig = px.bar(
        g,
        x="trials",
        y="target_lane",
        color="line_of_therapy",
        orientation="h",
        hover_data=["enrollment"],
        category_orders={"line_of_therapy": order},
        title="Line-of-Therapy Signals by Target Lane",
    )
    fig.update_xaxes(title="Studies")
    fig.update_yaxes(title="")
    return chart_layout(fig, 470, legend="right")


def prior_therapy_context_chart(df: pd.DataFrame) -> go.Figure:
    d = _split_signal_rows(
        df,
        "prior_therapy_context",
        "prior_context",
        exclude={"Prior-therapy context not specified"},
    )
    if d.empty:
        fig = go.Figure()
        fig.add_annotation(text="No explicit prior-therapy context detected in available registry text.", x=0.5, y=0.5, showarrow=False, font={"color": "#eaf2ff", "size": 14})
        return chart_layout(fig, 340, legend="none")
    g = d.groupby(["prior_context", "target_lane"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    fig = px.bar(
        g,
        x="trials",
        y="prior_context",
        color="target_lane",
        orientation="h",
        hover_data=["enrollment"],
        title="Prior-Therapy / Patient-Setting Context",
    )
    fig.update_xaxes(title="Studies")
    fig.update_yaxes(title="")
    return chart_layout(fig, max(430, min(760, 160 + 32 * g["prior_context"].nunique())), legend="right")


def biology_signal_chart(df: pd.DataFrame) -> go.Figure:
    d = _split_signal_rows(
        df,
        "biology_signals",
        "biology_signal",
        exclude={"No target biology signal beyond lane match"},
    )
    if d.empty:
        fig = go.Figure()
        fig.add_annotation(text="No lane-specific biology signals detected beyond the target query match.", x=0.5, y=0.5, showarrow=False, font={"color": "#eaf2ff", "size": 14})
        return chart_layout(fig, 340, legend="none")
    g = d.groupby(["biology_signal", "target_lane"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    fig = px.bar(
        g,
        x="trials",
        y="biology_signal",
        color="target_lane",
        orientation="h",
        hover_data=["enrollment"],
        title="Target-Specific Biology / Patient-Selection Signals",
    )
    fig.update_xaxes(title="Studies")
    fig.update_yaxes(title="")
    return chart_layout(fig, max(455, min(820, 170 + 32 * g["biology_signal"].nunique())), legend="right")


def partner_agent_chart(df: pd.DataFrame) -> go.Figure:
    d = _split_signal_rows(
        df,
        "combo_agents",
        "partner_agent",
        exclude={"No named partner agent detected"},
    )
    if d.empty:
        fig = go.Figure()
        fig.add_annotation(text="No named partner agents detected in available registry text.", x=0.5, y=0.5, showarrow=False, font={"color": "#eaf2ff", "size": 14})
        return chart_layout(fig, 340, legend="none")
    g = d.groupby(["partner_agent", "target_lane"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    ).sort_values("trials", ascending=False).head(22)
    fig = px.bar(
        g,
        x="trials",
        y="partner_agent",
        color="target_lane",
        orientation="h",
        hover_data=["enrollment"],
        title="Detected Named Partner Agents / Biology Terms",
    )
    fig.update_xaxes(title="Studies")
    fig.update_yaxes(title="")
    return chart_layout(fig, max(430, min(820, 160 + 28 * len(g))), legend="right")


def planned_trial_mix_chart(df: pd.DataFrame) -> go.Figure:
    d = df[df.get("is_planned", False)].copy()
    if d.empty:
        fig = go.Figure()
        fig.add_annotation(text="No planned / not-yet-recruiting records captured in the current scan.", x=0.5, y=0.5, showarrow=False, font={"color": "#eaf2ff", "size": 14})
        return chart_layout(fig, 340, legend="none")
    g = d.groupby(["target_lane", "status"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    fig = px.bar(
        g,
        x="target_lane",
        y="trials",
        color="status",
        hover_data=["enrollment"],
        title="Planned / Not-Yet-Recruiting Records by Lane",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 390, legend="right")


def forward_start_chart(planned_start_df: pd.DataFrame) -> go.Figure:
    d = planned_start_df.copy()
    if d.empty:
        return chart_layout(go.Figure(), 340, legend="none")
    d["event_label"] = d["target_lane"] + " · " + d["sponsor"].str.slice(0, 22) + " · " + d["nct_id"]
    d["start_display"] = d["start_date"].dt.strftime("%b %d, %Y")
    fig = px.scatter(
        d,
        x="start_date",
        y="event_label",
        size="enrollment",
        color="target_lane",
        custom_data=["start_display", "title", "status", "phase", "indication_hint", "modality_class", "line_of_therapy"],
        title="Forward Starts: Trials Expected to Begin",
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[1]}</b><br>Start: %{customdata[0]}<br>Status: %{customdata[2]}<br>Phase: %{customdata[3]}<br>Indication: %{customdata[4]}<br>Modality: %{customdata[5]}<br>LOT: %{customdata[6]}<extra></extra>"
    )
    fig.update_yaxes(title="", autorange="reversed")
    fig.update_xaxes(title="Planned / estimated start date", tickformat="%b %Y")
    return chart_layout(fig, max(430, min(820, 130 + len(d) * 24)), legend="right")


def forward_completion_chart(expected_completion_df: pd.DataFrame) -> go.Figure:
    d = expected_completion_df.copy()
    if d.empty:
        return chart_layout(go.Figure(), 340, legend="none")
    d["event_label"] = d["target_lane"] + " · " + d["sponsor"].str.slice(0, 22) + " · " + d["nct_id"]
    d["completion_display"] = d["primary_completion_date"].dt.strftime("%b %d, %Y")
    fig = px.scatter(
        d,
        x="primary_completion_date",
        y="event_label",
        size="enrollment",
        color="phase",
        custom_data=["completion_display", "title", "status", "target_lane", "indication_hint", "combo_category", "line_of_therapy"],
        title="Forward Completions: Primary Completion Windows",
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[1]}</b><br>Primary completion: %{customdata[0]}<br>Status: %{customdata[2]}<br>Lane: %{customdata[3]}<br>Indication: %{customdata[4]}<br>Therapy context: %{customdata[5]}<br>LOT: %{customdata[6]}<extra></extra>"
    )
    fig.update_yaxes(title="", autorange="reversed")
    fig.update_xaxes(title="Primary completion date", tickformat="%b %Y")
    return chart_layout(fig, max(430, min(820, 130 + len(d) * 24)), legend="right")
