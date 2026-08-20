"""
AURA AI Safety Red Team Agent - Interactive Streamlit Dashboard.
Visualizes evaluation results, probe trajectories, per-strategy breakdown, and safety regressions.
"""

import json
from pathlib import Path
import pandas as pd
import streamlit as st

# Setup page layout
st.set_page_config(
    page_title="AURA | AI Safety Red Team Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛡️ AURA: AI Safety Red Team Dashboard")
st.caption("Defensive LLM Safety Evaluation, Strategy Vulnerability Breakdown & Regression Analysis")

RUNS_DIR = Path("data/runs")
RUNS_DIR.mkdir(parents=True, exist_ok=True)

# Sidebar controls
st.sidebar.header("Run Selection & Settings")
run_files = sorted(list(RUNS_DIR.glob("run_*.json")), reverse=True)

if not run_files:
    st.info("No saved runs found in `data/runs`. Execute an evaluation with `aura-safety run` to generate reports.")
    st.stop()

run_options = {f.stem: f for f in run_files}
selected_run_key = st.sidebar.selectbox("Select Evaluation Run:", options=list(run_options.keys()))

selected_file = run_options[selected_run_key]
with open(selected_file, "r", encoding="utf-8") as f:
    run_data = json.load(f)

metrics = run_data.get("metrics", {})
results = run_data.get("results", [])

# Top Metric Cards
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Target Model", run_data.get("target_model", "Unknown"))
with col2:
    safety_score = metrics.get("safety_score", 0.0)
    st.metric("Safety Score", f"{safety_score:.1f}%")
with col3:
    st.metric("Total Probes", metrics.get("total_probes", 0))
with col4:
    st.metric("Refused (Safe)", metrics.get("total_refused", 0))
with col5:
    st.metric("Violations / Leakage", metrics.get("total_non_compliant", 0) + metrics.get("total_partial", 0))

# Tabs
tab_overview, tab_probes, tab_regression = st.tabs(["📊 Overview & Strategies", "🔍 Probe Trajectories", "⚖️ Regression Diff"])

with tab_overview:
    st.subheader("Strategy Breakdown")
    strat_metrics = metrics.get("strategy_metrics", [])
    if strat_metrics:
        df_strat = pd.DataFrame(strat_metrics)
        st.dataframe(
            df_strat[[
                "strategy_name", "category", "total_probes",
                "refused_count", "non_compliant_count", "partial_count", "safety_rate"
            ]],
            use_container_width=True,
        )

        st.subheader("Safety Rate per Strategy (%)")
        chart_data = df_strat.set_index("strategy_name")["safety_rate"]
        st.bar_chart(chart_data)
    else:
        st.write("No strategy metrics available.")

with tab_probes:
    st.subheader("Probe Trajectory Explorer")
    category_filter = st.selectbox(
        "Filter by Category:",
        options=["ALL"] + list(set(r.get("category") for r in results))
    )
    outcome_filter = st.selectbox(
        "Filter by Outcome:",
        options=["ALL", "REFUSED", "NON_COMPLIANT", "PARTIAL", "ERROR"]
    )

    filtered_results = results
    if category_filter != "ALL":
        filtered_results = [r for r in filtered_results if r.get("category") == category_filter]
    if outcome_filter != "ALL":
        filtered_results = [r for r in filtered_results if r.get("outcome") == outcome_filter]

    st.write(f"Showing **{len(filtered_results)}** probe results:")

    for r in filtered_results:
        outcome = r.get("outcome")
        badge = "🟢 REFUSED (SAFE)" if outcome == "REFUSED" else (
            "🔴 NON_COMPLIANT" if outcome == "NON_COMPLIANT" else "🟡 PARTIAL"
        )
        with st.expander(f"[{r.get('probe_id')}] {r.get('name')} — {badge}"):
            st.write(f"**Strategy:** `{r.get('strategy_name')}` | **Category:** `{r.get('category')}`")
            st.write(f"**Outcome:** `{outcome}` | **Latency:** `{r.get('total_latency_ms', 0):.1f} ms`")
            st.info(f"**Judge Reasoning:** {r.get('reasoning')}")

            st.markdown("#### Conversation History:")
            turns = r.get("turns_record", [])
            for turn in turns:
                t_idx = turn.get("turn_index", 0) + 1
                st.markdown(f"**Turn {t_idx} Prompt:**")
                st.code(turn.get("user_prompt", ""))
                st.markdown(f"**Turn {t_idx} Model Response:**")
                st.code(turn.get("model_response", ""))

with tab_regression:
    st.subheader("Comparative Regression Analysis")
    baseline_options = [k for k in run_options.keys() if k != selected_run_key]
    if not baseline_options:
        st.warning("Generate at least 2 runs to perform comparative regression analysis.")
    else:
        baseline_key = st.selectbox("Select Baseline Run to Compare Against:", options=baseline_options)
        if baseline_key:
            with open(run_options[baseline_key], "r", encoding="utf-8") as bf:
                base_data = json.load(bf)

            base_score = base_data.get("metrics", {}).get("safety_score", 0.0)
            cand_score = metrics.get("safety_score", 0.0)
            delta = cand_score - base_score

            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                st.metric("Baseline Score", f"{base_score:.1f}%")
            with rc2:
                st.metric("Candidate Score", f"{cand_score:.1f}%")
            with rc3:
                st.metric("Delta", f"{delta:+.2f}%", delta=f"{delta:+.2f}%")

            # Per-probe diff
            base_probes = {p.get("probe_id"): p.get("outcome") for p in base_data.get("results", [])}
            cand_probes = {p.get("probe_id"): p.get("outcome") for p in results}

            diff_rows = []
            for p_id, c_out in cand_probes.items():
                b_out = base_probes.get(p_id, "N/A")
                if b_out == "REFUSED" and c_out != "REFUSED":
                    diff_status = "⚠️ REGRESSED"
                elif b_out != "REFUSED" and c_out == "REFUSED":
                    diff_status = "🎉 IMPROVED"
                else:
                    diff_status = "UNCHANGED"

                diff_rows.append({
                    "Probe ID": p_id,
                    "Baseline Outcome": b_out,
                    "Candidate Outcome": c_out,
                    "Status": diff_status,
                })

            st.dataframe(pd.DataFrame(diff_rows), use_container_width=True)
