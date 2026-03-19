"""
IndusDiag — Streamlit UI
Properly wired to IndusDiagAgent (app/agent.py)

Place this file in your project root (same level as main.py).
Run:  streamlit run app.py
"""

import io
import json
import os
import sys
import tempfile
import time
import traceback
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Project root on sys.path ─────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IndusDiag",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:      #080b10;
    --surf:    #0d1117;
    --card:    #111820;
    --bdr:     #1c2433;
    --bdr2:    #263040;
    --teal:    #00d4aa;
    --teal-bg: rgba(0,212,170,.08);
    --amber:   #f5a623;
    --amb-bg:  rgba(245,166,35,.08);
    --red:     #f05050;
    --red-bg:  rgba(240,80,80,.08);
    --blue:    #4a9eff;
    --blu-bg:  rgba(74,158,255,.08);
    --text:    #dde6f0;
    --muted:   #5a6a7e;
    --mono:    'JetBrains Mono', monospace;
    --sans:    'DM Sans', sans-serif;
}

html, body, .stApp { background: var(--bg) !important; font-family: var(--sans) !important; color: var(--text) !important; }
.main .block-container { padding: 1.5rem 2rem 4rem !important; max-width: 1440px !important; }
#MainMenu, footer, .stDeployButton { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; border-bottom: 1px solid var(--bdr) !important; }

section[data-testid="stSidebar"] { background: var(--surf) !important; border-right: 1px solid var(--bdr) !important; }
section[data-testid="stSidebar"] * { color: var(--text) !important; }

