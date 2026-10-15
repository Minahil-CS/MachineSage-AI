import json
import os
import time
from pathlib import Path

import streamlit as st
from engine import analyze_incident, load_manual_chunks, retrieve_evidence, generate_ai_report, evaluate_incident

ROOT = Path(__file__).parent
st.set_page_config(page_title="MachineSage AI", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; max-width: 1200px;}
.hero {padding: 1.3rem 1.5rem; border-radius: 16px; background: linear-gradient(120deg,#12263a,#176b70); color:white; margin-bottom:1rem;}
.hero h1 {margin:0; color:white; font-size:2.2rem;}
.hero p {margin:.45rem 0 0 0; color:#e7f5f4;}
.small-note {font-size:.88rem; color: #667085;}
</style>
<div class="hero">
<h1>🛠️ MachineSage AI</h1>
<p>Evidence-first machine incident triage · Sensor checks · Manual-grounded AI assistance</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("About this prototype")
    st.write("A research/demo assistant for investigating example industrial machine incidents.")
    st.caption("Not a certified safety, diagnostic, or predictive-maintenance system.")
    st.divider()
    st.subheader("Inference configuration")
    use_ai = st.toggle("Use AMD-hosted model", value=False, help="Requires an OpenAI-compatible AMD Token Factory endpoint and API key.")
    api_base = st.text_input("API base URL", value=os.getenv("AMD_API_BASE_URL", ""), placeholder="https://…")
    model_name = st.text_input("Model name", value=os.getenv("AMD_MODEL", ""), placeholder="Model ID from provider")
    api_key = st.text_input("API key", value=os.getenv("AMD_API_KEY", ""), type="password", help="Stored only in this session; do not paste into GitHub.")
    st.caption("If unavailable, the app still runs with a transparent local evidence-based report.")

manual_chunks = load_manual_chunks(ROOT / "data" / "sample_manual.txt")

st.info("Demo mode uses synthetic readings and a sample reference manual. Replace the sample manual and thresholds with validated, machine-specific documentation before any real-world use.")

left, right = st.columns([1.05, 0.95], gap="large")
with left:
    st.subheader("1 · Describe a machine incident")
    preset = st.selectbox("Load a demo case", [
        "Custom incident",
        "Demo A — Pump vibration elevated",
        "Demo B — Motor temperature elevated",
        "Demo C — Pressure below operating range",
    ])
    presets = {
        "Demo A — Pump vibration elevated": {"machine":"Centrifugal pump P-101","vibration":8.2,"temperature":67.0,"pressure":4.1,"current":12.0,"description":"Operator reports unusual vibration and a rattling sound during operation."},
        "Demo B — Motor temperature elevated": {"machine":"Electric motor M-204","vibration":2.1,"temperature":96.0,"pressure":5.0,"current":18.5,"description":"Motor casing temperature is higher than its usual baseline."},
        "Demo C — Pressure below operating range": {"machine":"Process pump P-303","vibration":2.8,"temperature":71.0,"pressure":1.2,"current":10.2,"description":"Discharge pressure is lower than the expected operating range."},
    }
    defaults = presets.get(preset, {"machine":"Centrifugal pump P-101","vibration":3.1,"temperature":68.0,"pressure":4.2,"current":11.4,"description":""})
    machine = st.text_input("Machine / asset label", value=defaults["machine"])
    description = st.text_area("Operator report", value=defaults["description"], height=100, placeholder="Describe what was observed…")
    c1,c2 = st.columns(2)
    with c1:
        vibration = st.number_input("Vibration (mm/s, example units)", min_value=0.0, max_value=100.0, value=float(defaults["vibration"]), step=0.1)
        temperature = st.number_input("Temperature (°C)", min_value=-50.0, max_value=300.0, value=float(defaults["temperature"]), step=1.0)
    with c2:
        pressure = st.number_input("Pressure (bar, example units)", min_value=0.0, max_value=100.0, value=float(defaults["pressure"]), step=0.1)
        current = st.number_input("Current (A, example units)", min_value=0.0, max_value=500.0, value=float(defaults["current"]), step=0.1)
    submitted = st.button("Analyze incident", type="primary", use_container_width=True)

with right:
    st.subheader("2 · Evidence and analysis")
    if submitted:
        incident = {
            "machine": machine.strip() or "Unspecified asset",
            "description": description.strip(),
            "readings": {"vibration_mm_s": vibration, "temperature_c": temperature, "pressure_bar": pressure, "current_a": current},
        }
        checks = analyze_incident(incident)
        evidence = retrieve_evidence(checks, manual_chunks)
        with st.spinner("Preparing evidence-first report…"):
            report, provider_used, error = generate_ai_report(
                incident, checks, evidence,
                enabled=use_ai, api_base=api_base, model=model_name, api_key=api_key
            )
        st.session_state["last_result"] = {"incident": incident, "checks": checks, "evidence": evidence, "report": report, "provider": provider_used, "error": error}
    result = st.session_state.get("last_result")
    if result:
        checks = result["checks"]
        flags = [x for x in checks if x["status"] == "FLAG"]
        status = "Review recommended" if flags else "No configured threshold exceeded"
        st.metric("Rule-check status", status, delta=f"{len(flags)} flagged reading(s)" if flags else "0 flagged readings")
        cols = st.columns(4)
        for col, key, label, unit in zip(cols, ["vibration_mm_s","temperature_c","pressure_bar","current_a"], ["Vibration","Temperature","Pressure","Current"], ["mm/s","°C","bar","A"]):
            col.metric(label, f'{result["incident"]["readings"][key]:g} {unit}')
        st.markdown("#### Configured threshold checks")
        for check in checks:
            icon = "⚠️" if check["status"] == "FLAG" else "✅"
            st.write(f'{icon} **{check["label"]}:** {check["value"]} {check["unit"]} — {check["message"]}')
        st.markdown("#### AI / rule-based report")
        if result["provider"] == "AMD":
            st.success("Report generated using the configured AMD-hosted model.")
        else:
            st.caption("Local fallback report (AMD inference was not used for this result).")
        st.markdown(result["report"])
        if result["error"]:
            st.warning("AMD request was not completed: " + result["error"])
        st.markdown("#### Retrieved manual evidence")
        if result["evidence"]:
            for idx, item in enumerate(result["evidence"], 1):
                with st.expander(f'Evidence {idx} · {item["section"]}'):
                    st.write(item["text"])
        else:
            st.write("No matching passage found. The report should not claim manual support.")
        payload = {"incident": result["incident"], "checks": result["checks"], "evidence": result["evidence"], "report": result["report"], "provider_used": result["provider"]}
        st.download_button("Download incident report (JSON)", json.dumps(payload, indent=2), file_name="machinesage_incident_report.json", mime="application/json")
    else:
        st.write("Choose a demo case on the left and click **Analyze incident**.")
        st.markdown("""
        **What this demo shows**
        - Deterministic threshold checks with visible rules
        - Retrieval of relevant sample manual passages
        - An optional AMD-hosted model for explanation
        - Clear separation between measured values and AI interpretation
        """)

st.divider()
st.subheader("3 · Quick evaluation")
st.write("Run the bundled synthetic cases to inspect how the configured rules behave. These tests do not establish real-world safety or predictive accuracy.")
if st.button("Run demo evaluation"):
    results = evaluate_incident(manual_chunks)
    st.dataframe(results, use_container_width=True, hide_index=True)
    st.download_button("Download evaluation results (CSV)", results.to_csv(index=False), file_name="machinesage_demo_evaluation.csv", mime="text/csv")

st.caption("MachineSage AI · Hackathon prototype · Synthetic examples only · Human review required")
