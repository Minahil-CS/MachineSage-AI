# MachineSage AI — Evidence-Based Maintenance Copilot

MachineSage AI is a hackathon prototype for investigating **synthetic industrial machine incidents**. It combines transparent Python threshold checks, simple keyword retrieval over a demonstration manual, an optional OpenAI-compatible AMD-hosted model endpoint, and a downloadable incident report.

> **Safety and scope:** This is not a certified diagnostic or predictive-maintenance system. The thresholds are illustrative, and the bundled manual is fictional. Do not use the application to operate, repair, or assess real equipment. Qualified personnel and site-approved procedures must make all real-world decisions.

## Features

- Streamlit UI with three preloaded demo incidents and custom input
- Four configurable sensor checks: vibration, temperature, pressure, current
- Visible rule outputs and uncertainty notes
- Retrieval of relevant passages from `data/sample_manual.txt`
- Optional AMD-hosted inference through an OpenAI-compatible chat-completions endpoint
- Local fallback report when AMD inference is not configured or fails
- JSON incident export and synthetic rule-test CSV

## Quick start

Requires Python 3.10+.

```bash
git clone https://github.com/YOUR-USERNAME/MachineSage-AI.git
cd MachineSage-AI
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.venv\\Scripts\\Activate.ps1
```

**Windows Command Prompt**
```bat
.venv\\Scripts\\activate.bat
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The local demo works without an API key. Select a demo case and click **Analyze incident**.

## Optional AMD-hosted inference

1. Obtain API access through the hackathon's approved AMD Token Factory service.
2. Confirm the provider's current API base URL, model ID, and authentication format in its documentation.
3. In the app sidebar, enable **Use AMD-hosted model**, then enter the endpoint, model ID, and API key.
4. Run a demo and confirm the UI explicitly says the report was generated using the configured AMD-hosted model.

The app expects an OpenAI-compatible `POST /chat/completions` endpoint with bearer-token authentication. If your provider uses a different endpoint or request schema, adapt `generate_ai_report()` in `engine.py` according to the official provider documentation. The app falls back to the local report if the request fails.

**Never commit API keys.** Use the sidebar for local testing. For hosted deployments, store secrets in the platform's secret manager, never in source code or screenshots.

## Demo walkthrough

1. Start the app.
2. Select **Demo A — Pump vibration elevated**.
3. Click **Analyze incident**.
4. Show the vibration rule flag, evidence panel, and uncertainty statement.
5. Repeat with **Demo B — Motor temperature elevated** and **Demo C — Pressure below operating range**.
6. Click **Run demo evaluation** and download the CSV.
7. If AMD inference is configured, show that the app reports AMD as the provider only after a successful API response.

## Evaluation and limitations

The bundled evaluation checks whether selected synthetic cases trigger the expected illustrative rule flags. It does **not** evaluate an AI model's factual accuracy, prove predictive ability, or validate any industrial thresholds. A future evaluation should use authorized machine-specific data, expert-labelled outcomes, documented metrics, and a safety review.

## Repository structure

```text
MachineSage-AI/
├── app.py
├── engine.py
├── requirements.txt
├── data/
│   └── sample_manual.txt
├── tests/
│   └── test_engine.py
├── .gitignore
└── README.md
```

## Technology

- Python
- Streamlit
- pandas
- Requests
- Optional AMD-hosted model inference via an OpenAI-compatible API

## AMD integration statement

AMD inference is optional in the source code so the application can be tested without credentials. A submission claiming AMD-powered execution must be demonstrated with a successful request to an approved AMD-hosted model endpoint and must describe that evidence accurately. The local fallback alone does not satisfy an AMD workload requirement.

## License

MIT. See `LICENSE`.