.stTextInput > div > div > input,
.stTextArea textarea {
    background: var(--card) !important; border: 1px solid var(--bdr2) !important;
    border-radius: 8px !important; color: var(--text) !important; font-family: var(--sans) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus { border-color: var(--teal) !important; box-shadow: 0 0 0 2px rgba(0,212,170,.15) !important; }

.stButton > button {
    background: var(--teal) !important; color: #060a0d !important; border: none !important;
    border-radius: 8px !important; font-family: var(--sans) !important;
    font-weight: 600 !important; font-size: 14px !important; transition: opacity .15s !important;
}
.stButton > button:hover { opacity: .85 !important; }
.stButton > button:disabled { background: var(--bdr2) !important; color: var(--muted) !important; }

.stFileUploader > div {
    background: var(--card) !important; border: 1.5px dashed var(--bdr2) !important; border-radius: 10px !important;
}

[data-testid="stMetric"] {
    background: var(--card) !important; border: 1px solid var(--bdr) !important;
    border-radius: 10px !important; padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"] p { color: var(--muted) !important; font-size: 12px !important; }
[data-testid="stMetricValue"]   { color: var(--text) !important; font-family: var(--mono) !important; }

.stTabs [data-baseweb="tab-list"] {
    background: var(--surf) !important; border: 1px solid var(--bdr) !important;
    border-radius: 10px !important; padding: 4px !important; gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: var(--muted) !important;
    border-radius: 7px !important; font-family: var(--sans) !important;
    font-weight: 500 !important; font-size: 13px !important;
}
.stTabs [aria-selected="true"] { background: var(--card) !important; color: var(--teal) !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem !important; }

.stProgress > div > div { background: var(--bdr) !important; border-radius: 4px !important; }
.stProgress > div > div > div { background: var(--teal) !important; border-radius: 4px !important; }

/* Custom helpers */
.icard { background:var(--card); border:1px solid var(--bdr); border-radius:12px; padding:1.1rem 1.3rem; margin-bottom:.7rem; }
.a-teal  { border-left:3px solid var(--teal)  !important; }
.a-amber { border-left:3px solid var(--amber) !important; }
.a-red   { border-left:3px solid var(--red)   !important; }
.a-blue  { border-left:3px solid var(--blue)  !important; }

.ph {
    font-family:var(--mono); font-size:11px; font-weight:600; color:var(--teal);
    letter-spacing:.1em; text-transform:uppercase; border-bottom:1px solid var(--bdr);
    padding-bottom:.45rem; margin-bottom:.75rem;
}
.badge { display:inline-block; padding:2px 9px; border-radius:20px; font-size:11px; font-weight:700; font-family:var(--mono); }
.bc { background:var(--red-bg);  color:var(--red);   border:1px solid rgba(240,80,80,.3);  }
.bw { background:var(--amb-bg);  color:var(--amber); border:1px solid rgba(245,166,35,.3); }
.bo { background:var(--teal-bg); color:var(--teal);  border:1px solid rgba(0,212,170,.3);  }

.term {
    background:#04060a; border:1px solid var(--bdr); border-radius:10px;
    padding:1.2rem 1.4rem; font-family:var(--mono); font-size:12.5px;
    line-height:1.9; color:#7a9ab0; overflow-x:auto;
}
.tg{color:#2ecc71}.ta{color:#f0b429}.tr{color:#f05050}.tb{color:#4a9eff}.tm{color:#253040}.tw{color:var(--text);font-weight:600}

.chat-u { background:var(--teal-bg); border:1px solid rgba(0,212,170,.2); border-radius:12px 12px 2px 12px; padding:.65rem 1rem; margin:.35rem 0 .35rem 4rem; font-size:14px; }
.chat-a { background:var(--card);    border:1px solid var(--bdr);          border-radius:12px 12px 12px 2px; padding:.65rem 1rem; margin:.35rem 4rem .35rem 0; font-size:14px; }
.chat-lbl { font-size:10px; font-family:var(--mono); color:var(--teal); letter-spacing:.06em; margin-bottom:3px; }

.rbar { background:var(--bdr); border-radius:4px; height:6px; margin-top:5px; }
</style>
""", unsafe_allow_html=True)


# ── Pure helper functions ─────────────────────────────────────────────────────

def risk_color(score: float) -> str:
    if score >= 0.75: return "var(--red)"
    if score >= 0.50: return "var(--amber)"
    return "var(--teal)"

def risk_label(score: float) -> str:
    if score >= 0.75: return "CRITICAL"
    if score >= 0.50: return "HIGH"
    if score >= 0.25: return "MODERATE"
    return "LOW"

def sev_color(sev: str) -> str:
    s = sev.upper()
    if any(x in s for x in ("CRIT", "HIGH", "ERROR")): return "var(--red)"
    if any(x in s for x in ("WARN", "MED", "MODERATE")):  return "var(--amber)"
    return "var(--teal)"

def sev_acc(sev: str) -> str:
    s = sev.upper()
    if any(x in s for x in ("CRIT", "HIGH", "ERROR")): return "red"
    if any(x in s for x in ("WARN", "MED", "MODERATE")):  return "amber"
    return "teal"

def ph(text: str):
    st.markdown(f'<div class="ph">{text}</div>', unsafe_allow_html=True)

def icard(html: str, acc: str = ""):
    cls = f"icard a-{acc}" if acc else "icard"
    st.markdown(f'<div class="{cls}">{html}</div>', unsafe_allow_html=True)

# ── Extract normalised fields from a finding dict ─────────────────────────────

def f_sev(f: dict) -> str:
    for k in ("severity", "level", "issue_type", "type"):
        if k in f: return str(f[k]).upper()
    return "INFO"

def f_type(f: dict) -> str:
    for k in ("issue_type", "type", "name"):
        if k in f: return str(f[k])
    return "Finding"

def f_msg(f: dict) -> str:
    for k in ("message", "detail", "description", "msg", "summary"):
        if k in f: return str(f[k])
    skip = {"severity","level","issue_type","type","name","score","risk_score","index","tag","timestamp"}
    parts = [f"{k}: {v}" for k, v in f.items() if k not in skip]
    return "  ·  ".join(parts) if parts else str(f)

def f_score(f: dict) -> float:
    for k in ("score", "risk_score", "severity_score"):
        try: return float(f[k])
        except: pass
    return 0.0

def unwrap_risk(rp: dict) -> dict:
    """tool_compute_risk returns {"risk_profile": {...}} — unwrap if needed."""
    if "risk_profile" in rp and isinstance(rp["risk_profile"], dict):
        return rp["risk_profile"]
    return rp

def get_risk_score(rp: dict) -> float:
    rp = unwrap_risk(rp)
    for k in ("risk_score", "score"):
        try: return float(rp[k])
        except: pass
    return 0.0

def get_risk_level(rp: dict) -> str:
    rp = unwrap_risk(rp)
    for k in ("risk_level", "level"):
        if k in rp: return str(rp[k]).upper()
    return risk_label(get_risk_score(rp))


# ── Import check ──────────────────────────────────────────────────────────────

@st.cache_resource
def check_imports():
    try:
        from app.agent import IndusDiagAgent  # noqa
        return True, ""
    except Exception:
        return False, traceback.format_exc()

agent_ok, agent_err = check_imports()


# ── Session state defaults ────────────────────────────────────────────────────

_defaults = dict(
    agent=None, report=None, findings=[], scored=[],
    risk_profile={}, tool_log=[], df=None,
    chat=[], history_log=[], ran=False, error=None,
)
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        '<div style="font-family:var(--mono);font-size:20px;font-weight:700;'
        'color:var(--teal);letter-spacing:-.01em">⬡ IndusDiag</div>'
        '<div style="font-size:11px;color:var(--muted);font-family:var(--mono);'
        'letter-spacing:.06em;margin-bottom:1.4rem">INDUSTRIAL SENSOR DIAGNOSTICS</div>',
        unsafe_allow_html=True,
    )

    if not agent_ok:
        st.error("Cannot import `app.agent`. Run from the project root with your venv active.")
        with st.expander("Import error"):
            st.code(agent_err)

    st.markdown("**Asset ID**")
    asset_name = st.text_input("Asset ID", value="ConveyorMotorA", label_visibility="collapsed")

    st.markdown("**LLM Backend**")
    backend    = st.selectbox("Backend", ["OpenRouter", "Anthropic Claude"], label_visibility="collapsed")
    use_claude = backend == "Anthropic Claude"

    st.markdown("**Sample Data**")
    sample = st.selectbox("Sample", [
        "— none —",
        "conveyor_motor_overheat.csv",
        "flow_sensor_blockage.csv",
        "sensor_spike.csv",
    ], label_visibility="collapsed")

    if sample != "— none —":
        sp = ROOT / "data" / "samples" / sample
        if st.button("Load sample", use_container_width=True):
            if sp.exists():
                for k in ("ran","agent","report","findings","scored","risk_profile","tool_log","chat","error"):
                    st.session_state[k] = _defaults[k]
                st.session_state.df = pd.read_csv(sp)
                st.success(f"Loaded {sample}")
                st.rerun()
            else:
                st.error(f"File not found: {sp}")

    if st.session_state.history_log:
        st.markdown("---")
        st.markdown("**Recent Sessions**")
        for asset, score, ts in reversed(st.session_state.history_log[-6:]):
            col = "#f05050" if score >= .75 else "#f5a623" if score >= .5 else "#00d4aa"
            st.markdown(
                f'<div style="font-size:11px;font-family:var(--mono);padding:4px 0;'
                f'border-bottom:1px solid #1c2433;color:#5a6a7e">'
                f'<span style="color:{col}">■</span> {asset}'
                f'<span style="float:right">{score:.2f}</span></div>',
                unsafe_allow_html=True,
            )


# ── Page header ───────────────────────────────────────────────────────────────

hc1, hc2 = st.columns([3, 1])
with hc1:
    st.markdown(
        '<h1 style="font-family:var(--mono);font-size:26px;font-weight:700;'
        'color:var(--text);margin:0 0 4px">Industrial Sensor Diagnostics</h1>'
        '<p style="color:var(--muted);font-size:13px;margin:0">'
        'Parse · Detect · Score · Reason · Report — your real IndusDiag agent</p>',
        unsafe_allow_html=True,
    )
with hc2:
    if st.session_state.ran and st.session_state.risk_profile:
        rs  = get_risk_score(st.session_state.risk_profile)
        rl  = get_risk_level(st.session_state.risk_profile)
        col = risk_color(rs)
        st.markdown(
            f'<div style="text-align:right;padding-top:4px">'
            f'<div style="font-size:10px;color:var(--muted);font-family:var(--mono);letter-spacing:.07em">ASSET RISK</div>'
            f'<div style="font-size:36px;font-weight:700;font-family:var(--mono);color:{col};line-height:1.1">{rs:.2f}</div>'
            f'<div style="font-size:11px;color:{col};font-family:var(--mono);letter-spacing:.06em">{rl}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown('<div style="height:1px;background:#1c2433;margin:1rem 0 1.3rem"></div>', unsafe_allow_html=True)


# ── File input ────────────────────────────────────────────────────────────────

t1, t2 = st.tabs(["  Upload CSV  ", "  Paste CSV  "])

with t1:
    uploaded = st.file_uploader("Drop sensor CSV", type=["csv"], label_visibility="collapsed")
    if uploaded:
        try:
            new_df = pd.read_csv(uploaded)
            for k in ("ran","agent","report","findings","scored","risk_profile","tool_log","chat","error"):
                st.session_state[k] = _defaults[k]
            st.session_state.df = new_df
        except Exception as e:
            st.error(f"Could not parse CSV: {e}")

with t2:
    pasted = st.text_area(
        "Paste CSV content",
        height=130,
        placeholder="timestamp,tag,value,unit,asset,status\n2026-03-18 11:00:00,motor_temp,65.2,C,ConveyorMotorA,ok",
        label_visibility="collapsed",
    )
    if st.button("Parse pasted data"):
        if pasted.strip():
            try:
                new_df = pd.read_csv(StringIO(pasted))
                for k in ("ran","agent","report","findings","scored","risk_profile","tool_log","chat","error"):
                    st.session_state[k] = _defaults[k]
                st.session_state.df = new_df
            except Exception as e:
                st.error(f"Parse error: {e}")


# ── Data preview ──────────────────────────────────────────────────────────────

if st.session_state.df is not None:
    df = st.session_state.df

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{len(df):,}")
    c2.metric("Columns", len(df.columns))
    if "value" in df.columns:
        v = pd.to_numeric(df["value"], errors="coerce")
        c3.metric("Value range", f"{v.min():.2f} – {v.max():.2f}")
    if "status" in df.columns:
        c4.metric("Warning rows", int((df["status"] != "ok").sum()))

    with st.expander("Preview data"):
        st.dataframe(df.head(30), use_container_width=True, hide_index=True)

    st.markdown('<div style="height:.5rem"></div>', unsafe_allow_html=True)

    bc, lc = st.columns([2, 5])
    with bc:
        run_btn = st.button("▶  Run Diagnosis", use_container_width=True, disabled=not agent_ok)
    with lc:
        st.markdown(
            f'<p style="color:var(--muted);font-size:12px;padding-top:.65rem;font-family:var(--mono)">'
            f'asset: <span style="color:var(--teal)">{asset_name}</span> &nbsp;·&nbsp; '
            f'backend: <span style="color:var(--blue)">{backend}</span></p>',
            unsafe_allow_html=True,
        )

    # ── Run the agent ─────────────────────────────────────────────────────────
    if run_btn:
        st.session_state.error = None
        bar = st.progress(0, text="Initialising…")

        try:
            from app.agent import IndusDiagAgent
            import rich as _rich

            # ── Silence Rich globally so it doesn't write to Streamlit's stdout ──
            _orig_rprint = _rich.print
            _rich.print  = lambda *a, **kw: None

            # Also patch the rprint import inside agent module directly
            import app.agent as _agent_mod
            _agent_mod.rprint = lambda *a, **kw: None

            # ── Save CSV to a real temp file (parser.py expects a file path) ──
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False, dir=str(ROOT)
            )
            df.to_csv(tmp, index=False)
            tmp.close()
            tmp_path = tmp.name

            bar.progress(0.12, text="Phase 1 · Parsing sensor data…")

            agent = IndusDiagAgent(
                asset_name=asset_name,
                use_claude=use_claude,
                verbose=False,
            )
            # Silence _log at instance level too
            agent._log = lambda msg: None

            # ── Phase 1 ───────────────────────────────────────────────────
            agent.load_data(tmp_path)
            bar.progress(0.25, text="Phase 1 · Done — data parsed.")

            # ── Phase 2 ───────────────────────────────────────────────────
            bar.progress(0.35, text="Phase 2 · Running 5 detectors…")
            findings = agent.run_detection_tools()

            # ── Phase 3 ───────────────────────────────────────────────────
            bar.progress(0.52, text="Phase 3 · Scoring findings…")
            agent.run_scoring()

            # ── Phase 4 ───────────────────────────────────────────────────
            bar.progress(0.65, text="Phase 4 · Querying memory…")
            history = agent.retrieve_memory()

            # ── Phase 5 ───────────────────────────────────────────────────
            bar.progress(0.78, text="Phase 5 · Generating AI report…")
            report = agent.generate_report(history)

            # ── Phase 6 ───────────────────────────────────────────────────
            bar.progress(0.92, text="Phase 6 · Saving session…")
            agent.save_session()

            bar.progress(1.0, text="Complete ✓")
            time.sleep(0.3)
            bar.empty()

            # Restore rich.print
            _rich.print = _orig_rprint

            # ── Read all results from agent.session directly ──────────────
            raw_findings = agent.session.raw_findings  or []
            scored       = agent.session.scored_findings or []
            rp           = agent.session.risk_profile  or {}
            tool_log     = agent.session.tool_call_log or []

            # Unwrap if tool_compute_risk nested it
            if "risk_profile" in rp and isinstance(rp["risk_profile"], dict):
                rp = rp["risk_profile"]

            st.session_state.agent        = agent
            st.session_state.report       = report
            st.session_state.findings     = raw_findings
            st.session_state.scored       = scored
            st.session_state.risk_profile = rp
            st.session_state.tool_log     = tool_log
            st.session_state.chat         = []
            st.session_state.ran          = True
            st.session_state.error        = None

            rs = get_risk_score(rp)
            st.session_state.history_log.append(
                (asset_name, rs, time.strftime("%H:%M:%S"))
            )

            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            st.rerun()

        except Exception:
            bar.empty()
            st.session_state.error = traceback.format_exc()
            st.session_state.ran   = False

    # Show any error with full traceback
    if st.session_state.error:
        st.error("The agent raised an exception — full traceback below:")
        st.code(st.session_state.error, language="python")


# ── Results (only shown after a successful run) ───────────────────────────────

if st.session_state.ran and st.session_state.report is not None:

    agent    = st.session_state.agent       # IndusDiagAgent instance
    findings = st.session_state.findings    # raw_findings list
    scored   = st.session_state.scored      # scored_findings list
    rp       = st.session_state.risk_profile
    report   = st.session_state.report      # LLM report string
    tool_log = st.session_state.tool_log    # tool_call_log list

    rs  = get_risk_score(rp)
    rl  = get_risk_level(rp)
    rc  = risk_color(rs)

    st.markdown('<div style="height:.3rem"></div>', unsafe_allow_html=True)

    tabs = st.tabs([
        "  Overview  ",
        "  Detectors  ",
        "  Findings  ",
        "  AI Report  ",
        "  Q&A  ",
        "  Raw Log  ",
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 0 — Overview
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[0]:
        left, right = st.columns([3, 1])

        with left:
            ph("Phase 1 · Parse")
            pdata = agent.session.parsed_data if agent else None
            if pdata is not None:
                a, b, c, d = st.columns(4)
                a.metric("Asset",  asset_name)
                b.metric("Rows",   len(pdata))
                c.metric("Tag",    pdata["tag"].iloc[0]  if "tag"  in pdata.columns else "—")
                d.metric("Unit",   pdata["unit"].iloc[0] if "unit" in pdata.columns else "—")

            st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
            ph("Telemetry Chart")
            if pdata is not None and "value" in pdata.columns:
                chart = pdata.copy()
                chart["value"] = pd.to_numeric(chart["value"], errors="coerce")
                if "timestamp" in chart.columns:
                    try:
                        chart["timestamp"] = pd.to_datetime(chart["timestamp"])
                        chart = chart.set_index("timestamp")
                    except Exception:
                        pass
                st.line_chart(chart[["value"]], color="#00d4aa", height=210)

            st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
            ph("Phase 3 · Value Statistics")
            if pdata is not None and "value" in pdata.columns:
                v = pd.to_numeric(pdata["value"], errors="coerce").dropna()
                s1, s2, s3, s4 = st.columns(4)
                s1.metric("Mean",  f"{v.mean():.3f}")
                s2.metric("Std",   f"{v.std():.3f}")
                s3.metric("Min",   f"{v.min():.3f}")
                s4.metric("Max",   f"{v.max():.3f}")

        with right:
            ph("Risk Profile")
            pct = int(rs * 100)
            icard(
                f'<div style="text-align:center">'
                f'<div style="font-size:10px;color:var(--muted);font-family:var(--mono);letter-spacing:.08em;margin-bottom:4px">RISK SCORE</div>'
                f'<div style="font-size:58px;font-weight:700;font-family:var(--mono);color:{rc};line-height:1">{rs:.2f}</div>'
                f'<div style="font-size:12px;font-family:var(--mono);color:{rc};letter-spacing:.07em;margin:5px 0 12px">{rl}</div>'
                f'<div class="rbar"><div style="width:{pct}%;height:6px;background:{rc};border-radius:4px"></div></div>'
                f'</div>',
                acc="red" if rs >= .75 else "amber" if rs >= .5 else "teal",
            )

            st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
            ph("Dominant Issue")
            dom = rp.get("dominant_issue", "—")
            icard(f'<span style="font-family:var(--mono);font-size:13px;color:var(--amber)">{dom}</span>', acc="amber")

            st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
            ph("Detector Summary")
            n_crit = sum(1 for f in findings if any(x in f_sev(f) for x in ("CRIT","HIGH","ERROR")))
            n_warn = sum(1 for f in findings if any(x in f_sev(f) for x in ("WARN","MED")))
            n_ok   = max(0, 5 - n_crit - n_warn)
            for cnt, lbl, col, acc in [
                (n_crit, "FAULT",   "var(--red)",   "red"),
                (n_warn, "WARNING", "var(--amber)", "amber"),
                (n_ok,   "PASS",    "var(--teal)",  "teal"),
            ]:
                st.markdown(
                    f'<div class="icard a-{acc}" style="padding:.6rem 1rem;margin-bottom:5px">'
                    f'<span style="font-family:var(--mono);font-size:22px;font-weight:700;color:{col}">{cnt}</span>'
                    f'<span style="color:var(--muted);font-size:12px;margin-left:8px">{lbl}</span></div>',
                    unsafe_allow_html=True,
                )

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 — Detectors
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[1]:
        ph("Phase 2 · Detector Tool Calls")

        DETECTORS = [
            ("run_spike_detector",          "Spike detection"),
            ("run_flatline_detector",        "Flatline detection"),
            ("run_missing_data_detector",    "Missing data detection"),
            ("run_out_of_range_detector",    "Out-of-range detection"),
            ("run_drift_detector",           "Drift detection"),
        ]

        for tool_name, label in DETECTORS:
            # Find this tool in the log
            entry = next((e for e in tool_log if e.get("tool") == tool_name), None)

            result_data = entry.get("result_summary", {}) if entry else {}

            # result_summary may be stored as a string repr — parse finding count safely
            n_found = 0
            if isinstance(result_data, dict):
                n_found = len(result_data.get("findings", []))
            elif isinstance(result_data, str):
                # It was stored as str(result) — count "issue_type" occurrences as proxy
                n_found = result_data.count("issue_type")

            ran_ok  = entry is not None
            has_hit = n_found > 0

            if has_hit:
                status, slabel, acc = "var(--red)",   "FAULT", "red"
                note = f"{n_found} finding(s)"
            elif ran_ok:
                status, slabel, acc = "var(--teal)",  "PASS",  "teal"
                note = "clean"
            else:
                status, slabel, acc = "var(--muted)", "—",     ""
                note = "not logged"

            st.markdown(
                f'<div class="icard a-{acc}" style="display:flex;align-items:center;gap:14px;'
                f'padding:.7rem 1rem;margin-bottom:6px">'
                f'<code style="font-family:var(--mono);font-size:12px;color:#6e8aaa;'
                f'background:#0d1117;padding:2px 8px;border-radius:4px;flex:1">{tool_name}</code>'
                f'<span style="font-family:var(--mono);font-size:12px;font-weight:700;'
                f'color:{status};min-width:54px">{slabel}</span>'
                f'<span style="font-size:12px;color:var(--muted)">{note}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if tool_log:
            st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
            ph("Full Tool Call Log")
            for entry in tool_log:
                with st.expander(f"🔧  {entry.get('tool', '?')}"):
                    st.json({
                        "tool":   entry.get("tool"),
                        "kwargs": entry.get("kwargs", {}),
                        "result": entry.get("result_summary", {}),
                    })

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 — Findings
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[2]:
        ph(f"Phase 3 · Findings  ({len(findings)} total)")

        if not findings:
            st.success("No anomalies detected — asset is operating normally.")
        else:
            for f in findings:
                sev   = f_sev(f)
                typ   = f_type(f)
                msg   = f_msg(f)
                score = f_score(f)
                col   = sev_color(sev)
                acc   = sev_acc(sev)
                pct   = int(min(score, 1.0) * 100)

                score_html = (
                    f'<span style="font-family:var(--mono);font-size:13px;color:{col}">{score:.2f}</span>'
                    if score else ""
                )
                bar_html = (
                    f'<div class="rbar">'
                    f'<div style="width:{pct}%;height:5px;background:{col};border-radius:4px"></div>'
                    f'</div>'
                    if score else ""
                )
                mb = "7px" if score else "0"

                st.markdown(
                    f'<div class="icard a-{acc}">'
                    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:5px">'
                    f'<span style="font-family:var(--mono);font-size:11px;font-weight:700;color:{col}">[{sev}]</span>'
                    f'<span style="font-size:14px;font-weight:500;flex:1">{typ}</span>'
                    f'{score_html}'
                    f'</div>'
                    f'<div style="font-size:13px;color:#8eaabf;margin-bottom:{mb}">{msg}</div>'
                    f'{bar_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        if scored:
            st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
            ph("Scored Findings (agent.session.scored_findings)")
            try:
                st.dataframe(pd.DataFrame(scored), use_container_width=True, hide_index=True)
            except Exception:
                st.json(scored)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 — AI Report
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[3]:
        ph("Phase 5 · LLM Diagnostic Report")
        st.markdown(
            f'<p style="font-size:12px;color:var(--muted);font-family:var(--mono);margin-bottom:1rem">'
            f'Generated by <span style="color:var(--blue)">{backend}</span></p>',
            unsafe_allow_html=True,
        )

        # Render the report — preserve line breaks, no HTML injection risk
        for line in report.split("\n"):
            if line.strip().startswith("#"):
                st.markdown(f"**{line.lstrip('#').strip()}**")
            elif line.strip():
                st.markdown(line)
            else:
                st.markdown("")

        st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)
        ph("Export")
        export_data = {
            "asset":        asset_name,
            "backend":      backend,
            "timestamp":    time.strftime("%Y-%m-%d %H:%M:%S"),
            "risk_score":   rs,
            "risk_level":   rl,
            "findings":     findings,
            "risk_profile": rp,
            "report":       report,
        }
        st.download_button(
            "⬇  Download report (JSON)",
            data=json.dumps(export_data, indent=2, default=str),
            file_name=f"indusdiag_{asset_name}_{time.strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4 — Q&A
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[4]:
        ph("Follow-up Q&A — agent.ask()")
        st.markdown(
            '<p style="font-size:13px;color:var(--muted);margin-bottom:1rem">'
            'Calls your real <code>IndusDiagAgent.ask()</code> — full session context is retained.</p>',
            unsafe_allow_html=True,
        )

        QUICK = [
            "What is the most urgent action?",
            "What is the root cause of this fault?",
            "Is an immediate shutdown necessary?",
            "Compare this to past incidents on this asset.",
        ]
        qcols = st.columns(len(QUICK))
        for i, q in enumerate(QUICK):
            if qcols[i].button(q, key=f"qq{i}", use_container_width=True):
                if agent:
                    with st.spinner("Asking agent…"):
                        try:
                            ans = agent.ask(q)
                        except Exception:
                            ans = traceback.format_exc()
                    st.session_state.chat.append({"role": "user",  "text": q})
                    st.session_state.chat.append({"role": "agent", "text": ans})
                    st.rerun()

        # Render chat history
        for msg in st.session_state.chat:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-u">{msg["text"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="chat-a">'
                    f'<div class="chat-lbl">IndusDiag</div>'
                    f'{msg["text"]}</div>',
                    unsafe_allow_html=True,
                )

        # Free text input
        with st.form("qa_form", clear_on_submit=True):
            user_q = st.text_input(
                "Ask a follow-up",
                placeholder="e.g. Should we shut this asset down immediately?",
                label_visibility="collapsed",
            )
            if st.form_submit_button("Send ↗") and user_q.strip() and agent:
                with st.spinner("Asking agent…"):
                    try:
                        ans = agent.ask(user_q.strip())
                    except Exception:
                        ans = traceback.format_exc()
                st.session_state.chat.append({"role": "user",  "text": user_q.strip()})
                st.session_state.chat.append({"role": "agent", "text": ans})
                st.rerun()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 5 — Raw Log
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[5]:
        ph("Full Agent Run Log")

        pdata = agent.session.parsed_data if agent else None

        lines = [
            f'<span class="tm"># IndusDiag — {time.strftime("%Y-%m-%d %H:%M:%S")}</span>',
            f'<span class="tm"># Asset: {asset_name}  |  Backend: {backend}</span>',
            "",
            f'<span class="tg">$</span> <span class="tw">python main.py --file sensor_data.csv '
            f'--asset {asset_name}{"  --claude" if use_claude else ""}</span>',
            "",
            '<span class="tb tw">━━━  PHASE 1 · PARSE  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>',
        ]
        if pdata is not None:
            lines += [
                f'  Asset:    <span class="tg">{asset_name}</span>',
                f'  Rows:     <span class="tg">{len(pdata)}</span>',
                f'  Columns:  <span class="tg">✓  {", ".join(pdata.columns.tolist())}</span>',
            ]
        lines += [
            "",
            '<span class="tb tw">━━━  PHASE 2 · DETECT  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>',
        ]
        det_tools = [e for e in tool_log if "detector" in e.get("tool", "")]
        for e in det_tools:
            tname = e.get("tool", "?")
            res   = e.get("result_summary", {})
            n     = len(res.get("findings", [])) if isinstance(res, dict) else 0
            if n == 0 and isinstance(res, str):
                n = res.count("issue_type")
            status = '<span class="tr tw">FAULT</span>' if n > 0 else '<span class="tg">PASS </span>'
            note   = f"{n} finding(s)" if n > 0 else "clean"
            pad    = " " * max(0, 36 - len(tname))
            lines.append(
                f'  [tool] <span style="color:#6e8aaa">{tname}</span>{pad}{status}'
                f'  <span class="tm">{note}</span>'
            )
        lines += [
            "",
            '<span class="tb tw">━━━  PHASE 3 · SCORE  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>',
            f'  Risk score:  <span style="color:{rc}">{rs:.2f}</span>',
            f'  Risk level:  <span style="color:{rc}">{rl}</span>',
        ]
        if rp.get("dominant_issue"):
            lines.append(f'  Dominant:    <span class="ta">{rp["dominant_issue"]}</span>')

        mem_tools = [e for e in tool_log if any(x in e.get("tool","") for x in ("history","memory","similar"))]
        if mem_tools:
            lines += [
                "",
                '<span class="tb tw">━━━  PHASE 4 · MEMORY  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>',
            ]
            for e in mem_tools:
                res     = e.get("result_summary", {})
                summary = res.get("summary", "") if isinstance(res, dict) else str(res)[:80]
                lines.append(
                    f'  [tool] <span style="color:#6e8aaa">{e["tool"]}</span>'
                    f'   <span class="tb">{summary}</span>'
                )

        lines += [
            "",
            '<span class="tb tw">━━━  PHASE 5 · REPORT  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>',
        ]
        for line in report.split("\n")[:18]:
            escaped = line.replace("<", "&lt;").replace(">", "&gt;")
            lines.append(f'  <span style="color:#8eaabf">{escaped}</span>')
        if len(report.split("\n")) > 18:
            lines.append('  <span class="tm">… see AI Report tab for full output</span>')

        lines += [
            "",
            '<span class="tb tw">━━━  PHASE 6 · SAVE  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>',
            f'  <span class="tg">Session saved → data/memory/{asset_name.lower()}.json</span>',
            "",
            f'<span class="tg">$</span> <span class="tm">_</span>',
        ]

        st.markdown(
            f'<div class="term">{"<br>".join(lines)}</div>',
            unsafe_allow_html=True,
        )


# ── Empty state ───────────────────────────────────────────────────────────────

elif st.session_state.df is None:
    st.markdown(
        '<div style="text-align:center;padding:5rem 2rem">'
        '<div style="font-size:56px;opacity:.12;margin-bottom:1rem">⬡</div>'
        '<div style="font-size:15px;color:var(--muted);margin-bottom:.5rem">No data loaded yet</div>'
        '<div style="font-size:13px;color:#253040">'
        'Upload a sensor CSV, paste raw data above, or pick a sample from the sidebar.'
        '</div></div>',
        unsafe_allow_html=True,
    )