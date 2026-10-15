import json
import re
from pathlib import Path

import pandas as pd
import requests


# Illustrative demo thresholds only. These are not universal machine limits.
THRESHOLDS = {
    "vibration_mm_s": {"label": "Vibration", "unit": "mm/s", "low": 0.0, "high": 7.1,
                       "note": "Illustrative demo threshold; use asset-specific validated limits."},
    "temperature_c": {"label": "Temperature", "unit": "°C", "low": -20.0, "high": 85.0,
                      "note": "Illustrative demo threshold; use asset-specific validated limits."},
    "pressure_bar": {"label": "Pressure", "unit": "bar", "low": 2.0, "high": 8.0,
                     "note": "Illustrative demo range; actual acceptable pressure depends on the asset."},
    "current_a": {"label": "Current", "unit": "A", "low": 0.0, "high": 25.0,
                  "note": "Illustrative demo threshold; use nameplate and operating data."},
}


def analyze_incident(incident):
    """Apply transparent, illustrative rules to the provided synthetic readings."""
    results = []
    readings = incident.get("readings", {})
    for key, rule in THRESHOLDS.items():
        value = float(readings.get(key, 0.0))
        outside = value < rule["low"] or value > rule["high"]
        if outside:
            if value < rule["low"]:
                message = f"Below illustrative lower bound ({rule['low']} {rule['unit']})."
            else:
                message = f"Above illustrative upper bound ({rule['high']} {rule['unit']})."
            status = "FLAG"
        else:
            message = f"Within illustrative configured range ({rule['low']}–{rule['high']} {rule['unit']})."
            status = "OK"
        results.append({
            "key": key, "label": rule["label"], "value": value, "unit": rule["unit"],
            "status": status, "message": message, "rule_note": rule["note"],
            "low": rule["low"], "high": rule["high"],
        })
    return results


def load_manual_chunks(path):
    text = Path(path).read_text(encoding="utf-8")
    chunks = []
    section = "General"
    buffer = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if buffer:
                chunks.append({"section": section, "text": " ".join(buffer)})
                buffer = []
            section = line.lstrip("# ").strip() or "General"
        else:
            buffer.append(line)
    if buffer:
        chunks.append({"section": section, "text": " ".join(buffer)})
    return chunks


def retrieve_evidence(checks, chunks, top_k=3):
    """Simple transparent keyword retrieval; returns passages, not authoritative citations."""
    flagged_terms = set()
    for check in checks:
        if check["status"] == "FLAG":
            flagged_terms.update(re.findall(r"[a-z]+", check["label"].lower()))
    scored = []
    for chunk in chunks:
        text = (chunk["section"] + " " + chunk["text"]).lower()
        score = sum(1 for term in flagged_terms if term in text)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        scored = [(0, chunk) for chunk in chunks[:1]]
    return [{"section": c["section"], "text": c["text"], "match_score": s, "source": "data/sample_manual.txt (illustrative sample)"} for s, c in scored[:top_k]]


def _local_report(incident, checks, evidence):
    flags = [c for c in checks if c["status"] == "FLAG"]
    lines = [
        f"### Incident summary\n**Asset:** {incident['machine']}",
        incident.get("description") or "No operator narrative supplied.",
        "### Rule-based observations",
    ]
    if flags:
        for c in flags:
            lines.append(f"- **{c['label']} flagged:** {c['message']} This is a configurable demo rule, not a confirmed fault.")
    else:
        lines.append("- No configured threshold was exceeded. This does not prove the machine is healthy.")
    lines += [
        "### Suggested next steps (review required)",
        "1. Confirm the sensor units, calibration, and timestamp against the asset's records.",
        "2. Compare readings with the manufacturer's documentation and the machine's normal baseline.",
        "3. Follow the site's approved isolation and safety procedures before any physical inspection.",
        "4. Ask a qualified technician to verify the findings before maintenance action.",
        "### Uncertainty",
        "This prototype uses illustrative thresholds and a small sample manual. It cannot diagnose a machine, predict failure, or establish that operation is safe.",
        "### Evidence",
    ]
    if evidence:
        for item in evidence:
            lines.append(f"- **{item['section']}** (sample manual): {item['text']}")
    else:
        lines.append("- No relevant manual passage was retrieved; no manual-backed claim is made.")
    return "\n\n".join(lines)


def generate_ai_report(incident, checks, evidence, enabled=False, api_base="", model="", api_key=""):
    local = _local_report(incident, checks, evidence)
    if not enabled:
        return local, "LOCAL", None
    if not (api_base.strip() and model.strip() and api_key.strip()):
        return local, "LOCAL", "Enter the AMD API base URL, model name, and API key in the sidebar."
    system_prompt = (
        "You are a cautious industrial maintenance documentation assistant for a synthetic demo. "
        "Do not claim to diagnose or predict failure. Do not invent sources, specifications, or measurements. "
        "Only refer to supplied readings and evidence. Clearly distinguish observations from hypotheses. "
        "State uncertainty. Recommend qualified human review and site safety procedures. "
        "The threshold rules are illustrative and not universal limits. Use concise Markdown."
    )
    user_payload = {
        "incident": incident,
        "threshold_checks": checks,
        "retrieved_sample_manual_evidence": evidence,
        "task": "Produce incident summary, observed flags, cautious possible explanations, evidence-linked checks, and uncertainty/human-review notes."
    }
    base = api_base.strip().rstrip("/")
    # Accept either a base URL or a full OpenAI-compatible chat-completions URL.
    url = base if base.endswith("/chat/completions") else base + "/chat/completions"
    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"},
            json={
                "model": model.strip(),
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
                ]
            },
            timeout=35,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "\n".join(str(part.get("text", part)) if isinstance(part, dict) else str(part) for part in content)
        if not str(content).strip():
            raise ValueError("Provider returned an empty message.")
        return str(content), "AMD", None
    except Exception as exc:
        safe_error = f"{type(exc).__name__}: {str(exc)[:240]}"
        return local, "LOCAL", safe_error


def evaluate_incident(chunks):
    cases = [
        ("Normal illustrative case", {"machine":"Demo pump A","description":"Routine reading","readings":{"vibration_mm_s":3.1,"temperature_c":68,"pressure_bar":4.2,"current_a":11.4}}, 0),
        ("High vibration", {"machine":"Demo pump B","description":"Reported vibration","readings":{"vibration_mm_s":8.2,"temperature_c":67,"pressure_bar":4.1,"current_a":12}}, 1),
        ("High temperature", {"machine":"Demo motor C","description":"Elevated casing temperature","readings":{"vibration_mm_s":2.1,"temperature_c":96,"pressure_bar":5,"current_a":18.5}}, 1),
        ("Low pressure", {"machine":"Demo pump D","description":"Low discharge pressure","readings":{"vibration_mm_s":2.8,"temperature_c":71,"pressure_bar":1.2,"current_a":10.2}}, 1),
    ]
    rows = []
    for name, incident, expected_flags in cases:
        checks = analyze_incident(incident)
        actual_flags = sum(c["status"] == "FLAG" for c in checks)
        rows.append({
            "case": name,
            "expected_flag_count": expected_flags,
            "actual_flag_count": actual_flags,
            "test_pass": actual_flags == expected_flags,
            "flagged_checks": ", ".join(c["label"] for c in checks if c["status"] == "FLAG") or "None",
            "scope": "Synthetic rule test only; not a model-accuracy or safety evaluation",
        })
    return pd.DataFrame(rows)
