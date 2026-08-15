# Self-Correcting Multi-Agent  Workflow

A small demo project that runs a self-correcting multi-agent workflow to produce beginner-friendly explanations for a given topic. The system uses three agents in a loop: a writer (creates a draft), a reviewer (evaluates and requests revisions), and a reviser (improves the draft). The workflow is driven by `langgraph` and uses the Groq and Anthropic chat models via LangChain integrations.

## Table of Contents
- **Project Overview** — What this repo does
- **Files** — Key source files and responsibilities
- **Requirements** — Python packages used
- **Environment** — `.env` variables and defaults
- **Quickstart** — Create venv, install deps, run CLI and API
- **API** — `POST /workflow` usage and examples
- **Examples** — CLI demo usage
- **Troubleshooting** — Common errors and fixes
- **Contributing & License**

## Project Overview

The workflow is implemented in `backend.py` and exposed via a FastAPI app in `app.py`.

- `backend.py` implements the StateGraph-based workflow:
  - `writer` uses the Anthropic chat model to generate a beginner-friendly explanation.
  - `reviewer` uses a Groq-structured output model to return a decision (`PASS` or `REVISE`) and feedback.
  - `reviser` uses Anthropic again to update the draft based on reviewer feedback.
  - The graph loops writers → reviewer → reviser until reviewer returns `PASS` or `MAX_REVISIONS` is reached.

- `app.py` exposes a REST API (`POST /workflow`) that runs the workflow and returns the result.

## Files

- `backend.py` — The core workflow implementation and a small CLI `run_demo()` for manual testing.
- `app.py` — FastAPI application exposing a single endpoint: `POST /workflow`.
- `requirements.txt` — Pinning for Python dependencies used by the project.
- `example.ipynb` — Notebook examples / experiments (if present).

## Requirements

This project targets Python 3.8+. Install dependencies with `pip` (recommend inside a virtual environment). The pinned requirements are in `requirements.txt` and include:

```
langgraph==1.2.10
langchain==1.3.14
langchain-groq==1.1.3
langchain-anthropic==1.5.6
python-dotenv==1.2.2
pydantic==2.13.4
fastapi==0.141.1
uvicorn[standard]==0.52.1
jinja2==3.1.6
```

## Environment

Create a `.env` file in the project root with the following variables (examples shown):

```
GROQ_MODEL=llama-3.1-8b-instant
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
GROQ_API_KEY=your_groq_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MAX_REVISIONS=5
```

Notes:
- If a variable is not set, `backend.py` uses sensible defaults for the model names and `MAX_REVISIONS`.
- Never commit secrets — add `.env` to `.gitignore` if not already ignored.

## Quickstart (macOS / Linux)

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Add a `.env` with your API keys and optional overrides.

4. Run the small CLI demo:

```bash
python backend.py
```

5. Run the API server (starts FastAPI on port 8000):

```bash
python app.py
# or
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/docs` to view interactive API docs.

## API

Endpoint: `POST /workflow`

Request body (JSON):

```json
{
  "topic": "What is an AI agent?"
}
```

Example curl:

```bash
curl -X POST "http://127.0.0.1:8000/workflow" \
  -H "Content-Type: application/json" \
  -d '{"topic":"What is an AI agent?"}'
```

Response: A JSON object containing the `result` with keys including:
- `topic` — original topic
- `events` — chronological list of agent outputs (writer/reviewer/reviser)
- `final_answer` — the final drafted answer
- `final_decision` — `PASS` or last reviewer decision
- `total_revisions` — number of revision cycles used
- `provider` and `model` metadata

## CLI Demo

Run `python backend.py` and enter a topic when prompted. The demo will print agent events and the final answer to the console.

## Troubleshooting

- 404 for `/`: `app.py` currently defines only `POST /workflow`. Visit `/docs` for the FastAPI UI. To add a root route, edit `app.py` and add a `@app.get('/')` handler or a redirect to `/docs`.
- `KeyError: 'revision_count'` — the CLI demo was updated to print `total_revisions`; ensure you are running the latest `backend.py`.
- `git push origin main` fails — ensure a remote `origin` exists and that you have committed changes. Example:

```bash
git remote add origin https://github.com/your-user/your-repo.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

## Security & Secrets

- Keep API keys out of source control. Use `.env` or a secret manager in production.

## Contributing

Feel free to open issues or pull requests. Suggested enhancements:
- Add tests and CI
- Add a small web UI that calls the API
- Add caching or rate-limiting when hitting the model APIs

## License

This project is provided as-is; add your preferred license file if you plan to publish it publicly.

---

If you'd like, I can also:

- add a `@app.get('/')` redirect to `/docs` in `app.py` (so browsers hitting `/` see the docs),
- add `.venv` to `.gitignore`,
- create a sample `.env.example` file with sanitized variable names.

Tell me which of those you'd like next and I'll apply the changes.
