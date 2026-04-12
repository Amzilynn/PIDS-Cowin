"""
Streamlit Dashboard — Session Report Viewer

Run with:
    streamlit run dso1/src/cv/dashboard.py -- --log session_log.csv
"""

import sys
import argparse
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Co-Win | Delegate Analysis",
    page_icon="🧠",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f0f1a; }
    h1, h2, h3 { color: #64b5f6; }
    .metric-card {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_log(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp_s"] = df["timestamp_ms"] / 1000.0
    return df


def score_color(val: float) -> str:
    if val >= 0.70:
        return "#4caf50"
    elif val >= 0.45:
        return "#ff9800"
    return "#f44336"


def main():
    st.title("🧠 Co-Win — Delegate Performance Report")

    # ── Sidebar: file upload or path ─────────────────────────
    st.sidebar.header("📂 Load Session")
    uploaded = st.sidebar.file_uploader("Upload session_log.csv", type="csv")
    fallback = st.sidebar.text_input("Or enter file path:", "session_log.csv")

    if uploaded:
        df = pd.read_csv(uploaded)
        df["timestamp_s"] = df["timestamp_ms"] / 1000.0
    elif Path(fallback).exists():
        df = load_log(fallback)
    else:
        st.info("👈 Upload a session log CSV or run the pipeline first.")
        st.stop()

    # ── Summary KPIs ──────────────────────────────────────────
    st.subheader("📊 Session Summary")
    c1, c2, c3, c4 = st.columns(4)

    for col, label, key in [
        (c1, "🏆 Performance",  "performance"),
        (c2, "💪 Confidence",   "confidence"),
        (c3, "😰 Stress",       "stress"),
        (c4, "⚡ Engagement",   "engagement"),
    ]:
        val = df[key].mean()
        col.metric(label, f"{val:.0%}")

    st.divider()

    # ── Timeline charts ───────────────────────────────────────
    st.subheader("📈 Performance Over Time")
    fig = px.line(
        df, x="timestamp_s",
        y=["performance", "confidence", "stress", "engagement"],
        labels={"timestamp_s": "Time (s)", "value": "Score", "variable": "Metric"},
        color_discrete_map={
            "performance": "#64b5f6",
            "confidence":  "#4caf50",
            "stress":      "#f44336",
            "engagement":  "#ff9800",
        },
        template="plotly_dark",
    )
    fig.update_layout(legend_title_text="Metric", height=350)
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("😐 Emotion Distribution")
        if "emotion" in df.columns:
            emotion_counts = df["emotion"].value_counts().reset_index()
            emotion_counts.columns = ["emotion", "count"]
            fig2 = px.pie(
                emotion_counts, names="emotion", values="count",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.subheader("🎙️ Tone Distribution")
        if "tone_label" in df.columns:
            tone_counts = df["tone_label"].value_counts().reset_index()
            tone_counts.columns = ["tone", "count"]
            fig3 = px.bar(
                tone_counts, x="tone", y="count",
                template="plotly_dark",
                color="count",
                color_continuous_scale="Blues",
            )
            st.plotly_chart(fig3, use_container_width=True)

    # ── Body language ─────────────────────────────────────────
    st.subheader("🦴 Body Language Over Time")
    body_cols = [c for c in ["posture", "openness", "fidget"] if c in df.columns]
    if body_cols:
        fig4 = px.line(
            df, x="timestamp_s", y=body_cols,
            template="plotly_dark",
            labels={"timestamp_s": "Time (s)", "value": "Score"},
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ── Eye contact ───────────────────────────────────────────
    if "eye_contact" in df.columns:
        eye_pct = df["eye_contact"].map({True: 1, False: 0, "True": 1, "False": 0}).mean()
        st.metric("👁️ Eye Contact", f"{eye_pct:.0%}")

    st.divider()
    st.caption("Co-Win Delegate Training System — DSO1 Module")


if __name__ == "__main__":
    main()
